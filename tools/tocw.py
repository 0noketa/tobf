
# state-machine definition to Clockwise compiler

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
#   "..."              pushes every char-code in reversed order. 
#   b1 (n --)          assigns poped value in binary form as 1 bit output.
#                      b2, b3, ... are simlar to b1
#   s1 (0 cN...c0 --)  assigns all poped value as 1-bit value until 0.
#                      s2, s3, ... are similar to s1
#   + (n m -- n+m)
#   - (n m -- n-m)
#   * (n m -- n*m)
#   / (n m -- n/m)
#   % (n m -- n%m)     MOD
#   lsh (n m -- n<<m)
#   rsh (n m -- n>>m)
#   dropbit (n --)     removes n-th bit from assigned output
#   $ (-- n)           pushes input of current branch


from typing import Union, Tuple, List, Dict
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

def compile_message(msg: str, i: int = -1, size: int = -1, width=None):
    """msg: string of '0' and '1'\n
       size: size of input bits when output requires comment.
    """

    if len(msg) > 0:
        s = "S"
        b = "0"
        for c in msg:
            if c == b:
                s += " ;"
            if c != b:
                s += "+;" if c == "1" else "-;"
                b = c
    else:
        s = ""

    if i != -1 and size != -1:
        s2 = bin(i)[2:]
        s2 = "0" * (size - len(s2)) + s2

        s = s2[-size:] + " " + s

    if width is not None:
        s += " " * (width - len(s))

    return s


class Rpn:
    @classmethod
    def get_val(self, tkn: str) -> Union[int, str]:
        if tkn[0] in """'"`""":
            return tkn[1:-1]
        elif tkn.startswith("0b"):
            return int(tkn[2:], 2)
        elif tkn[0].isdigit():
            return int(tkn)
        else:
            raise Exception(f"unknown value {tkn}")

    @classmethod
    def get_intval(self, tkn: str) -> int:
        v = self.get_val(tkn)

        if type(v) == str:
            if len(v) == 0:
                v = 0
            else:
                v = ord(v)
        
        return v
    @classmethod
    def calc(self, arg: int, rpn: List[str], size=64):
        stack = []
        msg = ""

        for i in rpn:
            if i.startswith("b") and i[1:].isdigit():
                size = int(i[1:])
                fmt = "{:0" + str(size) + "b}"
                msg += fmt.format(stack.pop() % (1 << size))
            elif i.startswith("s") and i[1:].isdigit():
                size = int(i[1:])
                fmt = "{:0" + str(size) + "b}"

                while len(stack) > 0:
                    n = stack.pop()
                    if n == 0:
                        break
                    msg += fmt.format(n % (1 << size))

            elif i == "$":
                stack.append(arg)
            elif i == "+":
                stack.append(stack.pop() + stack.pop())
            elif i == "*":
                stack.append(stack.pop() * stack.pop())
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
            elif i == "&":
                stack.append(stack.pop() & stack.pop())
            elif i == "|":
                stack.append(stack.pop() | stack.pop())
            elif i == "^":
                stack.append(stack.pop() ^ stack.pop())
            elif i == "~":
                stack.append(~stack.pop() & ((1 << size) - 1))
            elif i == "dropbit":
                idx = stack.pop()

                if idx not in range(len(msg)):
                    raise Exception(f"can not drop char at {idx} in {msg}")

                msg = msg[:idx] + msg[idx + 1:]
            else:
                s = self.get_val(i)

                if type(s) == str:
                    for c in reversed(s):
                        stack.append(ord(c))
                else:
                    stack.append(s)

        return msg

class Branch:
    def __init__(self, idx: int, rpn: List[str] = [], next: str = "continue") -> None:
        self.idx = idx
        self.rpn = rpn
        self.msg = Rpn.calc(self.idx, self.rpn)
        self.next = next

    def get_next_stat_name(self):
        return self.next[1:] if self.next.startswith(">") else ""

