
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
# jz ( cond addr -- )
#   jump if cond is zero
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
# import module_name
#   include source file (just once)
# include module_name
#   include source file
# ( ... )
#   comment
from typing import Union, Tuple, List, Set
import sys
import os
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

        by_arity: List[List[str]] = [
            [],
            ["dup", "drop"],
            ["swap", "over", "2dup", "2drop", "+", "-"],
            ["rot"],
            ["2swap", "2over"],
            [],
            ["2rot"]
        ]

        j = i
        while j < len(src) and (src[j] in instructions):
            matched = False

            for k, oprs in enumerate(by_arity):
                if src[j] in oprs:
                    if size >= k:
                        matched = True
                    
                    break

            if matched:
                j += 1
                continue

            break

        return Vliw(src[i:j], base_stack)

    def __init__(self, src: List[str], base_stack: List[str] = None) -> None:
        """private"""
        self.src = src
        self.base_stack = Vliw.base_stack if base_stack == None else base_stack
        self.stack: List[str] = None
        self.uses_tuple_jugglers = False

        self.calc()

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
            elif i == "over":
                y = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(x)
                self.stack.append(y)
                self.stack.append(x)
            elif i == "2dup":
                self.uses_tuple_jugglers = True
                x2 = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(x)
                self.stack.append(x2)
                self.stack.append(x)
                self.stack.append(x2)
            elif i == "2swap":
                self.uses_tuple_jugglers = True
                y2 = self.stack.pop()
                y = self.stack.pop()
                x2 = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(y)
                self.stack.append(y2)
                self.stack.append(x)
                self.stack.append(x2)            
            elif i == "2rot":
                self.uses_tuple_jugglers = True
                z2 = self.stack.pop()
                z = self.stack.pop()
                y2 = self.stack.pop()
                y = self.stack.pop()
                x2 = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(y)
                self.stack.append(y2)
                self.stack.append(z)
                self.stack.append(z2)
                self.stack.append(x)
                self.stack.append(x2)            
            elif i == "2over":
                self.uses_tuple_jugglers = True
                y2 = self.stack.pop()
                y = self.stack.pop()
                x2 = self.stack.pop()
                x = self.stack.pop()
                self.stack.append(x)
                self.stack.append(x2)
                self.stack.append(y)
                self.stack.append(y2)
                self.stack.append(x)
                self.stack.append(x2)            
            elif i == "drop":
                self.stack.pop()
            elif i == "2drop":
                self.stack.pop()
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
        """used sources"""
        if self.stack == None:
            self.calc()

        used = len(self.base_stack)
        for i in range(len(self.base_stack)):
            if i >= len(self.stack):
                break
            if not self.result_contains_any(self.base_stack[i]) and self.stack[i] == self.base_stack[i]:
                used -= 1

        return used


# target description
stack_on_registers = []  # ["x", "y", "z", "X", "Y", "Z"]
named_cells_for_vliw = list(map(str, range(8)))  # ["x", "y", "z", "X", "Y", "Z"]
micro_instructions = ["swap", "dup", "rot", "over", "2swap", "2dup", "2rot", "2over", "drop"]  # ["swap", "dup", "rot", "over", "drop", "+", "-"]
min_vliw_size = 2
max_mem_size = 256
max_rstack_size = 0x100
max_dstack_size = 0x10000


jumpless_words = [
    "swap", "dup", "rot", "over", "drop",
    "2swap", "2dup", "2rot", "2over", "2drop",
    "+", "-", "*", "/", "mod", "<", ">", ">=", "<=", "=", "<>",
    "getc", "putc", "getInt", "putInt", ",", ".", "ln",
    "inc", "dec", "pInc", "pDec", "!", "@", "!b", "@b"
]
builtin_words = [
    ":", "{", "}", ";",
    "jmp", "jz", "jnz", "call", "if",
    "swap", "dup", "rot", "over", "drop",
    "2swap", "2dup", "2rot", "2over", "2drop",
    "+", "-", "*", "/", "mod", "<", ">", ">=", "<=", "=", "<>",
    "getc", "putc", "getInt", "putInt", ",", ".", "ln",
    "inc", "dec", "pInc", "pDec", "!", "@", "!b", "@b"
]

