
# load subsystem_name ...args
#   calls subsystem_name:init with args. and names as subsystem_name
# loadas alias_name subsystem_name ...args
#   calls subsystem_name:init with args. and names as alias_name
# unload subsystem_name ...args
#   calls subsystem_name:clean with args. deallocates memory area for subsystem.
# public ...vars
#   unavairable in main program.
#   declares variables as public.
#   public variables can be copied/moved from/to objects with similar interface via copy/move instruction.

# subsystem consts
#   size: 0
#   consts:init
#   consts:def value ...names
#     names values
# subsystem enums
#   size: 0
#   enums:init
#   enums:def ...names
#     defines enums with different value
# subsystem constset
#   size: 0
#   constsset:init
#   constsset:const value ...names
#     same as const:def
#   constset:enum ...names
#     sameas enums:def
# subsystem vars
#   size: n
#   vars:init n
#     staticaly allocates n bytes
#   vars:clean
#     clears n bytes
#   vars:clean fast
#     does not clear
#   vars:def ...names
#     defines names bound to memory addresses. they works as variable.
#   vars:set ...imms ...varss
#     imms: should have same number of values as variables.
#     varss: list of vars
#     set all immediates to variables.
#     set to every same named variable in varss if varss exists.
#   vars:add ...imms ...varss
#   vars:sub ...imms ...varss
#     similer to vars:set.
#   vars:move ...varss
#   vars:moveadd ...varss
#   vars:movesub ...varss
#   vars:copy ...varss
#   vars:copyadd ...varss
#   vars:copysub ...varss
#     similer to main instruction. "this" as source.


from typing import cast, Union, List, Tuple, Set, Dict, Callable
import io
from tobf import Tobf
from base import Subsystem, calc_small_pair, src_extension, separate_sign, SubsystemBase, InstructionBase, MacroProc


class Instruction_DefineConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=2)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        v = args[0]
        names = args[1:]

        for name in names:
            self._sub.def_const(name, main.valueof(v))

class Instruction_IncrementConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _decrement=False):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
        self._decrement = _decrement

    def put(self, main: Tobf, args:list):
        for name in args:
            if self._decrement:
                d = -1
            else:
                d = 1
            self._sub.replace_const(name, int(self._sub.valueof(name)) + d)

class Instruction_RedefineConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=2)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        v = args[0]
        for name in args[1:]:
            self._sub.replace_const(name, main.valueof(v))

