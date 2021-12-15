# SNUSP(Core SNUSP) to 1D language compiler
#
# Core SNUSP:
# https://esolangs.org/wiki/SNUSP#Core_SNUSP
from typing import Tuple, List
import atdbf


class SNUSP(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "SNUSP(Core SNUSP)"
    HELP = ""
    SYMS_START = ["$"]
    SYMS_EXIT = []
    SYMS_TURN = []
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = ["/"]
    SYMS_MIRROR_R_TO_D = ["\\"]
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = ["!"]
    SYMS_SKIPZ = ["?"]
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

if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(SNUSP))

