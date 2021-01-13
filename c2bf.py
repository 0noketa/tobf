from __future__ import annotations
# C(simple subset) to Brainfuck compiler

from typing import cast, Union, Tuple, List, Dict, Set
import sys
import io
import re
from bfa import Bfa

DEFAULT_STACK_SIZE = 16


class Function:
    def __init__(self, name: str, params: List[str], expr: Expr) -> None:
        self.name = name
        self.params = params
        self.expr = expr

        if self.expr.has_any(opr="return"):
            self.expr.move_branches_to_last(for_tail_jump=True)

    def is_pass(self) -> bool:
        """True if function returns arg0 and does nothing."""
        xs = self.expr.get_list()

        return (len(self.params) == 1 and len(xs) == 1
            and self.params[0] == xs[0].value)

funcs = dict()

def iscsymf(s: str) -> bool:
    return s.isalpha() or s == "_"

def iscsym(s: str) -> bool:
    return iscsymf(s) or s.isnumeric()

def define_function(name: str, params: List[str], expr: Expr):
    if name in funcs.keys():
        raise Exception(f"{name} was defined twice.")

    funcs[name] = Function(name, params, expr)

def get_function(name: str) -> Function:
    if name in funcs.keys():
        return funcs[name]
    else:
        raise Exception(f"function {name} is not defined")

def get_function_body(name: str) -> Expr:
    return get_function(name).expr

def get_function_params(name: str) -> List[str]:
    return get_function(name).params


def skip_escaped_char(s: str, i: int = 0) -> Tuple[int, int]:
    """returns (char_code, index)"""

    if len(s) == 0:
        return (0, 0)

    if s[i] != "\\":
        return (ord(s[i]), i + 1)
    else:
        if s[i + 1] == "x":
            return (int(s[i + 2:i + 4], 16), i + 4)
        elif s[i + 1] == "n":
            return (10, i + 1)
        elif s[i + 1] == "r":
            return (13, i + 1)
        elif s[i + 1] == "t":
            return (9, i + 1)
        else:
            return (ord(s[i + 1]), i + 1)

