# Minimal-2D to 1D language compiler
from typing import Tuple, List


class CellInfo:
    def __init__(self, left: int = -1, right: int = -1, up: int = -1, down: int = -1) -> None:
        self.left = left
        self.right = right
        self.up = up
        self.down = down

    def get(self, dx: int, dy: int) -> int:
        if dx != dy:
            if dx == -1:
                return self.left
            if dx == 1:
                return self.right
            if dy == -1:
                return self.up
            if dy == 1:
                return self.down

        raise Exception(f"unknown direction ({dx}, {dy})")

    def set(self, dx: int, dy: int, v: int) -> int:
        if dx != dy:
            if dx == -1:
                self.left = v
            if dx == 1:
                self.right = v
            if dy == -1:
                self.up = v
            if dy == 1:
                self.down = v
            
            return

        raise Exception(f"unknown direction ({dx}, {dy})")


class Minimal2D:
    def __init__(self, source: str = None) -> None:
        self.width = 0
        self.height = 0

        if source is not None:
            self.load_source(source)

    def load_source(self, s: str):
        ss = s.split("\n")
        self.width = max(map(len, ss))
        self.height = len(ss)

        self.source = [i + " " * (self.width - len(i)) for i in ss]

    def create_label_table(self):
        return [[CellInfo() for _ in range(self.width)] for _ in range(self.height)]

    def name_to_dir(self, name: str) -> Tuple[int, int]:
        return {
            "L": (-1, 0),
            "R": (1, 0),
            "U": (0, -1),
            "D": (0, 1)
        }[name]

    def is_valid_pos(self, x: int, y: int) -> bool:
        return x in range(self.width) and y in range(self.height)

    def compile_to_intermediate(self) -> List[Tuple[int, str, int]]:
        labels = self.create_label_table()
        stubs = []
        lbl = 0
        code = []
        stk = []
        x = 0
        y = 0
        dx = 1
        dy = 0

        while len(stk) > 0 or self.is_valid_pos(x, y):
            onexit = False

            if len(stk) > 0 and not self.is_valid_pos(x, y):
                code.append((lbl, "exit", 0))
                onexit = True
            else:
                cell_labels = labels[y][x]
                c = self.source[y][x]

                lbl0 = cell_labels.get(dx, dy)

                if lbl0 != -1:
                    code.append((lbl, "jmp", lbl0))
                    onexit = True

            if onexit:
                if len(stk) == 0:
                    break

                lbl += 1
                x, y, dx, dy = stk.pop()
                branch_idx = stubs.pop()

                branch_lbl, _, _ = code[branch_idx]
                code[branch_idx] = (branch_lbl, "jz", lbl)

                continue

            # sys.stderr.write(f"{lbl:08}: ({x}, {y}) -> ({dx}, {dy})\n")
            cell_labels.set(dx, dy, lbl)

            if c in "LRUD":
                code.append((lbl, "", 0))

                lbl += 1
                dx, dy = self.name_to_dir(c)

                x += dx
                y += dy

                continue
            elif c in "+-><,.":
                code.append((lbl, c, 1))
            elif c == "/":
                x2 = x + dx
                y2 = y + dy
                x3 = x2 + dx
                y3 = y2 + dy

                stubs.append(len(code))
                stk.append((x3, y3, dx, dy))

                code.append((lbl, "jz", -1))
            else:
                code.append((lbl, "", 0))

            x += dx
            y += dy
            lbl += 1

        return code


