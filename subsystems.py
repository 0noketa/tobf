
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


import io
from base import calc_small_pair, src_extension, separate_sign, Mainsystem, SubsystemBase, InstructionBase, MacroProc


class Instruction_DefineConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=2)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        v = args[0]
        names = args[1:]

        for name in names:
            self._sub.add_const(name, main.valueof(v))

class Instruction_IncrementConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=1)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        for name in args:
            self._sub.replace_const(name, str(int(self._sub.valueof(name)) + 1))

class Instruction_RedefineConst(InstructionBase):
    def __init__(self, _name, _sub: SubsystemBase):
        super().__init__(_name, _least_argc=2)
        self._sub = _sub
    def put(self, main: Mainsystem, args:list):
        v = args[0]
        for name in args[1:]:
            self._sub.replace_const(name, main.valueof(v))

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
        r.add_ins(Instruction_IncrementConst("inc", r))
        r.add_ins(Instruction_RedefineConst("redef", r))
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
        r.add_ins(Instruction_Clean("clean", r, 0))
        r.add_ins(Instruction_DefineVar("def", r))
        r.add_ins(Instruction_Pass("set", r, 0))
        r.add_ins(Instruction_Pass("add", r, 0))
        r.add_ins(Instruction_Pass("sub", r, 0))
        r.add_ins(Instruction_Pass("copy", r, 0))
        r.add_ins(Instruction_Pass("copyadd", r, 0))
        r.add_ins(Instruction_Pass("copysub", r, 0))
        r.add_ins(Instruction_Pass("move", r, 0))
        r.add_ins(Instruction_Pass("moveadd", r, 0))
        r.add_ins(Instruction_Pass("moveadd", r, 0))

        return r

    def put_init(self, args:list):
        if len(args) == 1 and args[0].isdigit():
            self.resize(int(args[0]))
        else:
            for arg in args:
                self.add_var(arg)

    def put_clean(self, args:list):
        if len(args) == 1 and args[0] == "fast":
            return

        self._main.put(">" * self.offset())
        self._main.put("[-]>" * self.size())
        self._main.put("<" * (self.offset() + self.size()))

    def put(self, name, args:list):
        if name == "init":
            self.put_init(args)
            return
        if name == "clean":
            self.put_init(args)
            return

        if name in ["move", "moveadd", "movesub", "copy", "copyadd", "copysub"]:
            vss = args

            if len(vss) == 0:
                return

            for i in vss:
                if not self._main.is_sub(i, "vars"):
                    Exception(f"destinations of [vars:{name}] should be vars")
                if set(self._vars) <= set(self._main.variablesof(i)):
                    Exception(f"destinations of [vars:{name}] should be subset of this vars")

            for v in self._vars:
                self._main.put_invoke(name, [self.name() + ":" + v] + [vs + ":" + v for vs in vss])
            
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
                if set(self._vars) <= set(self._main.variablesof(i)):
                    Exception(f"additional destinations of [vars:set] should have variables in this vars")

            vss = [self.name()] + vss

            for i in range(self.size()):
                imm = imms[i]
                self._main.put_invoke("set", [imm] + [sign + j + ":" + self._vars[i] for j in vss])
            
            return

        raise Exception(f"unknown instruction [vars:{name0}/{len(args)}] {self.name()}(vars):len={self.size()}")

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
                self.put(ins_name, ins_args)
            else:
                self._main.put_invoke(ins_name, ins_args)

