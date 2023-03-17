
# this program gernerates "Around and around, sleeping sound" program
# that generates text passed to this program. non-ASCII characters will be broken.
import sys


def create_value_generator(a, b, w=None, first=True):
    if w is None:
        w = max(a, b)

    src = [
        "@<" + "<>" * a  + "  " * (w - a) + ">@   ",
        "@ " + "><" * b  + "  " * (w - b) + " @   ",
        "@ " + "  " * w + "  @  ",
    ]

    if first:
        src.insert(0, "  " * w + "    @  ")

    col = w * 2 + 4

    return (src, col, col - 1)

def create_col_changer(from_, to_, w=None):
    if from_ < to_:
        src = [
            " " * (from_ - 1) + "@ " + " " * (to_ - from_ - 1) + "@",
            " " * (from_ - 1) + "@@" + " " * (to_ - from_ - 1) + " "
        ]
    else:
        src = [
            " " * (to_ - 1) + "@@" + " " * (from_ - to_ - 1) + " ",
            " " * (to_ - 1) + "@ " + " " * (from_ - to_ - 1) + "@"
        ]

    if w is not None:
        f = lambda s: s.ljust(w)
        src = list(map(f, src))

    return src

def interp(f, a, b):
    src, col, col2 = f(a, b)

    src.extend([
        " " * col2 + ">" + " " * (len(src[0]) - col2 - 1),
        " " * col2 + "Z" + " " * (len(src[0]) - col2 - 1)
    ])

    # print("\n".join(src))

    mem = [0, 0, 0]

    steps_lim = 65536
    x, y = (0, 0)
    dx, dy = (1, 0)
    w, h = (len(src[0]), len(src))
    p = 0

    while x in range(w) and y in range(h):
        if steps_lim == 0:
            raise Exception(f"ptr:{p}, ({x}, {y}) inf loop?")
        
        steps_lim -= 1

        c = src[y][x]

        if c == ">":
            p += 1

            if p not in range(len(mem)):
                raise Exception(f"ptr: {p}, ({x}, {y})")
        if c == "<":
            p -= 1

            if p not in range(len(mem)):
                raise Exception(f"ptr: {p}, ({x}, {y})")

            mem[p] = (mem[p] + 1) & 0xFF 
        if c == "Z":
            if p != 1:
                raise Exception(f"Z at {p}, [{','.join(mem)}]")

            return mem[p]
        if c == "@":
            if mem[p] == 0:
                if dx == 1:
                    dx, dy = (0, 1)
                elif dy == 1:
                    dx, dy = (-1, 0)
                elif dx == -1:
                    dx, dy = (0, -1)
                elif dy == -1:
                    dx, dy = (1, 0)
            else:
                if dx == 1:
                    dx, dy = (0, -1)
                elif dy == -1:
                    dx, dy = (-1, 0)
                elif dx == -1:
                    dx, dy = (0, 1)
                elif dy == 1:
                    dx, dy = (1, 0)

        x += dx
        y += dy

    raise Exception(f"({x}, {y}) -> ({dx}, {dy})")


def find_value(f, mx=16):
    import time

    r = []

    sys.stderr.write("-" * 64 + "|\r")
    sys.stderr.flush()

    s=False

    for i in range(256):
        x0, y0 = (256, 256)

        for x in range(1, mx + 1):
            if x > max(x0, y0):
                break
            for y in range(1, mx + 1):
                if y > max(x0, y0):
                    break
                try:
                    j = interp(f, x, y)

                    if i == j and max(x, y) < max(x0, y0):
                        x0, y0 = (x, y)
                except Exception as e:
                    # sys.stderr.write(f"{e}\n")
                    # if not s:
                    #     s = input().strip() == "s"
                    pass

            time.sleep(0.01)

        if 256 in [x0, y0]:
            r.append(None)
        else:
            r.append((x0, y0))

        if i % 4 == 0:
            sys.stderr.write("*")
            sys.stderr.flush()

        time.sleep(0.01)

    return r


