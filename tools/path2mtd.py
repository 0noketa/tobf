
# PATH to Minimal-2D compiler
# warning:
#   output.size == input.size * 81 + additional EOLs + first colums + lines for "#" and "$"

# interface of unit
#  012345678
# 0 Dd   uU 
# 1L       L
# 2l       l
# 3         
# 4         
# 5         
# 6r       r
# 7R       R
# 8 DdeE uU 
#  eeeeeeeee
#  EEEEEEEEE
#
# # L-L: path for left direction
# l-l: skipping path for left direction
# R-R: path for right direction
# r-r: skipping path for right direction
# U-U: path for up direction
# u-u: skipping path for up direction
# D-D: path for down direction
# d-d: skipping path for down direction
# E: (optional) entry path for "$"
# e: (optional) exit path for all direction

# !
unit_skip = """
 10D L01 
1  LD   1
0   LU  0
D L    UL
 RD   UL 
RD    R  
0  DR   0
1   UR  1
 10R U01 
""".strip("\n").split("\n")

# +
unit_add = """
 10   01 
1   L+  1
0   U   0
 +       
 DL   RU 
       + 
0   D   0
1  +R   1
 10   01 
""".strip("\n").split("\n")

# <
unit_left = """
 10   01 
1  LL   1
0  U    0
 /    RU 
 R  U  L 
 DL    / 
0    D  0
1  /UR  1
 10   01 
""".strip("\n").split("\n")

# \
unit_mirror = """
 10   01 
1   LL U1
0   U   0
DL   U  L
 DL   RU 
R  D   RU
0   D   0
1D RR   1
 10   01 
""".strip("\n").split("\n")

# #
unit_exit = """
 10   01 
1   LD  1
0   U   0
 R D     
 DL   RU 
R  D L L 
0   D   0
1  DR   1
 10   01 
""".strip("\n").split("\n")

# $
unit_entry = """
 10   01 
1   LD  1
0   U   0
 R D     
 DL   RU 
R  D L L 
0   D   0
1  DR   1
 10   01 
""".strip("\n").split("\n")

def rotated_mtd_ins(c):
    t = {
        "L": "U",
        "U": "R",
        "R": "D",
        "D": "L"
    }

    return t[c] if c in t.keys() else c

def rotated_mtd(code, n=1):
    code2 = code
    for _ in range(n):
        h = len(code2)
        w = len(code2[0]) if h > 0 else 0
        r = []
        for x in range(w):
            row = ""
            for y in range(h - 1, -1, -1):
                row += rotated_mtd_ins(code2[y][x])

            r.append(row)

        code2 = r

    return code2

def replaced(code, from_, to_):
    r = []
    for row in code:
        r2 = ""
        for c in row:
            r2 += to_ if c == from_ else c

        r.append(r2)
    
    return r

substitution_table = {
    "<": unit_left,
    "^": rotated_mtd(unit_left),
    ">": rotated_mtd(unit_left, 2),
    "v": rotated_mtd(unit_left, 3),
    "\\": unit_mirror,
    "/": rotated_mtd(unit_mirror),
    "!": unit_skip,
    "+": unit_add,
    "-": replaced(unit_add, "+", "-"),
    "}": replaced(unit_add, "+", ">"),
    "{": replaced(unit_add, "+", "<"),
    ",": replaced(unit_add, "+", ","),
    ".": replaced(unit_add, "+", "."),
    "#": unit_exit,
    " ": replaced(unit_add, "+", " "),
}

def row_includes(src, row_idx, c):
    return c in src[row_idx]
def col_includes(src, col_idx, c):
    src2 = [row[col_idx] for row in src]

    return c in src2
def src_includes(src, c):
    for i in range(len(src)):
        if row_includes(src, i, c):
            return True
    return False

def compile_row(src, row_idx):
    r = []
    row = src[row_idx]

    for y in range(9):
        s = " "

        if row_idx == 0:
            if y == 0:
                s = "D"
            if y == 7 and not src_includes(src, "$"):
                s = "R"

        for x, c in enumerate(row):
            if c not in substitution_table.keys():
                c = " " 
            s += substitution_table[c][y]

        r.append(s)

    if row_includes(src, row_idx, "#"):
        s = " "

        for x, c in enumerate(row):
            if c == "#":
                s += " " * 3 + "R" + " " * 5
            else:
                s += " " * 9
        
        r.append(s)

    if row_includes(src, row_idx, "$"):
        s = "R"

        for x, c in enumerate(row):
            if c == "$":
                s += " " * 4 + "U" + " " * 4
            else:
                s += " " * 9
        
        r.append(s)
    
    return r

def compile(src):
    src = list(filter(len, src))
    w = max(map(len, src))
    src = [i + " " * (w - len(i)) for i in src]

    code = []
    for i in range(len(src)):
        code.extend(compile_row(src, i))

    return code

if __name__ == "__main__":
    import sys

    src = [i.strip("\n") for i in sys.stdin.readlines()]

    print("\n".join(compile(src)))


# if you can not write in PATH, write in Brainfuck
#
# #include <stdio.h>
# int d,b,i;int t(){for(i=d*2;i--;)putchar(32);return 1;}int main(){for(
# puts("/$+!-<");(b=getchar())+1;)b==62||b==60||b>42&&b<47?(t(),putchar(
# b-62&&b-60?b:b+63),puts("")):b-91?b-93||(d?--d:0,t(),puts(">!\\/")):(t
# (),puts("!"),t(),++d,puts("/ v\\"));return puts("#");}
