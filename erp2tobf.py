
from __future__ import annotations
# my old rpn language to tobf+mod_jump compiler (slow and large)
# label_name ( ? -- ? )
#   call
# var_name ( -- val )
#   push value
# 'var_name ( -- addr )
#   push address
# 'array_name ( -- addr )
#   push address
# =var_name ( val -- )
#   set poped value
# @ ( addr -- val )
#   push value placed at poped address
# ! ( val addr -- )
#   pop 2 values. place first at second
# var var_name
#   define variable
# ary array_name size
#   define array
# : label_name
#   define label
# ;
#   return
# { ( -- addr )
#   push address of anonymous label. and skip until }
# }
#   return
# jmp
#   jump to poped address
# call
#   call poped address
# putc ( char -- )
#   print poped char
# getc ( -- char )
#   push input char
# ln
#   print newline
# + ( x y -- x+y )
#   add poped 2 values. and push it. 
# if ( cond t f -- t|f )
#   pop 3 values. if first is not zero, push second. or else push third. 
from typing import Union, List, Set
import sys
import io


class Vliw:
    base_stack = registers.copy()

    @classmethod
    def fetch_vliw(self, src: List[str], i: int, base_stack: List[str] = None) -> Vliw:
        base_stack = Vliw.base_stack if base_stack == None else base_stack
        size = len(base_stack)
        j = i
        while j < len(src):
            if src[j] in ["swap", "rot"]:
                j += 1
                continue

            if src[j] == "drop":
                if size == 0:
                    break
                size -= 1
                j += 1
                continue

            if src[j] == "dup":
                if size == 0:
                    break
                size += 1
                j += 1
                continue

            if src[j] in ["+", "-"]:
                if size < 2:
                    break
                size -= 1
                j += 1
                continue

            break

        return Vliw(src[i:j], base_stack)

    def __init__(self, src: List[str], base_stack: List[str] = None) -> None:
        """"base_stack: readonly. layout of stack on registers."""
        self.src = src
        self.base_stack = Vliw.base_stack if base_stack == None else base_stack
        self.stack: List[str] = None

    def calc(self) -> int:
        self.stack = self.base_stack.copy()

        for i in self.src:
            if i == "swap":
                y = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(y)
                self.stack.append(x)
            elif i == "rot":
                z = self.stack.pop()
                y = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(y)
                self.stack.append(z)
                self.stack.append(x)
            elif i == "dup":
                x = self.stack.pop()
                self.stack.append(x)
                self.stack.append(x)
            elif i == "drop":
                self.stack.pop()
            elif i in ["+", "-"]:
                y = self.stack.pop()
                x = self.stack.pop()
                if i == "-":
                    y = y.replace("+", "*")
                    y = y.replace("-", "+")
                    y = y.replace("*", "-")
                self.stack.append(x + i + y)

    def result_contains_any(self, v) -> bool:
        for i in range(len(self.stack)):
            if i < len(self.base_stack) and self.base_stack[i] == v:
                continue
            if v in self.stack[i]:
                return True
        return False

    def used(self) -> int:
        if self.stack == None:
            self.calc()

        used = len(self.base_stack)
        for i in range(len(self.base_stack)):
            if not self.result_contains_any(self.base_stack[i]) and self.stack[i] == self.base_stack[i]:
                used -= 1

        return used


stack_on_registers = ["x", "y", "z", "X", "Y", "Z"]

builtin_words = [
    ":", "{", "}", ";",
    "jmp", "call", "if",
    "swap", "dup", "rot", "drop",
    "+", "-", "*", "/", "<", "=", "<>",
    "getc", "putc", "getInt", "putInt", ",", ".", "ln",
    "inc", "dec", "pInc", "pDec", "!", "@", "!b", "@b"
]

def is_local_label(name: str) -> bool:
    return len(name) > 1 and name.startswith(".")

