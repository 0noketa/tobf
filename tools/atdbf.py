# Minimal-2D to 1D language compiler
#
# Minimal-2D:
# https://esolangs.org/wiki/Minimal-2D
from typing import Tuple, List, Dict, Callable
import sys

class CellInfo:
    def __init__(self, left: int = -1, right: int = -1, up: int = -1, down: int = -1) -> None:
        self.left = left
        self.right = right
        self.up = up
        self.down = down

    def get(self, dx: int, dy: int) -> int:
        if dx != dy:
            if dx == -1:
                return self.left
            if dx == 1:
                return self.right
            if dy == -1:
                return self.up
            if dy == 1:
                return self.down

        raise Exception(f"unknown direction ({dx}, {dy})")

    def set(self, dx: int, dy: int, v: int) -> int:
        if dx != dy:
            if dx == -1:
                self.left = v
            if dx == 1:
                self.right = v
            if dy == -1:
                self.up = v
            if dy == 1:
                self.down = v
            
            return

        raise Exception(f"unknown direction ({dx}, {dy})")

class LoaderState:
    def __init__(self,
            code: List[Tuple[int, str, int]],
            lbl: int, x: int, y: int, dx: int, dy: int, 
            stubs: List[int], 
            stk: List[Tuple[int, int, int, int]]
            ) -> None:
        self.code = code
        self.lbl = lbl
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.stubs = stubs
        self.stk = stk

    def get(self) -> Tuple[List[Tuple[int, str, int]], int, int, int, int, int]:
        return (self.code, self.lbl, self.x, self.y, self.dx, self.dy, self.stubs, self.stk)

