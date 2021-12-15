# Regimin to 1D language compiler
#
# Regimin:
# https://esolangs.org/wiki/Regimin
#
# Brainfuck output uses 8 cells start with Regimin's registers
from typing import Dict, Tuple, List, Callable
import sys
import atdbf


def regimin_inc1(stat: atdbf.LoaderState):
    stat.code.append((stat.lbl, "regimin_inc1", 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_inc2(stat: atdbf.LoaderState):
    stat.code.append((stat.lbl, "regimin_inc2", 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_inc3(stat: atdbf.LoaderState):
    stat.code.append((stat.lbl, "regimin_inc3", 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_dec1(stat: atdbf.LoaderState):
    stat.code.append((stat.lbl, "regimin_dec1", 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_dec2(stat: atdbf.LoaderState):
    stat.code.append((stat.lbl, "regimin_dec2", 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_dec3(stat: atdbf.LoaderState):
    stat.code.append((stat.lbl, "regimin_dec3", 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_skipz1(stat: atdbf.LoaderState):
    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append((stat.lbl, "regimin_jz1", -1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_skipz2(stat: atdbf.LoaderState):
    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append((stat.lbl, "regimin_jz2", -1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_skipz3(stat: atdbf.LoaderState):
    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append((stat.lbl, "regimin_jz3", -1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat



class Regimin(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "Regimin"
    HELP = ""
    SYMS_START = []
    SYMS_EXIT = []
    SYMS_TURN = list("<>^v")
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = []
    SYMS_MIRROR_R_TO_D = []
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_ROT_R = []
    SYMS_ROTNZ_R = []
    SYMS_ROTZ_R = []
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = []
    SYMS_PTR_DEC = []
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = []
    SYMS_GET = []
    INS_TBL = {
        "1": regimin_inc1,
        "2": regimin_inc2,
        "3": regimin_inc3,
        "4": regimin_dec1,
        "5": regimin_dec2,
        "6": regimin_dec3,
        "7": regimin_skipz1,
        "8": regimin_skipz2,
        "9": regimin_skipz3
    }
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)


class IntermediateExtension(atdbf.IntermediateExtension):
    def __init__(self) -> None:
        super().__init__()

    def is_register_based(self) -> bool:
        return True
    def n_registers(self) -> int:
        return 3
    def n_hidden_registers(self) -> int:
        return 1

    def requires_initialization(self) -> bool:
        return True
    def requires_finalization(self) -> bool:
        return True

    def has_instruction(self, name: str) -> bool:
        return name in [
            "regimin_inc1", "regimin_inc2", "regimin_inc3",
            "regimin_dec1", "regimin_dec2", "regimin_dec3",
            "regimin_jz1", "regimin_jz2", "regimin_jz3"
        ]
    def is_instruction_for_jump(self, name: str) -> bool:
        return name in [
            "regimin_jz1", "regimin_jz2", "regimin_jz3"
        ]
    def is_mergeable_instruction(self, name: str) -> bool:
        return name in [
            "regimin_inc1", "regimin_inc2", "regimin_inc3",
            "regimin_dec1", "regimin_dec2", "regimin_dec3"
        ]

    def can_compile_to(self, target_language: str) -> bool:
        return target_language in ["C", "Brainfuck", "bf", "disasm"]

    def get_initializer(self, target_language: str, stat: atdbf.CompilerState) -> List[str]:
        dst = {
            "C": [
                # hide main and rename regimin_main with cc option (this instruction will be changed)
                "return 0;}",
                "int regimin_main (uint8_t *reg1, uint8_t *reg2, uint8_t *reg3) {"
            ],
            "Brainfuck": []
        }
        return dst[target_language] if target_language in dst.keys() else []

    def get_finalizer(self, target_language: str, stat: atdbf.CompilerState) -> List[str]:
        dst = {
            "C": [],
            "Brainfuck": []
        }
        return dst[target_language] if target_language in dst.keys() else []

    def compile_instruction(self, target_language: str, op: str, arg: int, stat: atdbf.CompilerState):
        label = stat.labels.index(arg) if "jz" in op and arg in stat.labels else "invalid"
        get_bflabel = (lambda x: len(stat.labels) - stat.labels.index(x))
        at_first_cell = ">" * (self.n_registers() + self.n_hidden_registers())
        at_current_cell = "<" * (self.n_registers() + self.n_hidden_registers())

        def generate_bf_jz(i):
            if "jz" not in op:
                return []

            return [
                # move r to tmp and n
                ">" * i + "[" + "<" * i + ">>>+<<<",
                at_first_cell,
                ">+<",
                at_current_cell,
                ">" * i + "-]" + "<" * i,

                # move r from n
                at_first_cell,
                ">[<",
                at_current_cell,
                ">" * i + "+" + "<" * i,
                at_first_cell,
                ">-]<",

                # set !(tmp as bool) to n
                ">+<",
                at_current_cell,
                ">>>[<<<",
                at_first_cell,
                ">-<",
                at_current_cell,
                ">>>[-]]<<<",

                # clear m if n
                # replace label
                # if m {
                at_first_cell,
                ">[>[-]>[-]<<",
                "< [-]" + "+" * get_bflabel(arg) + " >-]>>[<<<" + f" jz1 {label}",
                at_current_cell
            ]

        templates_all = {
            "C": {
                "regimin_inc1": [f"*reg1 += {arg};"],
                "regimin_inc2": [f"*reg2 += {arg};"],
                "regimin_inc3": [f"*reg3 += {arg};"],
                "regimin_dec1": [f"*reg1 -= {arg};"],
                "regimin_dec2": [f"*reg2 -= {arg};"],
                "regimin_dec3": [f"*reg3 -= {arg};"],
                "regimin_jz1": [f"if (*reg1) goto L{label};"],
                "regimin_jz2": [f"if (*reg2) goto L{label};"],
                "regimin_jz3": [f"if (*reg3) goto L{label};"]
            },
            "Brainfuck": {
                "regimin_inc1": ["+" * arg],
                "regimin_inc2": [">" + "+" * arg + "<"],
                "regimin_inc3": [">>" + "+" * arg + "<<"],
                "regimin_dec1": ["-" * arg],
                "regimin_dec2": [">" + "-" * arg + "<"],
                "regimin_dec3": [">>" + "-" * arg + "<<"],
                "regimin_jz1": generate_bf_jz(0),
                "regimin_jz2": generate_bf_jz(1),
                "regimin_jz3": generate_bf_jz(2)
            }
        }

        templates = templates_all[target_language] if target_language in templates_all.keys() else {}

        return templates[op] if op in templates.keys() else []

    def can_invoke(self) -> bool:
        return True

    def input(self, prompt):
        s = input(prompt).strip()

        return 0 if len(s) == 0 else int(s)

    def initialize(self, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        self.reg1 = self.input("reg1:")
        self.reg2 = self.input("reg2:")
        self.reg3 = self.input("reg3:")

        return stat

    def finalize(self, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        print(f"reg1: {self.reg1}")
        print(f"reg2: {self.reg2}")
        print(f"reg3: {self.reg3}")

        return stat

    def invoke_instruction(self, name: str, arg: int, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        if name == "regimin_inc1":
            self.reg1 = (self.reg1 + arg) & 0xFF
        elif name == "regimin_inc2":
            self.reg2 = (self.reg2 + arg) & 0xFF
        elif name == "regimin_inc3":
            self.reg3 = (self.reg3 + arg) & 0xFF
        elif name == "regimin_dec1":
            self.reg1 = (self.reg1 - arg) & 0xFF
        elif name == "regimin_dec2":
            self.reg2 = (self.reg2 - arg) & 0xFF
        elif name == "regimin_dec3":
            self.reg3 = (self.reg3 - arg) & 0xFF
        elif name == "regimin_jz1":
            if self.reg1 == 0:
                stat.ip = arg - 1
        elif name == "regimin_jz2":
            if self.reg2 == 0:
                stat.ip = arg - 1
        elif name == "regimin_jz3":
            if self.reg3 == 0:
                stat.ip = arg - 1

        stat.ip += 1

        return stat

if __name__ == "__main__":
    sys.exit(atdbf.main(Regimin, IntermediateExtension()))

