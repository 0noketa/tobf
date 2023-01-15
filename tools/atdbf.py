
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

class IntermediateInstruction:
    def __init__(self, lbl, op, arg0, arg1) -> None:
        self.lbl = lbl
        self.op = op
        self.arg0 = arg0
        self.arg1 = arg1

class LoaderState:
    def __init__(self,
            source: List[str],
            code: List[IntermediateInstruction],
            lbl: int, x: int, y: int, dx: int, dy: int, 
            stubs: List[int], 
            stk: List[Tuple[int, int, int, int]]
            ) -> None:
        self.source = source
        self.code = code
        self.lbl = lbl
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.stubs = stubs
        self.stk = stk

    def get(self) -> Tuple[List[IntermediateInstruction], int, int, int, int, int, int]:
        return (self.source, self.code, self.lbl, self.x, self.y, self.dx, self.dy, self.stubs, self.stk)

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

    def compile_to_intermediate(self) -> List[IntermediateInstruction]:
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
                code.append(IntermediateInstruction(lbl, "exit", 0, 0))
                onexit = True
                c = " "
            else:
                cell_labels = labels[y][x]
                c = self.source[y][x]

                if c in cls.SYMS_EXIT:
                    code.append(IntermediateInstruction(lbl, "exit", 0, 0))
                    onexit = True
                else:
                    lbl0 = cell_labels.get(dx, dy)

                    if lbl0 != -1:
                        code.append(IntermediateInstruction(lbl, "jmp", 0, lbl0))
                        onexit = True

            if onexit:
                if len(stk) == 0:
                    break

                lbl += 1
                x, y, dx, dy = stk.pop()
                branch_idx = stubs.pop()

                v = code[branch_idx]
                v.arg1 = lbl

                continue

            # sys.stderr.write(f"{lbl:08}: ({x}, {y}) -> ({dx}, {dy})\n")
            cell_labels.set(dx, dy, lbl)

            if c in cls.SYMS_TURN:
                code.append(IntermediateInstruction(lbl, "", 0, 0))

                lbl += 1
                dx, dy = self.name_to_dir(c)

                x += dx
                y += dy

                continue
            elif c in cls.SYMS_MIRROR_R_TO_U:
                code.append(IntermediateInstruction(lbl, "", 0, 0))

                lbl += 1

                dx, dy = -dy, -dx

                x += dx
                y += dy

                continue
            elif c in cls.SYMS_MIRROR_R_TO_D:
                code.append(IntermediateInstruction(lbl, "", 0, 0))

                lbl += 1

                dx, dy = dy, dx

                x += dx
                y += dy

                continue
            elif c in cls.SYMS_SKIP:
                code.append(IntermediateInstruction(lbl, "", 0, 0))
                x += dx
                y += dy
            elif c in cls.SYMS_PUT:
                code.append(IntermediateInstruction(lbl, ".", 0, 1))
            elif c in cls.SYMS_GET:
                code.append(IntermediateInstruction(lbl, ",", 0, 1))
            elif c in cls.SYMS_PTR_INC:
                code.append(IntermediateInstruction(lbl, ">", 0, 1))
            elif c in cls.SYMS_PTR_DEC:
                code.append(IntermediateInstruction(lbl, "<", 0, 1))
            elif c in cls.SYMS_INC:
                code.append(IntermediateInstruction(lbl, "+", 0, 1))
            elif c in cls.SYMS_DEC:
                code.append(IntermediateInstruction(lbl, "-", 0, 1))
            elif c in cls.SYMS_MIRROR_R_TO_L:
                code.append(IntermediateInstruction(lbl, "", 0, 0))

                dx = -dx
                dy = -dy
            elif c in cls.SYMS_PTR_DOWN:
                code.append(IntermediateInstruction(lbl, ">", 0, self.data_width))
            elif c in cls.SYMS_PTR_UP:
                code.append(IntermediateInstruction(lbl, "<", 0, self.data_width))
            elif c in cls.SYMS_TURNNZ:
                stubs.append(len(code))
                stk.append((x + dx, y + dy, dx, dy))

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))

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

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))
            elif c in cls.SYMS_ROT_L:
                code.append(IntermediateInstruction(lbl, "", 0, 0))
                dx, dy = self.rotate_dir(dx, dy, clockwise=False)
            elif c in cls.SYMS_ROT_R:
                code.append(IntermediateInstruction(lbl, "", 0, 0))
                dx, dy = self.rotate_dir(dx, dy)
            elif c in cls.SYMS_ROTZ_R:
                dx2, dy2 = self.rotate_dir(dx, dy)

                stubs.append(len(code))
                stk.append((x + dx2, y + dy2, dx2, dy2))

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))
            elif c in cls.SYMS_ROTNZ_R:
                dx2, dy2 = self.rotate_dir(dx, dy)

                stubs.append(len(code))
                stk.append((x + dx, y + dy, dx, dy))

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))

                dx = dx2
                dy = dy2
            elif c in cls.SYMS_ROTZNZ_R_L:
                dx2, dy2 = self.rotate_dir(dx, dy)
                dx3, dy3 = self.rotate_dir(dx, dy, False)

                stubs.append(len(code))
                stk.append((x + dx2, y + dy2, dx2, dy2))

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))

                dx = dx3
                dy = dy3
            elif c == bf_bracket_left:
                x2, y2 = self.skip_bracket(x, y, dx, dy)

                stubs.append(len(code))
                stk.append((x2, y2, dx, dy))

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))
            elif c == bf_bracket_right:
                x2, y2 = self.skip_bracket(x, y, -dx, -dy)

                code.append(IntermediateInstruction(lbl, "jz", 0, lbl + 2))
                lbl += 1

                stk.append((x2 + dx * 2, y2 + dy * 2, dx, dy))

                stubs.append(len(code))
                code.append(IntermediateInstruction(lbl, "jmp", 0, -1))
            elif c in cls.SYMS_MIRRORNZ_R_TO_L:
                stubs.append(len(code))
                stk.append((x + dx, y + dy, dx, dy))

                code.append(IntermediateInstruction(lbl, "jz", 0, -1))

                dx = -dx
                dy = -dy
            elif c in cls.INS_TBL.keys():
                stat = cls.INS_TBL[c](LoaderState(self.source, code, lbl, x, y, dx, dy, stubs, stk))
                _, code, lbl, x, y, dx, dy, stubs, stk = stat.get()

                continue
            else:
                code.append(IntermediateInstruction(lbl, "", 0, 0))

            x += dx
            y += dy
            lbl += 1

        return code




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
    def compile_instruction(self, target_language: str, ins: IntermediateInstruction, stat: CompilerState) -> List[str]:
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
    def invoke_instruction(self, ins: IntermediateInstruction, stat: InterpreterState) -> InterpreterState:
        """returns modified state"""
        return stat

