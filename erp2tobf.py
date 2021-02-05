
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
# putInt ( int -- )
#   print poped int
# getInt ( -- int )
#   push input int.
# . ( int -- )
#   print poped int
# , ( -- int )
#   push input int.
# ln
#   print newline
# + ( x y -- x+y )
#   add poped 2 values. and push it. 
# - ( x y -- x-y )
#   add poped 2 values. and push it. 
# if ( cond t f -- t|f )
#   pop 3 values. if first is not zero, push second. or else push third. 
from typing import Union, Tuple, List, Set
import sys
import io


class Vliw:
    """for register-based targets"""

    base_stack = ["x", "y", "z", "X", "Y", "Z"]
    instructions = ["swap", "dup", "rot", "drop", "+", "-"]

    @classmethod
    def fetch_vliw(self, src: List[str], i: int, base_stack: List[str] = None, instructions: List[str] = None) -> Vliw:
        """base_stack: readonly. layout of stack on registers.\n
           instructions: readonly. micro instructions for on-register calc.
        """
        base_stack = Vliw.base_stack if base_stack == None else base_stack
        instructions = Vliw.instructions if instructions == None else instructions
        size = len(base_stack)
        j = i
        while j < len(src) and (src[j] in instructions):
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
        """private"""
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
            if i >= len(self.stack):
                break
            if not self.result_contains_any(self.base_stack[i]) and self.stack[i] == self.base_stack[i]:
                used -= 1

        return used


# target description (tobf does not use vliw for builtin stack-jugggler)
stack_on_registers = ["x", "y", "z"]  # ["x", "y", "z", "X", "Y", "Z"]
micro_instructions = []  # ["swap", "dup", "rot", "drop", "+", "-"]
min_vliw_size = 4
max_mem_size = 256
max_rstack_size = 0x100
max_dstack_size = 0x10000


jumpless_words = [
    "swap", "dup", "rot", "drop",
    "+", "-", "*", "/", "<", "=", "<>",
    "getc", "putc", "getInt", "putInt", ",", ".", "ln",
    "inc", "dec", "pInc", "pDec", "!", "@", "!b", "@b"
]
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

    if name.startswith("="):
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
    r = set()
    for i in range(len(src) - 1):
        if src[i].startswith("'") and len(src[i]) > 1 and (src[i][1:] in vars):
            r |= set([src[i][1:]])

    return list(r)
def get_arrays(src: List[str]) -> List[str]:
    r = []
    for i in range(len(src) - 1):
        if src[i] == "ary":
            r.append(src[i + 1])

    return r
def get_array_size(src: List[str], name: str = None) -> int:
    if name == None:
        arrays = get_arrays(src)
        return sum([get_array_size(src, a) for a in arrays])

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
def get_mem_size(src: List[str]) -> int:
    pointable_vars = get_pointable_vars(src)
    
    return len(pointable_vars) + get_array_size(src)

def label(src: List[str], i: int, vars: List[str] = None, arrays: List[str] = None) -> int:
    """returns last(in src[:i + 1]) label number.\n
       label numbers include labels for calls.
    """
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
    """label number(in output) from label name(in source)
    """
    return word_info(src, name, i)[0]
def word_pos(src: List[str], name: str, i: int) -> int:
    """token index from label name
    """
    return word_info(src, name, i)[1]
def word_info(src: List[str], name: str, i: int) -> Tuple[int, int]:
    """returns (label number, index of token)
    """
    base = ""
    r = -1
    idx = -1
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
                idx = j

    return (r, idx)

def remove_local_names(src: List[str]):
    current_base = ""
    i = 0
    while i < len(src):
        tkn = src[i]

        if is_local_label(tkn):
            src[i] = current_base + tkn
        elif tkn.startswith("'") and (not (tkn.endswith("'") and len(tkn) == 3)) and is_local_label(tkn[1:]):
            src[i] = "'" + current_base + tkn[1:]
        elif tkn == ":" and i + 1 < len(src) and not is_local_label(src[i + 1]):
            current_base = src[i + 1]
            i += 1

        i += 1

def skip_anonymous_function(src: List[str], i: int) -> int:
    if src[i] != "{":
        return i

    d = 0
    for i in range(i + 1, len(src)):
        if src[i] == "}":
            if d == 0:
                return i + 1
            d -= 1
        elif src[i] == "{":
            d += 1
    
    return i

