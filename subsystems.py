
# load subsystem_name ...args
#   calls subsystem_name:init with args. and names as subsystem_name
# loadas alias_name subsystem_name ...args
#   calls subsystem_name:init with args. and names as alias_name
# unload subsystem_name ...args
#   calls subsystem_name:clean with args. deallocates memory area for subsystem.

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
#   vars:def ...names
#     defines names memory addresses. they works as variable.

import io
from base import src_extension, separate_sign, Mainsystem, SubsystemBase, InstructionBase, MacroProc


class Instruction_DefineConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=2)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        v = args[0]
        names = args[1:]

        for name in names:
            self._sub.add_const(name, main.valueof(v))

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

class Instruction_Init(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _least_argc=0):
        super().__init__(_name, _least_argc=_least_argc)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        self._sub.put_init(args)

class Instruction_Clean(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _least_argc=0):
        super().__init__(_name, _least_argc=_least_argc)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        self._sub.put_clean(args)

class Instruction_Pass(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase, _least_argc=0):
        super().__init__(_name, _least_argc=_least_argc)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        self._sub.put(self._name, args)

class Subsystem_ConstSet(SubsystemBase):
    """constant definitions"""
    def __init__(self, _name="constset"):
        super().__init__(_name)
    def copy(self, name):
        r = super().copy(name)
        r.add_ins(Instruction_DefineConst("const", r))
        r.add_ins(Instruction_DefineEnum("enum", r))
        return r

class Subsystem_Consts(SubsystemBase):
    """constant definitions"""
    def __init__(self, _name="consts"):
        super().__init__(_name)
    def copy(self, name):
        r = super().copy(name)
        r.add_ins(Instruction_DefineConst("def", r))
        return r

class Subsystem_Enums(SubsystemBase):
    """constant definitions"""
    def __init__(self, _name="enums"):
        super().__init__(_name)
    def copy(self, name):
        r = super().copy(name)
        r.add_ins(Instruction_DefineEnum("def", r))
        return r

class Subsystem_Vars(SubsystemBase):
    """local variable area"""
    def __init__(self, _name="vars"):
        super().__init__(_name)
    def copy(self, name):
        r = super().copy(name)
        r.add_ins(Instruction_Init("init", r, 1))
        r.add_ins(Instruction_DefineVar("def", r))
        return r
    def put_init(self, args:list):
        self._sub.resize(int(args[0]))

class Subsystem_Code(SubsystemBase):
    def __init__(self, _name="code"):
        super().__init__(_name)
        self._macs = {}
        self._read = False
    def copy(self, _name):
        r = super().copy(_name)
        r._codes = self._macs.copy()
        r._read = self._read
        r.add_ins(Instruction_Init("init", r, 1))
        return r

    def make_qname(self, name, params=[], args=[]):
        if name[0] in ["+", "-"]:
            sign = name[0]
            name = name[1:]
        else:
            sign = ""

        if self.has_var(name):
            name = self._name + ":" + name

        return sign + name

    def put_init(self, args:list):
        if self._read:
            return

        file = args[0] + "." + src_extension
        size, vs, ms = self._main.read_file(file)

        self.resize(size)

        for v in vs:
            self.add_var(v)

        for key in ms.keys():
            self._macs[key] = ms[key]

            self.add_ins(Instruction_Pass(key, self, len(ms[key].params)))

        self._read = True

        self.put("init", [])

        super().put_init(args)

    def has_ins(self, name, args):
        if not self._read and name == "init":
            return True

        return name in self._macs.keys()

    def put(self, name, args:list):
        if not self._read and name == "init":
            return self.put_init(args)

        if not (name in self._macs.keys()):
            return Exception(f"unknown instruction {name}")

        mac = self._macs[name]

        if len(mac.params) != len(args):
            raise Exception(f"{name} uses {len(mac.params)} args, got {len(args)}")

        for c in mac.codes:
            c2 = c.copy()

            for i in range(len(c2)):
                sign, name = separate_sign(c2[i])

                if name in mac.params:
                    name = args[mac.params.index(name)]
                elif i > 0 and (name in self._vars):
                    name = self._name + ":" + name

                c2[i] = sign + name

            ins_name = c2[0]
            ins_args = c2[1:]

            if ins_name in self._macs.keys():
                self.put(ins_name, ins_args)
            else:
                self._main.put_invoke(ins_name, ins_args)