class IntermediateCompiler:
    NAME = ""

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
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

    def is_register_based(self) -> bool:
        return self.ex is not None and self.ex.is_register_based()

    def n_ex_registers(self) -> bool:
        if self.ex is not None:
            return self.ex.n_registers()
        
        return 0

    def n_hidden_ex_registers(self) -> bool:
        if self.ex is not None:
            return self.ex.n_hidden_registers()
        
        return 0

    def get_extension_finalizer(self, stat: CompilerState) -> List[str]:
        dst = []
        if self.ex is not None:
            if self.ex.can_compile_to(type(self).NAME) and self.ex.requires_finalization():
                dst.extend(self.ex.get_finalizer(type(self).NAME, stat))

        return dst

    def compile_extension(self, ins: IntermediateInstruction, stat: CompilerState) -> List[str]:
        if self.ex is not None:
            if self.ex.can_compile_to(type(self).NAME) and self.ex.has_instruction(ins.op):
                return self.ex.compile_instruction(type(self).NAME, ins, stat)

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

    def invoke_extension(self, ins: IntermediateInstruction, stat: InterpreterState) -> InterpreterState:
        if self.ex is not None:
            if self.ex.can_invoke() and self.ex.has_instruction(ins.op):
                return self.ex.invoke_instruction(ins, stat)

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
        return sorted(list(set([v.arg1 for v in self.src if self.is_instruction_for_jump(v.op)])))

    def get_active_labels(self) -> List[int]:
        return sorted(list(set([v.lbl for v in self.src if v.lbl != -1])))

    def skip_mergeable(self, idx: int) -> Tuple[int, int]:
        if idx not in range(len(self.src)):
            return (len(self.src), 0)

        v0 = self.src[idx]
        arg0 = v0.arg1

        if not self.is_mergeable_instruction(v0.op):
            return (idx + 1, arg0)

        for i, v in enumerate(self.src[idx + 1:]):
            if v.op != v0.op or v.arg0 != v0.arg0 or v.lbl != -1:
                return (idx + 1 + i, arg0)

            arg0 += v.arg1

        return (len(self.src), arg0)

    def merge_increment(self):
        old_size = len(self.src)

        i = 0
        while i < len(self.src):
            v = self.src[i]

            if self.is_mergeable_instruction(v.op):
                j, arg2 = self.skip_mergeable(i) 
                v.arg1 = arg2
                self.src = self.src[:i + 1] + self.src[j:]

            i += 1

        return len(self.src) != old_size

    def rename_label(self, from_: int, to_: int):
        x = len(self.src)
        for i, v in enumerate(self.src):
            if v.lbl == from_:
                v.lbl = to_

            if self.is_instruction_for_jump(v.op) and v.arg1 == from_:
                v.arg1 = to_

    def update_labels(self):
        labels = self.get_used_labels()

        for i, v in enumerate(self.src):
            if v.lbl in labels:
                self.rename_label(v.lbl, i)
            else:
                v.lbl = -1

    def remove_nop(self) -> bool:
        """takes labels from every nop and removes all nop\n
           returns True if any nop was removed
        """
    
        old_size = len(self.src)
        i = old_size
        while i > 0:
            i -= 1
            v = self.src[i]

            if v.lbl == -1:
                if i > 0 and v.op != "":
                    for j in range(i - 1, -1, -1):
                        v2 = self.src[j]

                        if v2.op != "":
                            break

                        if v2.lbl != -1:
                            self.src[i] = IntermediateInstruction(v2.lbl, v.op, v.arg0, v.arg1)
                            self.src[j] = IntermediateInstruction(-1, "", 0, 0)
                            break

                if v.op == "":
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
                v0 = self.src[i - 1]
                v = self.src[i]

                if self.is_instruction_for_jump(v0.op) and v0.arg1 == v.lbl:
                    if v0.lbl == -1:
                        self.src.pop(i - 1)
                        optimized = True
                    else:
                        self.rename_label(v0.lbl, v.lbl)
                        self.src.pop(i - 1)
                        optimized = True

                    continue

                if self.is_instruction_for_jump(v0.op) and v.op == "jmp" and v0.arg1 == v.arg1 and v0.lbl == -1:
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if v0.op in ["jmp", "exit"] and v.op == "jmp" and v.lbl != -1:
                    self.rename_label(v.lbl, v.arg1)
                    self.src.pop(i)
                    optimized = True

                    continue

                if v0.op in ["jmp", "exit"] and v.lbl == -1:
                    self.src.pop(i)
                    optimized = True

                    continue

                if v0.op == "" and v0.lbl != -1 and v.lbl != -1:
                    self.rename_label(v0.lbl, v.lbl)
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if v0.op == v.op and v0.arg1 == v.arg1 and (v.op == "exit" or self.is_instruction_for_jump(v.op)):
                    if v0.lbl == -1:
                        self.src.pop(i - 1)
                        optimized = True

                        continue
                    elif v.lbl == -1:
                        self.src.pop(i)
                        optimized = True

                        continue
                    elif v0.lbl != -1 and v.lbl != -1:
                        self.rename_label(v.lbl, v0.lbl)
                        self.src.pop(i)
                        optimized = True

                        continue

                if (v0.op != v.op and v0.arg0 == v.arg0
                        and (set([v0.op, v.op]) == set(["+", "-"])
                                or set([v0.op, v.op]) == set([">", "<"]))):
                    lbl2 = v0.lbl if v.lbl == -1 else v.lbl
                    op2 = (v.op if v0.arg1 < v.arg1
                            else v0.op if v0.arg1 > v.arg1
                            else "")
                    arg2 = abs(v.arg1 - v0.arg1)
                    self.src[i - 1] = IntermediateInstruction(lbl2, op2, v.arg0, arg2)
                    self.src.pop(i)
                    optimized = True

                    continue

                if v0.op == "jmp" and v0.arg1 == v.lbl:
                    self.src[i - 1] = IntermediateInstruction(v0.lbl, "", 0, 0)
                    optimized = True

                    continue

                i += 1

    def reduce_loops(self):
        old_size = len(self.src)

        i = 0
        while i < len(self.src):
            v = self.src[i]

            if v.op == "jz":
                # R/D
                # U-L
                #
                # L0: if (!*p) goto L1;
                # *p -= 1;
                # goto L0;
                # L1:
                if v.arg1 == i + 3:
                    # this pattern will include many jz with the same destination.
                    v2 = self.src[i + 1]
                    v3 = self.src[i + 2]

                    if (v2.lbl == -1 and v3.lbl == -1
                            and v2.op in ["+", "-"] and v2.arg0 == v.arg0
                            and v3.op == "jmp" and v3.arg1 == i):
                        self.src[i] = IntermediateInstruction(v.lbl, "assign", v.arg0, 0)
                        self.src.pop(i + 2)
                        self.src.pop(i + 1)

                        self.update_labels()

                        i += 1
                        continue

                # L0: *p -= 1;
                # if (!*p) goto L1;
                # goto L0;
                # L1:
                if i > 0 and v.arg1 == i + 2:
                    # this pattern will include many jz with the same destination.
                    v2 = self.src[i - 1]
                    v3 = self.src[i + 1]

                    if (v.lbl == -1 and v3.lbl == -1
                            and v2.op in ["+", "-"] and v2.arg0 == v.arg0
                            and v3.op == "jmp" and v3.arg1 == i - 1):
                        self.src[i - 1] = IntermediateInstruction(v2.lbl, "assign", v.arg0, 0)
                        self.src.pop(i + 1)
                        self.src.pop(i)

                        if i > 1:
                            v4 = self.src[i - 2]

                            if v4.op == "jz" and v4.arg1 == i + 2 and v4.arg0 == v.arg0:
                                self.src[i - 2] = IntermediateInstruction(v4.lbl, "", 0, 0)

                        self.update_labels()
                        continue

            i += 1

        return len(self.src) != old_size

    def remove_conditional_jump_by_const(self) -> bool:
        optimized = False

        for i, v in enumerate(self.src):
            # from:
            #   jmp x
            #   x: jmp y
            #   y: jmp z
            # to:
            #   jmp z
            #   x: jmp z
            #   y: jmp z
            if self.is_instruction_for_jump(v.op):
                j = i
                v2 = self.src[i]
                vs = set([v2])
                v3 = self.src[v2.arg1]
                while v3.op == v.op and v3.arg0 == v.arg0:
                    j = v2.arg1

                    if v3 in vs:
                        break

                    v2 = v3
                    vs.add(v2)
                    v3 = self.src[v2.arg1]

                self.src[i] = IntermediateInstruction(v.lbl, v.op, v.arg0, v2.arg1)

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
            if self.is_instruction_for_jump(v.op) or v.op == "exit":
                for j in range(i + 1, len(self.src)):
                    v2 = self.src[j]

                    if v2.op == v.op:
                        if v2.lbl != -1:
                            if v.arg1 != v2.arg1:
                                break

                            if v.lbl == -1:
                                v.lbl = i

                            self.rename_label(v2.lbl, v.lbl)

                        self.src[j] = IntermediateInstruction(-1, "", 0, 0)
                        optimized = True
                    else:
                        break


        j = -1
        vi = -1
        v = -1
        for i, ins in enumerate(self.src):
            if ins.op == "assign":
                j = i
                vi = ins.arg0
                v = ins.arg1
            else:
                if j != -1 and vi == ins.arg0 and ins.lbl == -1:
                    if ins.op == "jz":
                        if v == 0:
                            ins.op = "jmp"
                            ins.arg0 = 0
                        else:
                            self.src[i] = IntermediateInstruction(-1, "", 0, 0)

                        optimized = True                       
                        continue
                    if ins.op == "assign":
                        v = ins.arg1
                        self.src[j].arg1 = ins.arg1
                        self.src[i] = IntermediateInstruction(-1, "", 0, 0)

                        optimized = True                         
                        continue
                    if ins.op == "+":
                        v += ins.arg1
                        self.src[j].arg1 += ins.arg1
                        self.src[i] = IntermediateInstruction(-1, "", 0, 0)
                        
                        optimized = True 
                        continue
                    if ins.op == "-":
                        v -= ins.arg1
                        self.src[j].arg1 -= ins.arg1
                        self.src[i] = IntermediateInstruction(-1, "", 0, 0)
                        
                        optimized = True 
                        continue

                if j != -1:
                    j = -1
                    vi = -1
                    v = -1


        return optimized

