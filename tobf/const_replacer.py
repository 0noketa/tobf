from typing import Tuple, List
from base import calc_small_triple
import sys

class Instruction:
    def __init__(self, op: str, arg: int):
        self.op = op
        self.arg = arg

    def __str__(self) -> str:
        return f"{self.op}{self.arg}"

    def __repr__(self) -> str:
        return self.__str__()

class ReplacementCode:
    """expresses difference between input state and output state\n
        from_: first pointer index\n
        to_: last pointer index\n
        code: list of (instruction, argument))\n
        is_initial: code is placed at the first of entire source code\n
        instructions:\n
            '=': assignment\n
            '+': addition\n
            '!': known\n
            '?': unknown\n
    """
    def __init__(self, from_: int, to_: int, code: List[Instruction], is_initial=False) -> None:
        self.from_ = from_
        self.to_ = to_
        self.code = code
        self.is_initial = is_initial

    def find_similar_values(self, target: int, d: int, is_reversed=False) -> List[int]:
        """target: avg\n
           d: acceptable distance\n
           is_reversed: uses reversed index\n
           returns indices of instructions that create similar values
        """

        r = []

        code = reversed(self.code) if is_reversed else self.code

        for idx, i in enumerate(code):
            if abs(i.arg - target) <= d:
                r.append(idx)

        return r

    def find_nearest_assignment(self, i: int, is_reversed=False, include_initial=False) -> int:
        code = list(reversed(self.code)) if is_reversed else self.code
        ops = "!=" if include_initial else "="

        for j in range(1, len(self.code)):
            if i - j < 0 and i + j >= len(self.code):
                break

            if i + j < len(self.code) and code[i + j].op in ops:
                return i + j

            if i - j > 0 and code[i - j].op in ops:
                return i - j

        return -1


class ConstReplacer:
    """optimizes simple patterns in brainfuck
    """

    @classmethod
    def valid_source(self, src: str) -> bool:
        for i in ",.[]":
            if i in src:
                return False
        
        return True

    @classmethod
    def unroll(self, src: str) -> str:
        """unrolls simple loops\n
           from: +[>+<-]\n
           to: [-]>++<
        """
        return src

    @classmethod
    def find_optimizable(self, s: str, start_: int, min_length: int) -> Tuple[int, str]:
        """returns (index, pattern)"""

        i = start_
        while i < len(s):
            first = i
            while first < len(s):
                if s[first] in "<>+-0":
                    break

                first += 1
            
            if first >= len(s):
                return [-1, ""]

            last = first + 1
            while last < len(s):
                if s[last] in ",.[]":
                    break

                last += 1

            if last - first >= min_length:
                return [first, s[first:last]]

            i = last + 1

        return [-1, ""]

    @classmethod
    def extract_optimizable(self, s: str) -> str:
        for i in range(len(s)):
            if s[i] in ",.[]":
                return s[:i]
        
        return s

    @classmethod
    def create_instructions(self, src: str, is_initial=False) -> ReplacementCode:
        default_op = "!" if is_initial else "?"
        base = 0
        mem = [Instruction(default_op, 0)]
        p = 0

        for i in src:
            if i == ">":
                p += 1
                if len(mem) <= base + p:
                    mem.append(Instruction(default_op, 0))
            if i == "<":
                p -= 1
                if p < 0:
                    p = 0
                    base += 1
                    mem.insert(0, Instruction(default_op, 0))
            if (i in "+-") and mem[p].op not in "+=":
                mem[p] = Instruction('+', 0)
            if i == "+":
                mem[p].arg += 1
            if i == "-":
                mem[p].arg -= 1
            if i == "0":
                mem[p] = Instruction('=', 0)

        return ReplacementCode(base, p, mem, is_initial=is_initial)


    @classmethod
    def compile_instructions(self, src: ReplacementCode) -> str:
        # 0,F,0,0,L,0
        # < >>>>> <
        # 0,L,0,0,F,0
        # > <<<<< >

        if src.from_ <= src.to_:
            from_ = src.from_
            to_ = src.to_
            left = "<"
            right = ">"
            code = src.code
            is_reversed = False
        else:
            from_ = len(src.code) - src.from_ - 1
            to_ = len(src.code) - src.to_ - 1
            left = ">"
            right = "<"
            code = list(reversed(src.code))
            is_reversed = True


        if from_ > 0:
            s = left * from_
        else:
            s = ""

        remained = list(range(len(src.code)))
        zeroed = []

        for idx, i in enumerate(code):
            if i.op in ["!", "?"]:
                remained.remove(idx)

            if i.op != "!":
                continue

            if i.arg == 0:
                zeroed.append(idx)

        for idx, i in enumerate(code):
            s0 = right if idx > 0 else ""

            if idx not in remained:
                s += s0
                continue

            if i.op == "=" and not src.is_initial:
                s0 += "[-]"

            done = False

            if i.arg > 8:
                asgn_idx = src.find_nearest_assignment(
                        idx,
                        is_reversed=is_reversed,
                        include_initial=src.is_initial)

                if (asgn_idx in remained) or (asgn_idx in zeroed):
                    d = abs(asgn_idx - idx)
                    x, y, z = calc_small_triple(i.arg)

                    if d * 4 + 3 + x + y + z < i.arg:
                        mov = left if asgn_idx < idx else right
                        ret = right if asgn_idx < idx else left
                        o = "+" if i.arg > 0 else "-"

                        s0 += o * z + mov * d

                        if asgn_idx in remained:
                            s0 += "[-]"

                        s0 += "+" * x + "[" + ret * d + o * y + mov * d + "-]"

                        if asgn_idx in remained:
                            s0 += "+" * code[asgn_idx].arg

                            remained.remove(asgn_idx)
                            zeroed.append(asgn_idx)

                        s0 += ret * d

                        done = True


            if not done:
                if i.arg > 0:
                    s0 += "+" * i.arg
                if i.arg < 0:
                    s0 += "-" * -i.arg

            remained.remove(idx)

            if i.op == "=" and i.arg == 0:
                zeroed.append(idx)

            s += s0

        s += left * (len(src.code) - to_ - 1)

        return s
    
    def __init__(self, s: str) -> None:
        if not ConstReplacer.valid_source(s):
            raise Exception("can not optimize source code")

        self.src = s

def optimize(src: str, req=8, is_initial=False) -> str:
    src = "".join([i for i in src if i in "><+-,.[]"]).replace("[-]", "0")

    r = ""

    i = 0
    while i < len(src):
        j, s = ConstReplacer.find_optimizable(src, i, req)


        if j == -1:
            r += src[i:].replace("0", "[-]")
            break

        r += src[i:j].replace("0", "[-]")

        is_init = is_initial and j == 0
        code = ConstReplacer.create_instructions(s, is_initial=is_init)

        r += ConstReplacer.compile_instructions(code)

        i = j + len(s)

    return r


if __name__ == "__main__":
    req = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    src = "".join(sys.stdin.readlines())
    
    print(optimize(src, req, True))