def is_local_label(name: str) -> bool:
    return len(name) > 1 and name.startswith(".")

def is_call(src: List[str], name: str, i: int, vars: List[str] = None, arrays: List[str] = None) -> bool:
    vars = get_vars(src) if vars == None else vars
    arrays = get_arrays(src) if arrays == None else arrays

    if name in ["var", "ary"]:
        return False

    if name.startswith("'") or  name.startswith('"'):
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

def is_str(tkn: str) -> bool:
    return len(tkn) >= 2 and tkn.startswith('"') and tkn.endswith('"')
def get_strs(src: List[str]) -> List[str]:
    return list(sorted(set([s[1:-1] for s in src if is_str(s)])))
def get_strs_size(src: List[str]) -> int:
    ss = get_strs(src)
    return sum(map(len, ss)) + len(ss)
def get_strs_base(src: List[str]) -> int:
    return len(get_pointable_vars(src)) + get_array_size(src)
def get_str_pos(src: List[str], idx: int) -> int:
    ss = get_strs(src)
    tkn = src[idx][1:-1]

    if tkn not in ss:
        return -1

    i = ss.index(tkn)

    return get_strs_base(src) + sum(map(len, ss[:i])) + i

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
    
    return len(pointable_vars) + get_array_size(src) + get_strs_size(src)

def label(src: List[str], i: int, vars: List[str] = None, arrays: List[str] = None) -> int:
    """returns last(in src[:i + 1]) label number.\n
       label numbers include labels for calls.
    """
    r = 0
    vars = get_vars(src) if vars == None else vars
    arrays = get_arrays(src) if arrays == None else arrays
    for i in range(i):
        if src[i] in [":", "{", "}"]:
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

def replace_alias(s):
    tbl = {
        "eq": "=",
        "neq": "<>",
    }

    return tbl[s] if s in tbl else s

def tokens(src: str):
    src = src.strip()
    while len(src):
        if src[0] == '"':
            if '"' in src[1:]:
                i = src.index('"', 1) + 1
            else:
                i = len(src)

            yield src[:i]

            src = src[i:].strip()
        else:
            ss = src.split(maxsplit=1)

            yield ss[0].strip()

            src = ss[1].strip() if len(ss) > 1 else ""

def load(file: io.TextIOWrapper, loaded: List[str] = [], inc_dir: List[str] = []) -> List[str]:
    s = file.read()
    inc_dir = inc_dir + ["."]

    src = list(map(replace_alias, tokens(s)))

    # comment
    i = 0
    while "(" in src:
        i = src.index("(")
        if ")" in src[i + 1:]:
            j = src.index(")", i + 1)
        else:
            j = len(src)

        src = src[:i] + src[j + 1:]

    i = 0
    while i < len(src):
        if src[i] in ["import", "include"]:
            j = i + 1
            if not (src[j] in loaded) or src[i] == "include":
                if src[i] == "import":
                    loaded.append(src[j])

                d = ""
                f = src[i + 1] + ".erp"
                for d2 in reversed(inc_dir):
                    f2 = os.path.join(d2, f)

                    if os.path.isfile(f2):
                        d = d2
                        f = f2

                        break

                if d == "":
                    raise Exception(f"can not open {f}")

                with io.open(f) as f:
                    src2 = load(f, loaded, inc_dir)
            else:
                src2 = []

            src = src[:i] + src2 + src[i + 2:]
        else:
            i += 1

    return src