class IntermediateToText(IntermediateCompiler):
    NAME = "Abstract2DBrainfuck IL assembly"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = []

        for i in self.src:
            dst.append(f"{i.lbl:4}:{i.op} {i.arg0} {i.arg1}")

        return dst


class IntermediateToC(IntermediateCompiler):
    NAME = "C"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = f"""
#include <stdio.h>
#include <stdint.h>
""".split("\n")

        if self.is_register_based():
            for i in range(self.n_ex_registers()):
                dst.append(f"static uint8_t r{i};")
            for i in range(self.n_hidden_ex_registers()):
                dst.append(f"static uint8_t h{i};")
        else:
            dst.extend(f"""
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
""".split("\n"))

        labels = self.get_used_labels()
        stat = CompilerState(labels)
        initializer = self.get_extension_initializer(stat)

        # this number of following steps are already used
        optimized_steps = 0

        if None in initializer:
            sep_idx = initializer.index(None)

            dst.extend(initializer[:sep_idx])

            initializer = initializer[sep_idx + 1:]

        dst.append("int main(int argc, char *argv[]) {")

        dst.extend(initializer)

        for idx, i in enumerate(self.src):
            if optimized_steps > 0:
                optimized_steps -= 1
                continue

            if i.lbl != -1:
                dst.append(f"L{labels.index(i.lbl)}:")

            if self.is_register_based():
                v = f"r{i.arg0}"
            else:
                v = "*p"

            if i.op == "jz":
                i2 = self.src[idx + 1]

                # from:
                #   jz x
                #   jmp y
                #   x:
                # to:
                #   jnz y
                #   x:
                if i2.op == "jmp" and i2.lbl == -1 and i.arg1 == idx + 2:
                    dst.append(f"if ({v}) goto L{labels.index(i2.arg1)};")
                    optimized_steps = 1
                else:
                    dst.append(f"if (!{v}) goto L{labels.index(i.arg1)};")
            elif i.op == "jmp":
                dst.append(f"goto L{labels.index(i.arg1)};")
            elif i.op == "+":
                dst.append(f"{v} += {i.arg1};")
            elif i.op == "-":
                dst.append(f"{v} -= {i.arg1};")
            elif i.op == ">":
                dst.append(f'ptr_inc({i.arg1})')
            elif i.op == "<":
                dst.append(f'ptr_dec({i.arg1})')
            elif i.op == ",":
                dst.append(f"{v} = getchar();")
            elif i.op == ".":
                dst.append(f"putchar({v});")
            elif i.op == "assign":
                dst.append(f"{v} = {i.arg1};")
            elif i.op == "exit":
                dst.append("return 0;")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        dst.append("return 0;")
        dst.append("}")

        return dst