class Abstract2DBrainfuck:
    """abstract superset of some 2D Brainfuck that has not complex features"""


    # language definition
    NAME = "language name"
    HELP = ""
    SYMS_START = []
    SYMS_EXIT = []
    SYMS_TURN = []  # LRUD. currently can not assign multiple symbol to the same direction
    SYMS_TURNNZ = []  # if not zero
    SYMS_MIRROR_R_TO_U = []  # /
    SYMS_MIRROR_R_TO_D = []  # \
    SYMS_MIRROR_R_TO_L = []  # L<->R U<->D 
    SYMS_MIRROR_H = [] # L<->R 
    SYMS_MIRROR_V = [] # U<->D
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_ROT_R = []
    SYMS_ROT_L = []
    SYMS_ROTZ_R = []
    SYMS_ROTZ_L = []
    SYMS_ROTNZ_R = []
    SYMS_ROTNZ_L = []
    SYMS_ROTZNZ_R_L = []
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = [] # skip next
    SYMS_SKIPZ = [] # if zero
    SYMS_PTR_INC = []
    SYMS_PTR_DEC = []
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = []
    SYMS_DEC = []
    SYMS_PUT = []
    SYMS_GET = []
    # instructions with other functions
    INS_TBL: Dict[str, Callable[[LoaderState], LoaderState]] = {}
    DEFAULT_MEM_WIDTH = -1 # if not -1, uses 2D memory

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        self.width = 0
        self.height = 0
        self.argv = argv

        if type(self).DEFAULT_MEM_WIDTH != -1:
            self.data_width = 32

        if source is not None:
            self.load_source(source)

    def load_source(self, s: str):
        ss = s.split("\n")
        self.width = max(map(len, ss))
        self.height = len(ss)

        self.source = [i + " " * (self.width - len(i)) for i in ss]

    def find_entry_point(self):
        cls = type(self)

        if len(cls.SYMS_START) == 0:
            return (0, 0)

        for y, row in enumerate(self.source):
            for x, c in enumerate(row):
                if c in cls.SYMS_START:
                    return (x, y)
        
        return (0, 0)

    def create_label_table(self):
        return [[CellInfo() for _ in range(self.width)] for _ in range(self.height)]

    def name_to_dir(self, name: str) -> Tuple[int, int]:
        cls = type(self)
        if len(cls.SYMS_TURN) < 4 or name not in cls.SYMS_TURN:
            raise Exception(f"{cls.NAME} has not any non-conditional direction controll")

        return {
            cls.SYMS_TURN[0]: (-1, 0),
            cls.SYMS_TURN[1]: (1, 0),
            cls.SYMS_TURN[2]: (0, -1),
            cls.SYMS_TURN[3]: (0, 1)
        }[name]

    def is_valid_pos(self, x: int, y: int) -> bool:
        return x in range(self.width) and y in range(self.height)

    def skip_bracket(self, x, y, dx, dy):
        cls = type(self)
        if len(cls.SYMS_BF_BRACKETS) < 2:
            raise Exception(f"{cls.NAME} has not Brainfuck-like loop")

        begin = self.source[y][x]
        end = {
            cls.SYMS_BF_BRACKETS[0]: cls.SYMS_BF_BRACKETS[1],
            cls.SYMS_BF_BRACKETS[1]: cls.SYMS_BF_BRACKETS[0]
        }[begin]
        d = 0
        x += dx
        y += dy
        while x in range(self.width) and y in range(self.height) and (d > 0 or self.source[y][x] != end):
            if self.source[y][x] == begin:
                d += 1
            if self.source[y][x] == end:
                d -= 1
            x += dx
            y += dy

        return (x + dx, y + dy)

    def rotate_dir(self, dx, dy, clockwise=True) -> Tuple[int, int]:
        if dx == 1 if clockwise else dx == -1:
            return (0, 1)
        if dy == 1 if clockwise else dy == -1:
            return (-1, 0)
        if dx == -1 if clockwise else dx == 1:
            return (0, -1)
        if dy == -1 if clockwise else dy == 1:
            return (1, 0)

    def compile_to_intermediate(self) -> List[Tuple[int, str, int]]:
        cls = type(self)
        if len(cls.SYMS_BF_BRACKETS):
            bf_bracket_left, bf_bracket_right = cls.SYMS_BF_BRACKETS
        else:
            bf_bracket_left = ""
            bf_bracket_right = ""

        labels = self.create_label_table()
        stubs = []
        lbl = 0
        code = []
        stk = []
        x, y = self.find_entry_point()
        dx = 1
        dy = 0

        while len(stk) > 0 or self.is_valid_pos(x, y):
            onexit = False
            lbl0 = -1

            if len(stk) > 0 and not self.is_valid_pos(x, y):
                code.append((lbl, "exit", 0))
                onexit = True
                c = " "
            else:
                cell_labels = labels[y][x]
                c = self.source[y][x]

                if c in cls.SYMS_EXIT:
                    code.append((lbl, "exit", 0))
                    onexit = True
                else:
                    lbl0 = cell_labels.get(dx, dy)

                    if lbl0 != -1:
                        code.append((lbl, "jmp", lbl0))
                        onexit = True

            if onexit:
                if len(stk) == 0:
                    break

                lbl += 1
                x, y, dx, dy = stk.pop()
                branch_idx = stubs.pop()

                branch_lbl, op, _ = code[branch_idx]
                code[branch_idx] = (branch_lbl, op, lbl)

                continue

            # sys.stderr.write(f"{lbl:08}: ({x}, {y}) -> ({dx}, {dy})\n")
            cell_labels.set(dx, dy, lbl)

            if c in cls.SYMS_TURN:
                code.append((lbl, "", 0))

                lbl += 1
                dx, dy = self.name_to_dir(c)

                x += dx
                y += dy

                continue
            elif c in cls.SYMS_MIRROR_R_TO_U:
                code.append((lbl, "", 0))

                lbl += 1

                dx, dy = -dy, -dx

                x += dx
                y += dy

                continue
            elif c in cls.SYMS_MIRROR_R_TO_D:
                code.append((lbl, "", 0))

                lbl += 1

                dx, dy = dy, dx

                x += dx
                y += dy

                continue
            elif c in cls.SYMS_SKIP:
                code.append((lbl, "", 0))
                x += dx
                y += dy
            elif c in cls.SYMS_PUT:
                code.append((lbl, ".", 1))
            elif c in cls.SYMS_GET:
                code.append((lbl, ",", 1))
            elif c in cls.SYMS_PTR_INC:
                code.append((lbl, ">", 1))
            elif c in cls.SYMS_PTR_DEC:
                code.append((lbl, "<", 1))
            elif c in cls.SYMS_INC:
                code.append((lbl, "+", 1))
            elif c in cls.SYMS_DEC:
                code.append((lbl, "-", 1))
            elif c in cls.SYMS_MIRROR_R_TO_L:
                code.append((lbl, "", 0))

                dx = -dx
                dy = -dy
            elif c in cls.SYMS_PTR_DOWN:
                code.append((lbl, ">", self.data_width))
            elif c in cls.SYMS_PTR_UP:
                code.append((lbl, "<", self.data_width))
            elif c in cls.SYMS_TURNNZ:
                stubs.append(len(code))
                stk.append((x + dx, y + dy, dx, dy))

                code.append((lbl, "jz", -1))

                if c == cls.SYMS_TURNNZ[0]:
                    dx, dy = (-1, 0)
                if c == cls.SYMS_TURNNZ[1]:
                    dx, dy = (1, 0)
                if c == cls.SYMS_TURNNZ[2]:
                    dx, dy = (0, -1)
                if c == cls.SYMS_TURNNZ[3]:
                    dx, dy = (0, 1)
            elif c in cls.SYMS_SKIPZ:
                x2 = x + dx
                y2 = y + dy
                x3 = x2 + dx
                y3 = y2 + dy

                stubs.append(len(code))
                stk.append((x3, y3, dx, dy))

                code.append((lbl, "jz", -1))
            elif c in cls.SYMS_ROT_L:
                code.append((lbl, "", 0))
                dx, dy = self.rotate_dir(dx, dy, clockwise=False)
            elif c in cls.SYMS_ROT_R:
                code.append((lbl, "", 0))
                dx, dy = self.rotate_dir(dx, dy)
            elif c in cls.SYMS_ROTZ_R:
                dx2, dy2 = self.rotate_dir(dx, dy)

                stubs.append(len(code))
                stk.append((x + dx2, y + dy2, dx2, dy2))

                code.append((lbl, "jz", -1))
            elif c in cls.SYMS_ROTNZ_R:
                dx2, dy2 = self.rotate_dir(dx, dy)

                stubs.append(len(code))
                stk.append((x + dx, y + dy, dx, dy))

                code.append((lbl, "jz", -1))

                dx = dx2
                dy = dy2
            elif c in cls.SYMS_ROTZNZ_R_L:
                dx2, dy2 = self.rotate_dir(dx, dy)
                dx3, dy3 = self.rotate_dir(dx, dy, False)

                stubs.append(len(code))
                stk.append((x + dx2, y + dy2, dx2, dy2))

                code.append((lbl, "jz", -1))

                dx = dx3
                dy = dy3
            elif c == bf_bracket_left:
                x2, y2 = self.skip_bracket(x, y, dx, dy)

                stubs.append(len(code))
                stk.append((x2, y2, dx, dy))

                code.append((lbl, "jz", -1))
            elif c == bf_bracket_right:
                x2, y2 = self.skip_bracket(x, y, -dx, -dy)

                code.append((lbl, "jz", lbl + 2))
                lbl += 1

                stk.append((x2 + dx * 2, y2 + dy * 2, dx, dy))

                stubs.append(len(code))
                code.append((lbl, "jmp", -1))
            elif c in cls.SYMS_MIRRORNZ_R_TO_L:
                stubs.append(len(code))
                stk.append((x + dx, y + dy, dx, dy))

                code.append((lbl, "jz", -1))

                dx = -dx
                dy = -dy
            elif c in cls.INS_TBL.keys():
                stat = cls.INS_TBL[c](LoaderState(code, lbl, x, y, dx, dy, stubs, stk))
                code, lbl, x, y, dx, dy, stubs, stk = stat.get()

                continue
            else:
                code.append((lbl, "", 0))

            x += dx
            y += dy
            lbl += 1

        return code


class Minimal2D(Abstract2DBrainfuck):
    # language definition
    NAME = "Minimal-2D"
    HELP = ""
    SYMS_START = []
    SYMS_EXIT = []
    SYMS_TURN = list("LRUD")
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = []
    SYMS_MIRROR_R_TO_D = []
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = ["/"]
    SYMS_PTR_INC = [">"]
    SYMS_PTR_DEC = ["<"]
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = [","]
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)


class CompilerState:
    def __init__(self, labels: List[int]) -> None:
        self.labels = labels


class InterpreterState:
    def __init__(self, data: List[int], ptr: int, ip: int):
        self.data = data
        self.ptr = ptr
        self.ip = ip

    def get(self):
        return (self.data, self.ptr, self.ip)