class Expr:
    def __init__(self, opr="<ERROR>", args: List[Expr] = [], value: str = None):
        self.opr = opr
        self.args = args
        self.value = value
        self.dependency = None

    def __str__(self, dpt=0) -> str:
        if self.opr == "<NIL>" or (self.opr in ["{", ";"] and len(self.args) == 0):
            return ""
        r = ""
        if self.opr in ["+", "-", "*", "/", "%", "=", "+=", "-=", "*=", "/=", "%=", "<", ">", "<=", ">=", "&&", "||", "!", "~"]:
            r += "(" + f" {self.opr} ".join([arg.__str__(dpt) for arg in self.args]) + ")"
        elif self.opr == ";":
            r += "".join(["  " * dpt + arg.__str__(dpt) + ";\n" for arg in self.args])
        elif self.opr == "{":
            r += "{" + "".join(["  " * dpt + arg.__str__(dpt) + "\n" for arg in self.args]) + "}"
        elif self.opr == "[":
            r += "[" + ",".join([arg.__str__(dpt) for arg in self.args]) + "]"
        elif self.opr == ",":
            r += "(" + ",".join([arg.__str__(dpt) for arg in self.args]) + ")"
        elif self.opr == ":":
            r += self.value + ":" + self.args[0].__str__(dpt)
        elif self.opr == "?":
            r += "(" + self.args[0].__str__(dpt) + " ? " + self.args[1].__str__(dpt) + " : " + self.args[1].__str__(dpt) + ")"
        elif self.opr == "if":
            r += "if (" + self.args[0].__str__(dpt) + ")\n" + self.args[1].__str__(dpt + 1)
            if len(self.args) > 2:
                r += "else\n" + self.args[2].__str__(dpt + 1)
        elif self.opr == "while":
            r += "while (" + self.args[0].__str__(dpt) + ") " + self.args[1].__str__(dpt)
        elif self.opr == "call":
            r += self.value + self.args[0].__str__(dpt)
        else:
            r += f"{self.opr}:{self.value}"
        
        return r

    def get_list(self) -> List[Expr]:
        self.flatten_args()

        if self.opr in ["[", "{"]:
            return self.args[0].get_list()
        elif self.opr in [",", ";"]:
            r = []

            for arg in self.args:
                if arg.opr == self.opr:
                    r.extend(arg.get_list())
                elif arg.opr != "<NIL>":
                    r.append(arg)

            return r
        elif self.opr == "<NIL>":
            return []
        else:
            return [self]

    @classmethod
    def get_name_in_vardecl(self, expr):
        if expr.opr == "<ID>":
            return expr.value
        elif expr.opr == "=":
            if expr.args[0].opr == "<ID>":
                return expr.args[0].value

        return "<ERROR>"

    @classmethod
    def get_names_in_vardecl(self, expr: Union[Expr, List[Expr]]) -> List[str]:
        names = expr if type(expr) == list else expr.get_list()
        names = list(map(Expr.get_name_in_vardecl, names))

        return [name for name in names if name != "<ERROR>"]

    @classmethod
    def get_expr_in_vardecl(self, expr):
        if expr.opr == "<ID>":
            return None
        elif expr.opr == "=":
            if expr.args[0].opr == "<ID>":
                return expr.args[1]

        return None

    def has_any_io(self) -> bool:
        b, vs, vsg, any_io = self.find_dependency()

        return any_io

    def has_any(self, opr: str = None, any_opr: Set[str] = None, expr: Expr = None, path=[]) -> bool:
        if self in path:
            raise Exception(f"{self}")

        for arg in self.args:
            if arg.has_any(opr=opr, expr=expr, path=path+[self]):
                return True
        
        if any_opr != None:
            return self.opr in any_opr
        if opr != None:
            return self.opr == opr
        if expr != None:
            return self == expr
        
        return False
    def has_only_tail_return(self) -> bool:
        if self.opr == "return":
            return True

        if len(self.args) == 0:
            return False

        if self.opr == "{" and len(self.args) == 1:
            return self.args[0].has_only_tail_return()

        if self.opr == ";":
            if self in self.args:
                raise Exception(f"(self)")

            for arg in self.args:
                if arg.has_only_tail_return():
                    return True

            return False

        if self.opr in ["if", "while"]:
            if self.args[0].has_any(opr="return"):
                raise Exception(f"condition contains any return")

        if self.opr == "while":
            for arg in self.args[1:]:
                if arg.has_any(opr="return"):
                    raise Exception(f"""[return] in [while] is not implemented""")

        if self.opr == "if":
            for arg in self.args[1:]:
                if not arg.has_only_tail_return():
                    return False
            
            return True

        return False

    @classmethod
    def copy_exprs(self, xs: List[Expr]) -> List[Expr]:
        r = []

        for x in xs:
            r.append(Expr(x.opr, Expr.copy_exprs(x.args), x.value))

        return r

    def move_branches_to_last(self, for_tail_jump=False):
        """for_tail_jump: moves only branches that contains any of [return], [break], [continue], [goto]\n
           deformates\n
           from:\n
           { if (a) { b; } else { c; } d; }\n
           to:\n
           { if (a) { b; d; } else { c; d; } }\n
           [this deformation] + [ignoring code after [return]] enables interruptive [return] without call/jump simulation.
        """

        if len(self.args) != len(set(self.args)):
            raise Exception(f"{self}")

        for arg in self.args:
            arg.move_branches_to_last(for_tail_jump)

        if self.opr == ";":
            for i in range(len(self.args)):
                arg = self.args[i]

                if arg.opr == "if":
                    branch = arg

                    if for_tail_jump:
                        any_jump = False

                        for arg in branch.args[1:]:
                            if arg.has_any(opr="return"):
                                any_jump = True

                                break

                        if not any_jump:
                            break

                    if len(branch.args) == 2:
                        branch.args.append(Expr(";", []))

                    for j in range(1, 3):
                        # for avoiding name confliction
                        branch_arg = Expr("{", [Expr(";", [branch.args[j]])])
                        branch.args[j] = Expr(";", [branch_arg] + Expr.copy_exprs(self.args[i + 1:]))
                        branch.args[j].move_branches_to_last(for_tail_jump)

                    self.args = self.args[:i + 1]
                    
                    break

    def forget_dependency(self):
        self.dependency = None

    def find_dependency(self, forget_old=False) -> Tuple[bool, List[str], List[str], bool]:
        """returns (\n
           // has any dependency such as sideefect\n
           result,\n
           // function call can ignore them if they are auto\n
           concerned_vars,\n
           // expressions can not determin that is var local or global? then expressions treats vars as local\n
           // determined by functions are here
           concerned_global_vars,\n
           // True if any I/O or asm exist
           any_io
           )
        """
        if forget_old:
            self.forget_dependency()

        if self.dependency != None:
            pass
        if self.opr == "<BUILTIN>":
            self.dependency = (True, [], [], False)
        elif self.opr in ["__c2bf_input", "__c2bf_print"]:
            vs = []
            vsg = []
            for arg in self.args:
                b, vs2, vsg2, any_io = arg.find_dependency()
                if b:
                    vs.extend(vs2)
                    vsg.extend(vsg2)

            self.dependency = (True, vs, vsg, True)
        elif self.opr in ["<NUM>", "<STR>", "<NIL>"]:
            self.dependency = (False, [], [], False)
        elif self.opr == "<ID>":
            self.dependency = (True, [self.value], [], False)
        else:
            deps0 = [arg.find_dependency() for arg in self.args]
            deps = zip(self.args, deps0)

            local_vars = []
            any_dep = False
            vs = []
            vsg = []
            any_io = False
            for arg, (b, vs2, vsg2, any_io2) in deps:
                if arg.opr == "var":
                    local_vars.extend(Expr.get_names_in_vardecl(arg))

                if b:
                    any_dep = True
                    vs.extend(map(vs2.remove, local_vars))
                    vsg.extend(vsg2)

                if any_io2:
                    any_io = True

            if self.opr == "call":
                f = get_function(self.value)

                b, vs2, vsg2, any_io2 = f.expr.find_dependency()

                vsg.extend(vsg2)
                vsg.extend(list(set(vs2) - set(f.params)))

                any_io = any_io or any_io2

            any_dep = any_dep or any_io

            self.dependency = (any_dep, list(set(vs)), list(set(vsg)), any_io)

        return self.dependency

    def is_string(self, template=[]) -> bool:
        if len(template) == 0:
            return True
        
        if self.opr != template[0]:
            return False
        
        if len(template) == 1:
            return True

        if len(self.args) != 1 and len(template) > 1:
            return False

        return self.args[0].is_string(template[1:])

    def flatten_args(self):
        for arg in self.args:
            arg.flatten_args()

        if self.opr == ";":
            self.args = [arg for arg in self.args if arg.opr != "<NIL>"]
            while True:
                if self.is_string([";", ";"]):
                    self.args = self.args[0].args
                    continue
                break

        if self.opr == "{":
            while True:
                if self.is_string(["{", "{"]):
                    self.args = self.args[0].args
                    continue
                break

        if self.opr in ["+", "*", ";", ","]:
            new_args: List[Expr] = []

            for arg in self.args:
                if arg.opr == self.opr:
                    new_args.extend(arg.args)
                elif arg.opr != "<NIL>":
                    new_args.append(arg)

            self.args = new_args

        if self.opr == ";":
            new_args = []

            for arg in self.args:
                new_args.append(arg)
                if arg.has_only_tail_return():
                    break

                self.args = new_args

    def calc_consts(self) -> Expr:
        self.flatten_args()

        self.args = [arg.calc_consts() for arg in self.args]

        self.flatten_args()

        b, vs, vsg, any_io = self.find_dependency()

        if self.opr == "call":
            f = get_function(self.value)
            f.expr = f.expr.calc_consts()

        if self.opr == "if":
            cond = self.args[0]

            if cond.opr == "<NUM>":
                if cond.value == 0:
                    if len(self.args) == 3:
                        return self.args[2]
                    else:
                        return Expr("<NIL>", [])
                else:
                    return self.args[1]

        if self.opr == "=" and len(self.args) == 2:
            lvalue = self.args[0].get_list()
            rvalue = self.args[1].get_list()

            if len(lvalue) == 1 and len(rvalue) == 1 and self.args[0].opr != "[" and self.args[1].opr != "[":
                lvalue = lvalue[0]
                rvalue = rvalue[0]

                if lvalue.opr == "<ID>" and rvalue.opr == "<ID>" and lvalue.value == rvalue.value:
                    return Expr("<NIL>", [])
            elif len(lvalue) == 1 and len(rvalue) > 0 and self.args[1].opr == ",":
                return Expr("=", [self.args[0], rvalue[-1]])
            else:
                raise Exception(f"unknown format of assignment ({self.args[0].opr}/{len(lvalue)}) = ({self.args[1].opr}/{len(rvalue)})")

        if self.opr == ";":
            new_args: List[Expr] = []
            last_lvalue = None

            for arg in self.args:
                if arg.opr == "=" and len(arg.args) == 2 and arg.args[0].opr == "<ID>":
                    lvalue = arg.args[0].value
                    rvalue = arg.args[1]

                    b, vs, vsg, any_io = rvalue.find_dependency()

                    if (lvalue in vs) or any_io:
                        pass
                    elif lvalue == last_lvalue:
                        old_assignment = new_args[-1]

                        if not old_assignment.args[1].has_any_io():
                            new_args.pop()

                    last_lvalue = lvalue
                else:
                    last_lvalue = None

                    if arg.opr == "<NIL>":
                        continue

                new_args.append(arg)

            self.args = new_args

        if self.opr in ["+", "*"]:
            s = 0 if self.opr == "+" else 1
            new_args: List[Expr] = []

            for arg in self.args:
                if arg.opr == "<NUM>":
                    if self.opr == "+":
                        s += arg.value
                    else:
                        s *= arg.value
                else:
                    new_args.append(arg)

            self.args = new_args

            if len(self.args) == 0:
                return Expr("<NUM>", [], s)
            elif len(self.args) == 1:
                if (self.opr == "+" and s == 0
                        or self.opr == "*" and s == 1):
                    return new_args[0]
                elif self.opr == "*" and s == 0:
                    b, vs, vsg, any_io = self.args[0].find_dependency()

                    if not b:
                        return Expr("<NUM>", [], s)

            self.args.append(Expr("<NUM>", [], s))

        return self

    def has_any_io(self) -> bool:
        if self.opr == "call":
            f = get_function(self.value)
            b, vs, vsg, any_io = f.expr.find_dependency()

            if any_io:
                return True

        return False

    def uses_outer_vars(self) -> bool:
        b, vs, vsg, any_io = self.find_dependency()

        return b

    def compile(self, stack_size=DEFAULT_STACK_SIZE, ptr=0, out=sys.stdout, inline=True, root: Expr = None):
        self.flatten_args()

        if self.opr == "{":
            if len(self.args) == 0:
                return

            out.write("{\n")

            xs = self.args[0].get_list()

            for i in range(len(xs)):
                x = xs[i]
            # for x in xs:
                x.compile(stack_size, ptr, out, inline)

                if x.has_any(opr="return") and x.has_only_tail_return():
                    break

            out.write("}\n")

            return

        if self.opr in [",", ";"]:
            for arg in self.args:
                arg.compile(stack_size, ptr, out, inline)

                if arg.has_any(opr="return") and arg.has_only_tail_return():
                    break

            return

        if self.opr in ["if", "while"] and self.args[0].has_any(opr="return"):
            raise Exception(f"[return] in condition")

        if self.opr == "if":
            if len(self.args) == 3:
                self.args[0].compile(stack_size, ptr + 2, out, inline)

                out.write(f"<stk{ptr + 1}>+\n")
                out.write(f"<stk{ptr + 2}>[[-] <stk{ptr + 1}>-\n")

                self.args[1].compile(stack_size, ptr + 2, out, inline)
                out.write(f"<stk{ptr + 2}>[- <stk{ptr}>+ ]\n")

                out.write("]\n")
                out.write(f"<stk{ptr + 1}>[-\n")

                self.args[2].compile(stack_size, ptr + 2, out, inline)
                out.write(f"<stk{ptr + 2}>[- <stk{ptr}>+ ]\n")

                out.write("]\n")
            else:
                out.write(f"<stk{ptr}> [-]\n")
                self.args[0].compile(stack_size, ptr, out, inline)

                if len(self.args) == 1:
                    out.write(f"<stk{ptr}> [-]\n")
                elif len(self.args) == 2:
                    out.write(f"<stk{ptr}> [[-]\n")

                    self.args[1].compile(stack_size, ptr + 1, out, inline)

                    out.write("]\n")

                    out.write(f"<stk{ptr + 1}>[- <stk{ptr}>+ ]\n")

            return

        if self.opr == "while":
            out.write(f"<stk{ptr + 1}> [-]\n")
            self.args[0].compile(stack_size, ptr + 1, out, inline)
            out.write(f"<stk{ptr + 1}> [\n")

            if self.args[1].has_any(opr="return"):
                raise Exception(f"[return] in [while] is not implemented")

            if len(self.args) > 1:
                self.args[1].compile(stack_size, ptr + 1, out, inline)

            out.write(f"<stk{ptr + 1}> [-]\n")

            self.args[0].compile(stack_size, ptr + 1, out, inline)

            out.write("]\n")

            return

        if self.opr == ":":
            self.args[0].compile(stack_size, ptr, out, inline)

            return

        if self.opr == "return":
            for arg in self.args:
                arg.compile(stack_size, ptr, out, inline)

            return

        if self.opr in ["==", "!="]:
            if self.opr == "==":
                out.write(f"<stk{ptr}>+\n")

            self.args[0].compile(stack_size, ptr + 1, out, inline)
            self.args[1].compile(stack_size, ptr + 2, out, inline)

            out.write(f"<stk{ptr + 2}>[- <stk{ptr + 1}>- ]\n")

            if self.opr == "==":
                out.write(f"<stk{ptr + 1}>[[-] <stk{ptr}>- ]\n")
            else:
                out.write(f"<stk{ptr + 1}>[[-] <stk{ptr}>+ ]\n")

            return

        if self.opr in [">", "<", ">=", "<="]:
            if self.opr.startswith(">"):
                self.args[0].compile(stack_size, ptr + 1, out, inline)
                self.args[1].compile(stack_size, ptr + 2, out, inline)
            else:
                self.args[1].compile(stack_size, ptr + 1, out, inline)
                self.args[0].compile(stack_size, ptr + 2, out, inline)

            if self.opr.endswith("="):
                out.write(f"<stk{ptr + 2}>[-\n")
                out.write(f"  <stk{ptr}>[-]\n")
                out.write(f"  <stk{ptr + 1}>[- <stk{ptr + 3}>+ <stk{ptr + 4}>+ ]\n")
                out.write(f"  <stk{ptr + 3}>[- <stk{ptr + 1}>+ ]\n")
                out.write(f"  <stk{ptr + 4}>[[-] <stk{ptr + 1}>- <stk{ptr}>+ ]\n")
                out.write(f"]\n")
            else:
                out.write(f"<stk{ptr + 1}>[-\n")
                out.write(f"  <stk{ptr}>+\n")
                out.write(f"  <stk{ptr + 2}>[- <stk{ptr + 3}>+ <stk{ptr + 4}>+ ]\n")
                out.write(f"  <stk{ptr + 3}>[- <stk{ptr + 2}>+ ]\n")
                out.write(f"  <stk{ptr + 4}>[[-] <stk{ptr + 2}>- <stk{ptr}>- ]\n")
                out.write(f"]\n")

            return

        if self.opr in ["=", "+=", "-="]:
            dsts = self.args[0].get_list()
            srcs = self.args[1].get_list()

            if len(dsts) != len(srcs):
                raise Exception(f"len(lvalues) != len(rvalues)")

            for i in range(len(dsts)):
                src = srcs[i]

                out.write(f"<stk{ptr + i}>[-]\n")
                src.compile(stack_size, ptr + i, out, inline)

            for i in range(len(dsts)):
                dst = dsts[i]

                if self.opr == "=":
                    out.write(f"<{dst.value}>[-]\n")

                if self.opr == "-=":
                    out.write(f"<stk{ptr + i}>[- <{dst.value}>- ]\n")
                else:
                    out.write(f"<stk{ptr + i}>[- <{dst.value}>+ ]\n")


            return

        if self.opr in ["+", "-"]:
            self.args[0].compile(stack_size, ptr, out, inline)
            self.args[1].compile(stack_size, ptr + 1, out, inline)

            out.write(f"<stk{ptr + 1}>[- <stk{ptr}>{self.opr} ]\n")

            return

        if self.opr == "*":
            self.args[0].compile(stack_size, ptr + 2, out, inline)
            self.args[1].compile(stack_size, ptr + 3, out, inline)

            out.write(f"<stk{ptr + 3}>[-\n")
            out.write(f"  <stk{ptr + 2}>[- <stk{ptr + 1}>+ <stk{ptr}>+ ]\n")
            out.write(f"  <stk{ptr + 1}>[- <stk{ptr + 2}>+ ]\n")
            out.write(f"] <stk{ptr + 2}>[-]\n")

            return

        if self.opr == "!":
            out.write(f"<stk{ptr}>+\n")

            self.args[0].compile(stack_size, ptr + 1, out, inline)

            out.write(f"<stk{ptr + 1}>[[-] <stk{ptr}>- ]\n")

            return

        if self.opr == "~":
            out.write(f"<stk{ptr}>-\n")

            self.args[0].compile(stack_size, ptr + 1, out, inline)

            out.write(f"<stk{ptr + 1}>[- <stk{ptr}>- ]\n")

            return

        if self.opr == "__c2bf_input":
            if len(self.args) == 0:
                out.write(f"<stk{ptr}>,\n")

                return

            for arg in self.args:
                if arg.opr != "<ID>":
                    raise Exception(f"not implemented type of lvalue")

                out.write(f"<{arg.value}>,")

            return

        if self.opr == "__c2bf_print":
            exprs = self.args[0].get_list()

            for expr in exprs:
                out.write(f"<stk{ptr}>[-]\n")
                expr.compile(stack_size, ptr, out, inline)
                out.write(f"<stk{ptr}>.\n")

            return

        if self.opr in [
                "__c2bf_move", "__c2bf_moveadd", "__c2bf_movesub",
                "__c2bf_copy", "__c2bf_copyadd", "__c2bf_copysub"]:
            exprs = self.args[0].get_list()

            src_expr = exprs[0]
            dst_exprs = exprs[1:]
            inc = "-" if self.opr.endswith("sub") else "+"

            if self.opr in ["__c2bf_move", "__c2bf_copy"]:
                for expr in dst_exprs:
                    out.write(f"<{expr.value}>[-]\n")

            if self.opr.startswith("__c2bf_move"):
                if src_expr.opr == "<ID>":
                    out.write(f"<stk{src_expr.value}>[-\n")
                else:
                    src_expr.compile(stack_size, ptr, out, inline)
                    out.write(f"<stk{ptr}>[-\n")
            else:
                src_expr.compile(stack_size, ptr + 1, out, inline)
                out.write(f"<stk{ptr + 1}>[-\n")
                out.write(f"  <stk{ptr}>+\n")

            for expr in dst_exprs:
                out.write(f"  <{expr.value}>{inc}\n")

            out.write(f"]\n")

            return

        if self.opr == "var":
            vs = self.args[0].get_list()
            names = list(map(Expr.get_name_in_vardecl, vs))
            exprs = list(map(Expr.get_expr_in_vardecl, vs))

            out.write(" ".join([f"({name})" for name in names]) + "\n")

            for i in range(len(exprs)):
                name = names[i]
                expr = exprs[i]

                if expr == None:
                    continue

                out.write(f"<stk{ptr}>[-]\n")
                expr.compile(stack_size, ptr, out, inline)

                out.write(f"<stk{ptr}>[- <{name}>+ ]\n")

            # currently "var"  returns just one variable
            out.write(f"<stk{ptr}>[-]\n")
            out.write(f"<{names[0]}>[- <stk{ptr}>+ <stk{ptr + 1}>+ ]\n")
            out.write(f"<stk{ptr + 1}>[- <{names[0]}>+ ]\n")

            return

        if self.opr == "call":
            args = self.args[0].get_list()
            params = get_function_params(self.value)

            f = get_function(self.value)

            # simply replaces with arg
            if f.is_pass():
                args[0].compile(stack_size, ptr, out, inline)

                return

            out.write("{\n")

            for i in range(len(args)):
                arg = args[i]
                param = params[i]

                out.write(f"<stk{ptr}>[-]\n")
                arg.compile(stack_size, ptr, out, inline)

                out.write(f"({param})\n")
                out.write(f"<stk{ptr}>[- <{param}>+ ]\n")

            expr = f.expr
            expr.compile(stack_size, ptr, out, inline, root=expr)

            for i in range(len(args)):
                param = params[i]
                out.write(f"<{param}>[-]\n")

            out.write("}\n")

            return

        if self.opr == "<ID>":
            out.write(f"<{self.value}>[- <stk{ptr}>+ <stk{ptr + 1}>+ ]\n")
            out.write(f"<stk{ptr + 1}>[- <{self.value}>+ ]\n")

            return

        if self.opr == "<NUM>":
            n = int(self.value)

            if n > 0:
                out.write(f"<stk{ptr}>" + "+" * n + "\n")

            return

        if self.opr == "<BUILTIN>":
            out.write(f"<stk{ptr}> {self.value}\n")

            return

