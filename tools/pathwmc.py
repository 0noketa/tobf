# PATH (with macro instructions) to 1D language compiler
#
# extension:
#   a-u w-z: jumps to the same symbol in upper-case.
#   A-U W-Z: returns to the same symbol in lower-case. every symbol should be unique.
# example:
#     aa# /A,\
#         \}./
#   means:
#     ,.},.}
# limitation:
#   macro instructions can not be used inside any macro instruction. 
#   a-z and A-Z can not be used in comments. they will cause any problem.
from typing import Tuple, List
import atdbf


# !
stacks = {}

for c in range(ord("A"), ord("Z") + 1):
    stacks[chr(c)] = []


def get_call_index(code: List[str], x0: int, y0: int, c0: str):
    r = 0
    for y, row in enumerate(code):
        for x, c in enumerate(row):
            if c.islower():
                if x == x0 and y == y0:
                    if c != c0:
                        raise Exception(f"expected {c0} at ({x}, {y}). but {c} was found.")

                    return r

                r += 1

    return r

def find_macro(code: List[str], c0: str, idx: int):
    for y, row in enumerate(code):
        for x, c in enumerate(row):
            if c == c0:
                if idx == 0:
                    return (x, y)
                
                idx -= 1

    raise Exception(f"{c0} is not defined")

def pathwm_call(stat: atdbf.LoaderState) -> atdbf.LoaderState:
    c = stat.source[stat.y][stat.x]
    stacks[c.upper()].append((stat.x, stat.y))

    idx = get_call_index(stat.source, stat.x, stat.y, c)
    stat.x, stat.y = find_macro(stat.source, c.upper(), idx)

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "", 0, 0))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def pathwm_ret(stat: atdbf.LoaderState) -> atdbf.LoaderState:
    c = stat.source[stat.y][stat.x]
    stat.x, stat.y = stacks[c].pop()

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "", 0, 0))
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat


tbl = {}
for i in range(ord("a"), ord("z") + 1):
    c = chr(i)

    if c != "v":
        tbl[c] = pathwm_call
        tbl[c.upper()] = pathwm_ret

class PATHWithMacroFunctions(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "PATH with macro functions"
    HELP = ""
    SYMS_START = ["$"]
    SYMS_EXIT = ["#"]
    SYMS_TURN = []
    SYMS_TURNNZ = list("<>^v")
    SYMS_MIRROR_R_TO_U = ["/"]
    SYMS_MIRROR_R_TO_D = ["\\"]
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = ["!"]
    SYMS_SKIPZ = []
    SYMS_PTR_INC = ["}"]
    SYMS_PTR_DEC = ["{"]
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = [","]
    INS_TBL = tbl
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        if len(source.strip()):
            calls = len(list(filter(str.islower, source)))
            w = max(map(len, source.splitlines()))
            source = (source + "#" * w + "\n") * (calls + 1)

        super().__init__(source, argv)

if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(PATHWithMacroFunctions))