def remove_anonymous_functions(src: List[str], dst: List[List[str]], prefix: str = "erp_func_") -> List[str]:
    """dst: (out) list of function code"""
    i = 0
    while i < len(src):
        tkn = src[i]

        if tkn == "{":
            j = skip_anonymous_function(src, i)

            src2 = remove_anonymous_functions(src[i + 1:j - 1], dst, prefix)

            # merge functions
            if src2 in dst:
                f = dst.index(src2)
            else:
                f = len(dst)
                dst.append(src2)

            src[i] = f"'{prefix}{f}"

            for k in range(j - 1, i, -1):
                src.pop(k)

        i += 1

    return src


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
    last_label = 255
    rstack_size = 16
    dstack_size = 32
    anon_func_prefix = "erp_func_"

    optimize(src)

    has_main = main_exists(src)
    anon_funcs = []
    remove_local_names(src)
    src = remove_anonymous_functions(src, anon_funcs, anon_func_prefix)

    if has_main:
         anons = []
    else:
        anons = ["{"]
        src = ["}", "drop"] + src

    for i in range(len(anon_funcs)):
        anons += [":", f"{anon_func_prefix}{i}"] + anon_funcs[i] + [";"]

    src = anons + src

    optimize(src)

    vars = get_vars(src)
    pointable_vars = get_pointable_vars(src, vars)
    arrays = get_arrays(src)
    mem_size = get_mem_size(src)
    rstack_name = "rstack"
    dstack_name = "dstack"
    mem_name = "memory"
    dst = []
    lazy = []
    main_label = -1
    label_diff = 1

    if mem_size > max_mem_size or rstack_size > max_rstack_size or dstack_size > max_dstack_size:
        raise Exception("tryed to use many memory cells")

    def append_push(v, stack="d", copy=False):
        stack_name = rstack_name if stack == "r" else dstack_name

        if copy:
            dst.append(f"{stack_name}:@push {v}")
        else:
            dst.append(f"{stack_name}:@push -{v}")
        
    def append_push_imm(v, stack="d"):
        append_push(v, stack=stack, copy=True)
    def append_pop(v, stack="d"):
        stack_name = rstack_name if stack == "r" else dstack_name

        dst.append(f"{stack_name}:@pop {v}")

    def fetch_native_vliw(src: str, i: int) -> List[str]:
        vliw = []

        for i in range(i, len(src)):
            tkn = src[i]

            if tkn in ["swap", "dup", "rot", "drop", "+", "-"]:
                vliw.append(tkn)
            elif tkn == "inc":
                vliw.append("1+")
            elif tkn == "dec":
                vliw.append("1-")
            elif tkn == "getc":
                vliw.append(",")
            elif tkn == "putc":
                vliw.append(".")
            elif tkn.startswith("'") and tkn.endswith("'") and len(tkn) == 3:
                vliw.append(str(ord(tkn[1])))
            elif tkn.isdigit():
                vliw.append(tkn)
            else:
                break

        return vliw
    def append_native_vliw(vliw: List[str]):
        dst.append(f"{dstack_name}:@calc " + " ".join(vliw))

    i = 0
    while i < len(src):
        tkn = src[i]

        vliw = fetch_native_vliw(src, i)

        if len(vliw) > 1:
            append_native_vliw(vliw)

            i += len(vliw)
            continue

        if tkn in micro_instructions:
            vliw = Vliw.fetch_vliw(src, i, stack_on_registers, micro_instructions)

            if len(vliw.src) >= min_vliw_size:
                def push_vliw():
                    vliw.calc()

                    dst.append(f"""# vliw ({" ".join(vliw.src)} : -- {" ".join(vliw.stack)})""")

                    for i in list(reversed(vliw.base_stack))[:vliw.used()]:
                        append_pop(i)

                    old_cell = ""        
                    for i in range(len(vliw.base_stack) - vliw.used(), len(vliw.stack)):
                        cell = vliw.stack[i]

                        if len(cell) == 1:
                            append_push(f"{cell}", copy=True)
                            old_cell = ""
                        elif cell == old_cell:
                            append_push(f"b")
                        else:
                            dst.append(f"copy {cell[0]} b")
                            i = 1
                            while i < len(cell):
                                o = { "+": "add", "-": "sub" }[cell[i]]
                                v = cell[i + 1]
                                dst.append(f"copy{o} {v} b")

                                i += 2
                            append_push(f"b")
                            old_cell = cell

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
            dst.append(f"# : {src[i + 1]}")
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
            dst.append(f"ifelse x e")
            append_push("y")
            dst.append(f"else x e")
            append_push("z")
            dst.append(f"endifelse x e")
        elif tkn == "drop":
            dst.append(f"{dstack_name}:@pop")
        elif tkn in ["dup", "swap", "rot"]:
            dst.append(f"{dstack_name}:@{tkn}")
        elif tkn == "getc":
            dst.append(f"{dstack_name}:@push input")
        elif tkn == "putc":
            dst.append(f"{dstack_name}:@pop print")
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
            dst.append(f"{dstack_name}:@{tkn}")
        elif tkn in ["+", "-"]:
            o = {"+": "add", "-": "sub"}[tkn]
            dst.append(f"{dstack_name}:@{o}")
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
            dst.append(f"clear z")
            dst.append(f"while x")
            dst.append(f"copyadd y z")
            dst.append(f"dec x")
            dst.append(f"endwhile x")
            append_push("z")
        elif tkn.startswith("=") and (tkn[1:] in vars):
            append_pop(f"x")
 
            if tkn[1:] in pointable_vars:
                dst.append(f"{mem_name}:@w_move x {pointable_vars.index(tkn[1:])}")
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
                v = word_label(src, tkn[1:], i)

                if i + 1 < len(src) and src[i + 1] == "jmp":
                    dst.append(f"erp:@goto set {v}")
                    dst.append(f"erp:@at {label(src, i + 1)}")
                    i += 1
                else:
                    append_push_imm(f"{v}")
        elif tkn.startswith("@"):
            append_pop("x")
            dst.append(f"{mem_name}:@r_copy x y")
            append_push("y")
        elif tkn.startswith("!"):
            append_pop("y")
            append_pop("x")
            dst.append(f"{mem_name}:@w_move x y")
        elif tkn.isdigit():
            append_push_imm(tkn)
        elif tkn in pointable_vars:
            dst.append(f"{mem_name}:@r_copy {pointable_vars.index(tkn)} x")
            append_push(f"x")
        elif tkn in vars:
            append_push(f"_{tkn}", copy=True)
        else:
            append_push_imm(label(src, i), "r")
            dst.append(f"erp:@goto set {word_label(src, tkn, i)}")
            dst.append(f"erp:@at {label(src, i)}")

        i += 1

    dst.append(f"erp:@end {last_label}")

    head = [
        " ".join([f"_{v}" for v in vars]) + " " + " ".join(stack_on_registers) + " b e tmp0 tmp1",
        "tmp tmp0 tmp1",
        "loadas out code mod_print",
        "loadas in code mod_input",
        "loadas erp code mod_jump"
    ]

    mem_loaders = [
        (rstack_size, f"loadas {rstack_name} stk {rstack_size}"),
        (dstack_size, f"loadas {dstack_name} stk {dstack_size}")
    ]

    if mem_size > 0:
        if mem_size > 8:
            mem_loaders.append((mem_size, f"loadas {mem_name} mem {mem_size}"))
        else:
            mem_loaders.append((mem_size, f"loadas {mem_name} fastmem {mem_size}"))

    mem_loaders.sort(key=(lambda x: x[0]))
    head.extend([ldr[1] for ldr in mem_loaders])

    if len(pointable_vars) > 0:
        for i in range(len(pointable_vars)):
            head.append(f"{mem_name}:@w_move _{pointable_vars[i]} {i}")
            dst.append(f"{mem_name}:@r_move {i} _{pointable_vars[i]}")

    head.append("erp:@begin 0")

    if main_label != -1:
        head.extend([
            f"{rstack_name}:@push {last_label}",        
            f"erp:@goto set {main_label}"
        ])


    dst = head + dst

    dst.append("end")

    return dst

