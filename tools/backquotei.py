# ` interpreter
#
# behavior:
#   jump condition can be selected.
#   because Cat program uses jump-on-NEQ, and NAND program uses jump-on-EQ.
#
# `
# https://esolangs.org/wiki/%60

import sys

OP_SETI = 0
OP_SET = 1
OP_JMPI = 2
OP_JMP = 3
OP_NOP = 4


def parse_val(src: str):
    pfx = False
    src = src.strip()

    if src.startswith("+"):
        pfx = True
        src = src[1:].strip()

    return (pfx, int(src))

def parse(src: str):
    if "`" not in src:
        return (OP_NOP, 0, 0)
    
    src2 = src.split("`")
    if len(src2) != 2:
        return (OP_NOP, 0, 0)
    
    left0, right0 = src2
    left_pfx, left = parse_val(left0)
    right_pfx, right = parse_val(right0)

    if left_pfx:
        if right_pfx:
            ins = (OP_JMPI, left, right)
        else:
            ins = (OP_JMP, left, right)
    else:
        if right_pfx:
            ins = (OP_SETI, left, right)
        else:
            ins = (OP_SET, left, right)

    return ins


class Tape:
    def __init__(self, data, input_stream=1, output_stream=0, eof=0) -> None:
        self.data = data
        self.input_stream = input_stream
        self.output_stream = output_stream
        self.eof = eof

    def has_address(self, i):
        return i in self.data.keys()

    def get(self, i):
        if i == self.input_stream:
            c = sys.stdin.read(1)
            return ord(c) if len(c) else self.eof
        elif self.has_address(i):
            return self.data[i]
        else:
            return 0

    def set(self, i, v):
        if i == self.output_stream:
            sys.stdout.write(chr(v))
            sys.stdout.flush()
        elif self.has_address(i):
            self.data[i] = v

class ListTape(Tape):
    def __init__(self, data, input_stream=1, output_stream=0, eof=0) -> None:
        super().__init__(data, input_stream, output_stream, eof)

    def has_address(self, i):
        return i in range(len(self.data))

    def set(self, i, v):
        if i == self.output_stream:
            sys.stdout.write(chr(v))
            sys.stdout.flush()
        elif self.has_address(i):
            self.data[i] = v
        elif i < 0:
            pass
        else:
            self.data = self.data + [0 for _ in range(i - len(self.data))]



def run(src, input_stream=1, output_stream=0, eof=0, cond=int.__eq__, data=None):
    if data is None:
        data = {}

    tape = (ListTape if type(data) is list else Tape)(data, input_stream, output_stream, eof)
    code = list(map(parse, filter(len, src.splitlines())))
    code = list(filter((lambda x: x[0] != OP_NOP), code))

    ip = 0
    currrent = 0
    while ip in range(len(code)):
        op, left, right = code[ip]

        if op == OP_SETI:
            currrent = right
            tape.set(left, right)
        elif op == OP_SET:
            currrent = tape.get(right)
            tape.set(left, currrent)
        elif op == OP_JMPI:
            if cond(currrent, left):
                ip += right
                continue
        elif op == OP_JMP:
            if cond(currrent, left):
                ip += tape.get(right)
                continue

        ip += 1

if __name__ == "__main__":
    import io

    # from https://esolangs.org/wiki/%60
    src = """
0`+72
0`+101
0`+108
0`+108
0`+111
0`+44
0`+32
0`+119
0`+111
0`+114
0`+108
0`+100
0`+33
"""

    cond = int.__eq__


    file_name = ""
    for arg in sys.argv[1:]:
        if arg.startswith("-h"):
            print("  -cond=func   eq/equ/equal or ne/neq/notequal")
            sys.exit(0)

        if arg.startswith("-cond="):
            val = arg[6:].lower()

            if val in ["eq", "equ", "equal"]:
                cond = int.__eq__
            elif val in ["ne", "neq", "notequal"]:
                cond = int.__ne__
        else:
            file_name = arg

    if file_name != "":
        with io.open(file_name, "r") as f:
            src = f.read()


    run(src, cond=cond)
