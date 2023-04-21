# 2fuck to 1D language compiler
#
# limitation:
#   "," reads EOF
#
# 2fuck
# https://codegolf.stackexchange.com/questions/257017/implement-a-2fuck-interpreter
from typing import Tuple, List, Dict
import atdbf


def twofuck_rotate(stat: atdbf.LoaderState):
    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx, stat.y + stat.dy, stat.dx, stat.dy))

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "jz", 0, -1))

    stat.dx, stat.dy = atdbf.Abstract2DBrainfuck.rotate_dir(stat.dx, stat.dy, False)
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat


class TwoFuck(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "2fuck"
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
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = ["]"]
    SYMS_PTR_DEC = ["["]
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = [","]  # incorrect. -> EOF == NOP
    INS_TBL = {
        "?": twofuck_rotate
    }
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)


if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(TwoFuck))