def is_call(src: List[str], name: str, i: int, vars: List[str] = None, arrays: List[str] = None) -> bool:
    vars = get_vars(src) if vars == None else vars
    arrays = get_arrays(src) if arrays == None else arrays

    if name.startswith("'"):
        return False

    if name in vars:
        return False

    if name in arrays:
        return False

    if name.isdigit():
        return False

    if i > 0 and src[i - 1] == ":":
        return False

    if name == "call":
        return True

    if name in builtin_words:
        return False

    return True

def get_vars(src: List[str]) -> List[str]:
    r = []
    for i in range(len(src) - 1):
        if src[i] == "var":
            r.append(src[i + 1])

    return r
def get_pointable_vars(src: List[str], vars: List[str] = None) -> List[str]:
    vars = get_vars(src) if vars == None else vars
    r = []
    for i in range(len(src) - 1):
        if src[i].startswith("'") and len(src[i]) > 1 and (src[i][1:] in vars):
            r.append(src[i][1:])

    return r
def get_arrays(src: List[str]) -> List[str]:
    r = []
    for i in range(len(src) - 1):
        if src[i] == "ary":
            r.append(src[i + 1])

    return r
def get_array_size(src: List[str], name: str) -> int:
    for i in range(len(src) - 2):
        if src[i] == "ary" and src[i + 1] == name:
            return int(src[i + 2])

    return -1
def get_array_pos(src: List[str], name: str) -> int:
    arrays = get_arrays(src)

    if name in arrays:
        i = arrays.index(name)
        return sum([get_array_size(src, a) for a in arrays[:i]])
    else:
        return -1

def label(src: List[str], i: int, vars: List[str] = None, arrays: List[str] = None) -> int:
    r = 1
    vars = get_vars(src) if vars == None else vars
    arrays = get_arrays(src) if arrays == None else arrays
    for i in range(i):
        if src[i] in [":", "{", "}", ";", "jmp"]:
            r += 1
        elif is_call(src, src[i], i, vars, arrays):
            r += 1

    return r
def word_label(src: List[str], name: str, i: int) -> int:
    base = ""
    r = -1
    vars = get_vars(src)
    arrays = get_arrays(src)

    for j in range(len(src)):
        if src[j] == ":":
            it = src[j + 1]

            if not is_local_label(it):
                base = it
                it = ""

                if is_local_label(name) and i < j:
                    break

            if name == base + it or name == it:
                r = label(src, j, vars, arrays)

    return r


def load(file: io.TextIOWrapper, loaded: List[str] = []) -> List[str]:
    s = file.read()

    src = list(filter(len, s.split()))

    i = 0
    while i < len(src):
        if src[i] == "import":
            j = i + 1
            if not (src[j] in loaded):
                with io.open(src[j] + ".erp") as f:
                    src2 = load(f, loaded)
            else:
                src2 = []

            src = src[:i] + src2 + src[i + 2:]
        else:
            i += 1

    return src