def next_tkn(src: str, i: int) -> int:
    pairs = {
        "(": ")",
        "[": "]",
        "{": "}"
    }

    while i < len(src) and src[i].isspace():
        i += 1

    if i >= len(src):
        return len(src)

    if src[i] in pairs.keys():
        left = src[i]
        right = pairs[left]
        d = 0

        for j in range(i + 1, len(src)):
            if src[j] == left:
                d += 1
            elif src[j] == right:
                if d == 0:
                    return j + 1
                else:
                    d -= 1

    if iscsymf(src[i]):
        for j in range(i + 1, len(src)):
            if not (iscsym(src[j])):
                return j
    elif src[i] == "0" and i + 2 < len(src) and src[i + 1] in "box":
        cset = "0123456789ABCDEF"

        if src[i + 1] == "b":
            cset = cset[:2]
        elif src[i + 1] == "o":
            cset = cset[:8]

        for j in range(i + 2, len(src)):
            if not (src[j] in cset):
                return j
    elif src[i].isnumeric():
        for j in range(i + 1, len(src)):
            if not src[j].isnumeric():
                return j
    elif src[i] in ["'", '"']:
        qt = src[i]
        j = i + 1
        esc = False
        while j < len(src):
            if esc:
                esc = False
            elif src[j] == "\\":
                esc = True
            elif src[j] == qt:
                return j + 1

            j = j + 1
    elif (len(src) >= i + 2
        and src[i:i + 2] in [
            "||", "&&",
            "==", "!=", ">=", "<=",
            "+=", "-=", "*=", "/=", "%=",
            "++", "--"]):
        return i + 2
    else:
        return i + 1

    return len(src)

