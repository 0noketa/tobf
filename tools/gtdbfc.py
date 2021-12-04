# Generic 2D Brainfuck to 1D language compiler
#
# Generic 2D Brainfuck:
# https://esolangs.org/wiki/Generic_2D_Brainfuck
from typing import Tuple, List, Dict
import mtdc


class Generic2DBrainfuck(mtdc.Abstract2DBrainfuck):
    """language definition"""
    NAME = "Generic 2D Brainfuck"
    HELP = "  -mem_width=N  select memory width\n"
    SYMS_START = []
    SYMS_EXIT = []
    SYMS_TURN = list("lrud")
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = []
    SYMS_MIRROR_R_TO_D = []
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_BF_BRACKETS = list("[]")
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = [">"]
    SYMS_PTR_DEC = ["<"]
    SYMS_PTR_UP = ["^"]
    SYMS_PTR_DOWN = ["v"]
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = [","]
    DEFAULT_MEM_WIDTH = 32

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

        for arg in argv:
            if arg.startswith("-mem_width="):
                self.data_width = int(arg[11:])


if __name__ == "__main__":
    import sys

    sys.exit(mtdc.main(Generic2DBrainfuck))