class IntermediateExtension:
    def __init__(self) -> None:
        pass

    def is_register_based(self) -> bool:
        """True when language uses registers instead of array"""
        return False
    def n_registers(self) -> int:
        return 0
    def n_hidden_registers(self) -> int:
        return 0

    def has_instruction(self, name: str) -> bool:
        return False
    def is_instruction_for_jump(self, name: str) -> bool:
        return False
    def is_instruction_with_sideefect(self, name: str) -> bool:
        return False
    def is_mergeable_instruction(self, name: str) -> bool:
        return False
    def requires_initialization(self) -> bool:
        return False
    def requires_finalization(self) -> bool:
        return False

    # for compilers
    def get_initializer(self, target_language: str, stat: CompilerState) -> List[str]:
        return []
    def get_finalizer(self, target_language: str, stat: CompilerState) -> List[str]:
        return []
    def can_compile_to(self, target_language: str, stat: CompilerState) -> bool:
        return False
    def compile_instruction(self, target_language: str, op: str, arg: int, stat: CompilerState) -> List[str]:
        return []

    # for interpreters
    def initialize(self, stat: InterpreterState) -> InterpreterState:
        """returns modified state"""
        return stat
    def finalize(self, stat: InterpreterState) -> InterpreterState:
        """returns modified state"""
        return stat
    def can_invoke(self) -> bool:
        return False
    def invoke_instruction(self, name: str, arg: int, stat: InterpreterState) -> InterpreterState:
        """returns modified state"""
        return stat

class IntermediateCompiler:
    NAME = ""

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        self.src = src
        self.mem_size = mem_size
        self.ex = extension

        self.known_ins = []

        labels = self.get_used_labels()
        act_labels = self.get_active_labels()

        for i in labels:
            if i not in act_labels:
                sys.stderr.write(f"label {i} does not exist.\n")

        self.update_labels()
        self.optimize()

    def get_extension_initializer(self, stat: CompilerState) -> List[str]:
        dst = []
        if self.ex is not None:
            if self.ex.can_compile_to(type(self).NAME) and self.ex.requires_initialization():
                dst.extend(self.ex.get_initializer(type(self).NAME, stat))

        return dst

    def get_extension_finalizer(self, stat: CompilerState) -> List[str]:
        dst = []
        if self.ex is not None:
            if self.ex.can_compile_to(type(self).NAME) and self.ex.requires_finalization():
                dst.extend(self.ex.get_finalizer(type(self).NAME, stat))

        return dst

    def compile_extension(self, op: str, arg: int, stat: CompilerState) -> List[str]:
        if self.ex is not None:
            if self.ex.can_compile_to(type(self).NAME) and self.ex.has_instruction(op):
                return self.ex.compile_instruction(type(self).NAME, op, arg, stat)

        return []

    def initialize_extension(self, stat: InterpreterState) -> InterpreterState:
        if self.ex is not None:
            if self.ex.can_invoke() and self.ex.requires_initialization():
                stat = self.ex.initialize(stat)

        return stat

    def finalize_extension(self, stat: InterpreterState) -> InterpreterState:
        if self.ex is not None:
            if self.ex.can_invoke() and self.ex.requires_finalization():
                stat = self.ex.finalize(stat)

        return stat

    def invoke_extension(self, op: str, arg: int, stat: InterpreterState) -> InterpreterState:
        if self.ex is not None:
            if self.ex.can_invoke() and self.ex.has_instruction(op):
                return self.ex.invoke_instruction(op, arg, stat)

        return stat

    def is_extension(self, name: str) -> bool:
        if self.ex is not None:
            if self.ex.has_instruction(name):
                return True

        return False

    def is_instruction_for_jump(self, name: str) -> bool:
        if name in ["jmp", "jz"]:
            return True

        if self.ex is not None:
            if self.ex.has_instruction(name) and self.ex.is_instruction_for_jump(name):
                return True

        return False

    def is_mergeable_instruction(self, name: str) -> bool:
        if name in [">", "<", "+", "-"]:
            return True

        if self.ex is not None:
            if self.ex.has_instruction(name) and self.ex.is_mergeable_instruction(name):
                return True

        return False

    def compile(self) -> List[str]:
        return []

    def get_used_labels(self) -> List[int]:
        return sorted(list(set([arg for lbl, op, arg in self.src if self.is_instruction_for_jump(op)])))

    def get_active_labels(self) -> List[int]:
        return sorted(list(set([lbl for lbl, op, arg in self.src if lbl != -1])))

    def skip_mergeable(self, idx: int) -> Tuple[int, int]:
        if idx not in range(len(self.src)):
            return (len(self.src), 0)

        lbl0, op0, arg0 = self.src[idx]

        if not self.is_mergeable_instruction(op0):
            return (idx + 1, arg0)

        for i, (lbl, op, arg) in enumerate(self.src[idx + 1:]):
            if op != op0 or lbl != -1:
                return (idx + 1 + i, arg0)

            arg0 += arg

        return (len(self.src), arg0)

    def merge_increment(self):
        old_size = len(self.src)

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]

            if self.is_mergeable_instruction(op):
                j, arg2 = self.skip_mergeable(i) 
                self.src[i] = (lbl, op, arg2)
                self.src = self.src[:i + 1] + self.src[j:]

            i += 1

        return len(self.src) != old_size

    def rename_label(self, from_: int, to_: int):
        x = len(self.src)
        for i, (lbl, op, arg) in enumerate(self.src):
            if lbl == from_:
                self.src[i] = (to_, op, arg)

            if self.is_instruction_for_jump(op) and arg == from_:
                self.src[i] = (lbl, op, to_)

    def update_labels(self):
        labels = self.get_used_labels()

        for i, (lbl, op, arg) in enumerate(self.src):
            if lbl in labels:
                self.rename_label(lbl, i)
            else:
                self.src[i] = (-1, op, arg)

    def remove_nop(self) -> bool:
        """takes labels from every nop and removes all nop\n
           returns True if any nop was removed
        """
    
        old_size = len(self.src)
        i = old_size
        while i > 0:
            i -= 1
            lbl, op, arg = self.src[i]

            if lbl == -1:
                if i > 0 and op != "":
                    for j in range(i - 1, -1, -1):
                        lbl2, op2, arg2 = self.src[j]

                        if op2 != "":
                            break

                        if lbl2 != -1:
                            self.src[i] = (lbl2, op, arg)
                            self.src[j] = (-1, "", 0)
                            break

                if op == "":
                    self.src.pop(i)

        return old_size != len(self.src)

    def optimize(self):
        self.optimize0()
        self.update_labels()

        if self.merge_increment():
            self.update_labels()

        if self.reduce_loops():
            self.update_labels()

        if self.remove_conditional_jump_by_const():
            self.update_labels()

            if type(self).NAME != "interpreter":
                if self.remove_conditional_jump_by_const():
                    self.update_labels()

            if self.remove_nop():
                self.update_labels()
        
        if type(self).NAME != "interpreter":
            self.optimize0()
            self.update_labels()

            if self.merge_increment():
                self.update_labels()

            if self.remove_conditional_jump_by_const():
                self.update_labels()

            if self.remove_nop():
                self.update_labels()

            if self.reduce_loops():
                self.update_labels()

    def optimize0(self):
        optimized = True
        while optimized:
            optimized = False

            self.update_labels()
            if self.remove_nop():
                self.update_labels()

            i = 1
            while i < len(self.src):
                lbl0, op0, arg0 = self.src[i - 1]
                lbl, op, arg = self.src[i]

                if self.is_instruction_for_jump(op0) and arg0 == lbl and lbl0 == -1:
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if self.is_instruction_for_jump(op0) and arg0 == lbl and lbl0 != -1:
                    self.rename_label(lbl0, lbl)
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if self.is_instruction_for_jump(op0) and op == "jmp" and arg0 == arg and lbl0 == -1:
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if op0 in ["jmp", "exit"] and op == "jmp" and lbl != -1:
                    self.rename_label(lbl, arg)
                    self.src.pop(i)
                    optimized = True

                    continue

                if op0 in ["jmp", "exit"] and lbl == -1:
                    self.src.pop(i)
                    optimized = True

                    continue

                if op0 == "" and lbl0 != -1 and lbl != -1:
                    self.rename_label(lbl0, lbl)
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if op0 == op and arg0 == arg and (op == "exit" or self.is_instruction_for_jump(op)):
                    if lbl0 == -1:
                        self.src.pop(i - 1)
                        optimized = True

                        continue
                    elif lbl == -1:
                        self.src.pop(i)
                        optimized = True

                        continue
                    elif lbl0 != -1 and lbl != -1:
                        self.rename_label(lbl, lbl0)
                        self.src.pop(i)
                        optimized = True

                        continue

                if (op0 != op
                        and (set([op0, op]) == set(["+", "-"])
                                or set([op0, op]) == set([">", "<"]))):
                    lbl2 = lbl0 if lbl == -1 else lbl
                    op2 = (op if arg0 < arg
                            else op0 if arg0 > arg
                            else "")
                    arg2 = abs(arg - arg0)
                    self.src[i - 1] = (lbl2, op2, arg2)
                    self.src.pop(i)
                    optimized = True

                    continue

                if op0 == "jmp" and arg0 == lbl:
                    self.src[i - 1] = (lbl0, "", 0)
                    optimized = True

                    continue

                i += 1

    def reduce_loops(self):
        old_size = len(self.src)

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]

            if op == "jz":
                # R/D
                # U-L
                #
                # L0: if (!*p) goto L1;
                # *p -= 1;
                # goto L0;
                # L1:
                if arg == i + 3:
                    # this pattern will include many jz with the same destination.
                    lbl2, op2, arg2 = self.src[i + 1]
                    lbl3, op3, arg3 = self.src[i + 2]

                    if lbl2 == -1 and lbl3 == -1 and op2 in ["+", "-"] and op3 == "jmp" and arg3 == i:
                        self.src[i] = (lbl, "assign", 0)
                        self.src.pop(i + 2)
                        self.src.pop(i + 1)

                        self.update_labels()

                        i += 1
                        continue

                # L0: *p -= 1;
                # if (!*p) goto L1;
                # goto L0;
                # L1:
                if i > 0 and arg == i + 2:
                    # this pattern will include many jz with the same destination.
                    lbl2, op2, arg2 = self.src[i - 1]
                    lbl3, op3, arg3 = self.src[i + 1]

                    if lbl == -1 and lbl3 == -1 and op2 in ["+", "-"] and op3 == "jmp" and arg3 == i - 1:
                        self.src[i - 1] = (lbl2, "assign", 0)
                        self.src.pop(i + 1)
                        self.src.pop(i)

                        if i > 1:
                            lbl4, op4, arg4 = self.src[i - 2]

                            if op4 == "jz" and arg4 == i + 2:
                                self.src[i - 2] = (lbl4, "", 0)

                        self.update_labels()
                        continue

            i += 1

        return len(self.src) != old_size

    def remove_conditional_jump_by_const(self) -> bool:
        optimized = False

        for i, (lbl, op, arg) in enumerate(self.src):
            # from:
            #   jmp x
            #   x: jmp y
            #   y: jmp z
            # to:
            #   jmp z
            #   x: jmp z
            #   y: jmp z
            if self.is_instruction_for_jump(op):
                j = i
                lbl2, op2, arg2 = self.src[i]
                while self.src[arg2][1] == op:
                    j = arg2

                    lbl2, op2, arg2 = self.src[j]

                self.src[i] = (lbl, op, arg2)

                if i != j:
                    optimized = True

            # from:
            #   jz x
            #   jz y
            #   jmp z
            # to:
            #   jz x
            #   nop
            #   jmp z
            if self.is_instruction_for_jump(op) or op == "exit":
                for j in range(i + 1, len(self.src)):
                    lbl2, op2, arg2 = self.src[j]

                    if op2 == op:
                        if lbl2 != -1:
                            if arg != arg2:
                                break

                            if lbl == -1:
                                lbl = i
                                self.src[i] = (lbl, op, arg)

                            self.rename_label(lbl2, lbl)

                        self.src[j] = (-1, "", 0)
                        optimized = True
                    else:
                        break

            if op in ["jmp", "exit"]:
                for j in range(i + 1, len(self.src)):
                    lbl2, op2, arg2 = self.src[j]

                    if lbl2 == -1:
                        self.src[j] = (-1, "", 0)
                        optimized = True
                    else:
                        break

        return optimized

