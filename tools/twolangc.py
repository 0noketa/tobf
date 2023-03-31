# 2L to 1D language compiler (stub)
#
# 2L
# https://esolangs.org/wiki/2L
from typing import Tuple, List, Dict
import atdbf


def twolang_wall(stat: atdbf.LoaderState):
    stat.x -= stat.dx
    stat.y -= stat.dy

    dx2, dy2 = atdbf.Abstract2DBrainfuck.rotate_dir(stat.dx, stat.dy, False)
    dx3, dy3 = atdbf.Abstract2DBrainfuck.rotate_dir(stat.dx, stat.dy)

    stat.stubs.append(len(stat.code))
    stat.stk.append((stat.x + dx2, stat.y + dy2, dx2, dy2))

    stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "jz", 0, -1))

    stat.dx = dx3
    stat.dy = dy3
    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

def twolang_cmd(stat: atdbf.LoaderState):
    if stat.dx == 0:
        if stat.dy == 1:
            # down
            stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "2l.ptr_dec", 0, 1))
        else:
            # up
            stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "2l.ptr_inc", 0, 1))
    else:
        if stat.dx == 1:
            # right
            stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "2l.inc", 0, 1))
        else:
            # left
            stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "2l.dec", 0, 1))

    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat


class TwoLanguage(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "2L"
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
    SYMS_BF_BRACKETS = []
    SYMS_SKIP = []
    SYMS_SKIPZ = []
    SYMS_PTR_INC = []
    SYMS_PTR_DEC = []
    SYMS_PTR_UP = []
    SYMS_PTR_DOWN = []
    SYMS_INC = []
    SYMS_DEC = []
    SYMS_PUT = []
    SYMS_GET = []
    INS_TBL = {
        "+": twolang_wall,
        "*": twolang_cmd
    }
    INITIAL_DIR = (0, 1)
    DEFAULT_MEM_WIDTH = -1

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)


class IntermediateExtension(atdbf.IntermediateExtension):
    def __init__(self) -> None:
        super().__init__()

    def is_register_based(self) -> bool:
        return False

    def n_registers(self) -> int:
        return 0
    def n_hidden_registers(self) -> int:
        return 0

    def requires_initialization(self) -> bool:
        return True

    def has_instruction(self, name: str) -> bool:
        return name in ["2l.ptr_inc", "2l.ptr_dec", "2l.inc", "2l.dec"]

    def is_mergeable_instruction(self, name: str) -> bool:
        return (super().is_mergeable_instruction(name)
                or (name in ["2l.ptr_inc", "2l.ptr_dec", "2l.inc", "2l.dec"]))

    def can_compile_to(self, target_language: str) -> bool:
        return target_language in ["Python", "exec", "C", "Brainfuck", "disasm"]

    def get_initializer(self, target_language: str, stat: atdbf.CompilerState) -> List[str]:
        dst = {
            "exec": ["ptr = 2"],
            "Python": ["ptr = 2"],
            "C": [
                "static int twolang_io(int n) { if (p != &data[1]) return 0; while (n--) if (data[0] != 0) { putchar(data[0]); } else { data[0] = getchar(); } return 1; }",
                "#define twolang_inc(n) { if (!twolang_io(n)) *p += n; }",
                "#define twolang_dec(n) { if (!twolang_io(n)) *p -= n; }",
                None,
                "ptr_inc(2)"
            ],
            "Brainfuck": {
                ">>>>>>+>+<<<<<<<"
            }
        }
        return dst[target_language] if target_language in dst.keys() else []

    def compile_instruction(self, target_language: str, ins: atdbf.IntermediateInstruction, stat: atdbf.CompilerState):
        py_io = [
            f"      if ptr == 1:",
            f"        for _ in range({ins.arg1}):",
            f"          if mem[0] == 0:",
            f"            mem[0] = getc()",
            f"          else:",
            f"            putc(mem[0])",
            f"      else:",
        ]
        templates_all = {
            "exec": None,
            "Python": {
                "2l.ptr_inc": [f"      ptr += {ins.arg1}"],
                "2l.ptr_dec": [f"      ptr -= {ins.arg1}"],
                "2l.inc": py_io + [f"        mem[ptr] = (mem[ptr] + {ins.arg1}) & CELL_MASK"],
                "2l.dec": py_io + [f"        mem[ptr] = (mem[ptr] - {ins.arg1}) & CELL_MASK"]
            },
            "C": {
                "2l.ptr_inc": [
                    f"ptr_inc({ins.arg1})"
                ],
                "2l.ptr_dec": [
                    f"ptr_dec({ins.arg1})"
                ],
                "2l.inc": [
                    f"twolang_inc({ins.arg1})"
                ],
                "2l.dec": [
                    f"twolang_dec({ins.arg1})"
                ]
            },
            "Brainfuck": {
                "2l.ptr_inc": [
                    ">+>" * ins.arg1
                ],
                "2l.ptr_dec": [
                    "<-<" * ins.arg1
                ],
                "2l.inc": [
                    # broken
                    # any: 0 v 1 v 1 current 0 next 0
                    # IO : 0 v 1 current 0 next 0
                    """
                    >>>+<<<
                    <[<]
                    +[  -
                        >>[<<+>>-]
                        <<[ - GT0
                            >>>>[<<+<<->>>>-]
                            +
                            <<<<[>>>>-<<<< LT2 IO
                                -
                                >[  .[<+>-]
                                ]
                                <[  [>+<-]
                                    >>-<<
                                ]
                                >>[ -
                                    <,>
                                    >>[>]
                                    >>-<<
                                    <<[<]
                                ]
                                >>+<<
                            ]
                            >>[<<+>>-]
                            [ GTE2
                                >>>>+<<<<-
                            ]
                            >>+<<
                    ]   ]
                    >>[>]
                    >>[ - INC
                        <<<+>>>
                    ]
                    <<<
                    """ * ins.arg1
                    # any: 0 v 1 v 1 current 0 next 0
                    # IO : 0 v 1 current 0 next 0
                ],
                "2l.dec": [
                    """
                    -
                    """ * ins.arg1
                ]
            }
        }

        templates_all["exec"] = templates_all["Python"]

        templates = templates_all[target_language] if target_language in templates_all.keys() else {}

        return templates[ins.op] if ins.op in templates.keys() else []

    def can_invoke(self) -> bool:
        return True

    def initialize(self, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        stat.ptr = 2

        return stat

    def invoke_instruction(self, ins: atdbf.IntermediateInstruction, stat: atdbf.InterpreterState) -> int:
        if ins.op == "2l.ptr_inc":
            stat.ptr = (stat.ptr + ins.arg1) % len(stat.data)
        elif ins.op == "2l.ptr_dec":
            stat.ptr = (stat.ptr - ins.arg1) % len(stat.data)
        elif ins.op in ["2l.inc", "2l.dec"]:
            if stat.ptr == 1:
                for _ in range(ins.arg1): 
                    if stat.data[0] == 0:
                        stat.data[0] = ord(sys.stdin.read(1))
                    else:
                        sys.stdout.write(chr(stat.data[0]))
            else:
                if ins.op == "2l.inc":
                    stat.data[stat.ptr] = (stat.data[stat.ptr] + ins.arg1) & 0xFF
                else:
                    stat.data[stat.ptr] = (stat.data[stat.ptr] - ins.arg1) & 0xFF

        stat.ip += 1

        return stat


if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(TwoLanguage, IntermediateExtension()))