class IntermediateCompiler:
    def __init__(self, src: List[Tuple[int, str, int]]):
        self.src = src

        self.optimize()

    def compile(self) -> List[str]:
        return ""

    def get_used_labels(self) -> List[int]:
        return sorted(list(set([arg for lbl, op, arg in self.src if op in ["jmp", "jz"]])))

    def skip_mergeable(self, idx: int, labels: List[int] = None) -> int:
        if labels is None:
            labels = self.get_used_labels()

        if idx not in range(len(self.src)):
            return len(self.src)

        lbl0, op0, _ = self.src[idx]

        if op0 not in "+-><":
            return idx + 1

        for i in range(idx + 1, len(self.src)):
            lbl, op, _ = self.src[i]

            if op != op0 or lbl in labels:
                return i

        return len(self.src)

    def replace_destination_labels(self, from_: int, to_: int):
        for i, (lbl, op, arg) in enumerate(self.src):
            if op in ["jmp", "jz"] and arg == from_:
                self.src[i] = (lbl, op, to_)

    def optimize(self):
        optimized = True
        while optimized:
            # sys.stderr.write(f"code size: {len(self.src)}\n")
            optimized = False

            labels = self.get_used_labels()

            i = 0
            while i < len(self.src):
                lbl, op, arg = self.src[i]

                if op == "" and lbl not in labels:
                    self.src.pop(i)
                else:
                    i += 1

            i = 1
            while i < len(self.src):
                lbl0, op0, arg0 = self.src[i - 1]
                lbl, op, arg = self.src[i]

                if op0 == "" and lbl0 in labels and lbl not in labels:
                    self.src[i] = (lbl0, op, arg)
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if op0 in ["jmp", "jz"] and arg0 == lbl and lbl0 not in labels:
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if op0 in ["jmp", "jz"] and op == "jmp" and arg0 == arg and lbl0 not in labels:
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if op0 in ["jmp", "exit"] and op == "jmp" and lbl in labels:
                    self.replace_destination_labels(lbl, arg)
                    self.src.pop(i)
                    optimized = True

                    continue

                if op0 == "" and lbl0 in labels and lbl in labels:
                    self.replace_destination_labels(lbl0, lbl)
                    self.src.pop(i - 1)
                    optimized = True

                    continue

                if op0 == "exit" and op == "exit":
                    if lbl0 not in labels:
                        self.src.pop(i - 1)
                        optimized = True

                        continue
                    elif lbl not in labels:
                        self.src.pop(i)
                        optimized = True

                        continue
                    elif lbl0 in labels and lbl in labels:
                        self.replace_destination_labels(lbl, lbl0)
                        self.src.pop(i)
                        optimized = True

                        continue

                if (op0 != op
                        and (set([op0, op]) == set(["+", "-"])
                                or set([op0, op]) == set(["+", "-"]))
                        and lbl not in labels):
                    self.src[i - 1] = (lbl0, "", 0)
                    self.src.pop(i)
                    optimized = True

                    continue

                if op0 == "jmp" and arg0 == lbl:
                    self.src[i - 1] = (lbl0, "", 0)
                    optimized = True

                    continue

                i += 1


class IntermediateToC(IntermediateCompiler):
    def __init__(self, src: List[Tuple[int, str, int]]):
        super().__init__(src)

    def compile(self) -> List[str]:
        dst = """
#include <stdio.h>
#include <stdint.h>
#ifndef DATA_SIZE
#define DATA_SIZE 0x1000
#endif
#ifdef USE_RING
uint8_t data[DATA_SIZE];
size_t i = 0;
#define p (&data[i])
#define ptr_inc(d) i = (i + d) % DATA_SIZE;
#define ptr_dec(d) i = (i - d) % DATA_SIZE;
#else
uint8_t data[DATA_SIZE], *p = data;
#ifdef UNSAFE_MODE
#define ptr_inc(d) p += d;
#define ptr_dec(d) p -= d;
#else
#define ptr_inc(d) p += d; if (p < data) return 1;
#define ptr_dec(d) p -= d; if (p < data) return 1;
#endif
#endif

int main(int argc, char *argv[]) {
""".split("\n")
        labels = self.get_used_labels()

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]

            if lbl in labels:
                dst.append(f"L{labels.index(lbl)}:")
            
            if op == "jz":
                dst.append(f"if (!*p) goto L{labels.index(arg)};")
            if op == "jmp":
                dst.append(f"goto L{labels.index(arg)};")
            if op == "+":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"*p += {j - i};")
                i = j
                continue
            if op == "-":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"*p -= {j - i};")
                i = j
                continue
            if op == ">":
                j = self.skip_mergeable(i, labels) 
                dst.append(f'ptr_inc({j - i})')
                i = j
                continue
            if op == "<":
                j = self.skip_mergeable(i, labels) 
                dst.append(f'ptr_dec({j - i})')
                i = j
                continue
            if op == ",":
                dst.append(f"*p = getchar();")
            if op == ".":
                dst.append(f"putchar(*p);")
            if op == "exit":
                dst.append("return 0;")

            i += 1

        dst.append("return 0;")
        dst.append("}")

        return dst


