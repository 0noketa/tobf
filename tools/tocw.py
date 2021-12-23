
# state-machine definition to Clockwise compiler (stub)

# input language:
#   state : label_name (| '/' num_input) ':' '\n' (code|branch)*
#   code : rpn_expr ';' next_label '\n'
#   branch : cond ':' code
#   cond : value | value '-' value | '_'
#   next_label : | '>' ID | "continue" | "exit"
#   rpn_expr : (value | '$')*
#   value : ID | DIGITS | '"' CHAR '"' | "'" CHAR "'"
#
#   every state takes some input bits (fixed size).
#   states named as "default" will be used for undefined branches of states with same input size.
#   every branch has RPN expr as output description, and name of next state.
#   branch for _ is used for undefined branches.
#
# compile-time RPN expression:
#   b1 (n --)          assigns poped value in binary form as 1 bit output.
#                      b2, b3, ... are simlar to b1
#   + (n m -- n+m)
#   - (n m -- n-m)
#   * (n m -- n*m)
#   / (n m -- n/m)
#   % (n m -- n%m)     MOD
#   lsh (n m -- n<<m)
#   rsh (n m -- n>>m)
#   dropbit (n --)     removes n-th bit from assigned output
#   $ (-- n)           pushes input of current branch


from typing import List, Dict
import sys
import math
import re
from functools import reduce


# if compiler uses accumlator for >=2 values (currently no plan exists)
ACC_IS_MULTI_BIT=False


def reverse_bits(i, size):
    s = bin(i)[2:]
    s = "0" * (size - len(s)) + s
    s = s[-size:]
    return int("".join(reversed(s)), 2)

def draw_path(dst, input_size=7, base_x=0, base_y=0, branches={}, n_path=0, exit=[0xFF]):
    input_types = 1 << input_size

    # every path for continuation and goto destination
    for n in range(n_path + 1):
        base_x2 = base_x + 6 * n

        for i in range(input_types):
            j = reverse_bits(i, input_size)

            if i % 2 == 0:
                dst[base_y + i][base_x2 + 4] = "S"
                dst[base_y + i][base_x2] = "S" # for debug
            else:
                dst[base_y + i][base_x2 + 2] = "S"
        
            if (j not in exit
                    and (j not in branches and n == 0
                        or j in branches and branches[j] == n - 1)):
                if i % 2 == 0:
                    dst[base_y + i][base_x2] = "S"
                    dst[base_y + i][base_x2 + 1] = "+"
                    dst[base_y + i][base_x2 + 2] = "?"
                    dst[base_y + i][base_x2 + 3] = " "
                else:
                    dst[base_y + i][base_x2 + 3] = "+"
                    dst[base_y + i][base_x2 + 4] = "?"

def draw_filter_unit(dst, input_size=7, base_x=0, base_y=0, stat=None, branch=(0, 0, [], "exit"), default_branch=([], "exit"), n_path=0, exit=[0xFF]):
    """stub"""

    """
    > S.? S.! S.?  >101
      ? S ? S ? S  >other
      R+R R+R R+R
    """

    from_, to_, rpn, next = branch
    rpn2, next2 = default_branch

    if from_ != to_:
        raise Exception(f"currently validator accepts only 1 value")

    key = f"{{:0{input_size}b}}".format(from_)

    for i, c in enumerate(key):
        rot = "?" if c == "1" else "!"
        base_x2 = base_x + i * 3

        if ACC_IS_MULTI_BIT:
            dst[base_y][base_x2 + 0] = "S"

        dst[base_y][base_x2 + 1] = "." 
        dst[base_y][base_x2 + 2] = rot

        dst[base_y + 1][base_x2 + 0] = rot
        dst[base_y + 1][base_x2 + 2] = "S" 

        dst[base_y + 2][base_x2 + 0] = "R" 
        dst[base_y + 2][base_x2 + 1] = "+" 
        dst[base_y + 2][base_x2 + 2] = "R"

    base_x2 = base_x + input_size * 3

    template = stat.calc(rpn)
    template2 = stat.calc(rpn2)

    template_w = max(len(template), len(template2))

    dst[base_y] = dst[base_y][:base_x2] + template + dst[base_y][base_x2 + template_w:]
    dst[base_y + 1] = dst[base_y + 1][:base_x2] + template2 + dst[base_y + 1][base_x2 + template_w:]

    base_x2 += template_w
    draw_path(dst, base_x2, base_y, branches, n_path, exit)