class IntermediateToText(IntermediateCompiler):
    NAME = "Abstract2DBrainfuck IL assembly"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = []

        for lbl, op, arg in self.src:
            dst.append(f"{lbl:4}:{op} {arg}")

        return dst


class IntermediateToC(IntermediateCompiler):
    NAME = "C"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = f"""
#include <stdio.h>
#include <stdint.h>
#ifndef DATA_SIZE
#define DATA_SIZE {self.mem_size}
#endif
#ifdef USE_RING
static uint8_t data[DATA_SIZE];
static size_t i = 0;
#define p (&data[i])
#define ptr_inc(d) i = (i + d) % DATA_SIZE;
#define ptr_dec(d) i = (i - d) % DATA_SIZE;
#else
static uint8_t data[DATA_SIZE], *p = data;
#ifdef UNSAFE_MODE
#define ptr_inc(d) p += d;
#define ptr_dec(d) p -= d;
#else
#define ptr_inc(d) p += d; if (p >= data + DATA_SIZE) return 1;
#define ptr_dec(d) p -= d; if (p < data) return 1;
#endif
#endif

int main(int argc, char *argv[]) {{
""".split("\n")

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for lbl, op, arg in self.src:
            if lbl != -1:
                dst.append(f"L{labels.index(lbl)}:")
            
            if op == "jz":
                dst.append(f"if (!*p) goto L{labels.index(arg)};")
            elif op == "jmp":
                dst.append(f"goto L{labels.index(arg)};")
            elif op == "+":
                dst.append(f"*p += {arg};")
            elif op == "-":
                dst.append(f"*p -= {arg};")
            elif op == ">":
                dst.append(f'ptr_inc({arg})')
            elif op == "<":
                dst.append(f'ptr_dec({arg})')
            elif op == ",":
                dst.append(f"*p = getchar();")
            elif op == ".":
                dst.append(f"putchar(*p);")
            elif op == "assign":
                dst.append(f"*p = {arg};")
            elif op == "exit":
                dst.append("return 0;")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append("return 0;")
        dst.append("}")

        return dst


