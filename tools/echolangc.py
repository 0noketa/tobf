# EchoLang to Python Compiler (stub)
#
# limitations:
#   uses Python's tokenizer.
#   variable/label names are any of single number(excludes signs), id, string. spaces are ignored. and odd number of quotations causes any problem.
#   "listen" reads a char, strings will be pushed in left-to-right order. this compiler can be modified for exportable labels as Python funcs with mainloop(entry=0) + wrappers.
#
# EchoLang
# https://esolangs.org/wiki/EchoLang
from typing import cast, Union
import io
import tokenize


class Instruction:
    def __init__(self, src="", dst="", label: Union[str, None] = None):
        self.src = src
        self.dst = dst
        self.label = label

def count_labels(code: list[Instruction]) -> int:
    lbl = 0
    for idx2, ins in enumerate(code):
        if ins.src in ["label", "gosub", "subif"]:
            lbl += 1
    
    return lbl

def label_index_to_id(code: list[Instruction], idx: int) -> int:
    lbl = 0
    for idx2, ins in enumerate(code):
        if ins.src in ["label", "gosub", "subif"]:
            lbl += 1
    
        if idx2 == idx:
            return lbl

    return -1

def label_index(code: list[Instruction], label: str) -> int:
    for idx, ins in enumerate(code):
        if ins.src == "label" and ins.label == label:
            return idx
    
    return -1

def label_to_id(code: list[Instruction], label: str) -> int:
    idx = label_index(code, label)

    return label_index_to_id(code, idx)

