# Brainfuck compiler
#
# fast loading. generates shorter code with low optimizability.
from typing import Tuple, List
import atdbf


class BrainfuckCompiler2(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "BrainFuck"
    HELP = ""

    SYMS_BF_BRACKETS = list("[]")
    SYMS_PTR_INC = [">"]
    SYMS_PTR_DEC = ["<"]
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = [","]

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

    def compile_to_intermediate(self) -> List[Tuple[int, str, int]]:
        INC_OR_DEC = type(self).SYMS_INC + type(self).SYMS_DEC
        PTR_INC_DEC = type(self).SYMS_PTR_INC + type(self).SYMS_PTR_DEC
        LBRKT = type(self).SYMS_BF_BRACKETS[0::2]
        RBRKT = type(self).SYMS_BF_BRACKETS[1::2]
        dst = []
        lbls = 0
        lbl = -1
        stk = []

        def label(lbl, cmd, arg):
            if lbl != -1:
                lbl = len(dst)

            dst.append(atdbf.IntermediateInstruction(lbl, cmd, 0, arg))

            return -1

        src = "".join(self.source)
        i = 0
        while i in range(len(src)):
            if src[i] in INC_OR_DEC:
                n = 0
                while i < len(src) and src[i] in INC_OR_DEC:
                    if src[i] in type(self).SYMS_INC:
                        n += 1
                    else:
                        n -= 1
                    i += 1

                if n > 0:
                    lbl = label(lbl, "+", n)
                if n < 0:
                    lbl = label(lbl, "-", -n)

                continue
            elif src[i] in PTR_INC_DEC:
                n = 0
                while i < len(src) and src[i] in PTR_INC_DEC:
                    if src[i] in type(self).SYMS_PTR_INC:
                        n += 1
                    else:
                        n -= 1
                    i += 1
                
                if n > 0:
                    lbl = label(lbl, ">", n)
                if n < 0:
                    lbl = label(lbl, "<", -n)
                
                continue
            elif src[i] in type(self).SYMS_GET:
                lbl = label(lbl, ",", 0)
            elif src[i] in type(self).SYMS_PUT:
                lbl = label(lbl, ".", 0)
            elif src[i] in LBRKT:
                if (i + 2 < len(src)
                        and src[i + 1] in INC_OR_DEC
                        and src[i + 2] in RBRKT):
                    lbl = label(lbl, "assign", 0)
                    i += 2
                else:
                    stk.append(len(dst))
                    lbl = label(lbl, "jz", 0)
            elif src[i] in RBRKT:
                lbl2 = stk.pop()

                dst[lbl2].lbl = lbl2
                dst[lbl2].arg1 = len(dst) + 1
                label(lbl, "jmp", lbl2)
                lbl = 1

            i += 1

        if lbl != -1:
            lbl = label(lbl, "", 0)

        return dst

if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(BrainfuckCompiler2))

