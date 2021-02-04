
# a to-bf compiler

from __future__ import annotations
from typing import cast, Union, List, Tuple, Set, Dict, Type, Callable
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



class InstructionBase:
    def __init__(self, _name, _least_argc = 0):
        super().__init__()
        self._name = _name
        self._least_argc = _least_argc
    def name(self):
        return self._name
    def least_argc(self):
        return self._least_argc
    def put(self, main, args:list):
        pass

class SubsystemBase:
    """module-like extension that can be specialized like classes"""
    def __init__(self, main, name: str):
        self._address = cast(int, None)
        self._main = main
        self._name = name
        self._instructions: Dict[str, InstructionBase] = {}
        self._consts = {}
        self._enums = {}
        self._fixed = False
        self._vars = []
        self._pub_vars = []
        self._size = 0
    def name(self):
        return self._name
    def set_base(self, addr: int):
        if self._address != None:
            raise Exception(f"can not move subsystem instance")
        self._address = addr
    def fix(self, _fixed=True):
        self._fixed = _fixed
    def resize(self, size: int):
        if self._fixed:
            raise Exception(f"failed to resize fixed area of {self._name}")

        self._size = size
    def has_const(self, name: str) -> bool:
        return name in self._consts.keys()
    def def_const(self, name: str, value:int) -> bool:
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
    def def_enum(self, name: str) -> bool:
        if name.isdigit():
            return False

        if not (name in self._enums):
            self._enums.append(name)

        return True
    def array_size(self) -> int:
        """number of elements"""
        return 0
    def is_readable_array(self) -> bool:
        """True if subsystem implements arraylike structure, and allows direct-read."""
    def is_writable_array(self) -> bool:
        """True if subsystem implements arraylike structure, and allows direct-write."""
    def readable_vars(self) -> List[str]:
        """variables that are allowed direct-read. excludes array indices."""
        return self._pub_vars.copy()
    def writable_vars(self) -> List[str]:
        """variables that are allowed direct-write. excludes array indices."""
        return self._pub_vars.copy()
    def vars(self) -> List[str]:
        return self._vars.copy()
    def has_var(self, name: str) -> bool:
        return name in self.vars()
    def def_var(self, name: str, is_public=True) -> bool:
        if self._fixed and self._size <= len(self._vars):
            raise Exception(f"cant add var to fixed area of {self._name}")
        if name.isdigit():
            return False

        if not (name in self._vars):
            self._vars.append(name)

            if is_public:
                self._pub_vars.append(name)

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
    def put(self, name:str, args:list, tmps: List[int]):
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
        return self._address + n
    def size(self):
        return len(self._vars) if self._size == -1 else self._size

class Subsystem(SubsystemBase):
    """interface"""
    def __init__(self,
            main,
            name: str,
            args: List[str],
            instantiate: Callable[[int, Union[Subsystem, None], Union[List[str], None]], int]):
        pass


class MacroProc:
    def __init__(self, name, params, codes):
        self.name = name
        self.params = params
        self.codes = codes