class State:
    def __init__(self, defaults: dict) -> None:
        """defaults: branch_index -> State"""
        self.name = ""
        self.defaults = defaults

    def read(self, src: List[str], idx: int = 0) -> int:
        """returns line number"""

        re_id = """(?:[A-Za-z_]\w*)"""
        re_num = """(?:[1-9]\d*|0b[10]+|0)"""
        re_chr = """(?:'[^']*'|"[^"]*")"""
        re_val = """(?:I|N|C)""".replace("I", re_id).replace("N", re_num).replace("C", re_chr)
        re_rpn_tkn = """(?:V|[\$\+\-\*%])""".replace("V", re_val)
        re_set0 = """(?:V\s*-\s*V)""".replace("V", re_val)
        re_ptn = """(?:V|S)""".replace("V", re_val).replace("S", re_set0)

        re_goto = """(?:|V(?:\s+V)*\s*);\s*(?:|exit|continue|>I)$""".replace("V", re_rpn_tkn).replace("I", re_id)

        re_set = """(?:(V)\s*-\s*(V))""".replace("V", re_val)
        re_rpn = """(V)(.*)""".replace("V", re_rpn_tkn)
        re_label = """(I)(?:|\s*/\s*(N))\s*:\s*$""".replace("I", re_id).replace("N", re_num)
        re_branch = """(P)\s*:\s*(G)""".replace("P", re_ptn).replace("G", re_goto)

        self.name = ""
        self.n_input = 0
        self.branches: List[Branch] = []
        self.default_branch: Tuple[List[str], str] = None

        name = None

        for i in range(idx, len(src)):
            s = src[i].strip()

            if s.startswith("#") or len(s) == 0:
                continue

            m = re.match(re_label, s)
            if m is not None:
                if name is not None:
                    break

                name, n = m.groups()
                self.name = name
                self.n_input = int(n) if n is not None else 0
                self.branches = [None] * (1 << self.n_input)

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

                if cond is None or cond.strip() == "_":
                    self.default_branch = (rpn, next)

                    continue

                m = re.match(re_set, cond)
                if m is not None:
                    from_, to_ = m.groups()
                else:
                    from_ = to_ = cond

                from_ = Rpn.get_intval(from_)
                to_ = Rpn.get_intval(to_)

                self.append_branch(from_, to_, rpn, next)

                continue

            raise Exception(f"error: {s}")

        self.fill_undefined_branches()

        return i

    def append_branch(self, from_, to_, rpn, next):
        for i in range(from_, min(to_ + 1, len(self.branches))):
            self.branches[i] = Branch(i, rpn, next)

    def fill_undefined_branches(self):
        for i, branch in enumerate(self.branches):
            if branch is not None:
                continue

            if self.default_branch is not None:
                rpn, next = self.default_branch
                self.branches[i] = Branch(i, rpn, next)

                continue

            if self.n_input in self.defaults:
                default = self.defaults[self.n_input]
                branch = default.branches[i]
                self.branches[i] = Branch(i, branch.rpn, branch.next)

                continue

            self.branches[i] = Branch(i)

    def get_branches(self, next: str):
        """returns list of index of branch that connected to `next`"""
        return [i for i, branch in enumerate(self.branches) if branch.next == next]

    def get_unique_branches(self) -> List[int]:
        """returns index list"""
        r = []
        rw = []
        es = []

        for i, b in enumerate(self.branches):
            pair = (b.msg, b.next)

            if pair not in es:
                r.append(i)
                rw.append(1)
                es.append(pair)
            else:
                rw[es.index(pair)] += 1

        r2 = sorted(zip(rw, r), key=lambda x: x[0])
        r2 = map(list.pop, map(list, r2))
        r = list(r2)

        return r

def get_width(dst):
    return max(map(len, dst))

def pad(dst, w=None, h=None):
    if h is None:
        h = len(dst)
    else:
        h = max(len(dst), h)

    if w is None:
        w = get_width(dst)
    else:
        w = max(get_width(dst), w)

    if min(map(len, dst)) < w:
        for i, s in enumerate(dst):
            if len(s) < w:
                dst[i].extend([" "] * (w - len(s)))
    
    if h > len(dst):
        dst.extend([list(" " * w) for _ in range(h - len(dst) + 1)])

def draw_char(dst, x=0, y=0, c=" "):
    pad(dst, x + 1, y + 1)

    dst[y][x] = c
  
def draw_line(dst, base_x=0, base_y=0, s="", vertical=False):
    if vertical:
        for i, c in enumerate(s):
            draw_char(dst, base_x, base_y + i, c)
    else:
        for i, c in enumerate(s):
            draw_char(dst, base_x + i, base_y, c)


