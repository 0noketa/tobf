
# generates all branches for a byte with input loop

import math


template_w = 24
def template(i):
    s = bin(i)[2:]
    s = "0" * (7 - len(s)) + s 
    s = list(reversed(s))

    return s + list(" " * (template_w - len(s)))

left_pad_w = 2




# frame
base_x = max(left_pad_w, 1)

dst = [[" " for _ in range(147 + left_pad_w + template_w)] for _ in range(130)]



for i in range(7):
    n = int(math.pow(2, i))

    for j in range(n):
        dst[j][base_x] = "."
    for j in range(n + 1):
        dst[n + j][base_x + j] = "R"
    for j in range(n):
        dst[j][base_x + j + 1] = "?"
        dst[n + j + 1][base_x + j] = "R"

    # input + "?" * n
    base_x += 1 + n

for i in range(128):
    msg = template(i)

    dst[i] = dst[i][:base_x] + msg + dst[i][base_x + template_w:]

base_x += template_w

dst[0][base_x + 2] = "R"
dst[1][base_x + 2] = "S"
dst[1][base_x + 4] = "R"

for i in range(2, 128):
    if i % 2 == 0:
        dst[i][base_x] = "S"
        dst[i][base_x + 1] = "+"
        dst[i][base_x + 2] = "?"
        dst[i][base_x + 3] = " "
        dst[i][base_x + 4] = "S"
    else:
        dst[i][base_x + 2] = "S"
        dst[i][base_x + 3] = "+"
        dst[i][base_x + 4] = "?"

dst[0][0] = "?"
dst[1][0] = "+"
dst[2][0] = "S"
dst[128][base_x + 2] = "+"
dst[129][0] = "R"
dst[129][base_x + 1] = "S"
dst[129][base_x + 2] = "?"
dst[129][base_x + 3] = "S"
dst[129][base_x + 4] = "R"


print("\n".join(filter(len, map("".join, dst))))