class IntermediateToX86(IntermediateCompiler):
    """uses NASM"""
    NAME = "x86"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = """
; link to something like this

; #include <stdio.h>
; #include <stdint.h>
; extern void bf_main();
; uint8_t bf_data[1024];
; uint32_t bf_getc() { return getchar(); }
; void bf_putc(uint32_t v) { putchar(v); }
; int main(int argc, char *argv[]) { bf_main(); return 0; }

; msvc(x86)/MinGW(x86): nasm -fwin32 --prefix _
; tcc(win32): nasm -felf

; cdecl
extern bf_putc, bf_getc
; data
extern bf_data
global bf_main
section .text
bf_main:
mov edx, bf_data
""".split("\n")

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for lbl, op, arg in self.src:
            if lbl != -1:
                dst.append(f".L{labels.index(lbl)}:")
            
            if op == "jz":
                dst.append("movzx eax, byte[edx]")
                dst.append("or eax, eax")
                dst.append(f"jz .L{labels.index(arg)}")
            elif op == "jmp":
                dst.append(f"jmp .L{labels.index(arg)}")
            elif op == "+":
                dst.append(f"add byte[edx], {arg}")
            elif op == "-":
                dst.append(f"sub byte[edx], {arg}")
            elif op == ">":
                dst.append(f"add edx, {arg}")
            elif op == "<":
                dst.append(f"sub edx, {arg}")
            elif op == ",":
                dst.append("push edx")
                dst.append("call bf_getc")
                dst.append("pop edx")
                dst.append("mov byte[edx], al")
            elif op == ".":
                dst.append("movzx eax, byte[edx]")
                dst.append("push edx")
                dst.append("push eax")
                dst.append("call bf_putc")
                dst.append("pop eax")
                dst.append("pop edx")
            elif op == "assign":
                if arg == 0:
                    dst.append("xor eax, eax")
                else:
                    dst.append(f"mov eax, {arg}")
            elif op == "exit":
                dst.append("ret")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append("ret")

        return dst


class IntermediateToBrainfuckAsmCompiler(IntermediateCompiler):
    NAME = "BrainfuckAsmCompiler"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = ["mov $1, 0"]

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for lbl, op, arg in self.src:
            if lbl != -1:
                dst.append(f"L{labels.index(lbl)}:")
            
            if op == "jz":
                dst.append("mov $0, [$1]")
                dst.append(f"jz $0, L{labels.index(arg)}")
            elif op == "jmp":
                dst.append(f"jmp L{labels.index(arg)}")
            elif op == "+":
                dst.append("mov $0, [$1]")
                dst.append(f"add $0, {arg}")
                dst.append("mov [$1], $0")
            elif op == "-":
                dst.append("mov $0, [$1]")
                dst.append(f"sub $0, {arg}")
                dst.append("mov [$1], $0")
            elif op == ">":
                dst.append(f"add $1, {arg}")
            elif op == "<":
                dst.append(f"sub $1, {arg}")
            elif op == ",":
                dst.append("in $0")
                dst.append("mov [$1], $0")
            elif op == ".":
                dst.append("mov $0, [$1]")
                dst.append("out $0")
            elif op == "assign":
                dst.append(f"mov [$1], {arg}")
            elif op == "exit":
                dst.append("jmp Lexit")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append("Lexit:")

        return dst


class IntermediateToAsmbf(IntermediateCompiler):
    NAME = "asmbf"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = ["mov r1, 0"]

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for lbl, op, arg in self.src:
            if lbl != -1:
                dst.append(f"@mtdc_{labels.index(lbl)}:")
            
            if op == "jz":
                dst.append("rcl r0, r1")
                dst.append(f"jz r0, @mtdc_{labels.index(arg)}")
            elif op == "jmp":
                dst.append(f"jmp @mtdc_{labels.index(arg)}")
            elif op == "+":
                dst.append(f"amp r1, {arg}")
            elif op == "-":
                dst.append(f"smp r1, {arg}")
            elif op == ">":
                dst.append(f"add r1, {arg}")
            elif op == "<":
                dst.append(f"sub r1, {arg}")
            elif op == ",":
                dst.append("in r0")
                dst.append("sto r1, r0")
            elif op == ".":
                dst.append("rcl r0, r1")
                dst.append("out r0")
            elif op == "assign":
                dst.append(f"mov r0, {arg}")
                dst.append("sto r1, r0")
            elif op == "exit":
                dst.append("jmp @mtdc_exit")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append("@mtdc_exit")

        return dst