def compile(src: List[str], rstack_size=8, dstack_size=64, bf16=False, anon_func_prefix="erp_func_"):
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
    strs = get_strs(src)
    arrays = get_arrays(src)
    mem_size = get_mem_size(src)
    rstack_name = "rstack"
    dstack_name = "dstack"
    mem_name = "memory"
    dst = []
    lazy = []
    main_label = -1
    last_label = label(src, len(src), vars, arrays)
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

            if tkn in ["swap", "dup", "rot", "over", "2swap", "2dup", "2rot", "2over", "drop", "+", "-"]:
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

        if tkn in micro_instructions:
            vliw = Vliw.fetch_vliw(src, i, named_cells_for_vliw, micro_instructions)

            if len(vliw.src) >= min_vliw_size or vliw.uses_tuple_jugglers:
                def push_vliw():
                    used = vliw.used() + 1

                    # rename register 
                    base = len(named_cells_for_vliw) - used
                    stack_layout = " ".join([str(int(vliw_dst) - base) for vliw_dst in vliw.stack[base:]])

                    dst.append(f"{dstack_name}:@juggle {used} {stack_layout}")

                push_vliw()
                i += len(vliw.src)
                continue

        vliw = fetch_native_vliw(src, i)

        if len(vliw) > 1:
            append_native_vliw(vliw)

            i += len(vliw)
            continue

        if tkn == "{":
            append_push_imm(label(src, i))
            lazy.append(len(dst))
            dst.append("erp:@goto set __dummy__")
            dst.append(f"erp:@at {label(src, i)}")
        elif tkn == "}":
            dst[lazy.pop()] = f"erp:@goto set {label(src, i)}"
            dst.append(f"erp:@goto {rstack_name}:@pop_as_set 0")
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
            dst.append(f"erp:@goto {rstack_name}:@pop_as_set 0")
        elif tkn == "jmp":
            dst.append(f"erp:@goto {dstack_name}:@pop_as_set 0")
        elif tkn == "jz":
            append_pop("x")
            append_pop("y")
            dst.append(f"erp:@goto_ifn y move x")
        elif tkn == "jnz":
            append_pop("x")
            append_pop("y")
            dst.append(f"erp:@goto_if y move x")
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
        elif tkn == "2drop":
            dst.append(f"{dstack_name}:@calc drop drop")
        elif tkn in ["dup", "swap", "rot", "over"]:
            dst.append(f"{dstack_name}:@{tkn}")
        elif (tkn[1:] in ["dup", "swap", "rot", "over"]) and tkn[0].isdigit() and (int(tkn[0]) in range(3)):
            dst.append(f"{dstack_name}:@calc {tkn}")
        elif tkn == "getc":
            dst.append(f"{dstack_name}:@push input")
        elif tkn == "putc":
            dst.append(f"{dstack_name}:@pop print")
        elif tkn in ["getInt", ","]:
            dst.append(f"unload out")
            dst.append("loadas in code mod_input")
            dst.append(f"in:readlnint x")
            dst.append(f"unload in")
            dst.append("loadas out code mod_print")
            append_push("x")
        elif tkn in ["putInt", "."]:
            append_pop("x")
            dst.append(f"out:writeint x")
        elif tkn == "ln":
            dst.append(f"set 10 x")
            dst.append(f"print x")
        elif tkn == "call":
            append_push_imm(label(src, i), "r")
            dst.append(f"erp:@goto {dstack_name}:@pop_as_set 0")
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
            dst.append(f"clear y")
            append_push("z")
        elif tkn == "/":
            append_pop("y")
            append_pop("x")
            dst.append(f"clear z")
            dst.append(f"if y")
            dst.append(f"while x")
            dst.append(f"  copy y e")
            dst.append(f"  while e")
            dst.append(f"    copy x b")
            dst.append(f"    if b")
            dst.append(f"      dec x")
            dst.append(f"    endif b")
            dst.append(f"    dec e")
            dst.append(f"  endwhile e")
            dst.append(f"  inc z")
            dst.append(f"endwhile x")
            dst.append(f"endif y")
            dst.append(f"clear x")
            append_push("z")
        elif tkn == "mod":
            append_pop("y")
            append_pop("x")
            dst.append(f"tmp -tmp0")
            dst.append(f"if y")
            dst.append(f"while x")
            dst.append(f"  copy y e")
            dst.append(f"  while e")
            dst.append(f"    copy x b")
            dst.append(f"    ifelse b z")
            dst.append(f"      dec x e")
            dst.append(f"    else b z")
            dst.append(f"      moveadd y tmp0")
            dst.append(f"      movesub e tmp0")
            dst.append(f"      clear y x e")
            dst.append(f"    endifelse b z")
            dst.append(f"  endwhile e")
            dst.append(f"endwhile x")
            dst.append(f"endif y")
            dst.append(f"clear x")
            append_push("tmp0")
            dst.append(f"tmp tmp0")
        elif tkn.startswith("=") and (tkn[1:] in vars):
 
            if tkn[1:] in pointable_vars:
                append_pop(f"x")
                dst.append(f"{mem_name}:@w_move x {pointable_vars.index(tkn[1:])}")
            else:
                append_pop(f"_{tkn[1:]}")
        elif tkn.startswith('"'):
            append_push_imm(get_str_pos(src, i))
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
                    if v == -1:
                        sys.stderr.write(f"error:n")
                        sys.stderr.write(f"tkn{i}: {tkn}\n")
                        sys.stderr.write(f"next:{label(src, i + 1)}:n")
                    dst.append(f"erp:@goto set {v}")
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

    dst.append("erp:@end")

    head = [
        " ".join([f"_{v}" for v in vars]) + " x y z b e tmp0 tmp1",
        "tmp tmp0 tmp1",
        "loadas out code mod_print",
        # "loadas in code mod_input",
        "loadas erp code mod_jump2"
    ]

    mem_loaders = [
        (rstack_size, f"loadas {rstack_name} stk {rstack_size}"),
        # does not use @calc version of 2dup 2swap..., everything in @juggle
        (dstack_size, f"loadas {dstack_name} stk {dstack_size}")
    ]

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

    if len(strs) > 0:
        p = get_strs_base(src)
        for s in strs:
            for c in s:
                head.append(f"{mem_name}:@set {ord(c)} {p}")
                p += 1
            p += 1


    head.append(f"erp:@begin {last_label + 1}")

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
        
        if src[i] == "call" and i + 1 < len(src) and src[i + 1] == ";":
            src[i] = "jmp"
        elif is_call(src, src[i], i) and i + 1 < len(src) and src[i + 1] == ";":
            src[i] = "'" + src[i]
            src[i + 1] = "jmp"

        if src[i] in ["jmp", ";"] and i + 1 < len(src) and src[i + 1] == ";":
            j = i + 1
            while j < len(src) and src[j] == ";":
                src.pop(j)

        i += 1