def draw_branching_unit(dst, input_size=7, base_x=0, base_y=0, output_templates={}, branches={}, n_path=0, exit=[0xFF]):
    """branches: Dict[input_char: int, path_number: int]\n
       exit: input_chars for exit\n
       if char does not exist both branches and exit, this char will be ignored.
    """

    input_types = 1 << input_size

    base_x0 = base_x
    base_x += 2

    for i in range(input_size):
        n = int(math.pow(2, i))

        if ACC_IS_MULTI_BIT:
            for j in range(n):
                dst[base_y + j][base_x] = "S"

            base_x += 1

        for j in range(n):
            dst[base_y + j][base_x] = "."

        for j in range(n + 1):
            dst[base_y + n + j][base_x + j] = "R"
        for j in range(n):
            dst[base_y + j][base_x + j + 1] = "?"
            dst[base_y + n + j + 1][base_x + j] = "R"

        # input + "?" * n
        base_x += 1 + n

    template_w = 0
    for i in range(input_types):
        msg = write_message(reverse_bits(i, input_size), output_templates, input_size)
        template_w = len(msg)

        dst[base_y + i] = dst[base_y + i][:base_x] + msg + dst[base_y + i][base_x + template_w:]

    base_x += template_w

    draw_path(dst, input_size, base_x, base_y, branches, n_path, exit)

    dst[base_y + 0][base_x0 + 0] = "?"
    dst[base_y + 1][base_x0 + 0] = "+"
    dst[base_y + 1][base_x0 + 1] = "S"
    dst[base_y + 2][base_x0 + 0] = "S"
    dst[base_y + 2][base_x0 + 1] = "+"
    dst[base_y + 3][base_x0 + 0] = "?"
    dst[base_y + 3][base_x0 + 1] = "R"
    dst[base_y + 4][base_x0 + 0] = "S"

    continue_base = max(4, input_types)
    dst[base_y + continue_base][base_x + 2] = "+"
    dst[base_y + continue_base][base_x + 4] = "+"
    dst[base_y + continue_base + 1][base_x0 + 0] = "R"
    dst[base_y + continue_base + 1][base_x + 1] = "S"
    dst[base_y + continue_base + 1][base_x + 2] = "?"
    dst[base_y + continue_base + 1][base_x + 3] = "S"
    dst[base_y + continue_base + 1][base_x + 4] = "?"


def write_message(i, output_templates, size):
    s = bin(i)[2:]
    s = "0" * (size - len(s)) + s
    s = s[-size:]
    s = list(s) + [" "]

    if i in output_templates:
        s2 = output_templates[i]

        s3 = "S"
        b = "0"
        for c in s2:
            if c == b:
                s3 += " ;"
            if c != b:
                s3 += "+;" if c == "1" else "-;"
                b = c


        s += s3

    return s + list(" " * (template_w - len(s)))