class IntermediateToCASL2(IntermediateCompiler):
    NAME = "CASL2"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def make_cas(self, lbl, op, args):
        return f"{lbl:10}{op:18}{args}"
    def compile(self) -> List[str]:
        lib = """
; result:GR0
; never returns EOF
GETC      START
          LD      GR0, IBUFINIT
          OR      GR0, GR0
          JNZ     GETC1
          ; init
          IN      IBUF, IBUFSZ
          LD      GR1, =0
          ST      GR1, IIDX
          LD      GR1, =1
          ST      GR1, IBUFINIT
GETC1     LD      GR1, IIDX
          SUBL    GR1, IBUFSZ
          JNZ     GETC2
          ; at EOS
          LD      GR1, =0
          ST      GR1, IIDX
          LD      GR1, =0
          ST      GR1, IBUFSZ
          LD      GR1, =0
          ST      GR1, IBUFINIT
          LD      GR0, =10
          RET
GETC2     LD      GR1, IIDX
          LD      GR0, IBUF, GR1
          OR      GR0, GR0
          JNZ     GETC3
          ; at EOL
          LD      GR1, =0
          ST      GR1, IIDX
          LD      GR1, =0
          ST      GR1, IBUFSZ
          LD      GR1, =0
          ST      GR1, IBUFINIT
          LD      GR0, =10
          RET
GETC3     ADDL    GR1, =1
          ST      GR1, IIDX
          RET
IBUFSZ    DC      0
IBUFINIT  DC      0
IIDX      DC      0
IBUF      DS      256
          END

; parameter:GR0
; if GR0 == 10: print line
; if GR0 == 0: print line when buffer is not empty
PUTC      START
          LD      GR1, GR0
          OR      GR1, GR1
          JZE     IFNEMPTY
          LD      GR1, GR0
          SUBL    GR1, =10
          JZE     FLUSH
          LD      GR1, OIDX
          ST      GR0, OBUF, GR1
          ADDL    GR1, =1
          ST      GR1, OIDX
          SUBL    GR1, =126
          JZE     FLUSH
          RET
IFNEMPTY  LD      GR1, OIDX
          OR      GR1, GR1
          JZE     ENDPUTC
FLUSH     OUT     OBUF, OIDX
          LD      GR1, =0
          ST      GR1, OIDX
ENDPUTC   RET
OIDX      DS      1
OBUF      DS      128
          END
""".split("\n")
        dst = [
            "PROG      START",
            "          LD GR1, =16"
        ]
        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        tab = " " * 10

        for lbl, op, arg in self.src:
            if lbl != -1:
                s = f"L{labels.index(lbl)}"
                s += " " * (10 - len(s))
            else:
                s = tab

            if op == "":
                dst.append(s + "NOP")            
            elif op == "jz":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + "OR GR0, GR0")
                dst.append(tab + f"JZE L{labels.index(arg)}")
            elif op == "jmp":
                dst.append(tab + f"JUMP L{labels.index(arg)}")
            elif op == "+":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + f"ADDL GR0, ={arg}")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif op == "-":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + f"SUBL GR0, ={arg}")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif op == ">":
                dst.append(s + f"ADDL GR1, ={arg}")
            elif op == "<":
                dst.append(s + f"SUBL GR1, ={arg}")
            elif op == ",":
                dst.append(s + "LD GR4, GR1")
                dst.append(tab + "CALL GETC")
                dst.append(tab + "LD GR1, GR4")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif op == ".":
                dst.append(s + "LD GR4, GR1")
                dst.append(tab + "LD GR0, DATA, GR1")
                dst.append(tab + "CALL PUTC")
                dst.append(tab + "LD GR1, GR4")
            elif op == "assign":
                dst.append(s + f"LD GR0, ={arg}")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif op == "exit":
                dst.append(s + "JUMP ONEXIT")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append("ONEXIT    LD GR0, =0")
        dst.append(tab + "CALL PUTC")
        dst.append(tab + "RET")
        dst.append(f"DATA      DS {self.mem_size}")
        dst.append(tab + "END")
        dst += lib

        return dst


class IntermediateToPATH(IntermediateCompiler):
    NAME = "PATH"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        labels = self.get_used_labels()

        dst = [
            "\\"
        ]

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        current_label = -1

        for lbl, op, arg in self.src:
            if lbl != -1:
                current_label = labels.index(lbl)
                dst.append("!")
                dst.append("/ " + " " * (current_label * 3) + f"/!\\ label {current_label}")
            
            if op == "jz":
                dst_label = labels.index(arg)
                if current_label < dst_label:
                    dst.append("  " + " " * dst_label * 3 + "!")
                    dst.append("\\v" + " " * dst_label * 3 + f"\\ jz {dst_label}")
                    dst.append("//" + " " * dst_label * 3 + "!")
                else:
                    dst.append("  " + " " * dst_label * 3 + "  !")
                    dst.append("\\v" + " " * dst_label * 3 + f"  / jz {dst_label}")
                    dst.append("//" + " " * dst_label * 3 + "  !")
            elif op == "jmp":
                dst_label = labels.index(arg)
                if current_label < dst_label:
                    dst.append("  " + " " * dst_label * 3 + "!")
                    dst.append("\\ " + " " * dst_label * 3 + f"\\ jmp {dst_label}")
                    dst.append("  " + " " * dst_label * 3 + "!")
                else:
                    dst.append("  " + " " * dst_label * 3 + "  !")
                    dst.append("\\ " + " " * dst_label * 3 + f"  / jmp {dst_label}")
                    dst.append("  " + " " * dst_label * 3 + "  !")
            elif op in ["+", "-", ",", "."]:
                for _ in range(arg):
                    dst.append(f"{op}")
            elif op == ">":
                dst.append("}")
            elif op == "<":
                dst.append("{")
            elif op == "assign":
                dst.append("v")
                dst.append("-")
                dst.append("!")
                dst.append(" ")
                dst.append("^")
                for _ in range(arg):
                    dst.append(f"{op}")
            elif op == "exit":
                dst.append("#")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append("#")

        return dst


class IntermediateToEnigma2D(IntermediateCompiler):
    NAME = "Enigma-2D"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def new_code_line(self, labels, lbl_idx=-1):
        if lbl_idx == -1:
            return "".join([str(i)[-1] for i in range(len(labels))])
        else:
            return " " * lbl_idx + f"R" + " " * (len(labels) - lbl_idx - 1)
    def new_jump_lines(self, labels, current_label):
        turn = (lambda i: "D" if i > current_label else "U")
        r = [" " * i + turn(i) + " " * (len(labels) - i - 1) for i in range(len(labels))]

        # for exit
        r.append(" " * len(labels))

        return r

    def pad_lines(self, lines, idx=None, c=None, default=" "):
        """add space to every string.\n
           if both idx and c are not None, add c to idx-th line.
        """
        for i in range(len(lines)):
            lines[i] += c if idx is not None and i == idx else default

    def compile(self) -> List[str]:
        labels = self.get_used_labels()

        dst = []
        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        current_label = -1

        code_line = self.new_code_line(labels, current_label)
        code_line2 = " " * len(labels)
        jump_lines = self.new_jump_lines(labels, current_label)


        for lbl, op, arg in self.src:
            if lbl != -1:
                new_label = labels.index(lbl)

                if not code_line.endswith("D"):
                    code_line += "D"
                    self.pad_lines(jump_lines, new_label, "L")

                dst.append(code_line)
                if len(code_line2.strip()) > 0:
                    dst.append(code_line2)

                for i, jump_line in enumerate(jump_lines):
                    if len(jump_line.strip()) > (1 if i < len(labels) else 0):
                        dst.append(jump_line)

                current_label = labels.index(lbl)
                code_line = self.new_code_line(labels, current_label)
                code_line2 = " " * len(labels)
                jump_lines = self.new_jump_lines(labels, current_label)

            
            if op == "jz":
                dst_label = labels.index(arg)
                code_line += "[D]DR"
                code_line2 += " R  U"
                self.pad_lines(jump_lines, default="   ")
                self.pad_lines(jump_lines, dst_label, "L")
                self.pad_lines(jump_lines)
            elif op == "jmp":
                dst_label = labels.index(arg)
                code_line += "D"
                code_line2 += " "
                self.pad_lines(jump_lines, dst_label, "L")
            elif op in [">", "<", "+", "-", ",", "."]:
                code_line += op * arg
                code_line2 += " " * arg
                self.pad_lines(jump_lines, default=" " * arg)
            elif op == "assign":
                code_line += "[-]" + op * arg
                code_line2 += " " * (arg + 3)
                self.pad_lines(jump_lines, default="   " + " " * arg)
            elif op == "exit":
                code_line += "D"
                code_line2 += " "
                self.pad_lines(jump_lines, len(labels), "R")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append(code_line)
        if len(code_line2.strip()) > 0:
            dst.append(code_line2)
        for i, jump_line in enumerate(jump_lines):
            if len(jump_line.strip()) > (1 if i < len(labels) else 0):
                dst.append(jump_line)


        return dst


