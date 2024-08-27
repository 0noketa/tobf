
# a to-bf compiler

from __future__ import annotations
from typing import cast, Union, List, Tuple, Set, Dict, Type, Callable
import io

src_extension = "txt"

def split(s:str, sep=None, maxsplit=-1) -> List[str]:
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

    return (max(x, y), min(x, y))

def calc_small_triple(n: int) -> Tuple[int, int, int]:
    """n: result0 * result1\n
    {result0} > {result1}\n
    usage: +{result0}[>+{result1}<-]<+{result2}
    """

    x = n
    y = 1
    d = 0

    for i in range(16):
        x2, y2 = calc_small_pair(n - i, 1)

        if y2 != 1 and x + y + d > x2 + y2 + i:
            x = x2
            y = y2
            d = i

    return (x, y, d)

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
        self._is_constant_sub = False
        self._vars = []
        self._var_stack = {}
        self._pub_vars = []
        self._size = 0

    def __lt__(self, sub) -> bool:
        if self._address < sub._address:
            return True

        if self._address > sub._address:
            return False

        return self._size < sub._size

    def name(self):
        return self._name
    def set_base(self, addr: int):
        if self._address is not None and (self._size > 0 or not self._fixed):
            raise Exception(f"can not move subsystem instance")
        self._address = addr
    def def_as_const_sub(self, _is_constant_sub=True):
        self._is_constant_sub = _is_constant_sub
        self._size = 0
        self._address = 0
        self._fixed = True
    def is_const_sub(self):
        return self._is_constant_sub
    def fix(self, _fixed=True):
        self._fixed = _fixed
    def resize(self, size: int):
        if self._fixed:
            raise Exception(f"failed to resize fixed area of {self._name}")

        self._size = size
    def has_const(self, name: str) -> bool:
        return name in self._consts
    def def_const(self, name: str, value:int) -> bool:
        if name.isdigit():
            return False

        if name not in self._consts:
            self._consts[name] = value

        return True
    def replace_const(self, name: str, value:int) -> bool:
        if name not in self._consts:
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
    def has_short_move(self, dsts: List[str]) -> bool:
        """True if subsystem has short version of array-to-array move"""
        return False
    def has_short_copy(self, dsts: List[str]) -> bool:
        """True if subsystem has short version of array-to-array move"""
        return False
    def put_short_array_move(self, dsts: List[str]):
        raise Exception(f"not implemented")
    def put_short_array_copy(self, dsts: List[str]):
        raise Exception(f"not implemented")

    def vars(self) -> List[str]:
        return self._vars.copy()
    def has_var(self, name: str) -> bool:
        return name in self.vars()
    def def_var(self, name: str, is_public=True, stack=False) -> bool:
        if self._fixed and self._size <= len(self._vars):
            raise Exception(f"cant add var to fixed area of {self._name}")
        if name.isdigit():
            return False

        if stack:
            if name not in self._vars:
                idx = len(self._vars)
                self._vars.append(f"__tobf_hidden_var{idx}")
            else:
                idx = self._vars.index(name)
                self._vars[idx] = f"__tobf_hidden_var{idx}"

            if name not in self._var_stack:
                self._var_stack[name] = []
            else:
                self._var_stack[name].append(idx)
        elif name not in self._vars:
            idx = self.indexof_reserved_var()
        else:
            idx = -1

        if idx != -1:
            self._vars[idx] = name

            if is_public:
                self._pub_vars.append(name)

        return True
    def indexof_reserved_var(self):
        for i, name in enumerate(self._vars):
            if name.startswith("__tobf_reserved_var"):
                return i

        i = len(self._vars)

        self._vars.append(f"__tobf_reserved_var{i}")

        return i
    def undef_var(self, name):
        if name not in self._vars:
            return
        idx = self._vars.index(name)
        self._vars[idx] = f"__tobf_reserved_var{idx}"
    def pop_var(self, name):
        if name not in self._var_stack:
            return

        self.undef_var(name)

        if len(self._var_stack[name]) > 0:
            idx = self._var_stack[name].pop()
            self._vars[idx] = name
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
    def __init__(self, name: str, params: List[str], codes: List[List[str]], has_va=False):
        self.name = name
        self.params = params
        self.codes = codes
        self.has_va = has_va

    def put(self, name: str, args: List[str], put: Callable[[str, List[str]]], mod="", vars: List[str] = []):
        """mod, vars: information of module this macro function belongs to"""

        if (len(args) <= len(self.params) if self.has_va
                else len(args) != len(self.params)):
            msg_va = "+" if self.has_va else ""
            raise Exception(f"{self.name} uses {len(self.params)}{msg_va}, got {len(args)}")

        if self.has_va:
            va = args[len(self.params):]
            args = args[:len(self.params)]

        for code in self.codes:
            if len(code) == 0:
                continue

            ins_name = code[0]
            if ins_name in self.params:
                ins_name = args[self.params.index(ins_name)]
            ins_args0: List[str] = code[1:]
            ins_args = []
            skipping_va = 0

            i = 0
            while i < len(ins_args0):
                sign, c = separate_sign(ins_args0[i])

                if ":" in c:
                    obj, key = c.split(":")
                else:
                    obj = c
                    key = ""

                if obj == "*":
                    ins_args0.pop(i)
                    for a in reversed(va):
                        if key != "":
                            a = a + ":" + key
                        ins_args0.insert(i, a)

                    skipping_va = len(va)

                    continue

                if skipping_va > 0:
                    skipping_va -= 1
                else:
                    if obj in self.params:
                        obj = args[self.params.index(obj)]
                    elif obj in vars:
                        obj = mod + ":" + obj

                if key != "":
                    ins_args.append(sign + obj + ":" + key)
                else:
                    ins_args.append(sign + obj)

                i += 1

            put(ins_name, ins_args)

        return

