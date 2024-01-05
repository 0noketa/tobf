# 1-bit useless brainfuck dialect (I could not find out) to Clockwise

unit_start = """
  R
"""
unit_flip = """
 R +R
 R!
 R -!
 RR
 R  R
"""
unit_clear = """
  S
"""
unit_input = """
  .
"""
unit_output = """
  ;
"""
unit_begin = """
R  R
+
!-?
-
"""
unit_end = """
R  ?
+
R !S
R  ?
R R
R  R
"""
unit_if = """
 R 
 R!
"""
# same line as "if"
unit_else = """
  R

"""
unit_endif = """
R  R
R !S
R  ?-
+
S
R R
R  R
"""
# same line as "endif"
unit_endif_else = """

  !
  R

  
  
  
"""


# change symbols if this language exists
table = {
    "+": unit_flip,
    "0": unit_clear,
    ",": unit_input,
    ".": unit_output,
    "[": unit_begin,
    "]": unit_end,
    # "{": unit_if,
    # "|": unit_else,
    # "}": unit_endif
}


if __name__ == "__main__":
    import sys

    depth = 0
    source = "".join(map(str.strip, sys.stdin.readlines()))

    print(unit_start)

    for c in source:
        if c not in table:
            continue

        template = table[c]

        if template == unit_end:
            depth -= 1

        for s in template.splitlines():
            if len(s):
                s = "  " * depth + s

            print(s)

        if template == unit_begin:
            depth += 1


# echo (uses 8-bit bytes)
# +[
#   ,{
#       ,{
#           ,{
#               ,{
#                   ,{
#                       ,{
#                           ,{
#                               ,{
#                                   0
#                               | +....... -. 0+ }
#                           | +...... ,. ,.  0+ }
#                       | +..... ,. ,. ,. 0+ }
#                   | +.... ,. ,. ,. ,. 0+ }
#               | +... ,. ,. ,. ,. ,. 0+ }
#           | +.. ,. ,. ,. ,. ,. ,. 0+ }
#       | +. ,. ,. ,. ,. ,. ,. ,. 0+ }
#   | . ,. ,. ,. ,. ,. ,. ,. 0+ }
# ]
