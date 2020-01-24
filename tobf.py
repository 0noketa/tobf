
# a to-bf compiler for small outouts
# abi:
#   dynamic_addressing: every address is 8bits. only 256 bytes.
#     16bits addressing is planned as that cant be used both systems in once.
#     ex: initialize as 8bit addrs -> use -> clean -> initialize as 16bit addrs.
#   pointer: always points address 0 with value 0 at the beggining and the end
#   memory: temporary, ...vars, dynamic_memory
#     area of vars has no hidden workspace expects address 0).
#     dynamic_memory is optional. nothing exists until initialized manually. and can be cleaned up.
# linking(not yet):
#   sequencial or macro-injection.
#   linkers are required to read only first lines of every source.
# syntax:
#   program: var_decl "\n" instructions "end" "\n"
#   var_decl: id (" " id)*
#   instructions: (id (" " id)* "\n")*
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
# endif cond_var
#   like "next i" in basic. this rule simplifies compiler.
#   currently compiler disallows no cond_var instructions.
# ifelse cond_var work_var
#   work_var carries run_else flag
# else cond_var work_var
# endifelse cond_var work_var
# while cond_var
# endwhile cond_var
# end
#   can not be omitted

import io

def split(s:str, sep=None, maxsplit=-1) -> list:
    if sep == None:
        return list(filter(len, map(str.strip, s.strip().split(maxsplit=maxsplit))))
    else:
        return list(map(str.strip, s.strip().split(sep=sep, maxsplit=maxsplit)))

class Mainsystem:
    def has_var(self, name:str) -> bool:
        return False
    def addressof(self, name:str) -> int:
        return 0
    def valuesof(self, name:str) -> int:
        """constant"""
        return 0
    def put(self, s:str):
        pass
    def put_with(self, addr:int, s:str):
        """>>>something<<<"""
        pass
    def put_invoke(self, name:str, args:list):
        pass

class InstructionBase:
    def __init__(self, _name, _least_argc = 0):
        super().__init__()
        self._name = _name
        self._least_argc = _least_argc
    def name(self):
        return self._name
    def least_argc(self):
        return self._least_argc
    def put(self, main: Mainsystem, args:list):
        pass

class SubsystemBase:
    """module-like extension that can be specialized like classes"""
    def __init__(self, _name:str, _instructions:dict={}, _consts={}, _enums=[], _vars:list=[], _size=-1):
        self._loaded = False
        self._offset = 0
        self._main = None
        self._initialized = False
        self._name = _name
        self._instructions = _instructions.copy()
        self._consts = _consts.copy()
        self._enums = _enums.copy()
        self._vars = _vars.copy()
        self._size = _size
    def copy(self, _name:str):
        r = type(self)(_name)
        r._main=self._main
        r._instructions=self._instructions
        r._consts=self._consts
        r._enums=self._enums
        r._vars=self._vars
        r._size=self._size
        return r
    def load(self, offset:int, main:Mainsystem):
        if self._loaded:
            return False

        self._offset = offset
        self._loaded = True
        self._main = main

        return True
    def name(self):
        return self._name
    def resize(self, size:int):
        if self._initialized:
            return
        self._size = size
    def has_const(self, name: str) -> bool:
        return name in self._consts.keys()
    def add_const(self, name: str, value:int) -> bool:
        if name.isdigit():
            return False
        
        if not (name in self._consts):
            self._consts[name] = value

        return True
    def has_enum(self, name: str) -> bool:
        return name in self._enums
    def add_enum(self, name: str) -> bool:
        if name.isdigit():
            return False
        
        if not (name in self._enums):
            self._enums.append(name)

        return True
    def has_var(self, name: str) -> bool:
        return name in self._vars
    def add_var(self, name: str) -> bool:
        if name.isdigit():
            return False
        
        if not (name in self._vars):
            self._vars.append(name)

        return True
    def valueof(self, name: str) -> int:
        if self.has_const(name):
            return self._consts[name]
        if self.has_enum(name):
            return self._enums.index(name)

        return int(name)
    def addressof(self, name: str) -> int:
        if self.has_var(name):
            return self._vars.index(name) + self.offset()

        return self.offset()
    def add_ins(self, ins: InstructionBase) -> bool:
        if ins.name() in self._instructions.keys():
            return False

        self._instructions[ins.name()] = ins

        return True
    def has_ins(self, name:str, args:list):
        """arg: args as single string"""
        if not (name in self._instructions.keys()):
            return False

        ins: InstructionBase = self._instructions[name]

        return len(args) >= ins.least_argc()
    def put(self, name:str, args:list):
        if name == "init" and self._initialized:
            return
        if name == "clean" and not self._initialized:
            return

        ins: InstructionBase = self._instructions[name]

        ins.put(self._main, args)

        if name == "init":
            self._initialized = True
    def offset(self):
        """offset of this subsystem"""
        return self._offset
    def size(self):
        return len(self._vars) if self._size == -1 else self._size


