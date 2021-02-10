
# small array with slow code (<=256 elements)
#   data is smaller than mem.
#   code is shorter than fastmem.
#   better than them if you want to store structures after large array, and want short code.
#   this structure has 4 workspace. they should be shared as temporary (currently not).
# memory layout:
#   idx_for_search, idx_for_return, carried, padding_for_shift, v0, v1, ..., v(N-1)
#   uses like this:
#      0, 0, 0, 0,v0,v1,v2,v3
#     # a[2] = 16
#     *2, 2,16, 0,v0,v1,v2,v3
#     v0,*1, 2,16, 0,v1,v2,v3
#     v0,v1,*0, 2,16, 0,v2,v3
#     v0,v1, 0,*2, 0, 0,16,v3
#     v0, 0,*1, 0, 0,v1,16,v3
#      0,*0, 0, 0,v0,v1,16,v3
# init n
#   initializes for n cells
# clean
#   cleans all
# @clear
#   clears all
# @r_move imm_idx out_var
# @r_move var_idx out_var
# @r_copy imm_idx out_var
# @r_copy var_idx out_var
# @w_move imm_val imm_dst_idx
# @w_move imm_val var_dst_idx
# @w_move in_var imm_dst_idx
# @w_move in_var var_dst_idx
# @w_copy imm_val imm_dst_idx
# @w_copy imm_val var_dst_idx
# @w_copy in_var imm_dst_idx
# @w_copy in_var var_dst_idx
#   breaks vars prefixed with "-" (except in_var/out_var. they mean same as args of move/copy).
#   if want to save vars. requires tmp

from typing import cast, Union, List, Tuple, Set, Dict, Type, Callable
import sys
from tobf import Tobf
from base import separate_sign, calc_small_pair, SubsystemBase


