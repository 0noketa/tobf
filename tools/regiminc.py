# Regimin to 1D language compiler
#
# Regimin:
# https://esolangs.org/wiki/Regimin
#
# Brainfuck output uses 8 cells start with Regimin's registers
from typing import Dict, Tuple, List, Callable
import sys
import atdbf


def regimin_inc2(stat: atdbf.LoaderState):
    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "+", 1, 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_inc3(stat: atdbf.LoaderState):
    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "+", 2, 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_dec2(stat: atdbf.LoaderState):
    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "-", 1, 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_dec3(stat: atdbf.LoaderState):
    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "-", 2, 1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_skipz2(stat: atdbf.LoaderState):
    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "jz", 1, -1))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def regimin_skipz3(stat: atdbf.LoaderState):
    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "jz", 2, -1))
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
    SYMS_SKIPZ = ["7"]
    SYMS_PTR_INC = []
    SYMS_PTR_DEC = []
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["1"]
    SYMS_DEC = ["4"]
    SYMS_PUT = []
    SYMS_GET = []
    INS_TBL = {
        "2": regimin_inc2,
        "3": regimin_inc3,
        "5": regimin_dec2,
        "6": regimin_dec3,
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

    def can_compile_to(self, target_language: str) -> bool:
        return target_language in ["C", "Brainfuck", "erp", "disasm"]

    def get_initializer(self, target_language: str, stat: atdbf.CompilerState) -> List[str]:
        dst = {
            "C": [
                "#include <stdlib.h>",
                "int regimin_main (uint8_t *reg1, uint8_t *reg2, uint8_t *reg3);",
                None,
                'if (argc > 1) r0 = itoa(argv[1]);',
                'if (argc > 2) r1 = itoa(argv[2]);',
                'if (argc > 3) r2 = itoa(argv[3]);',
                "if (regimin_main(&r0, &r1, &r2) == 1) return 1;",
                'printf("%d\\n", (int)r0);',
                'printf("%d\\n", (int)r1);',
                'printf("%d\\n", (int)r2);',
                "return 0;",
                "}",
                "int regimin_main (uint8_t *reg1, uint8_t *reg2, uint8_t *reg3) {",
                "if (reg1) r0 = *reg1;",
                "if (reg2) r1 = *reg2;",
                "if (reg3) r2 = *reg3;"
            ],
            "Brainfuck": []
        }
        return dst[target_language] if target_language in dst.keys() else []

    def get_finalizer(self, target_language: str, stat: atdbf.CompilerState) -> List[str]:
        dst = {
            "C": [
                "if (reg1) *reg1 = r0;",
                "if (reg2) *reg2 = r1;",
                "if (reg3) *reg3 = r2;"
            ],
            "Brainfuck": []
        }
        return dst[target_language] if target_language in dst.keys() else []

    def compile_instruction(self, target_language: str, ins: atdbf.IntermediateInstruction, stat: atdbf.CompilerState):
        templates_all = {
            "C": {
            },
            "Brainfuck": {
            }
        }

        templates = templates_all[target_language] if target_language in templates_all.keys() else {}

        return templates[ins.op] if ins.op in templates.keys() else []

    def can_invoke(self) -> bool:
        return True

    def input(self, prompt):
        s = input(prompt).strip()

        return 0 if len(s) == 0 else int(s)

    def initialize(self, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        for i in range(3):
            stat.data[i] = self.input(f"reg{i + 1}:")

        return stat

    def finalize(self, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        for i in range(3):
            print(f"reg{i + 1}: {stat.data[i]}")

        return stat

if __name__ == "__main__":
    sys.exit(atdbf.main(Regimin, IntermediateExtension()))