def main_exists(src: List[str]) -> bool:
    for i in range(len(src) - 1):
        if src[i] == ":" and src[i + 1] == "main":
            return True

    return False

def optimize(src: List[str], repeat: int = None):
    # can spread inline functions
    if repeat != None:
        for _ in range(repeat):
            optimize(src)

        return

    i = 0
    while i < len(src):
        src[i] = src[i]

        if src[i] == "1" and i + 1 < len(src):
            if src[i + 1] == "+":
                src[i]  = "inc"
                src.pop(i + 1)
            elif src[i + 1] == "-":
                src[i]  = "dec"
                src.pop(i + 1)
        elif src[i].startswith("'") and src[i].endswith("'") and len(src[i]) == 3:
            src[i] = str(ord(src[i][1]))
        elif is_call(src, src[i], i):
            j = word_pos(src, src[i], i) + 2
            k = j
            while k < len(src):
                if src[k] not in jumpless_words:
                    break

                k += 1

            # this label can be inline
            if src[k] == ";":
                src.pop(i)

                for tkn in src[k - 1:j - 1:-1]:
                    src.insert(i, tkn)

                continue
        
        if is_call(src, src[i], i) and i + 1 < len(src) and src[i + 1] == ";":
            src[i] = "'" + src[i]
            src[i + 1] = "jmp"
        elif src[i] == "call" and i + 1 < len(src) and src[i + 1] == ";":
            src[i] = "jmp"

        if src[i] in ["jmp", ";"] and i + 1 < len(src) and src[i + 1] == ";":
            j = i + 1
            while j < len(src) and src[j] == ";":
                src.pop(j)

        i += 1

if __name__ == "__main__":
    src = load(sys.stdin, [])
    code = compile(src)

    for i in code:
        print(i)
