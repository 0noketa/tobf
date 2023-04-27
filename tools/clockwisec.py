# Clockwise to 1D language compiler
#
# implemented as:
#   accumlator is unsigned (affects to nothing)
#   input queue can contain EOF
#
# Clockwise:
# https://esolangs.org/wiki/Clockwise
from typing import Dict, Tuple, List, Callable
import sys
import atdbf


def clockwise_push(stat: atdbf.LoaderState) -> atdbf.LoaderState:
    stat.append_instruction("clockwise_push", 0, 0)
    stat.x += stat.dx
    stat.y += stat.dy

    return stat

def clockwise_pop(stat: atdbf.LoaderState) -> atdbf.LoaderState:
    stat.append_instruction("clockwise_pop", 0, 0)
    stat.x += stat.dx
    stat.y += stat.dy

    return stat

def clockwise_clear(stat: atdbf.LoaderState) -> atdbf.LoaderState:
    stat.append_instruction("assign", 0, 0)
    stat.x += stat.dx
    stat.y += stat.dy

    return stat


class Clockwise(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "Clockwise"
    HELP = ""
    SYMS_START = []
    SYMS_EXIT = []
    SYMS_TURN = []
    SYMS_TURNNZ = []
    SYMS_MIRROR_R_TO_U = []
    SYMS_MIRROR_R_TO_D = []
    SYMS_MIRROR_R_TO_L = []
    SYMS_MIRROR_H = []
    SYMS_MIRROR_V = []
    SYMS_MIRRORNZ_R_TO_L = []
    SYMS_ROT_R = ["R"]
    SYMS_ROTNZ_R = ["?"]
    SYMS_ROTZ_R = ["!"]
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = []
    SYMS_PTR_DEC = []
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = []
    SYMS_GET = []
    INS_TBL = {
        ".": clockwise_pop,
        ";": clockwise_push,
        "S": clockwise_clear
    }
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

class IntermediateExtension(atdbf.IntermediateExtension):
    def __init__(self) -> None:
        super().__init__()

    def is_register_based(self) -> bool:
        return True

    def n_registers(self) -> int:
        return 1
    def n_hidden_registers(self) -> int:
        return 0

    def requires_initialization(self) -> bool:
        return True

    def has_instruction(self, name: str) -> bool:
        return name in ["clockwise_push", "clockwise_pop"]

    def can_compile_to(self, target_language: str) -> bool:
        return target_language in ["exec", "Python", "C", "disasm"]

    def get_initializer(self, target_language: str, stat: atdbf.CompilerState) -> List[str]:
        pycode = [
            None,
            "  clockwise_iqueue = []",
            "  clockwise_eof = False",
            "  clockwise_ibuf = 0",
            "  clockwise_obuf = 0",
            "  clockwise_acc = 0",
            "  clockwise_iidx = -1",
            "  clockwise_oidx = 0",
        ]
        dst = {
            "exec": pycode,
            "Python": pycode,
            "C": [
                "#ifndef QUEUE_SIZE",
                "#define QUEUE_SIZE 256",
                "#endif",
                "#ifndef IO_BYTE_SIZE",
                "#define IO_BYTE_SIZE 7",
                "#endif",
                "uint8_t q[QUEUE_SIZE];",
                "int qi = 0, qz = 0;",
                "int ii = 0, oi = 0, ie = 0;",
                "uint8_t obuf = 0;",
                "void clockwise_pop() {",
                "#ifndef EXIT_ON_EOF",
                "  if (ie) { r0 = ((q[qi] >> --ii) & 1); if (ii == 0) { qi = (qi + 1) % qz; ii = IO_BYTE_SIZE; } } else ",
                "#endif",
                "  { if (ii == 0) { if (qz < QUEUE_SIZE) ++qz; if (feof(atdbf_in)) {",
                "#ifdef EXIT_ON_EOF",
                "      return;",
                "#else",
                "      q[qz - 1] = 0xFF; ie = 1;",
                "#endif",
                "    } else q[qz - 1] = fgetc(atdbf_in); ii = IO_BYTE_SIZE; } r0 = ((q[qz - 1] >> --ii) & 1) | (r0 & (~0 ^ 1)); }",
                "}",
                "void clockwise_push() { obuf = (obuf << 1) | (r0 & 1); if (++oi == IO_BYTE_SIZE) { fputc(obuf, atdbf_out); obuf = 0; oi = 0; } }",
                None
            ]
        }
        return dst[target_language] if target_language in dst.keys() else []

    def compile_instruction(self, target_language: str, ins: atdbf.IntermediateInstruction, stat: atdbf.CompilerState):
        pycode = {
            "clockwise_pop":
"""
      if clockwise_iidx == -1:
        if not clockwise_eof:
          s = input_file.read(1)
          clockwise_ibuf = ord(s[0]) if len(s) else 0xFF

          if len(s) == 0:
            clockwise_eof = True
        else:
          clockwise_ibuf = clockwise_iqueue.pop(0)

        clockwise_iqueue.append(clockwise_ibuf)
        clockwise_iidx = 6

      r0 = ((clockwise_ibuf >> clockwise_iidx) & 1)
      clockwise_iidx -= 1
""".splitlines(),
            "clockwise_push":
"""
      clockwise_obuf = ((clockwise_obuf << 1) | (r0 & 1)) & 0x7F
      clockwise_oidx += 1

      if clockwise_oidx == 7:
        output_file.write(chr(clockwise_obuf))
        clockwise_oidx = 0
        clockwise_obuf = 0
""".splitlines()
        }
        templates_all = {
            "exec": pycode,
            "Python": pycode,
            "C": {
                "clockwise_pop": [
                    "clockwise_pop();"
                ],
                "clockwise_push": [
                    "clockwise_push();"
                ]
            }
        }

        templates = templates_all[target_language] if target_language in templates_all.keys() else {}

        return templates[ins.op] if ins.op in templates.keys() else []

    def can_invoke(self) -> bool:
        return True

    def initialize(self, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        self.iqueue = []
        self.eof = False
        self.ibuf = 0
        self.obuf = 0
        self.acc = 0
        self.iidx = -1
        self.oidx = 0

        return stat

    def invoke_instruction(self, ins: atdbf.IntermediateInstruction, stat: atdbf.InterpreterState) -> int:
        if ins.op == "clockwise_pop":
            if self.iidx == -1:
                if not self.eof:
                    s = sys.stdin.read(1)
                    self.ibuf = ord(s[0]) if len(s) else 0xFF

                    if len(s) == 0:
                        self.eof = True
                else:
                    self.ibuf = self.iqueue.pop(0)

                self.iqueue.append(self.ibuf)
                self.iidx = 6

            stat.data[0] = ((self.ibuf >> self.iidx) & 1)
            self.iidx -= 1
        elif ins.op == "clockwise_push":
            self.obuf = ((self.obuf << 1) | (stat.data[0] & 1)) & 0x7F
            self.oidx += 1

            if self.oidx == 7:
                sys.stdout.write(chr(self.obuf))
                self.oidx = 0
                self.obuf = 0

        stat.ip += 1

        return stat

if __name__ == "__main__":
    sys.exit(atdbf.main(Clockwise, IntermediateExtension()))

