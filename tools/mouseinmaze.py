# "Mouse in a maze" (single-mouse subset of "Mice in a maze") to 1D language compiler
#
# limitation:
#   only one mouse is available. others will be ignored.
#   (Mice version can be implementad as barrel processor with some modification even if target is bf).
#
#   this dialect has implicit counter-clockwise rotation for pattens below.
#
#    src:
#      WWW
#     b  W
#      WaW
#       ^
#    dst:
#      a
#      b
#
#    src:
#      WWW
#     bK W
#      WaW
#       ^
#    dst:
#       | a
#       | jz B
#       | a
#       | ...
#      B| b
#       | ...
#
#    src:
#       b
#      WKW
#     c  W
#      WaW
#       ^
#    dst:
#       | a
#       | jz B
#       | c
#       | ...
#      B| b
#       | ...
#
#   this behaviour can be disabled with "-no_implicit_cc".
#
# Mice in a maze
# https://esolangs.org/wiki/Mice_in_a_maze
from typing import Tuple, List, Dict, cast
import atdbf


def mim_wall(stat: atdbf.LoaderState):
    stat.x -= stat.dx
    stat.y -= stat.dy

    dx2, dy2 = atdbf.Abstract2DBrainfuck.rotate_dir(stat.dx, stat.dy)

    if stat.compiler.implicit_counter_clockwise:
        # counter clockwise
        # WWW
        #<  W
        # W W
        #  ^
        if stat.source[stat.y + dy2][stat.x + dx2] == "W":
            dx2, dy2 = -dx2, -dy2

            # backward
            # WWW
            # W W
            #  x
            if stat.source[stat.y + dy2][stat.x + dx2] == "W":
                dx2, dy2 = -stat.dx, -stat.dy
            elif stat.source[stat.y + dy2][stat.x + dx2] == "K":       
                stat.stubs.append(len(stat.code))
                stat.stk.append((stat.x + dx2 * 2, stat.y + dy2 * 2, dx2, dy2))

                stat.append_instruction("jz", 0, -1)

                dx2, dy2 = -stat.dx, -stat.dy

    stat.dx, stat.dy = dx2, dy2
    stat.x += stat.dx
    stat.y += stat.dy

    return stat

def mim_cond_wall(stat: atdbf.LoaderState):
    stat.x -= stat.dx
    stat.y -= stat.dy

    dx2, dy2 = atdbf.Abstract2DBrainfuck.rotate_dir(stat.dx, stat.dy)

    if stat.compiler.implicit_counter_clockwise:
        # forward/counter clockwise
        #  ^
        # WKW
        #<  W
        # W W
        #  ^
        if stat.source[stat.y + dy2][stat.x + dx2] == "W":
            dx2, dy2 = -dx2, -dy2

            # forward/backward (left side K can be ignored. it shares condition)
            #  ^
            # WKW
            # ? W  ? is W or K
            # W W
            #  x
            if stat.source[stat.y + dy2][stat.x + dx2] in "WK":
                dx2, dy2 = -stat.dx, -stat.dy

    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + stat.dx * 2, stat.y + stat.dy * 2, stat.dx, stat.dy))

    stat.append_instruction("jz", 0, -1)

    stat.dx, stat.dy = dx2, dy2
    stat.x += stat.dx
    stat.y += stat.dy

    return stat


class MouseInAMaze(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "Mouse in a maze"
    HELP = """  -no_implicit_cc "Mice in a maze"-compatible mode.
                disables implicit counter-clockwise rotation.
  -mouse=N      selects active mouse
"""
    SYMS_START = []
    SYMS_EXIT = ["E"]
    SYMS_TURN = []
    SYMS_TURNNZ = []
    SYMS_ROT_R = ["C"]
    SYMS_ROT_L = ["A"]
    SYMS_MIRROR_R_TO_U = []
    SYMS_MIRROR_R_TO_D = []
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
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
        "W": mim_wall,
        "K": mim_cond_wall
    }
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

        self.mouse = None
        self.source = [f"W{i}W" for i in self.source]
        self.width += 2
        self.source.insert(0, "W" * self.width)
        self.source.append("W" * self.width)
        self.height += 2

        self.implicit_counter_clockwise = True

        for arg in argv:
            if arg == "-no_implicit_cc":
                self.implicit_counter_clockwise = False
            if arg.startswith("-mouse="):
                n = int(arg[7:])

                if n in range(1, 10):
                    self.mouse = str(n)

    def find_entry_point(self):
        mice = {}
        for y, s in enumerate(self.source):
            for x, c in enumerate(s):
                if (c == self.mouse if self.mouse is not None
                        else c.isdigit() and c != "0" and int(c) not in mice.keys()):
                    mice[int(c)] = (x, y)

        if len(mice.keys()):
            return mice[min(mice.keys())]

        return (0, 0)

if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(MouseInAMaze))
