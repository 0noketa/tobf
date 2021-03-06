
# a to-bf compiler for small programs
# abi:
#   pointer: always points address 0 with value 0 at the beggining and the end
#   memory: temporary, ...vars, dynamic_memory
#     area of vars has no hidden workspace except address 0. can be used like common-vars in old fortran.
#     dynamic_memory is optional. nothing exists until initialized manually. and can be cleaned up.
# linking(not yet):
#   sequencial or macro-injection.
#   linkers are required to read only first lines of every source.
# syntax:
#   program: var_decl "\n" instructions "end" "\n"
#   var_decl: id (" " val)*
#   instructions: (id (" " val)* "\n")*
#   val: digits | "'" | "'" char | id
# instructions:
# bool io_var ...out_vars
#   if io_var is not 0, io_var becomes to 1. and copies io_var to out_vars.
# not io_var ...out_vars
# bool_not io_var ...out_vars
#   if io_var is not 0, io_var becomes to 0. or else to 1. besides copies io_var to out_vars.
# set imm ...out_vars_with_sign
#   every destination can starts with "+" or "-", they means add or sub instead of set
#   aliases_with_inplicit_signs:
#     add imm ...out_vars
#     sub imm ...out_vars
#     clear ...out_vars
#       imm as 0 and no sign
#     inc ...out_vars
#       imm as 1 and sign as "+"
#     dec ...out_vars
#       imm as 1 and sign as "-"
# eq imm ...out_vars
# moveeq in_var ...out_vars
# copyeq in_var ...out_vars
#   similer to eq
# and in_var out_var
# nand in_var out_var
# or in_var ...out_vars
# nor in_var ...out_vars
#   similer to eq. breaks in_var
# move in_var ...out_vars_with_sign
#   in_var becomes to 0
#   aliases_with_implicit_signs:
#     moveadd in_var ...out_vars
#     movesub in_var ...out_vars
# copy in_var ...out_vars_with_sign
#   aliases_with_inplicit_signs:
#     copyadd in_var ...out_vars
#     copysub in_var ...out_vars
# resb imm
#   declare size of static memory. default=number of vars. works when no subsystem was loaded.
#   will be replaced.
# tmp addr
#   changes address of implicit it. not implemented.
# load subsystem_name ...args
#   loads subsystem after reserved vars and subsystems already loaded
# loadas alias_name subsystem_name ...args
#   loads and names as alias_name
# unload subsysten_name
#   unloads a subsystem. subsystem_name can be alias_name
# subsystem_name:any_name ...args
#   invokes a feature of subsystem
# if cond_var
#   cond_var is avarable until endif
# endif cond_var
#   like "next i" in basic. this rule simplifies compiler.
#   currently compiler disallows no cond_var instructions.
#   breaks cond_var
# ifelse cond_var work_var
#   work_var carries run_else flag
#   cond_var is avarable until "else"
# else cond_var work_var
# endifelse cond_var work_var
# ifgt var0 var1 tmp_var
#   skips block if var1 > var0.
#   breaks vars. no variable in args can not be used in this bleck.
# endifgt var0 var1 tmp_var
#   breaks vars.
# ifnotin cond_var ...imms
# endifnotin cond_var ...imms
#   skips block if any immediate equals to cond_var.
#   breaks cond_var
# while cond_var
# endwhile cond_var
# every ins0 ...args0 | ins1 ...args1 | ... <- ...sub_args0 | ...sub_args1 | ...
# ! ins0 ...args0 | ins1 ...args1 | ... <- ...sub_args0 | ...sub_args1 | ...
#   invoke every instruction with args + sub_args
# !!
#   remove all macro. no purpose.
# !! name ...
#   define macro. macro is avairable as $!name in args of !
# bf src
#   inline brainfuck.
# include_bf file_name mem_size
#   injects brainfuck code from file. included code should not leave changed pointer.
#   can be used to include something such as output of very smart txt2bf.
#   maybe some compiler generates includable code.
# include_bf file_name mem_size ...io_vars
#   before bf, copies io_vars to bf_memory_area.
#   after bf, moves bf_memory_area to variables.
# include_bf file_name
#   bf code uses only 1 byte. useless.
# include_bf file_name io_var
#   runs at selected var. useless.
# include_c file_name stack_size function_name ...in_vars out_var
#   uses C function.
# end
#   can not be omitted