def optimize_tobf(code: List[str]):
    def parse_push(s: str):
        if s.find(" ") == -1:
            qo0 = s
            p0 = ""
        else:
            qo0, p0 = s.split(" ", 1)

        qo0_s = qo0.split(":")

        if len(qo0_s) > 1:
            return ":".join(qo0_s[:-1]), qo0_s[-1], p0
        else:
            return "", qo0_s[0], p0
    def isvar(x):
        builtins = ["swap", "dup", "rot", "over", "putc", "getc", "input", "print"]
    
        return x.isidentifier() and (x not in builtins)

    def isval(x):
        return x.isdigit() or isvar(x)

    while True:
        optimized = False

        for i in range(len(code) - 1):
            m0, o0, p0 = parse_push(code[i])
            m1, o1, p1 = parse_push(code[i + 1])

            if m0 == m1 and o0 == "@push" and o1 == "@pop" and p0 == "input" and isvar(p1):
                code[i] = f"# input"
                code[i + 1] = f"input {p1}"

                optimized = True

                break

        for i in range(len(code) - 1):
            m0, o0, p0 = parse_push(code[i])
            m1, o1, p1 = parse_push(code[i + 1])

            if m0 == m1 and o0 == "@push" and o1 == "@pop" and isvar(p0) and p1 == "print":
                code[i] = f"# print"
                code[i + 1] = f"print {p0}"

                optimized = True

                break

        for i in range(len(code) - 1):
            m0, o0, p0 = parse_push(code[i])
            m1, o1, p1 = parse_push(code[i + 1])

            if m0 == m1 and o0 == "@push" and o1 == "@pop" and isval(p0) and isvar(p1):
                code[i] = f"# push and pop"
                code[i + 1] = f"set {p0} {p1}" if p0.isdigit() else f"copy {p0} {p1}"

                optimized = True

                break

        for i in range(len(code) - 2):
            m0, o0, p0 = parse_push(code[i])
            m1, o1, p1 = parse_push(code[i + 1])
            m2, o2, p2 = parse_push(code[i + 2])

            if (len(set([m0, m1, m2])) == 1
                    and o0 == "@push" and o2 == "@pop"
                    and isvar(p0) and p0 == p2
                    and o1 in ["@inc", "@dec"]):
                code[i] = f"# push and {o1} and pop"
                code[i + 1] = f"{o1[1:]} {p0}"

                code.pop(i + 2)

                optimized = True

                break

        # flatten
        # dstack:@push _x
        # dstack:@calc _y +
        # dstack:@pop _x
        # to
        # dstack:@push _x
        # dstack:@push _y
        # dstack:@add
        # dstack:@pop _x
        for i in range(len(code) - 2):
            m0, o0, p0 = parse_push(code[i])
            m1, o1, p1 = parse_push(code[i + 1])
            m2, o2, p2 = parse_push(code[i + 2])

            ps1 = p1.split(" ")
            if len(ps1) == 2:
                p1a, p1b = ps1

            if (len(set([m0, m1, m2])) == 1
                    and o0 == "@push"
                    and o1 == "@calc"
                    and o2 == "@pop"
                    and isvar(p0) and p0 == p2
                    and len(ps1) == 2
                    and (isval(p1a)
                        or p1a[0] == "-" and isval(p1a[1:]))
                    and p1b in ["+", "-"]):
                code[i + 1] = f"{m1}:@push {p1a}"
                o = "add" if p1b == "+" else "sub"
                code.insert(i + 2, f"{m1}:@{o}")

                optimized = True

                break

        for i in range(len(code) - 3):
            m0, o0, p0 = parse_push(code[i])
            m1, o1, p1 = parse_push(code[i + 1])
            m2, o2, p2 = parse_push(code[i + 2])
            m3, o3, p3 = parse_push(code[i + 3])

            if (len(set([m0, m1, m2, m3])) == 1
                    and o0 == "@push" and o1 == "@push"
                    and o3 == "@pop"
                    and isvar(p0) and p0 == p3
                    and isval(p1)
                    and o2 in ["@add", "@sub"]):

                code[i] = f"# simple {o2}"
                opfx = ("" if p1.isdigit()
                        else "move" if p1.startswith("-")
                        else "copy")
                osfx = "add" if o2 == "@add" else "sub"
                code[i + 1] = f"{opfx}{osfx} {p1} {p0}"

                code.pop(i + 2)
                code.pop(i + 2)

                optimized = True

                break

        if not optimized:
            break


if __name__ == "__main__":
    inc_dir = []
    dstack_size = 64
    rstack_size = 8
    bf16 = False

    for arg in sys.argv[1:]:
        if arg.startswith("-I"):
            inc_dir.append(arg[2:])

        if arg.startswith("-ds"):
            dstack_size = int(arg[3:])

        if arg.startswith("-rs"):
            rstack_size = int(arg[3:])

        if arg == "-bf8":
            bf16 = False
        if arg == "-bf16":
            bf16 = True

        if arg in ["-help", "-?", "-h"]:
            print(f"python {sys.argv[0]} [options] < src > dst")
            print(f"options:")
            print(f"  -Idir  add include/import search directory")
            print(f"  -dsN   select size of data stack ({dstack_size})")
            print(f"  -rsN   select size of call stack ({rstack_size})")
            # print(f"  -bf16  target is 16bit brainfuck")
            sys.exit(0)

    src = load(sys.stdin, [], inc_dir)
    code = compile(src,
            dstack_size=dstack_size,
            rstack_size=rstack_size,
            bf16=bf16)

    optimize_tobf(code)

    for i in code:
        print(i)
