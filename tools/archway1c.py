# Archway to 1D language compiler (stub)
#
# Archway
# https://esolangs.org/wiki/Archway
from typing import Tuple, List, Dict
import atdbf



class Archway(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "Archway"
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
    SYMS_MIRRORNZ_R_TO_U = ["/"]
    SYMS_MIRRORNZ_R_TO_D = ["\\"]
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
    INS_TBL = {}
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

    sys.exit(atdbf.main(Archway))