import io
from base import Mainsystem, SubsystemBase, InstructionBase, split, split_list, separate_sign, calc_small_pair, MacroProc
from bfa import Bfa
from c2bf import C2bf


class Tobf(Mainsystem):
    def __init__(self):
        self._vars = []
        self._reserved = -1
        self._subsystems = {}
        self._loaded_subsystems = {}
        self._idt = 0
        self._size = 0
        self._newest_subsystem_name = ""
        self._concatnative_macros = {}

    def reserve(self, size):
        """manually selects size of variable area\n
        can be reselected when no subsystem was loaded."""

        if len(self._loaded_subsystems.keys()) > 0:
            return False

        self._reserved = size

        return True

    def install_subsystem(self, subsystem: SubsystemBase):
        self._subsystems[subsystem.name()] = subsystem

    # maybe broken. do not unload if subsystem is not placed at the last.
    # and currently no subsystem can calculate its size without assigned baseaddress.
    def offsetof_next_subsystem(self) -> int:
        if len(self._loaded_subsystems) == 0:
            return self._reserved if self._reserved != -1 else len(self._vars) + 1

        next = 0
        for key in self._loaded_subsystems.keys():
            sub = self._loaded_subsystems[key]
            next2 = sub.offset() + sub.size()

            if next < next2:
                next = next2

        return next

    def offsetof_subsystem(self, alias:str) -> int:
        subsystem = self.subsystem_by_alias(alias)

        return subsystem.offset()

    def subsystem_by_name(self, name) -> SubsystemBase:
        """returns a subsystem"""
        if not (name in self._subsystems.keys()):
            raise Exception(f"subsystem {name} is not installed")

        return self._subsystems[name]

    def subsystem_by_alias(self, name) -> SubsystemBase:
        """returns an instance of subsystem"""

        if name == "" and self._newest_subsystem_name != "":
            name = self._newest_subsystem_name

        if not (name in self._loaded_subsystems.keys()):
            raise Exception(f"subsystem aliased as {name} is not loaded")

        return self._loaded_subsystems[name]

    def put_load(self, name:str, args:list, alias=""):
        if not (name in self._subsystems.keys()):
            raise Exception(f"subsystem {name} is not installed")

        if alias == "":
            alias = name

        if alias in self._loaded_subsystems.keys():
            raise Exception(f"subsystem aliased as {alias} is already loaded.")

        subsystem_base = self.subsystem_by_name(name)
        subsystem = subsystem_base.copy(alias)
        subsystem.load(self.offsetof_next_subsystem(), self)

        self._loaded_subsystems[alias] = subsystem
        self._newest_subsystem_name = alias

        if subsystem.has_ins("init", args):
            subsystem.put("init", args)

        return True

    def put_unload(self, name: str, args: list) -> bool:
        subsystem = self.subsystem_by_alias(name)

        if subsystem == None:
            return False

        if subsystem.has_ins("clean", args):
            subsystem.put("clean", args)

        self._loaded_subsystems.pop(name)

        self._newest_subsystem_name = ""

        return True
    def put(self, s):
        print("  " * self._idt + s)

    def uplevel(self):
        self._idt += 1
    def downlevel(self):
        self._idt = self._idt - 1 if self._idt > 0 else 0

    def begin_global(self, addr:int):
        self.put(">" * int(addr))

    def end_global(self, addr:int):
        self.put("<" * int(addr))

    def with_addr(self, addr:int, s:str):
        self.begin_global(addr)
        self.put(s)
        self.end_global(addr)

    def put_at(self, addr:int, s:str):
        self.with_addr(addr, s)

    def put_with_every(self, addrs:list, s:str):
        used = []
        for addr in addrs:
            if addr in used:
                continue

            used.append(addr)
            self.with_addr(addr, s)

    def has_var(self, name:str) -> bool:
        return name in self._vars
    def addressof_var(self, name:str) -> int:
        return int(self._vars.index(name) + 1)

    def is_var(self, value) -> bool:
        if type(value) != str:
            return False
        elif self.is_signed(value):
            sign, value2 = separate_sign(value)

            return self.is_var(value2)
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.subsystem_by_alias(sub_name)

            return sub.has_var(name)
        else:
            return self.has_var(value)

    def is_sub(self, value, typ="") -> bool:
        if not (value in self._loaded_subsystems.keys()):
            return False

        if typ == "":
            return True

        sub = self.subsystem_by_alias(value)

        return sub.basename() == typ

    def addressof(self, value) -> int:
        if type(value) != str:
            return value
        elif self.is_signed(value):
            sign, value2 = separate_sign(value)
            return self.addressof(value2)
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.subsystem_by_alias(sub_name)

            return sub.addressof(name)
        elif self.has_var(value):
            return self.addressof_var(value)
        elif value.isdigit():
            return int(value)
        else:
            raise Exception(f"failed to get address of {value}")

    def byteof(self, value, byte=False) -> int:
        return self.valueof(value, byte=True)

    def valueof(self, value, byte=False) -> int:
        if type(value) != str:
            return value
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.subsystem_by_alias(sub_name)

            return sub.valueof(name)
        elif self.is_val(value):
            return super().valueof(value)
        else:
            return value

    def variablesof(self, name: str) -> list:
        if self.is_sub(name):
            return self.subsystem_by_alias(name)._vars.copy()

    def begin(self, i):
        self.put(">" * int(i + 1))

    def end(self, i):
        self.put("<" * int(i + 1))

    def with_var(self, i, s):
        self.begin(i)
        self.put(s)
        self.end(i)

    def inc_or_dec(self, c, n):
        for i in range(n // 16):
            self.put(c * 8 + " " + c * 8)

        m = n % 16
        if m == 0:
            pass
        elif m > 8:
            m = m % 8
            self.put(c * 8 + " " + c * m)
        else:
            self.put(c * m)

    def inc(self, n):
        self.inc_or_dec("+", n)

    def dec(self, n):
        self.inc_or_dec("-", n)

    def clear(self, v):
        self.clear_vars([v], True)

    def clear_vars(self, out_vars:list, force=False, without=[]):
        cleared = [self.addressof(i) for i in without]

        for out_var in out_vars:
            sign, out_var = separate_sign(out_var)

            if not force and sign != "":
                    continue

            addr = self.addressof(out_var)

            if addr in cleared:
                continue

            cleared.append(addr)

            self.with_addr(addr, "[-]")


    def put_move(self, in_addr, out_vars):
        in_addr = self.addressof(in_addr)

        self.clear_vars(out_vars)

        self.with_addr(in_addr, "[")

        for out_var in out_vars:
            sign, out_var = separate_sign(out_var)
            out_addr = self.addressof(out_var)

            if in_addr == out_addr:
                raise Exception(f"move from and to {in_addr}")

            self.with_addr(out_addr, "-" if sign == "-" else "+")

        self.with_addr(in_addr, "-]")

    def move_global(self, in_addr, out_addrs):
        for out_addr in out_addrs:
            self.with_addr(out_addr, "[-]")

        self.moveadd_global(in_addr, out_addrs)

    def moveadd_global(self, in_addr, out_addrs):
        self.with_addr(in_addr, "[")

        for out_addr in out_addrs:
            self.with_addr(out_addr, "+")

        self.with_addr(in_addr, "-]")

    def load_it(self, addr):
        addr = self.addressof(addr)

        self.with_addr(addr, "[")
        self.put("+")
        self.with_addr(addr, "-]")

    def store_it(self, out_addrs):
        self.clear_vars(out_addrs)

        self.put("[")

        for out_addr in out_addrs:
            if type(out_addr) == str:
                sign, out_addr = separate_sign(out_addr)
                addr = self.addressof(out_addr)
            else:
                sign = ""
                addr = out_addr

            self.with_addr(addr, "-" if sign == "-" else "+")

        self.put("-]")

    def put_cmd(self, value, sign = ""):
        """simple commands for "set" instruction"""
        if value == "input":
            self.put(",")
        elif value == "print":
            self.put(".")
        else:
            if type(value) == str:
                value = self.valueof(value)

            if sign == "-":
                self.dec(value)
            else:
                self.inc(value)

    def put_set(self, value, args: list, addressof_tmp=0):
        n = 1
        m = self.valueof(value)

        if not (m in ["input", "print"]):
            n = int(m)
            n, m = calc_small_pair(n, len(args))
            value = m

            self.clear_vars(args)

        if n > 1 and n * m * len(args) <= n + 3 + m * len(args):
            value = int(n * m)
            n = 1


        if n > 1:
            self.put_at(addressof_tmp, "+" * n)
            self.put_at(addressof_tmp, "[")
            self.uplevel()

        for name in args:
            sign, name = separate_sign(name)
            addr = self.addressof(name)

            self.begin_global(addr)
            self.put_cmd(value, sign)
            self.end_global(addr)

        if n > 1:
            self.downlevel()
            self.put_at(addressof_tmp, "-]")

    def put_invoke(self, name:str, args:list):
        if ":" in name:
            sub_name, name = name.split(":", maxsplit=1)

            sub = self.subsystem_by_alias(sub_name)

            if sub == None:
                raise Exception(f"subsystem {sub_name} is not loaded")
            if not sub.has_ins(name, args):
                raise Exception(f"{sub.name()} hasnt {name}")

            return sub.put(name, args)

        # aliases
        if name in ["inc", "dec"]:
            sign = "+" if name == "inc" else "-"
            name = "set"
            args = ["1"] + [sign + arg for arg in args]
        if name == "clear":
            name = "set"
            args = ["0"] + args
        if name in ["print", "input"]:
            args = [name] + args
            name = "set"
        if name in ["add", "sub"]:
            sign = "+" if name == "add" else "-"
            name = "set"
            args = [args[0]] + [sign + x for x in args[1:]]
        if name in ["copyadd", "copysub"]:
            sign = "+" if name == "copyadd" else "-"
            name = "copy"
            args = [args[0]] + [sign + x for x in args[1:]]
        if name in ["moveadd", "movesub"]:
            sign = "+" if name == "moveadd" else "-"
            name = "move"
            args = [args[0]] + [sign + x for x in args[1:]]


        # ducktype checker (maybe doesnt work well)
        if name == "is_var":
            for arg in args:
                if not self.is_var(arg):
                    raise Exception(f"type check failed: {arg} should be variable")

            return True

        if name == "is_val":
            for arg in args:
                if self.is_var(arg) or self.is_sub(arg):
                    raise Exception(f"type check failed: {arg} should be value")

            return True

        if name == "is_sub":
            for arg in args:
                if not self.is_sub(arg):
                    raise Exception(f"type check failed: {arg} should be subsystem")

            return True

        if name == "is":
            if len(args) == 0:
                raise Exception("is/0 is not implemented")

            typ = args[0]
            for arg in args[1:]:
                if not self.is_sub(arg, typ):
                    raise Exception(f"type check failed: {arg} should be subsystem {typ}")

            return True

        if name == "resb":
            size = int(args[0])
            self.reserve(size)

            return True

        if name == "load":
            self.put_load(args[0], args[1:])

            return True

        if name == "loadas":
            self.put_load(args[1], args[2:], args[0])

            return True

        if name == "unload":
            self.put_unload(args[0], args[1:])

            return True

        if name == "swap":
            self.load_it(args[0])

            addr0 = self.addressof(args[0])
            addr1 = self.addressof(args[1])

            self.put_at(addr1, "[")
            self.put_at(addr0, "+")
            self.put_at(addr1, "-]")

            self.put("[")
            self.put_at(addr1, "+")
            self.put("-]")

            return True

        if name == "bool":
            self.clear_vars(args[1:])

            self.load_it(args[0])
            self.put("[")

            self.put_with_every([self.addressof(arg) for arg in args], "+")

            self.put("[-]]")

            return True

        if name in ["bool_not", "not"]:
            addr = self.addressof(args[0])

            self.put("+")
            self.put_at(addr, "[")
            self.put_at(0, "-")
            self.put_at(addr, "[-]]")

            self.clear_vars(args, without=[args[0]])

            self.put("[")
            self.put_with_every([self.addressof(arg) for arg in args], "+")
            self.put("-]")

            return True

        if name == "eq":
            import sys
            v = self.valueof(args[0])
            sys.stderr.write(f"eq {v}\n")

            for arg in args[1:]:
                addr = self.addressof(arg)

                self.put("+")

                self.put_at(addr, ("-" * v))
                self.put_at(addr, "[")
                self.put("-")
                self.put_at(addr, "[-]]")

                self.put("[")
                self.put_at(addr, "+")
                self.put("-]")

            return True

        if name in ["moveeq", "copyeq"]:
            addr0 = self.addressof(args[0])

            for arg in args[1:]:
                addr = self.addressof(arg)

                self.put_at(addr, "[")
                self.put("+")
                self.put_at(addr, "-]")

                self.put_at(addr0, "[")
                self.put_at(0, "-")
                if name == "copyeq" or len(args) > 2:
                    self.put_at(addr, "+")
                self.put_at(addr0, "-]")

                if name == "copyeq" or len(args) > 2:
                    self.put_at(addr, "[")
                    self.put_at(addr0, "+")
                    self.put_at(addr, "-]")

                self.put_at(addr, "+")

                self.put("[")
                self.put_at(addr, "-")
                self.put("[-]]")

            if name == "moveeq" or len(args) > 2:
                self.clear(addr0)

            return True

        if name in ["or", "nor"]:
            if len(args) < 2:
                raise Exception(f"[{name}/{len(args)}] is not implemented")

            addr0 = self.addressof(args[0])

            for arg in args[1:]:
                addr = self.addressof(arg)

                # move v?  it
                # move v0  +it v?
                # move v?  v0
                # if it  inc v?

                self.put_at(addr, "[")
                self.put("+")
                self.put_at(addr, "[-]]")

                self.put_at(addr0, "[")
                self.put("+")
                self.put_at(addr, "+")
                self.put_at(addr0, "[-]]")

                self.put_at(addr, "[")
                self.put_at(addr0, "+")
                self.put_at(addr, "-]")

                if name == "nor":
                    self.put_at(addr, "+")

                    self.put("[")
                    self.put_at(addr, "-")
                    self.put("-]")
                else:
                    self.put("[")
                    self.put_at(addr, "+")
                    self.put("-]")

            self.put_at(addr0, "-")

            return True

        if name in ["and", "nand"]:
            if len(args) != 2:
                raise Exception(f"[{name}/{len(args)}] is not implemented")

            addr0 = self.addressof(args[0])

            for arg in args[1:]:
                addr = self.addressof(arg)

                # breaks args[0]

                self.put_at(addr, "[")
                self.put("+")
                self.put_at(addr, "[-]]")

                if name == "nand":
                    self.put_at(addr, "+")

                self.put("[")
                self.put_at(addr0, "[")
                self.put_at(addr, "+" if name == "and" else "-")
                self.put_at(addr0, "[-]]")
                self.put("-]")

            return True

        if name == "!$":
            if len(args) == 0:
                self._concatnative_macros = {}
                return

            self._concatnative_macros[args[0]] = args[1:]

            return

        if name in ["every", "!"]:
            if not ("<-" in args):
                raise Exception(f"[every] requires <-")

            args2 = []
            for arg in args:
                if arg.startswith("$!"):
                    args2.extend(self._concatnative_macros[arg[2:]])
                else:
                    args2.append(arg)
            args = args2

            inss = split_list(args[:args.index("<-")], "|")
            argss = split_list(args[args.index("<-") + 1:], "|")

            for args2 in argss:
                for ins in inss:
                    ins2, *prefix = ins

                    self.put_invoke(ins2, prefix + args2)

            return True

        if name == "set":
            self.put_set(args[0], args[1:])

            return True

        if name == "copy":
            # move to it
            self.load_it(args[0])

            # copy and restore
            self.store_it(args[1:] + ["+" + args[0]])

            return True


        if name == "move":
            self.put_move(args[0], args[1:])

            return True

        if name in ["if", "while"]:
            addr = self.addressof(args[0])

            self.with_addr(addr, "[")
            self.uplevel()

            return True

        # validation
        if name in ["ifnotin", "endifnotin"]:
            if not self.is_var(args[0]):
                raise Exception(f"first arg of [{name}] should be variable")

            if len(list(filter(None, map(self.is_val, args[1:])))) != len(args[1:]):
                raise Exception(f"currently [{name}] accepts only one variable and immediates")

        if name == "ifnotin":
            addr = self.addressof(args[0])

            args2 = args[1:]
            args2 = set(map(self.byteof, args2))
            args2 = sorted(args2)

            base = 0
            for i in args2:
                j = i - base
                base = i

                self.with_addr(addr, "-" * j + "[")

            self.uplevel()

            return True

        if name == "endifnotin":
            addr = self.addressof(args[0])

            self.downlevel()
            self.with_addr(addr, "[-]" + "]" * (len(args) - 1))

            return True

        if name in ["endif", "endwhile"]:
            sign, v = separate_sign(args[0])
            addr = self.addressof(v)

            self.downlevel()

            self.with_addr(addr,
                "]" if name == "endwhile"
                else "-]" if sign == "-"
                else "[-]]")

            return True

        if name == "ifelse":
            a_then = self.addressof(args[0])
            s_else, v_else = separate_sign(args[1])
            a_else = self.addressof(v_else)

            self.with_addr(a_else, "+" if s_else == "+" else "[-]+")
            self.with_addr(a_then, "[")
            self.uplevel()

            return True

        if name == "else":
            s_then, v_then = separate_sign(args[0])
            s_else, v_else = separate_sign(args[1])
            a_then = self.addressof(v_then)
            a_else = self.addressof(v_else)

            self.downlevel()
            self.with_addr(a_else, "-" if s_else == "-" else "[-]")
            self.with_addr(a_then, "-]" if s_then == "-" else "[-]]")
            self.with_addr(a_else, "[")
            self.uplevel()

            return True

        if name == "endifelse":
            sign, v = separate_sign(args[1])
            addr = self.addressof(v)

            self.downlevel()
            self.with_addr(addr, "-]" if sign == "-" else "[-]]")

            return True

        if name in ["iflt", "endiflt"]:
            name = "ifgt" if name == "iflt" else "endifgt"
            right = args[0]
            left = args[1]
            args[0] = left
            args[1] = right

        if name == "ifgt":
            a_left = self.addressof(args[0])
            a_right = self.addressof(args[1])
            a_tmp = self.addressof(args[2])

            self.with_addr(a_tmp, "[-]")
            self.with_addr(a_left, "[")
            self.uplevel()

            self.with_addr(a_right, "[")
            self.with_addr(a_tmp, "+")
            self.with_addr(0, "+")
            self.with_addr(a_right, "-]")

            self.with_addr(a_tmp, "[")
            self.with_addr(a_right, "+")
            self.with_addr(a_tmp, "-]")

            self.with_addr(a_tmp, "+")
            self.with_addr(0, "[")
            self.with_addr(a_tmp, "-")
            self.with_addr(0, "[-]]")
            self.with_addr(a_tmp, "[[-]")


            return True

        if name == "endifgt":
            a_left = self.addressof(args[0])
            a_right = self.addressof(args[1])
            a_tmp = self.addressof(args[2])

            self.downlevel()

            self.with_addr(a_left, "[-]+")
            self.with_addr(a_tmp, "[-]]")

            self.with_addr(a_right, "-")
            self.with_addr(a_left, "-]")
            self.with_addr(a_right, "[-]")

            return True

        if name == "include_bf":
            if len(args) < 1:
                raise Exception("[include_bf/0] is not implemented")

            try:
                with io.open(args[0]) as bff:
                    bf = bff.read()
            except Exception:
                raise Exception(f"failed to open {args[0]}")

            if len(args) > 1 and args[1].isdigit():
                mem_size = int(args[1])
                vs = args[2:]

                if len(vs) > mem_size:
                    raise Exception("variables [include_bf] passed can not be stored to bf memory area.")
            else:
                vs = args[1:]

                if len(vs) > 0:
                    mem_size = len(vs)
                else:
                    mem_size = 1

            if mem_size <= 1 and len(vs) == 0:
                self.put_at(0, bf)

                return True

            if len(vs) == mem_size:
                direct_io = True

                p = -1
                for i in vs:
                    addr = self.addressof(i)

                    if p == -1:
                        p = addr
                    elif p + 1 == addr:
                        p += 1
                    else:
                        direct_io = False
                        break

                if direct_io:
                    self.put_at(self.addressof(vs[0]), bf)

                    return True

            bf_ptr = self.offsetof_next_subsystem()

            for i in range(len(vs)):
                addr = self.addressof(vs[i])

                self.put_at(addr, "[")
                self.put_at(bf_ptr + i, "+")
                self.put_at(addr, "-]")

            self.put_at(bf_ptr, bf)

            for i in range(len(vs)):
                addr = self.addressof(vs[i])

                self.put_at(bf_ptr + i, "[")
                self.put_at(addr, "+")
                self.put_at(bf_ptr + i, "-]")

            for i in range(len(vs), mem_size):
                self.put_at(bf_ptr + i, "[-]")

            return True

        if name == "include_c":
            if len(args) < 4:
                raise Exception(f"[include_c/{len(args)}] is not implemented")

            c_file_name = args[0]
            c_stack_size = int(args[1])
            c_func_name = args[2]
            c_func_args_and_result = args[3:]
            c_func_args = c_func_args_and_result[:-1]
            c_base_ptr = self.offsetof_next_subsystem()

            shared_vars = [f"__tobf_shared{i}" for i in range(len(c_func_args))]

            try:
                c = C2bf(c_file_name, shared_vars=shared_vars, stack_size=c_stack_size)
                c_func_args2 = [f"__tobf_shared{i}" for i in range(len(c_func_args))]
                c_startup = f"""{{ __tobf_shared0 = {c_func_name}({",".join(c_func_args2)}); }}"""
                bf, _ = c.compile_to_bf(c_startup)
            except Exception:
                raise Exception(f"failed to open {c_file_name}")

            for i in range(len(c_func_args)):
                arg = c_func_args[i]

                if self.is_var(arg):
                    addr = self.addressof(arg)

                    self.put_at(addr, "[")
                    self.put_at(c_base_ptr + i, "+")
                    self.put_at(addr, "-]")
                else:
                    v = self.valueof(arg)
                    self.put_at(c_base_ptr + i, "+" * v)

            self.put_at(c_base_ptr, bf)

            addr = self.addressof(c_func_args_and_result[-1])

            self.put_at(c_base_ptr, "[")
            self.put_at(addr, "+")
            self.put_at(c_base_ptr, "-]")

            return True


        raise Exception(f"unknown instruction {name}")

    def compile_instruction(self, src):
        if type(src) == str:
            src = split(src)

        name, *args = src

        return self.put_invoke(name, args)

    def compile_all(self, src:list, comments=False):
        for i in src:
            if comments or i[0] == "bf":
                print(" ".join(i) if type(i) == list else i)

                if not comments:
                    continue

            self.compile_instruction(i)

        self.put("[-]")

    def compile_file(self, file_name, comments=False):
        size, vars, macros = Tobf.read_file(file_name)

        self._vars = vars
        self.reserve(size)
        self.compile_all(macros["main"].codes, comments)

    @staticmethod
    def read_file(file:str) -> tuple:
        """returns (size, vars, macros)"""

        size = -1
        vs = []
        ms = {"main": MacroProc("main", [], [])}
        try:
            f = io.open(file, "r")
            label = "main"

            mod = file.rsplit(".", maxsplit=1)[0] if "." in file else file
            vs = split(f.readline())

            if len(vs) > 0 and vs[0].isdigit():
                size = int(vs[0])
                vs = vs[1:]

            try:
                while f.readable():
                    src = f.readline().strip()

                    if len(src) == 0:
                        continue
                    if src.startswith("#"):
                        continue

                    cod = split(src)

                    if cod[0].startswith(":"):
                        label = cod[0][1:]

                        if not (label in ms.keys()):
                            ms[label] = MacroProc(label, [], [])

                        if len(ms[label].params) == 0:
                            ms[label].params = cod[1:].copy()

                        continue

                    if cod[0] == "end":
                        break

                    ms[label].codes.append(cod)
            except Exception as e:
                f.close()

                raise e

            f.close()
        except Exception as e:
            raise e

        if size == -1:
            size = len(vs) + 1

        return (size, vs, ms)