class IntermediateToGeneric2DBrainfuck(IntermediateToEnigma2D):
    NAME = "Generic 2D Brainfuck"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def from_enigma2d(self, s):
        s = s.replace("l", " ").replace("r", " ").replace("u", " ").replace("d", " ")
        s = s.replace("L", "l").replace("R", "r").replace("U", "u").replace("D", "d")
        
        return s

    def compile(self) -> List[str]:
        """Generic 2D Brainfuck is superset of Enigma-2D with incompatible symbols"""
        return [self.from_enigma2d(s) for s in super().compile()]


class IntermediateToErp(IntermediateCompiler):
    NAME = "erp"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

        if self.mem_size > 256:
            self.mem_size = 256

    def compile(self) -> List[str]:
        dst = [
            "( erp2bf src.erp -rs2 -ds4 )",
            # "import erp_base",
            f"ary mem {self.mem_size}",
            "var p",
            ": main",
            "'mem =p"
        ]
        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        branches = 0

        for lbl, op, arg in self.src:
            if lbl != -1:
                dst.append(f": .L{labels.index(lbl)}")
            
            if op == "jz":
                dst.append(f"p @ '.L{labels.index(arg)} jz")
                # dst.append(f"p @ '.Lif{branches} '.L{labels.index(arg)} if jmp")
                # dst.append(f": .Lif{branches}")
                branches += 1
            elif op == "jmp":
                dst.append(f"'.L{labels.index(arg)} jmp")
            elif op == "+":
                dst.append(f"p @ {arg} + p !")
            elif op == "-":
                dst.append(f"p @ {arg} - p !")
            elif op == ">":
                dst.append(f"p {arg} + =p")
            elif op == "<":
                dst.append(f"p {arg} - =p")
            elif op == ",":
                dst.append(f"getc p !")
            elif op == ".":
                dst.append(f"p @ putc")
            elif op == "assign":
                dst.append(f"{arg} p !")
            elif op == "exit":
                dst.append("'.Lexit jmp")
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

        dst.append(": .Lexit")
        dst.append(";")

        return dst

class IntermediateToBrainfuck(IntermediateCompiler):
    NAME = "Brainfuck"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None, n_args=0, n_results=0):
        super().__init__(src, mem_size, extension)

        self.n_args = n_args
        self.n_results = n_results

    def compile(self) -> List[str]:
        # memory layout: next_label, n, current_label, m, 0, cell0, 1, cell1, 1, ..., 1, current_cell, 0, next_cell, 0, ...
        # [[>+>+<<-]->[<+>-]>>+<-[0 -[1 -[2 [[-]>-<]
        # ]>[ label2 [-]]<
        # ]>[ label1 [-]]<
        # ]>[ label0 [-]]<
        # <<]
        n_registers = 4
        dst = []
        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        if self.ex is not None and self.ex.is_register_based():
            # new memory layout: reg0, reg1, ..., next_label, n, current_label, m
            at_current_cell = "<" * (self.ex.n_registers() + self.ex.n_hidden_registers())
            at_first_cell = ">" * (self.ex.n_registers() + self.ex.n_hidden_registers())

            dst.append(at_first_cell)

            if self.n_args > self.ex.n_registers():
                raise Exception(f"can not store all args to registers")
        else:
            at_current_cell = ">" * n_registers + ">>[>>]<"
            at_first_cell = "<[<<]" + "<" * n_registers

            if self.n_args > 0:
                dst.append(">" * self.n_args)

                for i in range(self.n_args - 1, -1, -1):
                    j = i * 2 + n_registers + 1
                    dst.append("<[" + ">" * j + "+" + "<" * j + "-]")

        current_label = -1
        n_jumps = 0

        def get_bflabel_sel(from_, to_):
            d = abs(from_ - to_)
            if d > (len(labels) - to_) + 3:
                return "[-]" + "+" * (len(labels) - to_)
            else:
                o = "-" if from_ < to_ else "+"
                return o * d

        dst.extend([
            "+" * (len(labels) + 1),
            "[[>+>+<<-]>[<+>-]<->>>+<" + "-[" * (len(labels) + 1) + "[[-]>-<]",
            "]>[<<< initial label",
            at_current_cell
        ])

        for lbl, op, arg in self.src:
            if lbl != -1:
                current_label = labels.index(lbl)

                dst.extend([
                    at_first_cell,
                    ">>>",
                    "[-]" + "]" * n_jumps + "]<",
                    "]>[" + f"label {current_label} x",
                    "<<<",
                    at_current_cell
                ])
                n_jumps = 0
            
            if op == "jz":
                dst.extend([
                    at_first_cell,
                    ">+<",
                    at_current_cell,
                    "[>+<-]>[<+>>>+<<-]>>[<<<",
                    at_first_cell,
                    ">-<",
                    at_current_cell,
                    ">>>[-]]<<<"
                ])
                dst.extend([
                    at_first_cell,
                    ">[>[-]>[-]<<"
                    "< " + get_bflabel_sel(current_label + 1, labels.index(arg)) + " >-]>>[<<<" + f" jz {labels.index(arg)}",
                    at_current_cell
                ])
                n_jumps += 1
            elif op == "jmp":
                dst.extend([
                    at_first_cell,
                    get_bflabel_sel(current_label + 1, labels.index(arg)) + " >>[-]>[-][<<<" + f"jmp {labels.index(arg)}",
                    at_current_cell
                ])
                n_jumps += 1
            elif op == "+":
                dst.append("+" * arg)
            elif op == "-":
                dst.append("-" * arg)
            elif op == ">":
                dst.append(">+>" * arg)
            elif op == "<":
                dst.append("<-<" * arg)
            elif op == ",":
                dst.append(",")
            elif op == ".":
                dst.append(".")
            elif op == "assign":
                dst.append("[-]" + "+" * arg)
            elif op == "exit":
                dst.extend([
                    at_first_cell,
                    "[-] >>[-]>[-][<<<" + f"exit(jmp {len(labels)})",
                    at_current_cell
                ])
                n_jumps += 1
            elif self.is_extension(op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(op, arg, stat))

                if self.is_instruction_for_jump(op):
                    n_jumps += 1


        dst.extend([
            at_first_cell,
            ">>>[-] " + "]" * n_jumps + " ]<",
            "<<] end",
            ">>[-]<<"
        ])

        if self.ex is not None and self.ex.is_register_based():
            dst.append(at_current_cell)

            if self.n_results > self.ex.n_registers():
                raise Exception(f"can not store registers to all results")
        else:
            if self.n_results > 0:
                dst.append(">" * self.n_results)

                for i in range(self.n_results - 1, -1, -1):
                    j = i * 2 + n_registers + 1
                    dst.append(">" * j + "<[" + "<" * j + "+" + ">" * j + "-]" + "<" * j)

        return dst