tbl = [
    (16, 16), None, None, None, 
    (14, 14), None, None, None, 
    None, None, None, None, 
    None, None, None, None, 
    (8, 10), None, None, None, 
    None, None, (13, 14), None, 
    (5, 8), None, None, None, 
    (10, 6), None, None, None, 
    (8, 12), None, (3, 6), None, 
    None, None, None, None, 
    (12, 14), None, (5, 10), None, 
    (9, 4), None, None, None, 
    (4, 4), None, None, None, 
    None, None, None, None, 
    (1, 8), None, (13, 10), None, 
    None, None, (13, 6), None, 
    (12, 16), None, None, None, 
    (6, 6), None, None, None, 
    (15, 8), None, None, None, 
    (3, 12), None, (11, 2), None, 
    (6, 8), None, (5, 2), None, 
    (2, 2), None, None, None, 
    None, None, None, None, 
    (7, 12), None, (9, 14), None, 
    (8, 4), None, None, None, 
    (3, 4), None, (9, 6), None, 
    (11, 8), None, None, None, 
    (2, 6), None, (7, 10), None, 
    (2, 8), None, None, None, 
    None, None, None, None, 
    None, None, None, None, 
    (15, 12), None, (15, 10), None, 
    (8, 16), None, (7, 14), None, 
    None, None, None, None, 
    (7, 8), None, None, None, 
    None, None, (5, 6), None, 
    (12, 4), None, None, None, 
    (7, 4), None, None, None, 
    (2, 4), None, None, None, 
    None, None, None, None, 
    (12, 8), None, (1, 10), None, 
    (10, 2), None, (7, 2), None, 
    (4, 2), None, (1, 2), None, 
    None, None, None, None, 
    (8, 6), None, (9, 10), None, 
    None, None, (1, 6), None, 
    (4, 14), None, None, None, 
    None, None, None, None, 
    (8, 8), None, None, None, 
    (11, 4), None, None, None, 
    (6, 4), None, (3, 14), None, 
    (1, 4), None, None, None, 
    (3, 16), None, (11, 6), None, 
    (5, 12), None, None, None, 
    (4, 6), None, None, None, 
    (2, 14), None, None, None, 
    (4, 8), None, None, None, 
    (9, 12), None, (3, 10), None, 
    None, None, None, None, 
    None, None, (1, 14), None, 
    (1, 16), None, (15, 14), None, 
    (13, 12), None, (11, 10), None, 
    (9, 8), None, (7, 6), None, 
    (5, 4), None, (3, 2), None
]



def txt2aass():
    c0 = -1
    col = -1
    while True:
        c = sys.stdin.read(1)

        if len(c) == 0:
            break

        c = ord(c)
        i = c

        idxs = [j for j, v in enumerate(tbl[:i + 1]) if v is not None]

        if len(idxs) == 0:
            idxs = [j for j, v in enumerate(tbl) if v is not None]

        j = idxs[-1]
        w = 15
        a, b = tbl[j]

        if c == c0:
            src = []
        elif c0 == j:
            src = []
        elif c0 != -1 and c0 < i and i - c0 <= 3:
            j = c0
            src = []
        else:
            src = []
            if c0 != -1:
                src.extend([
                    " " * col + ">"
                ])
            src2, col_from, col_to = create_value_generator(a, b, max(a, b), c0 == -1) 

            if col != -1:
                src.extend(create_col_changer(col, col_from))

            col = col_to

            src.extend(src2)


        if c == c0:
            src.extend([
                " " * col + "Z"
            ])
        elif i == j:
            src.extend([
                " " * col + ">",
                " " * col + "Z"
            ])
        else:
            if j != c0:
                src.extend([
                    " " * col + ">"
                ])
            for _ in range(i - j):
                src.extend([
                    " " * col + ">",
                    " " * col + "<"
                ])
            src.extend([
                    " " * col + "Z"
            ])


        print("\n".join(src))

        c0 = c


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "help":
        print("""
this program gernerates "Around and around, sleeping sound" program
that generates text passed to this program. non-ASCII characters will be broken.

python txt2aass.py < txt > program
  generates program from text.
python txt2aass.py help
python txt2aass.py find
    stub. finds parameters of selected template.
""")
        sys.exit(0)

    if len(sys.argv) > 1 and sys.argv[1] == "find":
        mx = int(sys.argv[2]) if len(sys.argv) > 2 else 16
        tbl = find_value(create_value_generator, mx)
        tbl_name = "tbl"

        print(f"{tbl_name} = [")
        for i, v in enumerate(tbl):
            if i % 4 == 0:
                sys.stdout.write("\n")

            if v is None:
                sys.stdout.write("None, ")
            else:
                a, b = v
                sys.stdout.write(f"({a}, {b}), ")
            
        print("]")

        sys.exit(0)

    txt2aass()