class States:
    def __init__(self, src) -> None:
        self.stats: Dict[str, State] = {}
        self.defaults: Dict[str, State] = {}

        i = 0
        while i < len(src):
            stat = State(self.defaults)

            j = stat.read(src, i)

            if i == j:
                break
            else:
                if stat.name == "default":
                    self.defaults[stat.n_input] = stat
                else:
                    self.stats[stat.name] = stat

                i = j

        self.n_path = len(self.stats)

        self.stat_names = []

        if "start" in self.stats:
            self.stat_names.append("start")

        self.stat_names.extend([name for name in (self.stats) if name != "start"])

    def draw_path(self, dst, base_x=0, base_y=0, stat: State = None, branches: List[int] = None):
        input_size = stat.n_input
        input_types = 1 << input_size

        # every path for continuation and goto destination
        for n in range(self.n_path + 1):
            base_x2 = base_x + 6 * n
            base_y2 = base_y

            if branches is None:
                idxs = zip(range(input_types), [reverse_bits(i, input_size) for i in range(input_types)])
                idxs = list(idxs)
                if len(idxs) < 2:
                    idxs.append((-1, -1))
            else:
                idxs = zip(branches, branches)

            for i, j in idxs:
                if i % 2 == 0:
                    draw_char(dst, base_x2 + 4, base_y2, "S")
                    draw_char(dst, base_x2, base_y2, "S") # for debug
                else:
                    draw_char(dst, base_x2 + 2, base_y2, "S")
            
                if j == -1 or j in stat.get_branches("exit"):
                    base_y2 += 1
                    continue

                next = stat.branches[j].get_next_stat_name()
                if (j in stat.get_branches("continue") and n == 0
                            or next != "" and self.stat_names.index(next) == n - 1):
                    if i % 2 == 0:
                        draw_line(dst, base_x2, base_y2, "S+? ")
                    else:
                        draw_line(dst, base_x2 + 3, base_y2, "+?")
                    
                base_y2 += 1


    def draw_joining_unit(self, dst, base_x=0, base_y=0, stat: State = None):
        """used for states that has no input"""

        base_x0 = base_x
        base_x += 2

        msg = compile_message(stat.branches[0].msg)
        
        draw_line(dst, base_x, base_y, msg)

        base_x += len(msg)

        self.draw_path(dst, base_x, base_y, stat)

        draw_line(dst, base_x0 + 0, base_y, "? +S?S", vertical=True)
        draw_line(dst, base_x0 + 1, base_y + 2, "S+R", vertical=True)

        draw_char(dst, base_x + 2, base_y + 5, "+")
        draw_char(dst, base_x + 4, base_y + 5, "+")
        draw_char(dst, base_x0 + 0, base_y + 6, "R")
        draw_line(dst, base_x + 1, base_y + 6, "S?S?")

        pad(dst)


    def draw_branching_unit(self, dst, base_x=0, base_y=0, stat: State = None):
        input_types = 1 << stat.n_input
        base_x0 = base_x
        base_x += 2

        for i in range(stat.n_input):
            n = int(math.pow(2, i))

            if ACC_IS_MULTI_BIT:
                for j in range(n):
                    draw_char(dst, base_x, base_y + j, "S")

                base_x += 1

            for j in range(n):
                draw_char(dst, base_x, base_y + j, ".")

            for j in range(n + 1):
                draw_char(dst, base_x + j, base_y + n + j, "R")
            for j in range(n):
                draw_char(dst, base_x + j + 1, base_y + j, "?")
                draw_char(dst, base_x + j, base_y + n + j + 1, "R")

            # input + "?" * n
            base_x += 1 + n

        msg_w = 0
        msgs = []
        for i in range(input_types):
            j = reverse_bits(i, stat.n_input)
            msg = compile_message(stat.branches[j].msg, j, stat.n_input)
            msg_w = max(len(msg), msg_w)
            msgs.append(msg)
        
        for i, msg in enumerate(msgs):
            msg = msg + " " * (msg_w - len(msg))
            draw_line(dst, base_x, base_y + i, msg)

        base_x += msg_w

        self.draw_path(dst, base_x, base_y, stat)

        draw_line(dst, base_x0 + 0, base_y + 0, "?+S?S", vertical=True)
        draw_line(dst, base_x0 + 1, base_y + 1, "S+R", vertical=True)

        continue_base = max(4, input_types)
        draw_char(dst, base_x + 2, base_y + continue_base + 1, "+")
        draw_char(dst, base_x + 4, base_y + continue_base + 1, "+")
        draw_char(dst, base_x0 + 0, base_y + continue_base + 2, "R")
        draw_line(dst, base_x + 1, base_y + continue_base + 2, "S?S?")

        pad(dst)

    def draw_filtering_unit(self, dst, base_x=0, base_y=0, stat: State = None):
        """
        > S.! S.? S.!  >101
          ? S ? S ? S  >other
          R+R R+R R+R
        """

        b_i, b2_i = stat.get_unique_branches()
        b = stat.branches[b_i]
        b2 = stat.branches[b2_i]

        key = f"{{:0{stat.n_input}b}}".format(b_i)

        base_x0 = base_x
        base_x += 2

        for i, c in enumerate(key):
            rot = "?" if c == "0" else "!"
            base_x2 = base_x + i * 3

            if ACC_IS_MULTI_BIT:
                draw_char(dst, base_x2 + 0, base_y, "S")

            draw_char(dst, base_x2 + 1, base_y, ".")
            draw_char(dst, base_x2 + 2, base_y, rot)

            draw_line(dst, base_x2 + 0, base_y + 1, "? S")
            draw_line(dst, base_x2 + 0, base_y + 2, "R+R")

        base_x2 = base_x + stat.n_input * 3

        msg = compile_message(b.msg, b_i, stat.n_input)
        msg2 = compile_message(b2.msg)
        msg_w = max(len(msg), len(msg2))

        draw_line(dst, base_x2, base_y + 0, msg)
        draw_line(dst, base_x2, base_y + 1, msg2)

        base_x2 += msg_w
        self.draw_path(dst, base_x2, base_y, stat, branches=stat.get_unique_branches())

        draw_line(dst, base_x0 + 0, base_y + 0, "?+S?S", vertical=True)
        draw_line(dst, base_x0 + 1, base_y + 1, "S+R", vertical=True)

        draw_char(dst, base_x2 + 2, base_y + 5, "+")
        draw_char(dst, base_x2 + 4, base_y + 5, "+")
        draw_char(dst, base_x0 + 0, base_y + 6, "R")
        draw_line(dst, base_x2 + 1, base_y + 6, "S?S?")

        pad(dst)

    def draw_ignoring_unit(self, dst, base_x=0, base_y=0, stat: State = None):
        """
        > ... >
        """

        b_i = stat.get_unique_branches()[0]
        b = stat.branches[b_i]
        base_x0 = base_x
        base_x += 2

        draw_line(dst, base_x, base_y, "." * stat.n_input)

        base_x2 = base_x + stat.n_input

        msg = compile_message(b.msg)
        msg_w = len(msg)

        draw_line(dst, base_x2, base_y + 0, msg)

        base_x2 += msg_w
        self.draw_path(dst, base_x2, base_y, stat, branches=stat.get_unique_branches() + [-1])

        draw_line(dst, base_x0 + 0, base_y + 0, "?+S?S", vertical=True)
        draw_line(dst, base_x0 + 1, base_y + 1, "S+R", vertical=True)

        draw_char(dst, base_x2 + 2, base_y + 5, "+")
        draw_char(dst, base_x2 + 4, base_y + 5, "+")
        draw_char(dst, base_x0 + 0, base_y + 6, "R")
        draw_line(dst, base_x2 + 1, base_y + 6, "S?S?")

        pad(dst)

    def compile(self):
        cw_codes = {}

        for name in self.stat_names:
            stat = self.stats[name]
            dst = [[" "]]

            if stat.n_input == 0:
                self.draw_joining_unit(dst,
                        base_x=0, base_y=0,
                        stat=stat)
            elif len(stat.get_unique_branches()) == 1:
                self.draw_ignoring_unit(dst,
                        base_x=0, base_y=0,
                        stat=stat)
            elif len(stat.branches) > 2 and len(stat.get_unique_branches()) == 2:
                self.draw_filtering_unit(dst,
                        base_x=0, base_y=0,
                        stat=stat)
            else:
                self.draw_branching_unit(dst,
                        base_x=0, base_y=0,
                        stat=stat)

            cw_codes[stat.name] = dst

        w = max([get_width(cw_codes[name]) for name in cw_codes])

        for name in self.stat_names:
            cw = cw_codes[name]

            for i, line in enumerate(cw):
                idx = len(line) - 6 * self.n_path
                pad_w = w - len(line)
                line = line[:idx] + list(" " * pad_w) + line[idx:]

                cw[i] = line

            base_x = w - 6 * (self.n_path - self.stat_names.index(name))
            cw.insert(-2, list(" " * w))
            cw.insert(-2, list(" " * w))

            draw_char(cw, base_x + 2, len(cw) - 4, "R")
            draw_char(cw, base_x + 4, len(cw) - 4, "+")
            draw_char(cw, base_x + 5, len(cw) - 4, "?")
            draw_char(cw, base_x + 5, len(cw) - 3, "S")
            draw_char(cw, base_x + 3, len(cw) - 2, "+")
            draw_char(cw, base_x + 5, len(cw) - 2, "+")
            draw_line(cw, base_x + 2, len(cw) - 1, "S?S?")

        for name in self.stat_names:
            cw = cw_codes[name]

            print("\n".join(filter(len, map("".join, cw))))

        base_x = w - 6 * self.n_path

        print(" " * base_x + "  S+  " * self.n_path)
        print(" " * base_x + "  R?SR" * self.n_path)

if __name__ == "__main__":
    import sys

    for arg in sys.argv[1:]:
        if arg == "-help":
            print("this program generates Clockwise program from declarative Mealy-machine-like state-machine definition")
            sys.exit(0)

    src = sys.stdin.readlines() + [""]

    states = States(src)

    states.compile()