def lex(src: str) -> List[str]:
    """postscript-like lex. every bracket-ed block as quoted chunk."""
    tkns = []
    src = src.strip()
    i = 0

    while i < len(src):
        j = next_tkn(src, i)
        tkns.append(src[i:j].strip())

        i = j

    # preprocess for internal language that requires ";" after "}" and does not accept ";" before "else".
    i = 1
    while i < len(tkns) - 1:
        # enables "if (abc) def; else ghi;"
        if tkns[i] == "else" and tkns[i - 1] == ";":
            tkns = tkns[:i - 1] + tkns[i:]
        elif tkns[i].startswith("{"):
            if tkns[i - 1] == "do":
                pass
            elif tkns[i + 1] == "else":
                pass
            else:
                tkns = tkns[:i + 1] + [";"] + tkns[i + 1:]

        i += 1

    return tkns

def get_tkn_index(tkns: list, tkn: str, i: int = 0) -> int:
    try:
        return tkns.index(tkn)
    except Exception:
        return len(tkns)

def parse(src):
    if type(src) == list:
        src = " ".join(src)

    tkns = lex(src)

    if len(tkns) == 0:
        return Expr("<NIL>", [])

    if len(tkns) == 1:
        tkn = tkns[0].strip()

        if tkn.startswith("__c2bf_"):
            return Expr(tkn, [])
        elif tkn == "return":
            return Expr("return", [])
        elif tkn.startswith("("):
            tkn = tkn[1:]

            if tkn.endswith(")"):
                tkn = tkn[:-1]

            return parse(tkn)
        elif tkn.startswith("["):
            tkn = tkn[1:]

            if tkn.endswith("]"):
                tkn = tkn[:-1]

            return Expr("[", [parse(tkn)])
        elif tkn.startswith("{"):
            tkn = tkn[1:]

            if tkn.endswith("}"):
                tkn = tkn[:-1]

            return Expr("{", [parse(tkn)])
        elif iscsymf(tkn[0]):
            return Expr("<ID>", [], tkn)
        elif tkn[0] == "'":
            c, _ = skip_escaped_char(tkn, 1)
            return Expr("<NUM>", [], c)
        elif tkn[0] == '"':
            return Expr("<STR>", [], tkn[1:-1])
        elif tkn[0] == "0" and len(tkn) > 2 and tkn[1] in "box":
            if tkn[1] == "b":
                base = 2
            elif tkn[1] == "o":
                base = 8
            else:
                base = 16

            return Expr("<NUM>", [], int(tkn[2:], base))
        elif tkn[0] == "0":
            return Expr("<NUM>", [], int(tkn, 8))
        elif tkn.isnumeric():
            return Expr("<NUM>", [], int(tkn))
        else:
            return Expr("<ERROR>", [], tkn)

    idx = get_tkn_index(tkns, ";", 0)

    if idx < len(tkns):
        left = parse(tkns[:idx])
        right = parse(tkns[idx + 1:])

        if left.opr == ";" and right.opr == ";":
            return Expr(";", left.args + right.args)
        else:
            return Expr(";", [left, right])

    if iscsymf(tkns[0][0]) and tkns[1] == ":":
        return Expr(":", [parse(tkns[1:])], tkns[0])
        
    if tkns[0] in ["if", "while"] and len(tkns) > 1 and tkns[1].strip().startswith("("):
        if len(tkns) > 2:
            else_idx = get_tkn_index(tkns, "else", 2)

            if else_idx < len(tkns):
                return Expr(tkns[0], [parse(tkns[1]), parse(tkns[2:else_idx]), parse(tkns[else_idx + 1:])])
            else:
                return Expr(tkns[0], [parse(tkns[1]), parse(tkns[2:])])
        else:
            return Expr(tkns[0], [parse(tkns[1]), parse(tkns[2:])])

    if tkns[0] in ["int", "char"]:
        return Expr("var", [parse(tkns[1:])], tkns[0])

    if tkns[0] in [
            "return", "goto", "break", "continue",
            "__c2bf_input", "__c2bf_print", "__c2bf_debug",
            "__c2bf_move", "__c2bf_moveadd", "__c2bf_movesub",
            "__c2bf_copy", "__c2bf_copyadd", "__c2bf_copysub"]:
        return Expr(tkns[0], [parse(tkns[1:])])

    if iscsymf(tkns[0][0]) and len(tkns) > 2 and tkns[1] == ":":
        return Expr(":", [parse(tkns[2:])], tkns[0])

    idx = get_tkn_index(tkns, ",", 0)

    if idx < len(tkns):
        left = parse(tkns[:idx])
        right = parse(tkns[idx + 1:])

        if left.opr == "," and right.opr == ",":
            return Expr(",", left.args + right.args)
        else:
            return Expr(",", [left, right])

    idx_aasg = get_tkn_index(tkns, "+=", 0)
    idx_sasg = get_tkn_index(tkns, "-=", 0)
    idx_asg = get_tkn_index(tkns, "=", 0)
    idx = min([idx_aasg, idx_sasg, idx_asg])

    if idx < len(tkns):
        opr = ("+=" if idx == idx_aasg
            else "-=" if idx == idx_sasg
            else "=" if idx == idx_asg
            else "<ERROR>")

        return Expr(opr, [parse(tkns[:idx]), parse(tkns[idx + 1:])])

    idx_eq = get_tkn_index(tkns, "==", 0)
    idx_neq = get_tkn_index(tkns, "!=", 0)
    idx_gt = get_tkn_index(tkns, ">", 0)
    idx_lt = get_tkn_index(tkns, "<", 0)
    idx_gte = get_tkn_index(tkns, ">=", 0)
    idx_lte = get_tkn_index(tkns, "<=", 0)
    idx = min([idx_eq, idx_neq, idx_gt, idx_lt, idx_gte, idx_lte])

    if idx < len(tkns):
        opr = ("==" if idx == idx_eq
            else "!=" if idx == idx_neq
            else ">" if idx == idx_gt
            else "<" if idx == idx_lt
            else ">=" if idx == idx_gte
            else "<=")

        return Expr(opr, [parse(tkns[:idx]), parse(tkns[idx + 1:])])

    idx_add = get_tkn_index(tkns, "+", 0)
    idx_sub = get_tkn_index(tkns, "-", 0)
    idx = min(idx_add, idx_sub)

    if idx < len(tkns):
        opr = "+" if idx_add < idx_sub else "-"

        return Expr(opr, [parse(tkns[:idx]), parse(tkns[idx + 1:])])

    idx_mul = get_tkn_index(tkns, "*", 0)
    idx_div = get_tkn_index(tkns, "/", 0)
    idx = min(idx_mul, idx_div)

    if idx < len(tkns):
        opr = "*" if idx_mul < idx_div else "/"

        return Expr(opr, [parse(tkns[:idx]), parse(tkns[idx + 1:])])

    if tkns[0] in ["!", "~"]:
        opr = tkns[0]

        return Expr(opr, [parse(tkns[1:])])

    if iscsymf(tkns[0][0]) and len(tkns) > 1 and tkns[1].strip().startswith("("):
        if len(tkns) > 2:
            define_function(tkns[0],
                Expr.get_names_in_vardecl(parse(tkns[1])),
                parse(tkns[2:]))

            return Expr("<NIL>", [])
        else:
            arg = parse(tkns[1:])
            args = arg.get_list()

            if (tkns[0] == "puts" and len(args) == 1
                        or tkns[0] == "fputs" and len(args) == 2)  and args[0].opr == "<STR>":
                s = args[0].value
                args = []

                i = 0
                while i < len(s):
                    c, i = skip_escaped_char(s, i)

                    args.append(c)

                if tkns[0] == "puts":
                    x = Expr("<NUM>", [], 10)
                else:
                    x = Expr("<NUM>", [], args[-1])
                    args = args[:-1]

                for arg in reversed(args):
                    x = Expr(",", [Expr("<NUM>", [], arg), x])

                return Expr("__c2bf_print", [x], tkns[0])
            else:
                return Expr("call", [arg], tkns[0])

    return Expr("<ERROR>", [], "".join(tkns))




