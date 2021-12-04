
# Minimal-2D to PATH compiler
# warning:
#   output.size == input.size * 121 + additional EOLs + first colums

# interface of unit
#  0123456789A
# 0    Vv     
# 1           
# 2           
# 3           
# 4H         H
# 5h         h
# 6           
# 7           
# 8           
# 9           
# A    Vv     
#
# H-H: path for horizontal direction
# h-h: skipping path for horizontal direction
# V-V: path for vertial direction
# v-v: skipping path for vertical direction

# L
unit_left = """
           
    !!     
    \\\\     
           
!\! ! \!/! 
!\ !\!  /! 
           
    \ /    
    !      
    //     
    !!     
""".strip("\n").split("\n")

# R
unit_right = """
           
    !!     
    \\\\     
    !      
 !\!/ !/!/!
 !\      /!
   !\  /   
    !      
    //     
    !!     
           
""".strip("\n").split("\n")

# /
unit_skip = """
    \\\\\\      
    !!     
           
    /</    
\! /!!!\ !/
\! ^! !^ !/
\  /!! \  /
    \<\    
           
    !!     
    ///    
""".strip("\n").split("\n")

# +
unit_add = """
           
    !!     
    \\\\     
    !      
 !\!+ +!/! 
 !\     /! 
    +      
    !      
    //     
    !!     
           
""".strip("\n").split("\n")


def mirrored_path_ins(c):
    t = {
        "<": "^",
        "^": "<",
        "v": ">",
        ">": "v"
    }

    return t[c] if c in t.keys() else c

def mirrored_path(code):
    h = len(code)
    w = len(code[0])
    r = []
    for x in range(w):
        row = ""
        for y in range(h):
            row += mirrored_path_ins(code[y][x])

        r.append(row)

    return r

def replaced(code, from_, to_):
    r = []
    for row in code:
        r2 = ""
        for c in row:
            r2 += to_ if c == from_ else c

        r.append(r2)
    
    return r

substitution_table = {
    "L": unit_left,
    "U": mirrored_path(unit_left),
    "R": unit_right,
    "D": mirrored_path(unit_right),
    "/": unit_skip,
    "+": unit_add,
    "-": replaced(unit_add, "+", "-"),
    ">": replaced(unit_add, "+", "}"),
    "<": replaced(unit_add, "+", "{"),
    ",": replaced(unit_add, "+", ","),
    ".": replaced(unit_add, "+", "."),
    " ": replaced(unit_add, "+", " ")
}

def compile_row(src, row_idx):
    r = []
    row = src[row_idx]

    for y in range(len(unit_left)):
        s = " "

        if row_idx == 0:
            if y == 0 or y == 4:
                s = "\\"

        for x, c in enumerate(row):
            if c not in substitution_table.keys():
                c = " " 
            s += substitution_table[c][y] + " "

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