class Tobf(Mainsystem):
    def __init__(self, _vars = []):
        self._vars = _vars
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
            put_err(f"subsystem {name} is not installed")
            return None

        return self._subsystems[name]

    def subsystem_by_alias(self, name) -> SubsystemBase:
        """returns an instance of subsystem"""

        if name == "" and self._newest_subsystem_name != "":
            name = self._newest_subsystem_name

        if not (name in self._loaded_subsystems.keys()):
            put_err(f"subsystem aliased as {name} is not loaded")
            return None

        return self._loaded_subsystems[name]

    def put_load(self, name:str, args:list, alias=""):
        if not (name in self._subsystems.keys()):
            put_err(f"subsystem {name} is not installed")
            return False
        
        if alias == "":
            alias = name

        if alias in self._loaded_subsystems.keys():
            put_err(f"subsystem aliased as {alias} is already loaded.")
            return False

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
            print(f"failed to get address of {value}")
            raise "error"

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
            sign, out_var = self.separate_sign(out_var)

            if not force and sign != "":
                    continue

            addr = self.addressof(out_var)
            self.with_addr(addr, "[-]")


    def put_move(self, in_addr, out_vars):
        in_addr = self.addressof(in_addr)

        self.clear_vars(out_vars)

        self.with_addr(in_addr, "[")

        for out_var in out_vars:
            sign, out_var = self.separate_sign(out_var)
            out_addr = self.addressof(out_var)

            if in_addr == out_addr:
                print(f"move from and to {in_addr}")
                raise "error"

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
                sign, out_addr = self.separate_sign(out_addr)        
                addr = self.addressof(out_addr)
            else:
                sign = ""
                addr = out_addr

            self.with_addr(addr, "-" if sign == "-" else "+")

        self.put("-]")

    def calc_small_pair(self, n, vs):
        """n: result0 * result1\n
        vs: num of vars\n
        +{result0}[>+{result1}<-]"""

        n = n % 256
        x = 1
        y = 256
        s = 256
        for i in range(1, 256):
            if n % i == 0:
                j = n // i
                s2 = int(i + j * vs)

                if s2 < s:
                    x = i
                    y = j
                    s = s2

        return max(x, y), min(x, y)

    def separate_sign(self, name):
        if type(name) == str and len(name) > 0 and name[0] in ["+", "-"]:
            return name[0], name[1:]
        else:
            return "", name

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
            n, m = self.calc_small_pair(n, len(args))
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
            sign, name = self.separate_sign(name)
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
                raise f"subsystem {sub_name} is not loaded"
            if not sub.has_ins(name, args):
                raise f"{sub.name()} hasnt {name}"

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
            addr = self.addressof(args[0])

            self.downlevel()

            self.with_addr(addr, "[-]]" if name == "endif" else "]")

            return True

        if name == "ifelse":
            v_then = self.addressof(args[0])
            v_else = self.addressof(args[1])

            self.with_addr(v_else, "[-]+")
            self.with_addr(v_then, "[")
            self.uplevel()

            return True

        if name == "else":
            v_then = self.addressof(args[0])
            v_else = self.addressof(args[1])

            self.downlevel()
            self.with_addr(v_else, "-")
            self.with_addr(v_then, "[-]]")
            self.with_addr(v_else, "[")
            self.uplevel()

            return True

        if name == "endifelse":
            v_from = vrs.addressof(args[1])

            self.downlevel()
            self.with_addr(v_from, "-]")

            return True

        print(f"unknown instruction {name}")
        raise "error"

    def compile_instruction(self, src:str):
        src = src.strip()

        if src.startswith("#") or len(src) == 0:
            return True

        name, *args = split(src)

        return self.put_invoke(name, args)
    
    def compile_all(self, src:list):
        for i in src:
            self.compile_instruction(i)

        self.put("[-]")




class Instruction_DefineConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=2)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        v = args[0]
        names = args[1:]

        for name in names:
            self._sub.add_const(name, self._sub.valueof(v))
class Instruction_DefineEnum(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        for name in args:
            self._sub.add_enum(name)
class Instruction_DefineVar(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        for name in args:
            self._sub.add_var(name)
class Instruction_ResizeVars(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        self._sub.resize(int(args[0]))
class Subsystem_ConstSet(SubsystemBase):
    """constant definitions"""
    def __init__(self, _name="constset"):
        super().__init__(_name)
        self.add_ins(Instruction_DefineConst("const", self))
        self.add_ins(Instruction_DefineEnum("enum", self))
class Subsystem_Consts(SubsystemBase):
    """constant definitions"""
    def __init__(self, _name="consts"):
        super().__init__(_name)
        self.add_ins(Instruction_DefineConst("def", self))
class Subsystem_Enums(SubsystemBase):
    """constant definitions"""
    def __init__(self, _name="enums"):
        super().__init__(_name)
        self.add_ins(Instruction_DefineEnum("def", self))
class Subsystem_Vars(SubsystemBase):
    """local variable area"""
    def __init__(self, _name="vars"):
        super().__init__(_name)
        self.add_ins(Instruction_ResizeVars("init", self))
        self.add_ins(Instruction_DefineVar("def", self))




if __name__ == "__main__":
    _line = input().strip()

    while _line.startswith("#"):
        _line = input().strip()
    
    compiler = Tobf(split(_line))
    compiler.install_subsystem(Subsystem_Enums())
    compiler.install_subsystem(Subsystem_Consts())
    compiler.install_subsystem(Subsystem_ConstSet())
    compiler.install_subsystem(Subsystem_Vars())

    _src = []
    _line = input().strip()

    while _line != "end":
        _src.append(_line)
        _line = input().strip()

    compiler.compile_all(_src)