class Instruction_DefineEnum(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        for name in args:
            self._sub.def_enum(name)

class Instruction_DefineVar(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        for name in args:
            self._sub.def_var(name)

class Instruction_Init(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _least_argc=0):
        super().__init__(_name, _least_argc=_least_argc)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        self._sub.put_init(args)

class Instruction_Clean(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _least_argc=0):
        super().__init__(_name, _least_argc=_least_argc)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        self._sub.put_clean(args)

class Instruction_Pass(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _least_argc=0):
        super().__init__(_name, _least_argc=_least_argc)
        self._sub = _sub
    def put(self, main: Tobf, args:list):
        self._sub.put(self._name, args)

class Subsystem_ConstSet(SubsystemBase):
    """constant definitions"""
    def __init__(self, main: Tobf, name: str, args: List[str], instantiate: Callable[[int], int]):
        super().__init__(main, name)
        self._main = cast(Tobf, self._main)

        self.resize(0)
        instantiate(0, self)

        self.add_ins(Instruction_DefineConst("const", self))
        self.add_ins(Instruction_DefineEnum("enum", self))

class Subsystem_Consts(SubsystemBase):
    """constant definitions"""
    def __init__(self, main: Tobf, name: str, args: List[str], instantiate: Callable[[int], int]):
        super().__init__(main, name)
        self._main = cast(Tobf, self._main)

        self.resize(0)
        instantiate(0, self)

        self.add_ins(Instruction_DefineConst("def", self))
        self.add_ins(Instruction_IncrementConst("inc", self))
        self.add_ins(Instruction_IncrementConst("dec", self, _decrement=True))
        self.add_ins(Instruction_RedefineConst("redef", self))

class Subsystem_Enums(SubsystemBase):
    """constant definitions"""
    def __init__(self, main: Tobf, name: str, args: List[str], instantiate: Callable[[int], int]):
        super().__init__(main, name)
        self._main = cast(Tobf, self._main)

        self.resize(0)
        instantiate(0, self)

        self.add_ins(Instruction_DefineEnum("def", self))

class Subsystem_Vars(SubsystemBase):
    """local variable area"""
    def __init__(self, main: Tobf, name: str, args: List[Union[int, str]], instantiate: Callable[[int], int]):
        super().__init__(main, name)
        self._main = cast(Tobf, self._main)

        if len(args) == 1 and args[0].isdigit():
            self.resize(self._main.valueof(args[0]))
        else:
            for arg in args:
                self.def_var(arg)

            self.resize(len(self._vars))

        instantiate(self.size(), self)

        self.add_ins(Instruction_Clean("clean", self, 0))
        self.add_ins(Instruction_DefineVar("def", self))
        self.add_ins(Instruction_Pass("set", self, 1))
        self.add_ins(Instruction_Pass("add", self, 1))
        self.add_ins(Instruction_Pass("sub", self, 1))

    def put_clean(self, args: List[Union[int, str]]):
        if len(args) == 1 and args[0] == "fast":
            return

        self._main.put_at(self.offset(), ("[-]>" * self.size()) + ("<" * self.size()))

    def put(self, name: str, args: List[Union[int, str]], tmps: List[int]):
        if name == "init":
            return
        if name == "clean":
            self.put_clean(args)
            return

        name0 = name
        sign = ""

        if name == "add":
            sign = "+"
            name = "set"
        if name == "sub":
            sign = "-"
            name = "set"

        if name == "set" and len(args) >= self.size():
            imms = args[:self.size()]
            vss = args[self.size():]

            for i in imms:
                if not self._main.is_val(i):
                    Exception(f"sources of [vars:set] should be immediates")

            for i in vss:
                if not self._main.is_sub(i, "vars"):
                    Exception(f"additional destinations of [vars:set] should be vars")
                if len(set(self._vars) & set(self._main.get_instance(i).writable_vars())) == 0:
                    Exception(f"additional destinations of [vars:set] should have variables in this vars")

            vss = [self.name()] + vss

            for i in range(self.size()):
                imm = imms[i]
                self._main.put_invoke("set", [imm] + [sign + j + ":" + self._vars[i] for j in vss], tmps)
            
            return

        raise Exception(f"unknown instruction [vars:{name0}/{len(args)}] {self.name()}(vars):len={self.size()}")


class Subsystem_Code(SubsystemBase):
    def __init__(self, tobf: Tobf, _name: str, args: List[Union[str, int]], instantiate: Callable[[int, Subsystem, List[str]], int]):
        super().__init__(tobf, _name)
        self._main = cast(Tobf, self._main)

        self._macs = {}
        file = args[0] + "." + src_extension
        pub_vars, vs, ms = self._main.read_file(file)

        self.resize(len(vs))

        for v in vs:
            self.def_var(v, is_public=(v in pub_vars))

        for key in ms.keys():
            self._macs[key] = ms[key]

            self.add_ins(Instruction_Pass(key, self, len(ms[key].params)))

        self._codes = self._macs.copy()

        self.add_ins(Instruction_Init("init", self, 1))

        instantiate(self.size(), self, args[1:])

    def put_init(self, args: List[Union[int, str]]):
        self.put("init", args, self._main.tmps_)

    def put_clean(self, args: List[Union[int, str]]):
        self.put("clean", args, self._main.tmps_)

    def make_qname(self, name, params=[], args=[]):
        if name[0] in ["+", "-"]:
            sign = name[0]
            name = name[1:]
        else:
            sign = ""

        if self.has_var(name):
            name = self._name + ":" + name

        return sign + name

    def has_ins(self, name, args):
        if name == "init":
            return True

        return name in self._macs.keys()

    def put(self, name: str, args: List[Union[int, str]], tmps: List[int] = None):
        if tmps == None:
            tmps = self._main.tmps_.copy()

        if name == "init" and "init" not in self._macs.keys():
            return

        if not (name in self._macs.keys()):
            return Exception(f"unknown instruction {self.name()}:{name}")

        mac = self._macs[name]

        if len(mac.params) != len(args):
            raise Exception(f"{name} uses {len(mac.params)} args, got {len(args)}")

        for c in mac.codes:
            c2 = c.copy()

            for i in range(len(c2)):
                sign, name = separate_sign(c2[i])

                if ":" in name:
                    sfix = name[name.index(":"):]
                    name = name[:name.index(":")]
                else:
                    sfix = ""

                if name in mac.params:
                    name = args[mac.params.index(name)]
                elif i > 0 and (name in self._vars):
                    name = self._name + ":" + name

                c2[i] = sign + name + sfix

            ins_name = c2[0]
            ins_args = c2[1:]

            if ins_name in self._macs.keys():
                self.put(ins_name, ins_args, tmps)
            else:
                self._main.put_invoke(ins_name, ins_args, tmps)

