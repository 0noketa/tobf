
# interpreter for Generic 2D Brainfuck
#
# Generic 2D Brainfuck:
# https://esolangs.org/wiki/Generic_2D_Brainfuck


import sys


class Tape:
    def __init__(self) -> None:
        self.start = None
    
    def new_value(self):
        return 0

    def set(self, addr, value=None):
        if self.start is None:
            self.start = addr
            self.left = [self.new_value() for _ in range(8)]
            self.right = [self.new_value() for _ in range(8)]

        if addr < self.start:
            i = self.start - addr - 1

            if i > len(self.left):
                self.left.extend([self.new_value() for _ in range(i - len(self.left) + 8)])

            if value is not None:
                self.left[i] = value

            return self.left[i]

        i = addr - self.start

        if i >= len(self.right):
            self.right.extend([self.new_value() for _ in range(i - len(self.right) + 8)])

        if value is not None:
            self.right[i] = value

        return self.right[i]

    def get(self, addr):
        return self.set(addr)

class Tape2D(Tape):
    def __init__(self) -> None:
        super().__init__()

    def new_value(self):
        return Tape()

def exec(src, input_file, output_file):
    if len(src) == 0:
        return

    w = max(map(len, src))
    h = len(src)
    src = [s + " " * (w - len(s)) for s in src]

    tape = Tape2D()
    px = 0
    py = 0
    x = 0
    y = 0
    dx = 1
    dy = 0
    while x in range(w) and y in range(h):
        c = src[y][x]

        if c == ">":
            px += 1
        elif c == "<":
            px -= 1
        elif c == "v":
            py += 1
        elif c == "^":
            py -= 1
        elif c == "r":
            dx = 1
            dy = 0
        elif c == "l":
            dx = -1
            dy = 0
        elif c == "d":
            dx = 0
            dy = 1
        elif c == "u":
            dx = 0
            dy = -1
        elif c == "+":
            row = tape.get(py)
            v = row.get(px)
            row.set(px, (v + 1) & 0xFF)
        elif c == "-":
            row = tape.get(py)
            v = row.get(px)
            row.set(px, (v - 1) & 0xFF)
        elif c == ",":
            tape.get(py).set(px, ord(input_file.read(1)))
        elif c == ".":
            output_file.write(chr(tape.get(py).get(px)))
        elif c == "[":
            if tape.get(py).get(px) == 0:
                d = 0
                x += dx
                y += dy
                while x in range(w) and y in range(h) and (d > 0 or src[y][x] != "]"):
                    if src[y][x] == "[":
                        d += 1
                    if src[y][x] == "]":
                        d -= 1

                    x += dx
                    y += dy
            else:
                if ((x + dx * 2) in range(w) and (y + dy * 2) in range(h)
                        and src[y + dy][x + dx] == "-"
                        and src[y + dy * 2][x + dx * 2] == "]"):
                    tape.get(py).set(px, 0)

                    x += dx * 2
                    y += dy * 2
        elif c == "]":
            if tape.get(py).get(px) != 0:
                d = 0
                x -= dx
                y -= dy
                while x in range(w) and y in range(h) and (d > 0 or src[y][x] != "["):
                    if src[y][x] == "]":
                        d += 1
                    if src[y][x] == "[":
                        d -= 1

                    x -= dx
                    y -= dy

        x += dx
        y += dy


if __name__ == "__main__":
    import io

    file_name = ""

    for arg in sys.argv[1:]:
        if len(arg) > 0 and arg[0] not in "/-":
            file_name = arg
        
        if arg in ["/?", "-?", "-h", "-help", "--help"]:
            print(f"python {sys.argv[0]} src.2b < input > output")
            print(f"python {sys.argv[0]} < src.2b > output")
            sys.exit(0)
    
    if file_name == "":
        src = sys.stdin.readlines()
    else:
        with io.open(file_name, "r") as f:
            src = f.readlines()

    exec(src, sys.stdin, sys.stdout)