class Subsystem_SlowMem(SubsystemBase):
    def __init__(self, main: Tobf, name, args: List[str], instantiate: Callable[[int, SubsystemBase], int]):
        super().__init__(main, name)

        if len(args) > 0:
            self.mem_size_ = self._main.valueof(args[0])
        else:
            self.mem_size_ = 16

        self.resize(4 + self.mem_size_)
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

    def put_clean(self, args: List[str]):
        if len(args) > 0 and "fast" in args:
            return

        self._main.put_at(self.offset(4), ("[-]>" * self.mem_size_) + ("<" * self.mem_size_))

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
            return self.offset(4)
        if value == "last":
            return self.offset(4 + self.mem_size_ - 1)

        if self._main.is_val(value):
            idx = self._main.valueof(value)

            if idx in range(self.mem_size_):
                return self.offset(4 + idx)

        raise Exception(f"can not get address of {value}")

    def has_ins(self, name: str, args: list) -> bool:
        return (name in [
                "init", "clean", "@clear"]
            or len(args) >= 2
                and name in [
                    "@set",
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
            raise Exception(f"cant use [fastmem:init] directly")

        if name in ["clean", "@clear"]:
            self.put_clean(args)

            return

        if name == "@set":
            sign, src = separate_sign(args[0])

            if not self._main.is_val(src):
                raise Exception(f"first argument for [slowmem:@set] should be immediate value")

            name = "@w_move"

        if name in [
                "@r_copyadd", "@r_copysub", "@r_copy",
                "@w_copyadd", "@w_copysub", "@w_copy"]:
            copy = True
            name = name.replace("copy", "move")
        else:
            copy = False

        if name in ["@r_moveadd", "@r_movesub"]:
            sign = "+" if name[-3:] == "add" else "-"
            args = [args[0]] + [sign + arg for arg in args[1:]]
            name = name[:-3]

        if name in ["@w_moveadd", "@w_movesub"]:
            name_suffix = name[-3:]
            name = name[:-3]
        else:
            name_suffix = ""

        if name == "@r_move":
            src = args[0]
            dsts = args[1:]

            sign, v = separate_sign(src)

            if self._main.is_val(v):
                n = self._main.valueof(v)
                addr = self.offset(4 + n)

                if copy:
                    self._main.put_copy(addr, dsts)
                else:
                    self._main.put_move(addr, dsts)

                return
            if self._main.is_var(v):
                addr = self._main.addressof(v)

                if sign != "-":
                    self._main.put_copy(addr, [f"+#{self.offset(0)}", f"+#{self.offset(1)}"])
                else:
                    self._main.put_move(addr, [f"+#{self.offset(0)}", f"+#{self.offset(1)}"])

                self._main.put(">" * self.offset())
                self._main.put("[>[>+<-]<[>+<-]> >>>[<<<<+>>>>-]<<<-]")

                if copy:
                    self._main.put(f">>>>[<+<+>>-]<[>+<-]<<<")
                else:
                    self._main.put(f">>>>[<<+>>-]<<<<")

                self._main.put(">[<<[>>>>+<<<<-]>>[<+>-]>[<+>-]<<-]<")
                self._main.put("<" * self.offset())

                self._main.put_move(self.offset(2), dsts)

            return

        if name == "@w_move":
            src = args[0]
            dsts = args[1:]

            sign, v = separate_sign(src)

            if self._main.is_val(v):
                # [?] = imm
                n = self._main.valueof(v)

                if name_suffix == "":
                    o = "[-]" + ("+" * n)
                else:
                    o = "+" if name_suffix == "add" else "-"
                    o = (o * n)

                for dst in dsts:
                    dst_sign, dst = separate_sign(dst)

                    if self._main.is_val(dst):
                        # [imm] = imm
                        m = self._main.valueof(dst)

                        self._main.put_at(self.offset(4 + m), o)
                    elif self._main.is_var(dst):
                        # [var] = imm
                        dst_addr = self._main.addressof(dst)

                        if dst_sign == "":
                            self._main.put_copy(dst_addr, [f"+#{self.offset(0)}", f"+#{self.offset(1)}"])
                        else:
                            self._main.put_move(dst_addr, [f"+#{self.offset(0)}", f"+#{self.offset(1)}"])

                        self._main.put(">" * self.offset())
                        self._main.put("[>[>+<-]<[>+<-]> >>>[<<<<+>>>>-]<<<-]")
                        self._main.put(f">>>>{o}<<<<")
                        self._main.put(">[<<[>>>>+<<<<-]>>[<+>-]<-]<")
                        self._main.put("<" * self.offset())

                return

            if self._main.is_var(v):
                # [?] = var
                addr = self._main.addressof(v)

                if name_suffix == "":
                    o = ""
                else:
                    o = "-" if name_suffix == "sub" else "+"

                dsts_with_imm = [f"{o}#{self.offset(4 + self._main.valueof(dst))}"
                        for dst in dsts if self._main.is_val(dst)]

                dsts_with_var = list(filter(self._main.is_var, dsts))

                # imms
                if copy or len(dsts_with_var) > 0:
                    self._main.put_copy(addr, dsts_with_imm)
                else:
                    self._main.put_move(addr, dsts_with_imm)

                # vars
                for i, dst in enumerate(dsts_with_var):
                    dst_sign, dst = separate_sign(dst)
                    dst_addr = self._main.addressof(dst)

                    # [var] = var

                    if copy or i + 1 < len(dsts_with_var):
                        self._main.put_copy(addr, [f"+#{self.offset(2)}"])
                    else:
                        self._main.put_move(addr, [f"+#{self.offset(2)}"])

                    if dst_sign == "":
                        self._main.put_copy(dst_addr, [f"+#{self.offset(0)}", f"+#{self.offset(1)}"])
                    else:
                        self._main.put_move(dst_addr, [f"+#{self.offset(0)}", f"+#{self.offset(1)}"])

                    self._main.put(">" * self.offset())
                    self._main.put("[>>[>+<-]<[>+<-]<[>+<-]> >>>[<<<<+>>>>-]<<<-]")
                    self._main.put(f">>")
                    if name_suffix == "":
                        self._main.put(f">>[-]<<")
                    self._main.put(f"""[>>{"-" if name_suffix == "sub" else "+"}<<-]<<""")
                    self._main.put(">[<<[>>>>+<<<<-]>>[<+>-]<-]<")
                    self._main.put("<" * self.offset())


            return

        raise Exception(f"wnknown ins: {name} {args}")
