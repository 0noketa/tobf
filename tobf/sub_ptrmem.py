
# array with pointers (no size limitation. no index)
# memory layout(size: 4, pointers: 2):
#   0 0 vs[0] 0  p>0 q>0 vs[1] 1  p>1 q>1 vs[2] 1  p>2 q>2 vs[3] 1  0 0 0 0
#
#   every 1 next to value is used for skip over this array.
# init n
#   initializes for n cells
# init n m
#   initializes for n cells with m pointers
# init n m disable_skip
#   avoids to prepare structure for skip
# clean
#   cleans all
# @set imm ptr_idx
#   imm can be "input" or "print"
# @add imm ptr_idx
# @sub imm ptr_idx
# @clear ptr_idx
#   clears pointed value
# @ptr_inc ptr_idx
# @ptr_dec ptr_idx
# @ptr_clear ptr_idx
#   assigns 0 to pointer
# @r_move ptr_idx ...out_vars
# @r_copy ptr_idx ...out_vars
# @w_move in_var ptr_idx
# @w_copy in_var ptr_idx

from typing import cast, Union, List, Tuple, Set, Dict, Type, Callable
import sys
from tobf import Tobf
from base import separate_sign, calc_small_pair, SubsystemBase


class Subsystem_PtrMem(SubsystemBase):
    def __init__(self, main: Tobf, name, args: List[str], instantiate: Callable[[int, SubsystemBase], int]):
        super().__init__(main, name)

        if len(args) > 0:
            self.mem_size_ = self._main.valueof(args[0])
        else:
            self.mem_size_ = 16

        self.mem_size_ = max(self.mem_size_, 2)

        if len(args) > 1:
            self.n_ptrs_ = self._main.valueof(args[1])
        else:
            self.n_ptrs_ = 1

        self.cell_size_ = self.n_ptrs_ + 2
        self.skip_enabled = len(args) <= 2 or args[2] != "disable_skip"

        self.resize((self.mem_size_ + 1) * self.cell_size_)
        self.fix()
        instantiate(self.size(), self)

        self.def_const("size", self.mem_size_)

    def array_size(self) -> bool:
        return self.mem_size_
    def is_readable_array(self) -> bool:
        return True
    def is_writable_array(self) -> bool:
        return True
    def readable_vars(self) -> bool:
        return ["first", "last"]
    def writable_vars(self) -> bool:
        return ["first", "last"]

    def put_init(self, args: List[str]):
        if not self.skip_enabled:
            return

        self._main.put_address_selector(self.offset())
        self._main.put(">" * (self.cell_size_ - 2))

        size = self.mem_size_ - 1
        while size > 0:
            if size >= 255:
                n = 255
                self._main.put(
                        "<" + "+" * 15
                        + "[>" + "+" * 15 + "<-]>")
            else:
                n = size
                self._main.put("+" * n)
            size -= n
            
            self._main.put(
                    "["
                    + "[" + ">" * self.cell_size_
                        + "+"
                        + "<" * self.cell_size_ + "-]"
                    + ">" * self.cell_size_
                    + ">+<"
                    + "-]")
        
        self._main.put(
                "<" * (self.cell_size_ - 1)
                + "[" + ("<" * self.cell_size_) + "]"
                + "<" * (self.cell_size_ - 1))

        self._main.put_address_deselector(self.offset())

    def put_clean(self, args: List[str]):
        if len(args) > 0 and "fast" in args:
            return

        if self.skip_enabled:
            # 0 0 v0 0  p1 q1 v1 1  0 0 0 0
            self._main.put_at(self.offset(),
                    ">" * (self.cell_size_ * 2 - 1)
                    + "[" + (">" * self.cell_size_) + "]"
                    + "<" * self.cell_size_
                    + "[-<[-]" + ("<[-]" * self.n_ptrs_) + "<]"
                    + "<[-]"
                    + "<" * self.n_ptrs_)
        else:
            self._main.put_at(self.offset(),
                    "ptrmem:clean without enable_skip is not implemented")

    def can_skip(self) -> bool:
        return self.skip_enabled
    def put_skip_right(self):
        self._main.put(
                ">" * (self.cell_size_ * 2 - 1)
                + "[" + (">" * self.cell_size_) + "]"
                + ">")
    def put_skip_left(self):
        self._main.put(
                "<" * (self.cell_size_ + 1)
                + "[" + ("<" * self.cell_size_) + "]"
                + "<" * (self.cell_size_ - 1))

    def has_var(self, name: str) -> bool:
        if self._main.is_val(name):
            idx = self._main.valueof(name)

            if idx in range(self.mem_size_):
                return True

        return name in ["first", "last"]

    def addressof(self, value: str) -> int:
        """direct I/O interface. index as variable"""

        if self.mem_size_ == 0:
            raise Exception(f"empty array has no readable address")

        if value == "first":
            idx = 0
        elif value == "last":
            idx = self.mem_size_ - 1
        elif self._main.is_val(value):
            idx = self._main.valueof(value)
        else:
            idx = -1

        if idx in range(self.mem_size_):
            return self.offset(idx * self.cell_size_ - 2)

        raise Exception(f"can not get address of {value}")

    def has_ins(self, name: str, args: list) -> bool:
        return (name in [
                "init", "clean",
                "@clear"]
            or len(args) >= 1
                and name in [
                    "@set", "@add", "@sub",
                    "@ptr_inc", "@ptr_dec", "@ptr_clear",
                    "@inc", "@dec"]
            or len(args) >= 2
                and name in [
                    "@w_moveadd", "@w_movesub", "@w_move",
                    "@w_copyadd", "@w_copysub", "@w_copy",
                    "@r_moveadd", "@r_movesub", "@r_move",
                    "@r_copyadd", "@r_copysub", "@r_copy"]
            or super().has_ins(name, args))

    def put(self, name: str, args: List[str], tmps: List[int] = None):
        name0 = name

        if tmps == None:
            tmps = self._main.tmps_.copy()

        if name == "init":
            raise Exception(f"cant use [ptrmem:init] directly")

        if name == "clean":
            raise Exception(f"cant use [ptrmem:clean] directly")

            return

        if name in ["@ptr_inc", "@ptr_dec", "@ptr_clear"]:
            self._main.put_address_selector(self.offset())

            for dst in args:
                n = self.valueof(dst)

                self._main.put((">" * (self.cell_size_ + n)) + "[")
                self._main.put((">" * self.cell_size_) + "]")

                # 0 0 v 1  p p v 1 0 0 0 0
                if name == "@ptr_clear":
                    self._main.put(("<" * self.cell_size_) + "[-" + ("<" * self.cell_size_) + "]")
                elif name == "@ptr_inc":
                    self._main.put("+[" + ("<" * self.cell_size_) + "]")
                else:
                    self._main.put(("<" * self.cell_size_) + "-" + ("<" * self.cell_size_) + "[" + ("<" * self.cell_size_) + "]")

                self._main.put("<" * n)

            self._main.put_address_deselector(self.offset())

            return

        if name == "@clear":
            name = "@set"
            args = [0] + args
        if name == "@inc":
            name = "@add"
            args = [1] + args
        if name == "@dec":
            name = "@set"
            args = [1] + args

        if name in ["@set", "@add", "@sub"]:
            if len(args) == 1:
                raise Exception(f"[ptrmem:{name}/1] is not implemented")

            src = args[0]
            dsts = args[1:]

            self._main.put_address_selector(self.offset())

            for dst in dsts:
                ptr = self.valueof(dst)

                if ptr >= self.n_ptrs_:
                    raise Exception(f"ptrmem {self.name()} has not pointer {ptr}")

                self._main.put((">" * (self.cell_size_ + ptr)) + "[")
                self._main.put((">" * self.cell_size_) + "]")

                self._main.put("<" * (ptr + 2))

                if src == "print":
                    if name != "@set":
                        raise Exception(f"[ptrmem:{name} print] is not implemented")
                    self._main.put(".")
                elif src == "input":
                    if name != "@set":
                        raise Exception(f"[ptrmem:{name} input] is not implemented")
                    self._main.put(",")
                else:
                    if name == "@set":
                        self._main.put("[-]")

                    o = "-" if name == "@sub" else "+"
                    n = self.valueof(src)
                    self._main.put(o * n)

                self._main.put(">" * (ptr + 2))
                self._main.put("<" * self.cell_size_)
                self._main.put("[" + ("<" * self.cell_size_) + "]")
                self._main.put("<" * ptr)

            self._main.put_address_deselector(self.offset())

            return

        if name in [
                "@r_copyadd", "@r_copysub", "@r_copy",
                "@w_copyadd", "@w_copysub", "@w_copy"]:
            copy = True
            name = name.replace("copy", "move")
        else:
            copy = False

        name_suffix = ""

        if name in ["@r_moveadd", "@r_movesub"]:
            name_suffix = name[-3:]
            name = name[:-3]

        if name in ["@w_moveadd", "@w_movesub"]:
            name_suffix = name[-3:]
            name = name[:-3]


        if name == "@r_move":
            src = self.valueof(args[0])
            dsts = args[1:]

            if src >= self.n_ptrs_:
                raise Exception(f"ptrmem {self.name()} has not pointer {src}")

            tmp = tmps.pop()

            self._main.put_address_selector(self.offset())

            self._main.put((">" * (self.cell_size_ + src)) + "[")
            self._main.put((">" * self.cell_size_) + "]")

            self._main.put("<" * (src + 2))

            self._main.put("[")

            self._main.put(">" * (src + 2))
            self._main.put("<" * self.cell_size_)
            self._main.put("[" + ("<" * self.cell_size_) + "]")
            self._main.put("<" * src)
            self._main.put(">" * (self.cell_size_ - 1))
            self._main.put("+")
            self._main.put("<" * (self.cell_size_ - 1))

            self._main.put((">" * (self.cell_size_ + src)) + "[")
            self._main.put((">" * self.cell_size_) + "]")

            self._main.put("<" * (src + 2))

            self._main.put("-]")

            self._main.put(">" * (src + 2))
            self._main.put("<" * self.cell_size_)
            self._main.put("[" + ("<" * self.cell_size_) + "]")
            self._main.put("<" * src)

            self._main.put(">" * (self.cell_size_ - 1) + "[")
            self._main.put("<" * (self.cell_size_ - 1))

            if copy:
                self._main.put((">" * (self.cell_size_ + src)) + "[")
                self._main.put((">" * self.cell_size_) + "]")

                self._main.put(("<" * (src + 2)) + "+" + (">" * (src + 2)))

                self._main.put(("<" * (self.cell_size_ + src)) + "[")
                self._main.put(("<" * self.cell_size_) + "]")
                self._main.put("<" * src)

            self._main.put_address_deselector(self.offset())

            self._main.put_at(tmp, "+")

            self._main.put_address_selector(self.offset())

            self._main.put(">" * (self.cell_size_ - 1) + "-]")
            self._main.put("<" * (self.cell_size_ - 1))

            self._main.put_address_deselector(self.offset())

            if name_suffix != "":
                dsts2 = []

                for dst in dsts:
                    sign, name = separate_sign(dst)

                    sign = "+" if name_suffix == "add" else "-"

                    dsts2.append(sign + name)
                
                dsts = dsts2

            self._main.put_move(tmp, dsts)

            tmps.append(tmp)

            return

        if name == "@w_move":
            dsts = args[1:]

            if copy:
                self._main.put_copy(args[0], [f"+#{self.offset(0)}"])
            else:
                self._main.put_move(args[0], [f"+#{self.offset(0)}"])

            self._main.put_address_selector(self.offset(0))
            self._main.put("[" + (">" * (self.cell_size_ - 1)) + "+" + ("<" * (self.cell_size_ - 1)) + "-]")

            if name_suffix == "":
                for dst in dsts:
                    # 0 0 v0 0  p q v1 1  0 0 0 0
                    n = self.valueof(dst)

                    if n >= self.n_ptrs_:
                        raise Exception(f"ptrmem {self.name()} has not pointer {n}")

                    self._main.put(">" * (self.cell_size_ + n))
                    self._main.put("[" + (">" * self.cell_size_) + "]")

                    self._main.put("<" * (n + 2))
                    self._main.put("[-]")
                    self._main.put(">" * (n + 2))
                    self._main.put("<" * (self.cell_size_ - n))

                    self._main.put("[" + ("<" * self.cell_size_) + "]")

                    self._main.put("<" * n)

            self._main.put((">" * (self.cell_size_ - 1)) + "[")

            o = "-" if name_suffix == "sub" else "+"

            for dst in dsts:
                # 0 0 v0 0  p q v1 1  0 0 0 0
                n = self.valueof(dst)

                if n >= self.n_ptrs_:
                    raise Exception(f"ptrmem {self.name()} has not pointer {n}")

                self._main.put(("<" * (self.cell_size_ - 1)) + (">" * (self.cell_size_ + n)))
                self._main.put("[" + (">" * self.cell_size_) + "]")

                self._main.put("<" * (n + 2))
                self._main.put(o)
                self._main.put(">" * (n + 2))
                self._main.put("<" * (self.cell_size_ - n))

                self._main.put("[" + ("<" * self.cell_size_) + "]")

                self._main.put("<" * n)
                self._main.put(">" * (self.cell_size_ - 1))

            self._main.put("-]" + ("<" * (self.cell_size_ - 1)))

            self._main.put_address_deselector(self.offset(0))

            return

        raise Exception(f"wnknown ins: {name} {args}")