def is_cpp(tkns):
    return len(tkns) >= 1 and tkns[0].startswith("#")

def load_cpped(filename: str, defined_names: Dict[str, str]={}, shared_vars=[]) -> List[str]:
    """returns preprocessed source"""

    cpp_ptn = re.compile("""\s*#\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*(.*|)""")
    define_ptn = re.compile("""\s*([a-zA-Z_][a-zA-Z0-9_]*)(?:\((\s*[a-zA-Z_][a-zA-Z0-9_]*(?:\s*,\s*[a-zA-Z_][a-zA-Z0-9_]*)*)\s*\)|)(.*)""")
    include_ptn = re.compile("""\s*(?:<([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)>|)(?:"([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)"|)""")

    src = ""
    with io.open(filename) as f:
        src = f.read()

    src = src.split("\n")
    src = list(filter(len, map(str.strip, src)))

    skipping = False
    skipping_depth = 0
    i = 0
    while i < len(src):
        line = src[i]

        if "//" in line:
            line = line[:line.index("//")]

        line = line.strip()

        if line == "":
            src = src[:i] + src[i + 1:]
            continue

        m = cpp_ptn.match(line)
        if m == None:
            if skipping:
                src = src[:i] + src[i + 1:]
            else:
                i = i + 1

            continue

        cpp_name, cpp_body = m.groups()
        src = src[:i] + src[i + 1:]

        if cpp_name == "endif":
            if skipping_depth == 0:
                skipping = False
            else:
                skipping_depth -= 1

                if skipping_depth < 0:
                    raise Exception(f"too many #endif")

            continue

        if cpp_name in ["else", "elif", "elsif"]:
            if skipping_depth == 0:
                skipping = not skipping

                if cpp_name in ["elif", "elsif"]:
                    cpp_name = "if"
                else:
                    # "#else"
                    continue
            else:
                continue

        if cpp_name in ["ifdef", "ifndef"]:
            if skipping:
                skipping_depth += 1
            else:
                macro_name = cpp_body.strip()

                if cpp_name == "ifdef":
                    skipping = not (macro_name in defined_names.keys())
                else:
                    skipping = macro_name in defined_names.keys()


            continue

        if skipping:
            continue

        if cpp_name == "pragma":
            args = list(filter(len, map(str.strip, cpp_body.split())))

            if len(args) == 0:
                continue

            if args[0] == "bf_shared":
                for name in args[1:]:
                    if name in shared_vars:
                        raise Exception(f"bf-shared variable {name} was declared twice")

                    shared_vars.append(name)

            continue

        if cpp_name == "include":
            m2 = include_ptn.match(cpp_body)

            if m2 == None:
                raise Exception(f"[include] uses unknown syntax")

            global_file, local_file = m2.groups()

            if global_file != None:

                sub = load_cpped(global_file, defined_names, shared_vars)
                src = src[:i] + sub + src[i:]

                i = i + len(sub)

                continue

            if local_file != None:
                sub = load_cpped(local_file, defined_names, shared_vars)
                src = src[:i] + sub + src[i:]

                i = i + len(sub)

                continue

            raise Exception("[include] uses unknown syntax")

        if cpp_name == "define":
            m2 = define_ptn.match(cpp_body)

            if m2 == None:
                raise Exception(f"[define] uses unknown syntax")

            gs2 = m2.groups()
            macro_name = gs2[0]
            macro_params = gs2[1] if gs2[1] != None else ""
            macro_body = gs2[2] if gs2[2] != None else ""

            macro_params = list(filter(len, map(str.strip, macro_params.split(","))))

            if len(macro_params) > 0:
                sys.stderr.write(f"# {macro_name}/{len(macro_params)} was defined. but define for macro function is not implemented.")

            if macro_name in defined_names.keys():
                sys.stderr.write(f"# {macro_name} was defined twire")

            defined_names[macro_name] = macro_body.strip()

            continue

        if cpp_name == "undef":
            macro_name = cpp_body.strip()

            if macro_name in defined_names.keys():
                del defined_names[macro_name]

            continue

    return src




