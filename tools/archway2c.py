# Archway2 to 1D language compiler (stub)
#
# Archway2
# https://esolangs.org/wiki/Archway
from typing import Tuple, List, Dict
import atdbf


def archway2_mirror_ruld(stat: atdbf.LoaderState):
    stat.x -= stat.dx
    stat.y -= stat.dy

    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "jz", 0, -1))

    stat.dx, stat.dy = -stat.dy, -stat.dx
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def archway2_mirror_lurd(stat: atdbf.LoaderState):
    stat.x -= stat.dx
    stat.y -= stat.dy

    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "jz", 0, -1))

    stat.dx, stat.dy = stat.dy, stat.dx
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat


class Archway2(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "Archway2"
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
    SYMS_MIRRORNZ_R_TO_U = []
    SYMS_MIRRORNZ_R_TO_D = []
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = [">"]
    SYMS_PTR_DEC = ["<"]
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = [","]
    INS_TBL = {
        "\\": archway2_mirror_lurd,
        "/": archway2_mirror_ruld
    }
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

    def find_entry_point(self):
        for i in range(len(self.source) - 1, -1, -1):
            if len(self.source[i].strip()) > 0:
                return (0, i)

        return (0, 0)


if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(Archway2))