class State:
    def __init__(self) -> None:
        pass

    def get_val(self, tkn: str) -> int:
        if tkn[0] in """'"`""":
            return ord(tkn[1])
        elif tkn.startswith("0b"):
            return int(tkn[2:], 2)
        elif tkn[0].isdigit():
            return int(tkn)
        else:
            raise Exception(f"unknown value {tkn}")

    def calc(self, arg, rpn):
        stack = []
        msg = ""

        for i in rpn:
            if i.startswith("b") and i[1:].isdigit():
                size = int(i[1:])
                fmt = "{:0" + str(size) + "b}"
                msg += fmt.format(stack.pop())
            elif i == "$":
                stack.append(arg)
            elif i == "+":
                stack.append(stack.pop() + stack.pop())
            elif i == "*":
                stack.append(stack.pop() + stack.pop())
            elif i == "-":
                x = stack.pop()
                stack.append(stack.pop() - x)
            elif i == "/":
                x = stack.pop()
                stack.append(stack.pop() // x if x != -1 else 0)
            elif i == "%":
                x = stack.pop()
                stack.append(stack.pop() // x if x != -1 else x)
            elif i == "lsh":
                x = stack.pop()
                stack.append(stack.pop() << x)
            elif i == "rsh":
                x = stack.pop()
                stack.append(stack.pop() >> x)
            elif i == "dropbit":
                idx = stack.pop()

                if idx not in range(len(msg)):
                    raise Exception(f"can not drop char at {idx} in {msg}")

                msg = msg[:idx] + msg[idx + 1:]
            else:
                stack.append(self.get_val(i))

        return msg

    def read(self, src: List[str], idx: int = 0) -> int:
        """returns line number"""

        re_id = """(?:[A-Za-z_]\w*)"""
        re_num = """(?:[1-9]\d*|0b[10]+|0)"""
        re_chr = """(?:'[^']'|"[^"]")"""
        re_val = """(?:I|N|C)""".replace("I", re_id).replace("N", re_num).replace("C", re_chr)
        re_rpn_tkn = """(?:V|[\$\+\-\*%])""".replace("V", re_val)
        re_set0 = """(?:V\s*-\s*V)""".replace("V", re_val)
        re_ptn = """(?:V|S)""".replace("V", re_val).replace("S", re_set0)

        re_goto = """(?:|V(?:\s+V)*\s*);\s*(?:|exit|continue|>I)$""".replace("V", re_rpn_tkn).replace("I", re_id)

        re_set = """(?:(V)\s*-\s*(V))""".replace("V", re_val)
        re_rpn = """(V)(.*)""".replace("V", re_rpn_tkn)
        re_label = """(I)(?:|\s*/\s*(N))\s*:\s*$""".replace("I", re_id).replace("N", re_num)
        re_branch = """(P)\s*:\s*(G)""".replace("P", re_ptn).replace("G", re_goto)

        self.label = ""
        self.n_input = 0
        self.init = []
        self.branches = []
        self.default_branch = None

        label = None

        for i in range(idx, len(src)):
            s = src[i].strip()

            if s.startswith("#") or len(s) == 0:
                continue

            m = re.match(re_label, s)
            if m is not None:
                if label is not None:
                    break

                label, n = m.groups()
                self.label = label
                self.n_input = int(n) if n is not None else 0

                continue

            cond = None
            m = re.match(re_branch, s)
            if m is not None:
                cond, s = m.groups()

            m = re.match(re_goto, s)
            if m is not None:
                rpn = []
                s = s.strip()
                while len(s) > 0:
                    m = re.match(re_rpn, s)
                    if m is None:
                        break

                    tkn, s = m.groups()

                    rpn.append(tkn)
                    s = s.strip()

                _, next = s.split(";")
                next = next.strip()

                if cond is not None:
                    if cond.strip() == "_":
                        self.default_branch = (rpn, next)

                        continue

                    m = re.match(re_set, cond)
                    if m is not None:
                        from_, to_ = m.groups()
                    else:
                        from_ = to_ = cond

                    from_ = self.get_val(from_)
                    to_ = self.get_val(to_)

                    self.branches.append((from_, to_, rpn, next))
                else:
                    self.init.append((rpn, next))

                continue

            raise Exception(f"error: {s}")

        return i




if __name__ == "__main__":
    import sys

    for arg in sys.argv[1:]:
        if arg == "-help":
            print("this program generates Clockwise program from Mealy-machine-like state-machine definition")
            sys.exit(0)

    src = sys.stdin.readlines() + [""]

    stats: Dict[str, State] = {}
    defaults: Dict[str, State] = {}

    i = 0

    while i < len(src):
        stat = State()

        j = stat.read(src, i)

        if i == j:
            break
        else:
            if stat.label == "default":
                defaults[stat.n_input] = stat
            else:
                stats[stat.label] = stat

            i = j


    if "start" not in stats:
        sys.stderr.write("start state is not defined\n")
        sys.exit(1)

    stat_names: List[str] = ["start"]

    for name in stats:
        if name not in stat_names:
            stat_names.append(name)

    n_path = len(stat_names)

    cw_codes = {}

    for name in stat_names:
        stat = stats[name]
        input_size = stat.n_input
        branches = {}
        exit_labels = []
        output_templates = {}

        if input_size == 0 or len(stat.init):
            sys.stderr.write("state with no input is not implemented\n")
            sys.exit(1)

        for i, (rpn, next) in enumerate(stat.init):
            print("init", i, len(rpn), next)

        for i in range(1 << input_size):
            found = False
            for (from_, to_, _, _) in stat.branches:
                if i in range(from_, to_ + 1):
                    found = True

            if found:
                continue

            if stat.default_branch is not None:
                rpn, next = stat.default_branch
                stat.branches.append((i, i, rpn, next))
            elif input_size in defaults:
                base_stat = defaults[input_size]
                if i in base_stat.branches:
                    stat.branches[i] = base_stat.branches[i]
                elif base_stat.default_branch is not None:
                    rpn, next = base_stat.default_branch
                    stat.branches.append((i, i, rpn, next))
                else:
                    stat.branches.append((i, i, [], "continue"))

        for i, (from_, to_, rpn, next) in enumerate(stat.branches):
            for n in range(from_, to_ + 1):
                template = stat.calc(n, rpn)
                if len(template) > 0:
                    output_templates[n] = template
                elif n in output_templates:
                    output_templates.pop(n)

                if next == "exit":
                    exit_labels.append(n)
                elif next.startswith(">"):
                    next2 = next[1:]
                    if next2 not in stat_names:
                        sys.stderr.write(f"state {next2} is not defined\n")
                        sys.exit(1)

                    branches[n] = stat_names.index(next2)

        template_w = 0

        for i, (from_, to_, rpn, next) in enumerate(stat.branches):
            for n in range(from_, to_ + 1):
                template = stat.calc(n, rpn)

                if len(template) > template_w:
                    template_w = len(template)

        if template_w != 0:
            template_w = template_w * 2 + 1

        template_w += 1 + input_size

        def f(n):
            r = 0
            for i in range(1, n):
                r += (1 << i) + 1

            if ACC_IS_MULTI_BIT:
                r += n

            return r

        w = 2 + f(input_size) + 2 + template_w + 6 * (n_path + 1)

        dst = [[" " for _ in range(w)] for _ in range(max(6, (1 << input_size) + 2))]

        draw_branching_unit(dst, input_size=input_size,
                base_x=0, base_y=0,
                output_templates=output_templates,
                n_path=n_path,
                branches=branches,
                exit=exit_labels)

        cw_codes[name] = dst

    w = 0
    for name in stat_names:
        cw = cw_codes[name]

        if len(cw) == 0:
            continue

        w2 = len(cw[0])
        if w2 > w:
            w = w2

    for name in stat_names:
        cw = cw_codes[name]

        for i, line in enumerate(cw):
            idx = len(line) - 6 * n_path
            pad_w = w - len(line)
            line = line[:idx] + list(" " * pad_w) + line[idx:]

            cw[i] = line

        base_x = w - 6 * (n_path - stat_names.index(name))
        cw.insert(-2, list(" " * len(cw[0])))
        cw.insert(-2, list(" " * len(cw[0])))
        cw[-4][base_x + 1] = "R"
        cw[-4][base_x + 3] = "+"
        cw[-4][base_x + 4] = "?"
        cw[-3][base_x + 4] = "S"
        cw[-2][base_x + 2] = "+"
        cw[-2][base_x + 4] = "+"
        cw[-1][base_x + 1] = "S"
        cw[-1][base_x + 2] = "?"
        cw[-1][base_x + 3] = "S"
        cw[-1][base_x + 4] = "?"

    for name in stat_names:
        cw = cw_codes[name]

        print("\n".join(filter(len, map("".join, cw))))

    base_x = w - 6 * n_path

    print(" " * base_x + " S+   " * n_path)
    print(" " * base_x + " R?SR " * n_path)