class C2bf:
    def __init__(self, file_name: str, defined_macros: Dict[str, str] = {}, shared_vars: List[str] = [], stack_size=DEFAULT_STACK_SIZE) -> None:
        self.src = ""
        self.stack_size = stack_size
        self.shared_vars = shared_vars

        self.src = C2bf.preprocess_file(file_name, defined_macros, self.shared_vars)

    @classmethod
    def preprocess_file(self, file_name, defined_macros: Dict[str, str] = {}, shared_vars: List[str] = {}) -> str:
        defined_macros.update({
            "__C2BF__": ""
        })

        src0 = load_cpped(file_name, defined_names=defined_macros, shared_vars=shared_vars)

        return "\n".join(src0)

    def compile_to_bfa(self, startup="{main()}", optimization_level=0) -> Bfa:
        # startup
        src = self.src + startup

        x = parse(src)
        bfa_src_out = io.StringIO(newline="\n")

        if optimization_level == 1:
            x = x.calc_consts()

        x.compile(self.stack_size, out=bfa_src_out, inline=True, root=x)

        bfa_src = (" ".join([f"({v})" for v in self.shared_vars]) + "\n"
            + " ".join([f"(stk{i})" for i in range(self.stack_size)]) + "\n"
            + bfa_src_out.getvalue())

        bfa_src_in = io.StringIO(bfa_src)
        bfa = Bfa.from_file(bfa_src_in)

        return bfa

    def compile_to_bf(self, startup="{main()}", optimization_level=0) -> Tuple[str, int]:
        """returns memory_size to run safe"""
        bfa = self.compile_to_bfa(startup, optimization_level=optimization_level)

        dst_out = io.StringIO()
        memory_size = bfa.compile(dst_out)

        return [dst_out.getvalue(), memory_size]

    @classmethod
    def compile_file_to_bfa(self, file_name:str, defined_macros: Dict[str, str] = {}, shared_vars: List[str] = [], stack_size=DEFAULT_STACK_SIZE, startup="{main()}", optimization_level=0) -> Bfa:
        c = C2bf(file_name, defined_macros=defined_macros, shared_vars=shared_vars, stack_size=stack_size)

        return c.compile_to_bfa(startup, optimization_level=optimization_level)

    @classmethod
    def compile_file_to_bf(self, file_name:str, defined_macros: Dict[str, str] = {}, shared_vars: List[str] = [], stack_size=DEFAULT_STACK_SIZE, startup="{main()}", optimization_level=0) -> Tuple[str, int]:
        c = C2bf(file_name, defined_macros=defined_macros, shared_vars=shared_vars, stack_size=stack_size)

        return c.compile_to_bf(startup, optimization_level=optimization_level)


