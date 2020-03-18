
# a to-bf compiler for small outouts
# abi:
#   pointer: always points address 0 with value 0 at the beggining and the end
#   memory: temporary, ...vars, dynamic_memory
#     area of vars has no hidden workspace expects address 0. can be used like common-vars in old fortran.
#     dynamic_memory is optional. nothing exists until initialized manually. and can be cleaned up.
# linking(not yet):
#   sequencial or macro-injection.
#   linkers are required to read only first lines of every source.
# syntax:
#   program: var_decl "\n" instructions "end" "\n"
#   var_decl: id (" " val)*
#   instructions: (id (" " val)* "\n")*
# instructions:
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
# move in_var ...out_vars_with_sign
#   in_var becomes to 0
#   aliases_with_inplicit_signs:
#     moveadd in_var ...out_vars 
#     movesub in_var ...out_vars 
# copy in_var ...out_vars_with_sign
#   aliases_with_inplicit_signs:
#     copyadd in_var ...out_vars 
#     copysub in_var ...out_vars 
# resb imm
#   declare size of static memory. default=number of vars. works when no subsystem was loaded.
# load subsystem_name ...args
#   loads subsystem after reserved vars and subsystems already loaded
# loadas alias_name subsystem_name ...args
#   loads and names as alias_name
# unload subsysten_name
#   unloads a subsystem. subsystem_name can be alias_name
# subsystem_name.any_name ...args
#   invokes a feature of subsystem
# if cond_var
#   cond_var is avarable until endif
# endif cond_var
#   like "next i" in basic. this rule simplifies compiler.
#   currently compiler disallows no cond_var instructions.
# ifelse cond_var work_var
#   work_var carries run_else flag
#   cond_var is avarable until "else"
# else cond_var work_var
# endifelse cond_var work_var
# while cond_var
# endwhile cond_var
# end
#   can not be omitted

import io
from base import Mainsystem, SubsystemBase, InstructionBase, split, separate_sign, calc_small_pair, MacroProc


class Tobf(Mainsystem):
    def __init__(self):
        self._vars = []
        self._reserved = -1
        self._subsystems = {}
        self._loaded_subsystems = {}
        self._idt = 0
        self._size = 0
        self._newest_subsystem_name = ""

    def reserve(self, size):
        """manually selects size of variable area\n
        can be reselected when on subsystem was loaded."""

        if len(self._loaded_subsystems.keys()) > 0:
            return False

        self._reserved = size

        return True

    def install_subsystem(self, subsystem: SubsystemBase):
        self._subsystems[subsystem.name()] = subsystem

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

    def put_with(self, addr:int, s:str):
        self.with_addr(addr, s)        

    def has_var(self, name:str) -> bool:
        return name in self._vars
    def addressof_var(self, name:str) -> int:
        return int(self._vars.index(name) + 1)

    def is_var(self, value) -> bool:
        if type(value) != str:
            return False
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.subsystem_by_alias(sub_name)

            return sub.has_var(name)
        else:
            return self.has_var(value)

    def addressof(self, value) -> int:
        if type(value) != str:
            return value
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

    def valueof(self, value) -> int:
        if type(value) != str:
            return value
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.subsystem_by_alias(sub_name)

            return sub.valueof(name)
        elif value.isdigit():
            return int(value)
        else:
            return value

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

    def clear_vars(self, out_vars:list, force=False):
        for out_var in out_vars:
            sign, out_var = separate_sign(out_var)

            if not force and sign != "":
                    continue

            addr = self.addressof(out_var)
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

    def put_set(self, value, args: list):
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
            self.inc(n)
            self.put("[")
            self.uplevel()

        for name in args:
            sign, name = separate_sign(name)
            addr = self.addressof(name) 

            self.begin_global(addr)
            self.put_cmd(value, sign)            
            self.end_global(addr)

        if n > 1:
            self.downlevel()
            self.put("-]")

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
            for arg in args[1:]:
                try:
                    self.addressof(arg)
                except Exception as e:
                    raise Exception(f"type check failed: {arg} should be variable")

            return True

        if name == "is_val":
            for arg in args[1:]:
                try:
                    self.valueof(arg)
                except Exception as e:
                    raise Exception(f"type check failed: {arg} should be value")

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

        if name == "set":
            self.put_set(args[0], args[1:])

            return True

        if name in "copy":
            # move to it
            self.load_it(args[0])

            # copy and restore
            self.store_it(args[1:] + ["+" + args[0]])

            return True


        if name in "move":
            self.put_move(args[0], args[1:])

            return True

        if name in ["if", "while"]:
            addr = self.addressof(args[0])

            self.with_addr(addr, "[")
            self.uplevel()

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

        if name in "ifgt":
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

        if name in "endifgt":
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


        raise Exception(f"unknown instruction {name}")

    def compile_instruction(self, src):
        if type(src) == str:
            src = split(src)
            
        name, *args = src

        return self.put_invoke(name, args)
    
    def compile_all(self, src:list, comments=False):
        for i in src:
            if comments:
                print(" ".join(i) if type(i) == list else i)

                if i[0] == "bf":
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