def compile(src: List[str]):
    vars = get_vars(src)
    pointable_vars = get_pointable_vars(src, vars)
    arrays = get_arrays(src)
    dst = []
    lazy = []
    main_label = -1
    mem_size = 64

    def append_push(v, stack="d", immediate=False, copy=False):
        pfx = stack
        if immediate:
            dst.append(f"stack:@set {v} {pfx}sp")
        else:
            if copy:
                dst.append(f"stack:@w_copy {v} {pfx}sp")
            else:
                dst.append(f"stack:@w_move {v} {pfx}sp")
        
        if stack == "r":
            dst.append(f"dec rsp")
        else:
            dst.append(f"inc dsp")
    def append_push_imm(v, stack="d"):
        append_push(v, stack, True)
    def append_pop(v, stack="d"):
        pfx = stack
        if stack == "r":
            dst.append(f"inc rsp")
        else:
            dst.append(f"dec dsp")
        dst.append(f"stack:@r_move {pfx}sp {v}")

    i = 0
    while i < len(src):
        tkn = src[i]

        if (tkn in ["swap", "dup", "rot"]):
            vliw = Vliw.fetch_vliw(src, i, stack_on_registers)

            if len(vliw.src) > 1:
                def push_vliw():
                    vliw.calc()

                    dst.append(f"""# vliw ({" ".join(vliw.src)} : -- {" ".join(vliw.stack)})""")

                    for i in list(reversed(vliw.base_stack))[:vliw.used()]:
                        append_pop(i)
        
                    for i in range(len(vliw.base_stack) - vliw.used(), len(vliw.stack)):
                        cell = vliw.stack[i]

                        if len(cell) == 1:
                            append_push(f"{cell}", copy=True)
                        else:
                            dst.append(f"copy {cell[0]} b")
                            i = 1
                            while i < len(cell):
                                o = { "+": "add", "-": "sub" }[cell[i]]
                                v = cell[i + 1]
                                dst.append(f"copy{o} {v} b")

                                i += 2
                            append_push(f"b")

                    dst.append(f"# end vliw")

                push_vliw()
                i += len(vliw.src)
                continue

        if tkn == "{":
            append_push_imm(label(src, i))
            lazy.append(len(dst))
            dst.append("erp:@goto set __dummy__")
            dst.append(f"erp:@at {label(src, i)}")
        elif tkn == "}":
            dst[lazy.pop()] = f"erp:@goto set {label(src, i)}"
            append_pop("x", "r")
            dst.append(f"erp:@goto move x")
            dst.append(f"erp:@at {label(src, i)}")
        elif tkn == ":":
            dst.append(f"erp:@at {label(src, i)}")
            if src[i + 1] == "main":
                main_label = label(src, i)
            i += 1
        elif tkn == "var":
            i += 1
        elif tkn == "ary":
            i += 2
        elif tkn == ";":
            append_pop("x", "r")
            dst.append(f"erp:@goto move x")
            dst.append(f"erp:@at {label(src, i)}")
        elif tkn == "jmp":
            append_pop("x")
            dst.append(f"erp:@goto move x")
            dst.append(f"erp:@at {label(src, i)}")
        elif tkn == "if":
            append_pop("z")
            append_pop("y")
            append_pop("x")
            dst.append(f"copy x b")
            dst.append(f"ifelse b e")
            append_push("y")
            dst.append(f"else b e")
            append_push("z")
            dst.append(f"endifelse b e")
        elif tkn == "drop":
            append_pop("x")
        elif tkn == "dup":
            append_pop("x")
            append_push("x", copy=True)
            append_push("x")
        elif tkn == "swap":
            append_pop("x")
            append_pop("y")
            append_push("x")
            append_push("y")
        elif tkn == "rot":
            # 1 2 3 -- 2 3 1
            append_pop("z")
            append_pop("y")
            append_pop("x")
            append_push("y")
            append_push("z")
            append_push("x")
        elif tkn == "getc":
            dst.append(f"input x")
            append_push("x")
        elif tkn == "putc":
            append_pop("x")
            dst.append(f"print x")
        elif tkn in ["getInt", ","]:
            dst.append(f"in:readlnint x")
            append_push("x")
        elif tkn in ["putInt", "."]:
            append_pop("x")
            dst.append(f"out:writeint x")
        elif tkn == "ln":
            dst.append(f"set 10 x")
            dst.append(f"print x")
        elif tkn == "call":
            append_pop("x")
            append_push_imm(label(src, i), "r")
            dst.append(f"erp:@goto move x")
            dst.append(f"erp:@at {label(src, i)}")
        elif tkn in ["inc", "dec", "pInc", "pDec"]:
            # sizeof(uintptr_t) == 1
            if tkn[0] == "p":
                tkn = tkn[1:].lower()
            append_pop("x")
            dst.append(f"{tkn} x")
            append_push("x")
        elif tkn in ["+", "-"]:
            o = {"+": "add", "-": "sub"}[tkn]
            append_pop("y")
            dst.append(f"dec dsp")
            dst.append(f"stack:@w_move{o} y dsp")
            dst.append(f"inc dsp")
        elif tkn in [">", "<"]:
            if tkn == ">":
                append_pop("y")
                append_pop("x")
            else:
                append_pop("x")
                append_pop("y")
            dst.append(f"clear z")
            dst.append(f"ifgt x y e")
            dst.append(f"inc z")
            dst.append(f"endifgt x y e")
            append_push("z")
        elif tkn in ["<>", "="]:
            append_pop("y")
            append_pop("x")
            dst.append(f"movesub y x")
            dst.append({"<>": "clear z", "=": "set 1 z"}[tkn])
            dst.append(f"if x")
            dst.append({"<>": "inc z", "=": "dec z"}[tkn])
            dst.append(f"endif x")
            append_push("z")
        elif tkn == "*":
            append_pop("y")
            append_pop("x")
            dst.append(f"copy x b")
            dst.append(f"clear z")
            dst.append(f"while b")
            dst.append(f"copyadd y z")
            dst.append(f"dec b")
            dst.append(f"endwhile b")
            append_push("z")
        elif tkn.startswith("=") and (tkn[1:] in vars):
            append_pop(f"x")
 
            if tkn[1:] in pointable_vars:
                dst.append(f"stack:@w_move x {pointable_vars.index(tkn[1:])}")
            else:
                dst.append(f"move x _{tkn[1:]}")
        elif tkn.startswith("'") and tkn.endswith("'") and len(tkn) == 3:
            append_push_imm(ord(tkn[1]))
        elif tkn.startswith("'"):
            if tkn[1:] in arrays:
                append_push_imm(f"{len(pointable_vars) + get_array_pos(src, tkn[1:])}")
            elif tkn[1:] in pointable_vars:
                append_push_imm(f"{pointable_vars.index(tkn[1:])}")
            else:
                append_push_imm(f"{word_label(src, tkn[1:], i)}")
        elif tkn.startswith("@"):
            append_pop("x")
            dst.append(f"stack:@r_copy x y")
            append_push("y")
        elif tkn.startswith("!"):
            append_pop("y")
            append_pop("x")
            dst.append(f"stack:@w_move x y")
        elif tkn.isdigit():
            append_push_imm(tkn)
        elif tkn in pointable_vars:
            dst.append(f"stack:@r_copy {pointable_vars.index(tkn)} x")
            append_push(f"x")
        elif tkn in vars:
            append_push(f"_{tkn}", copy=True)
        else:
            append_push_imm(label(src, i), "r")
            dst.append(f"erp:@goto set {word_label(src, tkn, i)}")
            dst.append(f"erp:@at {label(src, i)}")

        i += 1

    dst.append("erp:@end 255")

    head = [
        " ".join([f"_{v}" for v in vars]) + " " + " ".join(stack_on_registers) + " b e rsp dsp",
        "loadas out code mod_print",
        "loadas in code mod_input",
        "loadas erp code mod_jump",
        f"loadas stack mem {mem_size}",
        f"set {mem_size - 1} rsp"
    ]

    if len(pointable_vars) or len(arrays):
        for i in range(len(pointable_vars)):
            head.append(f"stack:@w_move _{pointable_vars[i]} {i}")
            dst.append(f"stack:@r_move {i} _{pointable_vars[i]}")

        dsp = len(pointable_vars)

        if len(arrays):
            dsp += get_array_pos(src, arrays[-1]) + get_array_size(src, arrays[-1])

        head.append(f"set {dsp} dsp")

    head.append("erp:@begin 0")

    if main_label != -1:
        head.extend([
            f"stack:@set 255 rsp",        
            f"dec rsp",
            f"erp:@goto set {main_label}"
        ])


    dst = head + dst

    dst.append("end")

    return dst

def optimize(src: List[str]):
    i = 0
    while i < len(src):
        if i + 1 < len(src):
            if src[i] == "swap" and  src[i + 1] == "swap":
                src.pop(i)
                src.pop(i)

        if src[i] == "drop":
            if src[i - 1].isdigit():
                i -= 1
                src.pop(i)
                src.pop(i)
                
                continue

        i += 1

if __name__ == "__main__":
    src = load(sys.stdin, [])
    # optimize(src)
    code = compile(src)

    for i in code:
        print(i)

