
# a to-bf compiler

import io

src_extension = "txt"

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
        self._initialized = False
        self._name = _name
        self._instructions = _instructions.copy()
        self._consts = _consts.copy()
        self._enums = _enums.copy()
        self._vars = _vars.copy()
        self._size = _size
    def copy(self, _name:str, _to=None):
        if _to == None:
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
    def is_intialized(self):
        return self._initialized
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

        return self._main.valueof(name)
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
    def put_init(self, args:list):
        self._initialized = True
    def put_clean(self, args:list):
        pass
    def offset(self):
        """offset of this subsystem"""
        return self._offset
    def size(self):
        return len(self._vars) if self._size == -1 else self._size