class IntermediateToX86(IntermediateCompiler):
    """uses NASM"""
    NAME = "x86"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = """
; link to something like this

; #include <stdio.h>
; #include <stdint.h>
; extern void bf_main();
; uint8_t bf_data[65536];
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

        optimized_steps = 0

        for idx, i in enumerate(self.src):
            if optimized_steps > 0:
                optimized_steps -= 1
                continue

            if i.lbl != -1:
                dst.append(f".L{labels.index(i.lbl)}:")

            if self.is_register_based():
                v = f"byte[bf_data + {i.arg0}]"
            else:
                v = "byte[edx]"

            if i.op == "jz":
                i2 = self.src[idx + 1]

                dst.append(f"movzx eax, {v}")
                dst.append("or eax, eax")

                if i2.op == "jmp" and i2.lbl == -1 and i.arg1 == idx + 2:
                    dst.append(f"jnz .L{labels.index(i2.arg1)}")
                    optimized_steps = 1
                else:
                    dst.append(f"jz .L{labels.index(i.arg1)}")
            elif i.op == "jmp":
                dst.append(f"jmp .L{labels.index(i.arg1)}")
            elif i.op == "+":
                dst.append(f"add {v}, {i.arg1}")
            elif i.op == "-":
                dst.append(f"sub {v}, {i.arg1}")
            elif i.op == ">":
                dst.append(f"add edx, {i.arg1}")
            elif i.op == "<":
                dst.append(f"sub edx, {i.arg1}")
            elif i.op == ",":
                dst.append("push edx")
                dst.append("call bf_getc")
                dst.append("pop edx")
                dst.append(f"mov {v}, al")
            elif i.op == ".":
                dst.append(f"movzx eax, {v}")
                dst.append("push edx")
                dst.append("push eax")
                dst.append("call bf_putc")
                dst.append("pop eax")
                dst.append("pop edx")
            elif i.op == "assign":
                if i.arg1 == 0:
                    dst.append("xor eax, eax")
                else:
                    dst.append(f"mov eax, {i.arg1}")
                dst.append(f"mov {v}, al")
            elif i.op == "exit":
                dst.append("ret")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        dst.append("ret")

        return dst


class IntermediateToBrainfuckAsmCompiler(IntermediateCompiler):
    NAME = "BrainfuckAsmCompiler"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = ["mov $1, 0"]

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for i in self.src:
            if i.lbl != -1:
                dst.append(f"L{labels.index(i.lbl)}:")
            
            if i.op == "jz":
                dst.append("mov $0, [$1]")
                dst.append(f"jz $0, L{labels.index(i.arg1)}")
            elif i.op == "jmp":
                dst.append(f"jmp L{labels.index(i.arg1)}")
            elif i.op == "+":
                dst.append("mov $0, [$1]")
                dst.append(f"add $0, {i.arg1}")
                dst.append("mov [$1], $0")
            elif i.op == "-":
                dst.append("mov $0, [$1]")
                dst.append(f"sub $0, {i.arg1}")
                dst.append("mov [$1], $0")
            elif i.op == ">":
                dst.append(f"add $1, {i.arg1}")
            elif i.op == "<":
                dst.append(f"sub $1, {i.arg1}")
            elif i.op == ",":
                dst.append("in $0")
                dst.append("mov [$1], $0")
            elif i.op == ".":
                dst.append("mov $0, [$1]")
                dst.append("out $0")
            elif i.op == "assign":
                dst.append(f"mov [$1], {i.arg1}")
            elif i.op == "exit":
                dst.append("jmp Lexit")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        dst.append("Lexit:")

        return dst


class IntermediateToAsm2bf(IntermediateCompiler):
    NAME = "asm2bf"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)
        self.output_prog_name = "atdbf"
        self.output_prog_base_addr = 0

    def compile(self) -> List[str]:
        dst = [
            # entry-point of standalone program
            f"@{self.output_prog_name}_start",
            f"call %{self.output_prog_name}",
            f"end",
            # entry-point of program as subroutine
            f"@{self.output_prog_name}",
            f"mov r2, {self.output_prog_base_addr}"
        ]

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for i in self.src:
            if i.lbl != -1:
                dst.append(f"@{self.output_prog_name}_{labels.index(i.lbl)}")
            
            if i.op == "jz":
                dst.append("rcl r1, r2")
                dst.append(f"jz r1, %{self.output_prog_name}_{labels.index(i.arg1)}")
            elif i.op == "jmp":
                dst.append(f"jmp %{self.output_prog_name}_{labels.index(i.arg1)}")
            elif i.op == "+":
                dst.append(f"amp r2, {i.arg1}")
            elif i.op == "-":
                dst.append(f"smp r2, {i.arg1}")
            elif i.op == ">":
                dst.append(f"add r2, {i.arg1}")
            elif i.op == "<":
                dst.append(f"sub r2, {i.arg1}")
            elif i.op == ",":
                dst.append("in r1")
                dst.append("sto r2, r1")
            elif i.op == ".":
                dst.append("rcl r1, r2")
                dst.append("out r1")
            elif i.op == "assign":
                dst.append(f"mov r1, {i.arg1}")
                dst.append("sto r2, r1")
            elif i.op == "exit":
                dst.append("jmp @atdbf_exit")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        dst.extend([
            f"@{self.output_prog_name}_exit",
            "ret"
        ])

        return dst


class IntermediateToElvmIr(IntermediateCompiler):
    NAME = "ELVM IR"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        dst = ["mov B, 0"]

        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        for i in self.src:
            if i.lbl != -1:
                dst.append(f"atdbf_{labels.index(i.lbl)}:")
            
            if i.op == "jz":
                dst.append("load A, B")
                dst.append(f"jeq A, 0, atdbf_{labels.index(i.arg1)}")
            elif i.op == "jmp":
                dst.append(f"jmp atdbf_{labels.index(i.arg1)}")
            elif i.op == "+":
                dst.append("load A, B")
                dst.append(f"add A, {i.arg1}")
                dst.append("store B, A")
            elif i.op == "-":
                dst.append("load A, B")
                dst.append(f"sub A, {i.arg1}")
                dst.append("store B, A")
            elif i.op == ">":
                dst.append(f"add B, {i.arg1}")
            elif i.op == "<":
                dst.append(f"sub B, {i.arg1}")
            elif i.op == ",":
                dst.append("getc A")
                dst.append("store B, A")
            elif i.op == ".":
                dst.append("load A, B")
                dst.append("putc A")
            elif i.op == "assign":
                dst.append(f"store B, {i.arg1}")
            elif i.op == "exit":
                stat = CompilerState(labels)
                dst.extend(self.get_extension_finalizer(stat))
                dst.append("exit")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        return dst


class IntermediateToCASL2(IntermediateCompiler):
    NAME = "CASL2"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
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

        for i in self.src:
            if i.lbl != -1:
                s = f"L{labels.index(i.lbl)}"
                s += " " * (10 - len(s))
            else:
                s = tab

            if i.op == "":
                dst.append(s + "NOP")            
            elif i.op == "jz":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + "OR GR0, GR0")
                dst.append(tab + f"JZE L{labels.index(i.arg1)}")
            elif i.op == "jmp":
                dst.append(tab + f"JUMP L{labels.index(i.arg1)}")
            elif i.op == "+":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + f"ADDL GR0, ={i.arg1}")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif i.op == "-":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + f"SUBL GR0, ={i.arg1}")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif i.op == ">":
                dst.append(s + f"ADDL GR1, ={i.arg1}")
            elif i.op == "<":
                dst.append(s + f"SUBL GR1, ={i.arg1}")
            elif i.op == ",":
                dst.append(s + "LD GR4, GR1")
                dst.append(tab + "CALL GETC")
                dst.append(tab + "LD GR1, GR4")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif i.op == ".":
                dst.append(s + "LD GR4, GR1")
                dst.append(tab + "LD GR0, DATA, GR1")
                dst.append(tab + "CALL PUTC")
                dst.append(tab + "LD GR1, GR4")
            elif i.op == "assign":
                dst.append(s + f"LD GR0, ={i.arg1}")
                dst.append(tab + "ST GR0, DATA, GR1")
            elif i.op == "exit":
                dst.append(s + "JUMP ONEXIT")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        dst.append("ONEXIT    LD GR0, =0")
        dst.append(tab + "CALL PUTC")

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        dst.append(tab + "RET")
        dst.append(f"DATA      DS {self.mem_size}")
        dst.append(tab + "END")
        dst += lib

        return dst


class IntermediateToPATH(IntermediateCompiler):
    NAME = "PATH"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        labels = self.get_used_labels()

        dst = [
            "\\"
        ]

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        current_label = -1

        for i in self.src:
            if i.lbl != -1:
                current_label = labels.index(i.lbl)
                dst.append("!")
                dst.append("/ " + " " * (current_label * 3) + f"/!\\ label {current_label}")
            
            if i.op == "jz":
                dst_label = labels.index(i.arg1)
                if current_label < dst_label:
                    dst.append("  " + " " * dst_label * 3 + "!")
                    dst.append("\\v" + " " * dst_label * 3 + f"\\ jz {dst_label}")
                    dst.append("//" + " " * dst_label * 3 + "!")
                else:
                    dst.append("  " + " " * dst_label * 3 + "  !")
                    dst.append("\\v" + " " * dst_label * 3 + f"  / jz {dst_label}")
                    dst.append("//" + " " * dst_label * 3 + "  !")
            elif i.op == "jmp":
                dst_label = labels.index(i.arg1)
                if current_label < dst_label:
                    dst.append("  " + " " * dst_label * 3 + "!")
                    dst.append("\\ " + " " * dst_label * 3 + f"\\ jmp {dst_label}")
                    dst.append("  " + " " * dst_label * 3 + "!")
                else:
                    dst.append("  " + " " * dst_label * 3 + "  !")
                    dst.append("\\ " + " " * dst_label * 3 + f"  / jmp {dst_label}")
                    dst.append("  " + " " * dst_label * 3 + "  !")
            elif i.op in ["+", "-", ",", "."]:
                for _ in range(i.arg1):
                    dst.append(f"{i.op}")
            elif i.op == ">":
                dst.append("}")
            elif i.op == "<":
                dst.append("{")
            elif i.op == "assign":
                dst.append("v")
                dst.append("-")
                dst.append("!")
                dst.append(" ")
                dst.append("^")
                for _ in range(i.arg1):
                    dst.append(f"{i.op}")
            elif i.op == "exit":
                stat = CompilerState(labels)
                dst.extend(self.get_extension_finalizer(stat))
                dst.append("#")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        stat = CompilerState(labels)
        dst.extend(self.get_extension_finalizer(stat))

        dst.append("#")

        return dst


class IntermediateToEnigma2D(IntermediateCompiler):
    NAME = "Enigma-2D"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
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


        for i in self.src:
            if i.lbl != -1:
                new_label = labels.index(i.lbl)

                if not code_line.endswith("D"):
                    code_line += "D"
                    self.pad_lines(jump_lines, new_label, "L")

                dst.append(code_line)
                if len(code_line2.strip()) > 0:
                    dst.append(code_line2)

                for j, jump_line in enumerate(jump_lines):
                    if len(jump_line.strip()) > (1 if j < len(labels) else 0):
                        dst.append(jump_line)

                current_label = labels.index(i.lbl)
                code_line = self.new_code_line(labels, current_label)
                code_line2 = " " * len(labels)
                jump_lines = self.new_jump_lines(labels, current_label)

            
            if i.op == "jz":
                dst_label = labels.index(i.arg1)
                code_line += "[D]DR"
                code_line2 += " R  U"
                self.pad_lines(jump_lines, default="   ")
                self.pad_lines(jump_lines, dst_label, "L")
                self.pad_lines(jump_lines)
            elif i.op == "jmp":
                dst_label = labels.index(i.arg1)
                code_line += "D"
                code_line2 += " "
                self.pad_lines(jump_lines, dst_label, "L")
            elif i.op in [">", "<", "+", "-", ",", "."]:
                code_line += i.op * i.arg1
                code_line2 += " " * i.arg1
                self.pad_lines(jump_lines, default=" " * i.arg1)
            elif i.op == "assign":
                code_line += "[-]" + ("-" if i.arg1 < 0 else "+") * i.arg1
                code_line2 += " " * (i.arg1 + 3)
                self.pad_lines(jump_lines, default="   " + " " * i.arg1)
            elif i.op == "exit":
                code_line += "D"
                code_line2 += " "
                self.pad_lines(jump_lines, len(labels), "R")
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

        dst.append(code_line)
        if len(code_line2.strip()) > 0:
            dst.append(code_line2)
        for i, jump_line in enumerate(jump_lines):
            if len(jump_line.strip()) > (1 if i < len(labels) else 0):
                dst.append(jump_line)


        return dst


class IntermediateToGeneric2DBrainfuck(IntermediateToEnigma2D):
    NAME = "Generic 2D Brainfuck"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
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

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

        if self.mem_size > 256:
            self.mem_size = 256

    def compile(self) -> List[str]:
        dst = [
            "( erp2bf src.erp -rs2 -ds4 )"
        ]
        if self.is_register_based():
            for i in range(self.n_ex_registers()):
                dst.append(f"var r{i}")
            for i in range(self.n_hidden_ex_registers()):
                dst.append(f"var h{i}")
            dst.extend([
                ": main"
            ])
        else:
            dst.extend([
                f"ary mem {self.mem_size}",
                "var p",
                ": main",
                "'mem =p"
            ])
        labels = self.get_used_labels()

        stat = CompilerState(labels)
        dst.extend(self.get_extension_initializer(stat))

        branches = 0

        for v in self.src:
            if v.lbl != -1:
                dst.append(f": .L{labels.index(v.lbl)}")

            if self.is_register_based():
                ld = f"r{v.arg0}"
                st = f"=r{v.arg0}"
            else:
                ld = "p @"
                st = "p !"

            if v.op == "jz":
                dst.append(f"{ld} '.L{labels.index(v.arg1)} jz")
                # dst.append(f"p @ '.Lif{branches} '.L{labels.index(arg)} if jmp")
                # dst.append(f": .Lif{branches}")
                branches += 1
            elif v.op == "jmp":
                dst.append(f"'.L{labels.index(v.arg1)} jmp")
            elif v.op == "+":
                dst.append(f"{ld} {v.arg1} + {st}")
            elif v.op == "-":
                dst.append(f"{ld} {v.arg1} - {st}")
            elif v.op == ">":
                dst.append(f"p {v.arg1} + =p")
            elif v.op == "<":
                dst.append(f"p {v.arg1} - =p")
            elif v.op == ",":
                dst.append(f"getc {st}")
            elif v.op == ".":
                dst.append(f"{ld} putc")
            elif v.op == "assign":
                dst.append(f"{v.arg1} {st}")
            elif v.op == "exit":
                dst.append("'.Lexit jmp")
            elif self.is_extension(v.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(v.op, v.arg1, stat))

        dst.append(": .Lexit")
        dst.append(";")

        return dst

class IntermediateToBrainfuck(IntermediateCompiler):
    NAME = "Brainfuck"

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None, n_args=0, n_results=0):
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

        if self.is_register_based():
            # new memory layout: reg0, reg1, ..., internal_reg0, internal_reg1, ..., next_label, n, current_label, m
            at_current_cell = "<" * (self.n_ex_registers() + self.n_hidden_ex_registers())
            at_first_cell = ">" * (self.n_ex_registers() + self.n_hidden_ex_registers())

            dst.append(at_first_cell)

            if self.n_args > self.n_ex_registers():
                raise Exception(f"can not store all args to registers")

            if self.n_hidden_ex_registers() == 0:
                raise Exception(f"registers-based to Brainfuck requires at least 1 hidden register")
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

        for i in self.src:
            if i.lbl != -1:
                current_label = labels.index(i.lbl)

                dst.extend([
                    at_first_cell,
                    ">>>",
                    "[-]" + "]" * n_jumps + "]<",
                    "]>[" + f"label {current_label} x",
                    "<<<",
                    at_current_cell
                ])
                n_jumps = 0
            
            if i.op == "jz":
                if self.is_register_based():
                    dst.extend([
                        ">"* i.arg0 + "[" + "<"* i.arg0 + ">>>+<<<",
                        at_first_cell,
                        ">+<",
                        at_current_cell,
                        ">"* i.arg0 + "-]" + "<"* i.arg0,
                        at_first_cell,
                        ">[<",
                        at_current_cell,
                        ">"* i.arg0 + "+" + "<"* i.arg0,
                        at_first_cell,
                        ">-]+<",
                        at_current_cell,
                        ">>>[<<<",
                        at_first_cell,
                        ">-<",
                        at_current_cell,
                        ">>>[-]]<<<",
                    ])
                else:
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
                    "< " + get_bflabel_sel(current_label + 1, labels.index(i.arg1)) + " >-]>>[<<<" + f" jz {labels.index(i.arg1)}",
                    at_current_cell,
                ])
                n_jumps += 1
            elif i.op == "jmp":
                dst.extend([
                    at_first_cell,
                    get_bflabel_sel(current_label + 1, labels.index(i.arg1)) + " >>[-]>[-][<<<" + f"jmp {labels.index(i.arg1)}",
                    at_current_cell
                ])
                n_jumps += 1
            elif i.op == "+":
                dst.append(">" * i.arg0 + "+" * i.arg1 + "<" * i.arg0)
            elif i.op == "-":
                dst.append(">" * i.arg0 + "-" * i.arg1 + "<" * i.arg0)
            elif i.op == ">":
                dst.append(">+>" * i.arg1)
            elif i.op == "<":
                dst.append("<-<" * i.arg1)
            elif i.op == ",":
                dst.append(">" * i.arg0 + "," + "<" * i.arg0)
            elif i.op == ".":
                dst.append(">" * i.arg0 + "." + "<" * i.arg0)
            elif i.op == "assign":
                dst.append(">" * i.arg0 + "[-]" + "+" * i.arg1 + "<" * i.arg0)
            elif i.op == "exit":
                dst.extend([
                    at_first_cell,
                    "[-] >>[-]>[-][<<<" + f"exit(jmp {len(labels)})",
                    at_current_cell
                ])
                n_jumps += 1
            elif self.is_extension(i.op):
                stat = CompilerState(labels)
                dst.extend(self.compile_extension(i, stat))

                if self.is_instruction_for_jump(i.op):
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

    def __init__(self, src: List[IntermediateInstruction], mem_size: int, extension: IntermediateExtension = None):
        super().__init__(src, mem_size, extension)

    def compile(self) -> List[str]:
        if self.is_register_based():
            data_size = self.n_ex_registers() + self.n_hidden_ex_registers()
            ptr = -1
        else:
            data_size = self.mem_size
            ptr = 0

        data = [0 for _ in range(data_size)]
        i = 0

        stat = InterpreterState(data, ptr, i)
        stat = self.initialize_extension(stat)
        data, ptr, i = stat.get()

        while i < len(self.src):
            v = self.src[i]
            
            if self.is_register_based():
                if v.op == "jz":
                    if data[v.arg0] == 0:
                        i = v.arg1
                    else:
                        i += 1
                    continue
                elif v.op == "+":
                    data[v.arg0] = (data[v.arg0] + v.arg1) & 0xFF
                    i += 1
                    continue
                elif v.op == "-":
                    data[v.arg0] = (data[v.arg0] - v.arg1) & 0xFF
                    i += 1
                    continue
                elif v.op == "assign":
                    data[v.arg0] = v.arg1
                    i += 1
                    continue


            if v.op == "jz":
                if data[ptr] == 0:
                    i = v.arg1
                    continue
            elif v.op == "jmp":
                i = v.arg1
                continue
            elif v.op == "+":
                data[ptr] = (data[ptr] + v.arg1) & 0xFF
            elif v.op == "-":
                data[ptr] = (data[ptr] - v.arg1) & 0xFF
            elif v.op == ">":
                ptr = (ptr + v.arg1) % data_size
            elif v.op == "<":
                ptr = (ptr - v.arg1) % data_size
            elif v.op == ",":
                s = sys.stdin.read(1)
                data[ptr] = ord(s) if len(s) else 255
            elif v.op == ".":
                sys.stdout.write(chr(data[ptr]))
                sys.stdout.flush()
            elif v.op == "assign":
                data[ptr] = v.arg1
            elif v.op == "exit":
                break
            elif self.is_extension(v.op):
                stat = InterpreterState(data, ptr, i)
                stat = self.invoke_extension(v, stat)
                data, ptr, i = stat.get()

                continue
            else:
                pass

            i += 1

        stat = InterpreterState(data, ptr, i)
        stat = self.finalize_extension(stat)

        return []


def main(loader: Abstract2DBrainfuck, extension: IntermediateExtension = None):
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
  asm2bf(asmbf) uses bflabels preprocessor
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
        "c": IntermediateToC,
        "Brainfuck": IntermediateToBrainfuck,
        "bf": IntermediateToBrainfuck,
        "Enigma2D": IntermediateToEnigma2D,
        "Generic2DBrainfuck": IntermediateToGeneric2DBrainfuck,
        "2b": IntermediateToGeneric2DBrainfuck,
        "PATH": IntermediateToPATH,
        "path": IntermediateToPATH,
        "pth": IntermediateToPATH,
        "erp": IntermediateToErp,
        "x86": IntermediateToX86,
        "asmbf": IntermediateToAsm2bf,
        "asm2bf": IntermediateToAsm2bf,
        "BrainfuckAsmCompiler": IntermediateToBrainfuckAsmCompiler,
        "bfasmcomp": IntermediateToBrainfuckAsmCompiler,
        "CASL2": IntermediateToCASL2,
        "cas": IntermediateToCASL2
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

