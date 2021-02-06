
# Mipinggfxgbtftybfhfyhfn's ArrowFuck(https://esolangs.org/wiki/ArrowFuck) to Brainfuck compiler

import io


class ArrowFuck:
    @classmethod
    def compile(self, src: io.TextIOWrapper, dst: io.TextIOWrapper, width: int = 0x100, height: int = 0x100) -> int:
        s = "".join([c for c in src.read() if c in "><v^+-,.[]"])
        
        while len(s):
            up = s.find("^")
            down = s.find("v")
            if up != -1 and (down == -1 or up < down):
                dst.write(s[:up] + ("<" * width))
                s = s[up + 1:]
            elif down != -1:
                dst.write(s[:down] + (">" * width))
                s = s[down + 1:]
            else:
                dst.write(s)
                s = ""

        return width * height

    def __init__(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, width: int = 0x100, height: int = 0x100) -> None:
        self.src = src
        self.dst = dst
        self.width = width
        self.height = height

    def compile_file(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, width: int = None, height: int = None) -> int:
        if src == None and self.src != None:
            src = self.src
        if dst == None and self.dst != None:
            dst = self.dst
        if width == None:
            width = self.width
        if height == None:
            height = self.height

        if src == None and dst == None:
            raise Exception(f"any of input and ouput was None")

        return ArrowFuck.compile(src, dst, width, height)


if __name__ == "__main__":
    import sys

    min_width = 4

    width = 256

    for i in sys.argv[1:]:
        if i.startswith("-w"):
            width = max(min_width, int(i[2:]))
        if i == "-?":
            sys.stderr.write("ArrawFuck to Brainfuck compiler\n")
            sys.stderr.write(f"python {sys.argv[0]} [-wWIDTH] < src > dst\n")
            sys.exit(0)

    af = ArrowFuck(sys.stdin, sys.stdout, width)

    af.compile_file()