def load(src: io.TextIOWrapper):
    code: list[Instruction] = []
    var_list = []
    declared_var_list = []
    label_list = []
    ids = []
    cmd = ""
    par_dpt = 0
    arg = ""
    sign = ""

    for i in tokenize.generate_tokens(src.readline):
        i = cast(tokenize.TokenInfo, i)

        if i.exact_type == tokenize.MINUS:
            sign = "-"
        elif i.exact_type == tokenize.PLUS:
            pass
        elif i.exact_type == tokenize.LPAR:
            if par_dpt != 0:
                raise Exception("syntax error LPAR")

            par_dpt += 1
        elif i.exact_type == tokenize.RPAR:
            if par_dpt != 1:
                raise Exception("syntax error RPAR")

            par_dpt -= 1

            if arg not in ids:
                ids.append(arg)

            id = ids.index(arg)

            if cmd in ["var", "get", "set"]:
                if id not in var_list:
                    var_list.append(id)

            if cmd in ["label", "goto", "goif", "gosub", "subif"]:
                # can not determin label index at here
                code.append(Instruction(cmd, "", arg))
            else:
                dst = ""
                if cmd == "get":
                    if id in declared_var_list:
                        dst = f"    echolang_stk.append(echolang_uservar_{var_list.index(id)})"
                    else:
                        dst = f"    echolang_stk.append(-1)"
                elif cmd == "set":
                    dst = f"    echolang_uservar_{var_list.index(id)} = echolang_pop()"
                elif cmd == "var":
                    declared_var_list.append(id)

                if dst != "":
                    code.append(Instruction(cmd, dst))
        else:
            if par_dpt == 1:
                arg = i.string
            elif i.type == tokenize.STRING:
                for c in i.string[1:-1]:
                    code.append(Instruction(i.string, f"    echolang_stk.append({ord(c)})"))
            elif i.type == tokenize.NUMBER:
                code.append(Instruction(i.string, f"    echolang_stk.append({sign}{i.string})"))
                sign = ""
            elif i.type != tokenize.NAME:
                pass
            else:
                dst = ""
                if i.string == "pop":
                    dst = "    echolang_pop()"
                elif i.string == "shout":
                    dst = "    echolang_out.write(str(echolang_pop()))"
                elif i.string == "say":
                    dst = "    echolang_out.write(chr(echolang_pop()))"
                elif i.string == "add":
                    dst = "    echolang_stk.append(echolang_pop() + echolang_pop())"
                elif i.string == "subtract":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(echolang_b - echolang_a)"
                elif i.string == "multiply":
                    dst = "    echolang_stk.append(echolang_pop() * echolang_pop())"
                elif i.string == "divide":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(echolang_b / echolang_a if echolang_a else -1)"
                elif i.string == "modulo":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(echolang_b % echolang_a if echolang_a else -1)"
                elif i.string == "and":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(1 if echolang_b and echolang_a else 0)"
                elif i.string == "or":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(1 if echolang_b or echolang_a else 0)"
                elif i.string == "not":
                    dst = "    echolang_stk.append(1 if echolang_pop() == 0 else 0)"
                elif i.string == "equal":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(1 if echolang_b == echolang_a else 0)"
                elif i.string == "greater":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(1 if echolang_b > echolang_a else 0)"
                elif i.string == "less":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(1 if echolang_b < echolang_a else 0)"
                elif i.string == "listen":
                    dst = "    echolang_c = echolang_in.read(1); echolang_stk.append(ord(echolang_c) if len(echolang_c) else -1)"
                elif i.string == "reverse":
                    dst = "    echolang_stk.reverse()"
                elif i.string == "swap":
                    dst = "    echolang_a = echolang_pop(); echolang_b = echolang_pop(); echolang_stk.append(echolang_a); echolang_stk.append(echolang_b)"
                elif i.string == "return":
                    dst = "    echolang_ip = echolang_cstk.pop()\n    continue"
                elif i.string == "locate":
                    dst = "    echolang_loc = echolang_pop()"
                elif i.string == "location":
                    dst = "    echolang_stk.append(echolang_loc)"
                elif i.string == "read":
                    dst = "    echolang_stk.append(echolang_tape_read(echolang_loc))"
                elif i.string == "write":
                    dst = "    echolang_tape_write(echolang_loc, echolang_pop())"
                elif i.string == "returnif":
                    dst = "    if echolang_pop():\n      echolang_ip = echolang_cstk.pop()\n      continue"
                else:
                    cmd = i.string
                    dst = ""

                if dst != "":
                    code.append(Instruction(i.string, dst))

    for idx, ins in enumerate(code):
        if ins.label is None:
            continue

        dst = ""
        if ins.src == "label":
            id = label_index_to_id(code, idx)

            if ins.label in label_list:
                raise Exception(f"label confliction {ins.label}")

            label_list.append(ins.label)

            code[idx].dst = f"    echolang_ip += 1\n  if echolang_ip == {id}:"
        elif ins.src == "goto":
            id = label_to_id(code, ins.label)
            dst = f"    echolang_ip = {id}\n    continue"
        elif ins.src == "goif":
            id = label_to_id(code, ins.label)
            dst = f"    if echolang_pop():\n      echolang_ip = {id}\n      continue"
        elif ins.src == "gosub":
            src_id = label_index_to_id(code, idx)
            dst_id = label_to_id(code, ins.label)
            dst = f"    echolang_cstk.append({src_id})\n    echolang_ip = {dst_id}\n    continue\n  if echolang_ip == {src_id}:"
        elif ins.src == "subif":
            src_id = label_index_to_id(code, idx)
            dst_id = label_to_id(code, ins.label)
            dst = (f"    if echolang_pop():\n"
                    + f"      echolang_cstk.append({src_id})\n"
                    + f"      echolang_ip = {dst_id}\n"
                    + f"      continue\n"
                    + f"    else:\n"
                    + f"      echolang_ip = {src_id}\n"
                    + f"  if echolang_ip == {src_id}:")

        if dst != "":
            code[idx].dst = dst

    result = []

    for i in range(len(var_list)):
        result.append(f"echolang_uservar_{i} = 0")
    
    result.append(f"echolang_stk = []\necholang_cstk = [{count_labels(code)}]\n"
                  + "echolang_tape = [0 for _ in range(ECHOLANG_TAPE_SIZE)]\necholang_loc = 0\necholang_ip = 0\n"
                  + "def echolang_pop():\n  return echolang_stk.pop() if len(echolang_stk) else -1\n"
                  + "def echolang_tape_read(i):\n  return echolang_tape[i] if i in range(ECHOLANG_TAPE_SIZE) else -1\n"
                  + "def echolang_tape_write(i, v):\n  if i in range(ECHOLANG_TAPE_SIZE):\n    echolang_tape[i] = v\n"
                  + f"while echolang_ip <= {count_labels(code)}:\n  if echolang_ip == 0:")
    for ins in code:
        result.append(ins.dst)
    
    result.append("    echolang_ip += 1")

    return "\n".join(result)


if __name__ == "__main__":
    import sys

    compile_only = False
    fname = ""
    src = ""

    for arg in sys.argv[1:]:
        if not arg.startswith("-"):
            fname = arg
            break

        if arg[1:] == "c":
            compile_only = True

    if fname != "":
        with io.open(fname) as f:
            src = load(f)
    else:
        src = load(sys.stdin)

    if compile_only:
        print("import sys")
        print("echolang_in = sys.stdin; echolang_out = sys.stdout; ECHOLANG_TAPE_SIZE = 0x10000")
        print(src)
    else:
        exec(src, { "echolang_in": sys.stdin, "echolang_out": sys.stdout, "ECHOLANG_TAPE_SIZE": 0x10000 })
