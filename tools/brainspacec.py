# BrainSpace to 1D language compiler
#
# BrainSpace:
# https://esolangs.org/wiki/BrainSpace_1.0
from typing import Tuple, List
import mtdc


class BrainSpace(mtdc.Abstract2DBrainfuck):
    """language definition"""
    NAME = "BrainSpace"
    HELP = ""
    SYMS_START = []
    SYMS_EXIT = ["x", "X"]
    SYMS_TURN = list("<>^vV")  # V == v
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = ["/"]
    SYMS_MIRROR_R_TO_D = ["\\"]
    SYMS_MIRROR_R_TO_L = ["%"]
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = ["?"]
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = ["*"]
    SYMS_PTR_INC = ["r", "R", "}"]
    SYMS_PTR_DEC = ["l", "L", "{"]
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["p", "P", "+"]
    SYMS_DEC = ["m", "M", "-"]
    SYMS_PUT = ["o", "O", "0"]
    SYMS_GET = ["i", "I", "1"]
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

    def name_to_dir(self, name: str) -> Tuple[int, int]:
        if name == "V":
            name = "v"

        return super().name_to_dir(name)


if __name__ == "__main__":
    import sys

    sys.exit(mtdc.main(BrainSpace))

