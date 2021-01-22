
# a to-bf compiler

import io

src_extension = "txt"

def split(s:str, sep=None, maxsplit=-1) -> list:
    if sep == None:
        return list(filter(len, map(str.strip, s.strip().split(maxsplit=maxsplit))))
    else:
        return list(map(str.strip, s.strip().split(sep=sep, maxsplit=maxsplit)))

def split_list(src:list, sep) -> list:
    r = []
    r2 = []

    for i in src:
        if i == sep:
            r.append(r2)
            r2 = []
        else:
            r2.append(i)

    if len(r2):
        r.append(r2)

    return r

def separate_sign(name):
    if type(name) == str and len(name) > 0 and name[0] in ["+", "-"]:
        return name[0], name[1:]
    else:
        return "", name

def calc_small_pair(n, vs):
    """n: result0 * result1\n
    vs: num of vars\n
    {result0} > {result1}\n
    usage: +{result0}[>+{result1}<-]"""

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


class Mainsystem:
    def is_val(self, value) -> bool:
        """is valid immediate"""
        sign, value = separate_sign(value)
        return (type(value) == int
            or type(value) == str
                and (value.isdigit()
                    or len(value) > 0 and value[0] == "'"))
    def is_var(self, value) -> bool:
        """is valid variable"""
        return False
    def is_signed(self, value) -> bool:
        """is valid signed value"""
        return (type(value) == str and len(value) > 1
            and value[0] in ["+", "-"])
    def is_sub(self, value, typ="") -> bool:
        """is valid subsystem"""
        return False
    def has_var(self, name:str) -> bool:
        """is valid variable of main"""
        return False
    def addressof(self, name:str) -> int:
        return 0
    def valueof(self, value:str) -> int:
        """constant"""
        if not self.is_val(value):
            return -1024

        sign, value = separate_sign(value)

        if value[0] == "'":
            return ord(value[1]) if len(value) > 1 else 32
        else:
            return int(value)
    def valuesof(self, name:str) -> int:
        """constant"""
        return 0
    def variablesof(self, name:str) -> list:
        """list of variables in a subsystem"""
        return []
    def offsetof_subsystem(self, alias:str) -> int:
        return 0
    def subsystem_by_name(self, name):
        """returns SubsystemBase"""
        return SubsystemBase()
    def subsystem_by_alias(self, name):
        """returns SubsystemBase"""
        return SubsystemBase()
    def put(self, s:str):
        pass
    def put_at(self, addr:int, s:str):
        """>>>something<<<"""
        pass
    def put_invoke(self, name:str, args:list):
        pass
    @staticmethod
    def read_file(file:str) -> tuple:
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
        self._main: Mainsystem = None
        self._basename = ""
        self._name = _name
        self._instructions = _instructions.copy()
        self._consts = _consts.copy()
        self._enums = _enums.copy()
        self._fixed = False
        self._vars = _vars.copy()
        self._size = _size
    def copy(self, _name:str, _to=None):
        if _to == None:
            r = type(self)(_name)
        else:
            r = _to(_name)
        r._basename = self._name if self._basename == "" else self._basename
        r._main=self._main
        r._instructions=self._instructions
        r._consts=self._consts
        r._enums=self._enums
        r._fixed=self._fixed
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
    def basename(self):
        return self._basename
    def fix(self, _fixed=True):
        self._fixed = _fixed
    def resize(self, size:int):
        if self._fixed:
            raise Exception(f"failed to resize fixed area of {self._name}")

        self._size = size
    def has_const(self, name: str) -> bool:
        return name in self._consts.keys()
    def add_const(self, name: str, value:int) -> bool:
        if name.isdigit():
            return False

        if not (name in self._consts):
            self._consts[name] = value

        return True
    def replace_const(self, name: str, value:int) -> bool:
        if not (name in self._consts):
            return False

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
        if self._fixed:
            raise Exception(f"cant add var to fixed area of {self._name}")
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

        return self._main.valueof(name)
    def addressof(self, name: str) -> int:
        if self.has_var(name):
            return self._vars.index(name) + self.offset()

        raise Exception(f"unknown var {name}")

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
    def can_skip(self) -> bool:
        """returns True if this class has shorter version of address calculator"""
        return False
    def put_skip_right(self):
        """skip right area for this subsystem.\n
        when called, pointer is pointing first cell of this subsystem.\n
        after calling, points next to the last cell."""
        self._main.put(">" * self.size())
    def put_skip_left(self):
        """skip left area for this subsystem"""
        self._main.put("<" * self.size())
    def put(self, name:str, args:list):
        if name == "init":
            return self.put_init(args)
        if name == "clean":
            return self.put_clean(args)

        ins: InstructionBase = self._instructions[name]

        ins.put(self._main, args)

    def put_init(self, args:list):
        pass
    def put_clean(self, args:list):
        pass
    def offset(self, n: int = 0):
        """adds base address of this subsystem"""
        return self._offset + n
    def size(self):
        return len(self._vars) if self._size == -1 else self._size


class MacroProc:
    def __init__(self, name, params, codes):
        self.name = name
        self.params = params
        self.codes = codes