def main(argv):
    optimization_level = 0
    stack_size = DEFAULT_STACK_SIZE
    defined_macros = {}
    include_dirs = []
    preprocess_only = False
    generates_bfa = False
    file_names = []
    i = 1

    for i in range(1, len(argv)):
        if not (argv[i][0] in "-/"):
            file_names.append(argv[i])

            continue

        opt_name = argv[i][1:]
        opt_arg = ""

        for sep in [":", "="]:
            if sep in opt_name:
                sep_idx = opt_name.index(sep)
                opt_arg = opt_name[sep_idx + 1:]
                opt_name = opt_name[:sep_idx]

        if opt_name == "":
            continue

        if opt_name.startswith("O"):
            optimization_level = int(opt_name[1:])

            continue

        if opt_name.startswith("D"):
            defined_macros[opt_name[1:]] = opt_arg

            continue

        if opt_name.startswith("I"):
            include_dirs.append(opt_name[1:])

            continue

        if opt_name == "E":
            preprocess_only = True

            continue

        if opt_name == "bfa":
            generates_bfa = True

            continue

        if opt_name == "stack_size":
            if len(argv) > 2:
                stack_size = max(1, abs(int(opt_arg)) & 0xFFFF)
            else:
                stack_size = DEFAULT_STACK_SIZE

            continue

    if len(file_names) == 0 or not file_names[0].endswith(".c"):
        print(f"python {argv[0]} [options] src")
        print("  -Onum           optimization level")
        print("  -Dname[=value]  define macro")
        print("  -Idir           add include directory")
        print("  -E              preprocess only")
        print("  -stack_size=n   change stack size")
        print("  -bfa            generates BFA code")
        print("  (this program accepts /name:value styled options)")

        return 0

    # try:
    if True:
        if preprocess_only:
            c2 = C2bf.preprocess_file(file_names[0], defined_macros=defined_macros)

            with io.open(file_names[0] + ".i", "w") as f:
                f.write(c2)
        elif generates_bfa:
            bfa = C2bf.compile_file_to_bfa(file_names[0],
                defined_macros=defined_macros,
                stack_size=stack_size,
                optimization_level=optimization_level)

            with io.open(file_names[0] + ".bfa", "w") as f:
                f.write(bfa.src)
        else:
            bf, memory_size = C2bf.compile_file_to_bf(file_names[0],
                defined_macros=defined_macros,
                stack_size=stack_size,
                optimization_level=optimization_level)

            sys.stderr.write(f"this program uses {memory_size} cells.\n")

            with io.open(file_names[0] + ".bf", "w") as f:
                f.write(bf)
    # except Exception as e:
    #     sys.stdout.write(str(e))

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))

