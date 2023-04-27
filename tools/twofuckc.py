# 2fuck to 1D language compiler
#
# limitation:
#   tape is not looped 
#
# 2fuck
# https://codegolf.stackexchange.com/questions/257017/implement-a-2fuck-interpreter
from typing import Tuple, List, Dict
import atdbf


ignore_eof = True


def twofuck_get(stat: atdbf.LoaderState):
    if ignore_eof:
        stat.code.append(atdbf.IntermediateInstruction(stat.lbl, "2fuck.get", 0, 1))
    else:
        stat.code.append(atdbf.IntermediateInstruction(stat.lbl, ",", 0, 1))

    stat.x += stat.dx
    stat.y += stat.dy
    stat.lbl += 1

    return stat

class TwoFuck(atdbf.Abstract2DBrainfuck):
    # language definition
    NAME = "2fuck"
    HELP = """
  -read_eof     read EOF
"""
    SYMS_TURN = list("<>^v")
    SYMS_ROTNZ_L = ["?"]
    SYMS_PTR_INC = ["]"]
    SYMS_PTR_DEC = ["["]
    SYMS_INC = ["+"]
    SYMS_DEC = ["-"]
    SYMS_PUT = ["."]
    SYMS_GET = []
    INS_TBL = {
        ",": twofuck_get
    }

    def __init__(self, source: str = None, argv: List[str] = []) -> None:
        super().__init__(source, argv)

        for arg in argv:
            if arg == "-read_eof":
                ignore_eof = False

class IntermediateExtension(atdbf.IntermediateExtension):
    def __init__(self) -> None:
        super().__init__()

    def can_compile_to(self, target_language: str) -> bool:
        if ignore_eof:
            return target_language in atdbf.all_targets
        else:
            return target_language in ["exec", "Python", "C", "Brainfuck", "disasm"]

    def compile_instruction(self, target_language: str, ins: atdbf.IntermediateInstruction, stat: atdbf.CompilerState):
        pycode = """
      twofuck_c = input_file.read(1)
      if len(twofuck_c):
        mem[ptr] = twofuck_c
"""

        templates_all = {
            "Python": {
                "2fuck.get": pycode
            },
            "Python": {
                "2fuck.get": pycode
            },
            "C": {
                "2fuck.get": "{ int c = feof(stdin) ? -1 : getchar(); if (c != -1) *p = c; }"
            },
            "Brainfuck": {
                "2fuck.get": ">,+[<[-]>-[<+>-]]<"                
            },
        }

        templates = templates_all[target_language] if target_language in templates_all.keys() else {}

        return templates[ins.op] if ins.op in templates.keys() else []

    def can_invoke(self) -> bool:
        return True

    def invoke_instruction(self, ins: atdbf.IntermediateInstruction, stat: atdbf.InterpreterState) -> atdbf.InterpreterState:
        if ins.op == "2fuck.get":
            s = sys.stdin.read(1)
            if len(s):
                stat.data[stat.ptr] = ord(s)

        stat.ip += 1

        return stat


if __name__ == "__main__":
    import sys

    sys.exit(atdbf.main(TwoFuck, IntermediateExtension))

