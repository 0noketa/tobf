
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
from base import src_extension, Mainsystem, SubsystemBase, InstructionBase


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
        self._codes = {}
        self._read = False
    def copy(self, _name):
        r = super().copy(_name)
        r._codes = self._codes.copy()
        r._read = self._read
        r.add_ins(Instruction_Init("init", r, 1))
        return r


    def put_init(self, args:list):
        if self._read:
            return

        file = args[0] + "." + src_extension
        size, vs, cs = self._main.read_file(file)

        self.resize(size)

        for v in vs:
            self.add_var(v)

        for key in cs.keys():
            c2 = []

            for c in cs[key]:
                name = c[0]
                args = c[1:]
                
                args = list(map(lambda x:
                        self._name + ":" + x if self.has_var(x)
                            else x,
                        args))
    
                c2.append([name] + args)

            self._codes[key] = c2

            self.add_ins(Instruction_Pass(key, self, 0))

        self._read = True

        self.put("init", [])

        super().put_init(args)

    def has_ins(self, name, args):
        if not self._read and name == "init":
            return True

        return name in self._codes.keys()

    def put(self, name, args:list):
        if not self._read and name == "init":
            return self.put_init(args)

        if not (name in self._codes.keys()):
            return

        cs = self._codes[name]

        for c in cs:
            name = c[0]
            args = c[1:]

            if name in self._codes.keys():
                name = self._name + ":" + name

            self._main.put_invoke(name, args)

