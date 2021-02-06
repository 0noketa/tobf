
# Brainfuck with "multi-dimentional memory" extension to Brainfuck compiler
# implements:
#   Mipinggfxgbtftybfhfyhfn's ArrowFuck(https://esolangs.org/wiki/ArrowFuck)
#   Zemeckis's 4DChess(https://esolangs.org/wiki/4DChess)
# limitation:
#   can not use large memory space for size of output.

from typing import List, Tuple
from functools import reduce
import io


class BrainfuckWithMultiDimMem:
    """abstract superset of 4DChess and Arrowfuck"""

    @classmethod
    def compile(self,
            src: io.TextIOWrapper,
            dst: io.TextIOWrapper,
            syms: List[Tuple[str, str]] = [("<", ">")],
            size: List[int] = [0x100]
            ) -> int:
        """"syms: list of pairs of instruction charracter for every rank\n"""

        if len(syms) != len(size):
            raise Exception(f"syms and size should have same length")

        ext = "".join(map("".join, syms))
        s = "".join([c for c in src.read() if c in "+-,.[]" + ext])
        ds = [reduce(int.__mul__, [1] + size[:i]) for i in range(len(syms))]
        
        for c in s:
            if c in "+-,.[]":
                dst.write(c)
                continue

            for i in range(len(syms)):
                up, down = syms[i]

                if c == up:
                    dst.write("<" * ds[i])
                    break
                elif c == down:
                    dst.write(">" * ds[i])
                    break

        return reduce(int.__mul__, size)

    def __init__(self,
            src: io.TextIOWrapper = None,
            dst: io.TextIOWrapper = None,
            syms: List[Tuple[str, str]] = [("<", ">")],
            size: List[int] = [0x100]
            ) -> None:
        self.src = src
        self.dst = dst
        self.syms = syms
        self.size = size

    def compile_file(self,
            src: io.TextIOWrapper = None,
            dst: io.TextIOWrapper = None,
            syms: List[Tuple[str, str]] = None,
            size: List[int] = None
            ) -> int:
        if src == None and self.src != None:
            src = self.src
        if dst == None and self.dst != None:
            dst = self.dst
        if syms == None:
            syms = self.syms
        if size == None:
            size = self.size

        if src == None and dst == None:
            raise Exception(f"any of input and ouput was None")

        return BrainfuckWithMultiDimMem.compile(src, dst, syms, size)

class Brainfuck(BrainfuckWithMultiDimMem):
    def __init__(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, size: Tuple[int] = (0x100)) -> None:
        super().__init__(src, dst, syms=[("<", ">")], size=list(size))
class ArrowFuck(BrainfuckWithMultiDimMem):
    def __init__(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, size: Tuple[int, int] = (0x100, 0x100)) -> None:
        super().__init__(src, dst, syms=[("<", ">"), ("^", "v")], size=list(size))
class FDChess(BrainfuckWithMultiDimMem):
    def __init__(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, size: Tuple[int, int, int, int] = (0x100, 0x100, 0x100, 0x100)) -> None:
        super().__init__(src, dst, syms=[("<", ">"), ("v", "^"), ("o", "*"), ("?", "@")], size=list(size))


if __name__ == "__main__":
    import sys

    min_width = 4

    lang = Brainfuck
    size = []

    for i in sys.argv[1:]:
        if i == "-bf":
            lang = Brainfuck
        if i == "-af":
            lang = ArrowFuck
        if i == "-4d":
            lang = FDChess
        if i.isdigit():
            size.append(max(min_width, int(i)))
        if i == "-?":
            sys.stderr.write("Brainfuck with multi-dimensional memory to Brainfuck compiler\n")
            sys.stderr.write(f"python {sys.argv[0]} [options] width height ... < src > dst\n")
            sys.stderr.write(f"  -bf         compiles Brainfuck\n")
            sys.stderr.write(f"  -af         compiles ArrowFuck\n")
            sys.stderr.write(f"  -4d         compiles 4DChess\n")
            sys.stderr.write(f"  ANY_DIGITS  width of memory\n")
            sys.stderr.write(f"                Brainfuck requires 1\n")
            sys.stderr.write(f"                ArrowFuck requires 2\n")
            sys.stderr.write(f"                4DChess requires 4\n")
            sys.exit(0)

    compiler = lang(sys.stdin, sys.stdout, size)

    compiler.compile_file()


# ArrowFuck samples
#
# as human-friendly Brainfuck:
#   rewind:
#       v[<]^
#     input: (pointer: at * (value: ?))
#       ?????? ... * ...
#       011111 ... 1 ...
#     output: (pointer: at * (value: ?))
#       *????? ... ? ...
#       011111 ... 1 ...
#   seekable flag:
#       v+[>[<->-]<[>+<-]>]^
#     input: (pointer: at * (value: ?))
#       *????? ... ? ...
#       000000 ... 1 ...
#     output: (pointer: at * (value: ?))
#       ?????? ... * ...
#       000000 ... 0 ...
# skip diagonal line:
#     [>v]
#   input: (pointer: at * (value: 1))
#     *???
#     ?1??
#     ??1?
#     ???0
#   output: (pointer: at * (value: 0))
#     1???
#     ?1??
#     ??1?
#     ???*
# draw N*N diagonal line:
#     [-[>v+^<-] +*M >v]
#   input: (pointer: at N (value: 3))
#     N???
#     ?0??
#     ??0?
#     ???0
#   output: (pointer: at * (value: 0))
#     M???
#     ?M??
#     ??M?
#     ???*
# skip L:
#     [[v]^[>]]
#   input: (pointer: at * (value: 1))
#     *??
#     1??
#     110
#     0??
#   output: (pointer: at * (value: 0))
#     1??
#     1??
#     11*
#     0??
# rotate data:
#     >[^^[vv[v]<[<]<+>>[>]^[^]^^]vv>]
#   input: (pointer: at * (value: ?))
#     ???ABC?
#     ???000?
#     ??*1110
#     001011?
#     001101?
#     001110?
#   output: (pointer: at * (value: 0))
#     ???000?
#     ???000?
#     ???111*
#     A01011?
#     B01101?
#     C01110?
# rotate data:
#     >v[^^[vv[v]^[<]<+>>[>]<[^]^^]vv>]
#   input: (pointer: at * (value: ?))
#     ??ABC?
#     ?*000?
#     001110
#     00110?
#     0010??
#     ??0???
#   output: (pointer: at * (value: 0))
#     ??000?
#     ??000?
#     C0111*
#     B0110?
#     A010??
#     ??0???
