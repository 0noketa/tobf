# "Around and around, sleeping sound" to 1D language compiler
#
# Around and around, sleeping sound:
# https://esolangs.org/wiki/Around_and_around,_sleeping_sound
from typing import Tuple, List
import atdbf


def aass_ptr_dec(stat: atdbf.LoaderState) -> atdbf.LoaderState:
    stat.code.append((stat.lbl, "<", 1))
    stat.code.append((stat.lbl + 1, "+", 1))
    stat.lbl += 2
    stat.x += stat.dx
    stat.y += stat.dy

    return stat

class AroundAndAroundSleepingSound(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "\"Around and around, sleeping sound\""
    HELP = ""
    SYMS_START = []
    SYMS_EXIT = []
    SYMS_TURN = []
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = []
    SYMS_MIRROR_R_TO_D = []
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_ROTZNZ_R_L = ["@"]
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = [">"]
    SYMS_PTR_DEC = []
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = []
    SYMS_DEC = []
    SYMS_PUT = ["Z"]
    SYMS_GET = []
    INS_TBL = {
        "<": aass_ptr_dec
    }
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)


if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(AroundAndAroundSleepingSound))