class IntermediateInterpreter(IntermediateCompiler):
    NAME = "interpreter"

    def __init__(self, src: List[Tuple[int, str, int]], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        data_size = self.mem_size
        labels = self.get_used_labels()
        data = [0 for _ in range(data_size)]
        ptr = 0
        stat = CompilerState(labels)
        stat = self.initialize_extension(stat)

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]
            
            if op == "jz":
                if data[ptr] == 0:
                    i = arg
                    continue
            elif op == "jmp":
                i = arg
                continue
            elif op == "+":
                data[ptr] = (data[ptr] + arg) & 0xFF
            elif op == "-":
                data[ptr] = (data[ptr] - arg) & 0xFF
            elif op == ">":
                ptr = (ptr + arg) % data_size
            elif op == "<":
                ptr = (ptr - arg) % data_size
            elif op == ",":
                s = sys.stdin.read(1)
                data[ptr] = ord(s) if len(s) else 255
            elif op == ".":
                sys.stdout.write(chr(data[ptr]))
                sys.stdout.flush()
            elif op == "assign":
                data[ptr] = arg
            elif op == "exit":
                break
            elif self.is_extension(op):
                stat = InterpreterState(data, ptr, i)
                stat = self.invoke_extension(op, arg, stat)
                data, ptr, i = stat.get()

                continue
            else:
                pass

            i += 1

        stat = CompilerState(labels)
        stat = self.finalize_extension(stat)

        return []


def main(loader=Minimal2D, extension: IntermediateExtension = None):
    import sys
    import io

    lang = "erp"
    file_name = ""
    mem_size = 65536

    for i, arg in enumerate(sys.argv[1:]):
        if not arg.startswith("-"):
            file_name = arg
            continue

        if arg.startswith("-mem_size="):
            mem_size = int(arg[10:])

        if arg.startswith("-lang="):
            lang = arg[6:]

        if arg.startswith("-t"):
            lang = arg[2:]

        if arg == "-run":
            lang = "run"

        if arg == "-disasm":
            lang = "disasm"

        if arg in ["-?", "-h", "-help", "--help"]:
            print(f"""{loader.NAME} to 1D language (or flattened 2D language) compiler
python {sys.argv[0]} [options] < src > dst
python {sys.argv[0]} [options] src > dst
python {sys.argv[0]} [options] -run src < input_data > output_data
options:
  -lang=name    select target language
  -tname        select target language
  -run          passes to interpreter
  -mem_size=N   select memory size
{loader.HELP}
target languages:
  C
  Brainfuck     labels should be fewer than 253
  Generic2DBrainfuck(2b)
                Generic 2D Brainfuck
  Enigma2D      Enigma-2D
  PATH          
  asmbf         uses bflabels preprocessor
  BrainfuckAsmCompiler(bfasmcomp)
                https://gitlab.com/hilmar-ackermann/brainfuckassembler
                https://github.com/esovm/BrainfuckAsmCompiler
  x86           uses NASM. requires external runtime-library.
  CASL2
  erp           only for helloworld.
""")
            return 0

    src = ""

    if file_name == "":
        src = "".join(sys.stdin.readlines())
    else:
        with io.open(file_name, "r") as f:
            src = "".join(f.readlines())

    m2d = loader(src, sys.argv)
    compilers = {
        "run": IntermediateInterpreter,
        "disasm": IntermediateToText,
        "C": IntermediateToC,
        "Brainfuck": IntermediateToBrainfuck,
        "bf": IntermediateToBrainfuck,
        "Enigma2D": IntermediateToEnigma2D,
        "Generic2DBrainfuck": IntermediateToGeneric2DBrainfuck,
        "2b": IntermediateToGeneric2DBrainfuck,
        "PATH": IntermediateToPATH,
        "erp": IntermediateToErp,
        "x86": IntermediateToX86,
        "asmbf": IntermediateToAsmbf,
        "BrainfuckAsmCompiler": IntermediateToBrainfuckAsmCompiler,
        "bfasmcomp": IntermediateToBrainfuckAsmCompiler,
        "CASL2": IntermediateToCASL2
    }

    if lang not in compilers.keys():
        sys.stderr.write(f"{lang} generator is not implemented\n")

        return 1

    if extension is not None:
        if lang == "run" and not extension.can_invoke():
            sys.stderr.write(f"interpreter can not execute {loader.NAME}\n")

            return 1
        if lang != "run" and not extension.can_compile_to(lang):
            sys.stderr.write(f"can not compile {loader.NAME} to {lang}\n")

            return 1

    code = m2d.compile_to_intermediate()
    compiler = compilers[lang](code, mem_size, extension)

    print("\n".join(compiler.compile()))

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())


# if you can not write in Minimal-2D, write in Brainfuck.
#
# #include <stdio.h>
# int c,d,i;void I(d){for(i=0;i++<d*3;)putchar(32);}int main(){puts("D");
# while(!feof(stdin)){(c=getchar())-91||(I(d),puts("/"),I(d),puts("RR D")
# ,++d||--d);c-93||(d&&d--,I(d),puts("DU/L"));c-43&&c-45&&c-62&&c-60&&c-
# 44&&c-46||(I(d),printf("%c\n",c));}return puts("");}