class IntermediateToX86(IntermediateCompiler):
    """uses NASM"""
    def __init__(self, src: List[Tuple[int, str, int]]):
        super().__init__(src)

    def compile(self) -> List[str]:
        dst = """
; link to something like this

; #include <stdio.h>
; #include <stdint.h>
; extern void bf_main();
; uint8_t bf_data[1024];
; uint32_t bf_getc() { return getchar(); }
; void bf_putc(uint32_t v) { putchar(v); }
; int main(int argc, char *argv[]) { bf_main(); return 0; }

; msvc(x86)/MinGW(x86): nasm -fwin32 --prefix _
; tcc(win32): nasm -felf

; cdecl
extern bf_putc, bf_getc
; data
extern bf_data
global bf_main
section .text
bf_main:
mov edx, bf_data
""".split("\n")
        labels = self.get_used_labels()

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]

            if lbl in labels:
                dst.append(f".L{labels.index(lbl)}:")
            
            if op == "jz":
                dst.append("movzx eax, byte[edx]")
                dst.append("or eax, eax")
                dst.append(f"jz .L{labels.index(arg)}")
            if op == "jmp":
                dst.append(f"jmp .L{labels.index(arg)}")
            if op == "+":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"add byte[edx], {j - i}")
                i = j
                continue
            if op == "-":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"sub byte[edx], {j - i}")
                i = j
                continue
            if op == ">":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"add edx, {j - i}")
                i = j
                continue
            if op == "<":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"sub edx, {j - i}")
                i = j
                continue
            if op == ",":
                dst.append("push edx")
                dst.append("call bf_getc")
                dst.append("pop edx")
                dst.append("mov byte[edx], al")
            if op == ".":
                dst.append("movzx eax, byte[edx]")
                dst.append("push edx")
                dst.append("push eax")
                dst.append("call bf_putc")
                dst.append("pop eax")
                dst.append("pop edx")
            if op == "exit":
                dst.append("ret")

            i += 1

        dst.append("ret")

        return dst


class IntermediateToCASL2(IntermediateCompiler):
    def __init__(self, src: List[Tuple[int, str, int]]):
        super().__init__(src)

    def make_cas(self, lbl, op, args):
        return f"{lbl:10}{op:18}{args}"
    def compile(self) -> List[str]:
        lib = """
; result:GR0
; never returns EOF
GETC      START
          LD      GR0, IBUFINIT
          OR      GR0, GR0
          JNZ     GETC1
          ; init
          IN      IBUF, IBUFSZ
          LD      GR1, =0
          ST      GR1, IIDX
          LD      GR1, =1
          ST      GR1, IBUFINIT
GETC1     LD      GR1, IIDX
          SUBL    GR1, IBUFSZ
          JNZ     GETC2
          ; at EOS
          LD      GR1, =0
          ST      GR1, IIDX
          LD      GR1, =0
          ST      GR1, IBUFSZ
          LD      GR1, =0
          ST      GR1, IBUFINIT
          LD      GR0, =10
          RET
GETC2     LD      GR1, IIDX
          LD      GR0, IBUF, GR1
          OR      GR0, GR0
          JNZ     GETC3
          ; at EOL
          LD      GR1, =0
          ST      GR1, IIDX
          LD      GR1, =0
          ST      GR1, IBUFSZ
          LD      GR1, =0
          ST      GR1, IBUFINIT
          LD      GR0, =10
          RET
GETC3     ADDL    GR1, =1
          ST      GR1, IIDX
          RET
IBUFSZ    DC      0
IBUFINIT  DC      0
IIDX      DC      0
IBUF      DS      256
          END

; parameter:GR0
; if GR0 == 10: print line
; if GR0 == 0: print line when buffer is not empty
PUTC      START
          LD      GR1, GR0
          OR      GR1, GR1
          JZE     IFNEMPTY
          LD      GR1, GR0
          SUBL    GR1, =10
          JZE     FLUSH
          LD      GR1, OIDX
          ST      GR0, OBUF, GR1
          ADDL    GR1, =1
          ST      GR1, OIDX
          SUBL    GR1, =126
          JZE     FLUSH
          RET
IFNEMPTY  LD      GR1, OIDX
          OR      GR1, GR1
          JZE     ENDPUTC
FLUSH     OUT     OBUF, OIDX
          LD      GR1, =0
          ST      GR1, OIDX
ENDPUTC   RET
OIDX      DS      1
OBUF      DS      128
          END
""".split("\n")
        dst = [
            "PROG      START",
            "          LD GR1, =16"
        ]
        labels = self.get_used_labels()

        tab = " " * 10

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]

            if lbl in labels:
                s = f"L{labels.index(lbl)}"
                s += " " * (10 - len(s))
            else:
                s = tab

            if op == "":
                dst.append(s + "NOP")
            
            if op == "jz":
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + "OR GR0, GR0")
                dst.append(tab + f"JZE L{labels.index(arg)}")
            if op == "jmp":
                dst.append(tab + f"JUMP L{labels.index(arg)}")
            if op == "+":
                j = self.skip_mergeable(i, labels) 
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + f"ADDL GR0, ={j - i}")
                dst.append(tab + "ST GR0, DATA, GR1")
                i = j
                continue
            if op == "-":
                j = self.skip_mergeable(i, labels) 
                dst.append(s + "LD GR0, DATA, GR1")
                dst.append(tab + f"SUBL GR0, ={j - i}")
                dst.append(tab + "ST GR0, DATA, GR1")
                i = j
                continue
            if op == ">":
                j = self.skip_mergeable(i, labels) 
                dst.append(s + f"ADDL GR1, ={j - i}")
                i = j
                continue
            if op == "<":
                j = self.skip_mergeable(i, labels) 
                dst.append(s + f"SUBL GR1, ={j - i}")
                i = j
                continue
            if op == ",":
                dst.append(s + "LD GR4, GR1")
                dst.append(tab + "CALL GETC")
                dst.append(tab + "LD GR1, GR4")
                dst.append(tab + "ST GR0, DATA, GR1")
            if op == ".":
                dst.append(s + "LD GR4, GR1")
                dst.append(tab + "LD GR0, DATA, GR1")
                dst.append(tab + "CALL PUTC")
                dst.append(tab + "LD GR1, GR4")
            if op == "exit":
                dst.append(s + "JUMP ONEXIT")

            i += 1

        dst.append("ONEXIT    LD GR0, =10")
        dst.append(tab + "CALL PUTC")
        dst.append(tab + "RET")
        dst.append("DATA      DS 128")
        dst.append(tab + "END")
        dst += lib

        return dst


class IntermediateToErp(IntermediateCompiler):
    def __init__(self, src: List[Tuple[int, str, int]]):
        super().__init__(src)

    def compile(self) -> List[str]:
        dst = [
            "( erp2bf src.erp -rs2 -ds4 )",
            # "import erp_base",
            "ary mem 256",
            "var p",
            ": main",
            "'mem =p"
        ]

        branches = 0
        labels = self.get_used_labels()

        i = 0
        while i < len(self.src):
            lbl, op, arg = self.src[i]

            if lbl in labels:
                dst.append(f": .L{labels.index(lbl)}")
            
            if op == "jz":
                dst.append(f"p @ '.Lif{branches} '.L{labels.index(arg)} if jmp")
                dst.append(f": .Lif{branches}")
                branches += 1
            if op == "jmp":
                dst.append(f"'.L{labels.index(arg)} jmp")
            if op == "+":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"p @ {j - i} + p !")
                i = j
                continue
            if op == "-":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"p @ {j - i} - p !")
                i = j
                continue
            if op == ">":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"p {j - i} + =p")
                i = j
                continue
            if op == "<":
                j = self.skip_mergeable(i, labels) 
                dst.append(f"p {j - i} - =p")
                i = j
                continue
            if op == ",":
                dst.append(f"getc p !")
            if op == ".":
                dst.append(f"p @ putc")
            if op == "exit":
                dst.append("'.Lexit jmp")

            i += 1

        dst.append(": .Lexit")
        dst.append(";")

        return dst


if __name__ == "__main__":
    import sys

    lang = "erp"

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.startswith("-lang="):
            lang = arg[6:]

        if arg in ["-?", "-h", "-help", "--help"]:
            print(f"python {sys.argv[0]} [options] < src > dst")
            print("options:")
            print("  -lang=lang_name   select target language")
            print("target languages: C, erp(only for helloworld), x86, CASL2")
            sys.exit(0)

    m2d = Minimal2D("".join(sys.stdin.readlines()))
    compilers = {
        "C": IntermediateToC,
        "erp": IntermediateToErp,
        "x86": IntermediateToX86,
        "CASL2": IntermediateToCASL2
    }

    if lang not in compilers.keys():
        sys.stderr.write(f"{lang} generator is not implemented\n")
        sys.exit(1)

    code = m2d.compile_to_intermediate()
    compiler = compilers[lang](code)

    print("\n".join(compiler.compile()))


# if you can not write in Minimal-2D, write in Brainfuck.
#
# #include <stdio.h>
# int c,d,i;void I(d){for(i=0;i++<d*3;)putchar(32);}int main(){puts("D");
# while(!feof(stdin)){(c=getchar())-91||(I(d),puts("/"),I(d),puts("RR D")
# ,++d||--d);c-93||(d&&d--,I(d),puts("DU/L"));c-43&&c-45&&c-62&&c-60&&c-
# 44&&c-46||(I(d),printf("%c\n",c));}return puts("");}
