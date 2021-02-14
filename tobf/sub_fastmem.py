
# smallest array with fast & largest code (<=256 elements)
#   fastmem has no hidden workspace. can be used for static slicing.
#   ex:
#     loadas a fastmem 8
#     input a
#     unload a fast
#     loadas a fastmem 4
#     loadas b fastmem 4
#     print a 10 b 10
#   currently fastmem is more orthogonal than mem. every combination of args work fine. mem should be rewritten.
#   do not use for large(>=16) array if use dynamic-addressing. code size will easily become *10 .. *100 or more.
#   will not be fast on optimized envirionments.
# init n
#   initializes for n cells
#   does not require clean memory.
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


class Subsystem_FastMem(SubsystemBase):
    def __init__(self, main: Tobf, name, args: List[str], instantiate: Callable[[int, SubsystemBase], int]):
        super().__init__(main, name)

        if len(args) > 0:
            self.mem_size_ = self._main.valueof(args[0])
        else:
            self.mem_size_ = 16

        self.resize(self.mem_size_)
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

        self._main.put_at(self.offset(), ("[-]>" * self.mem_size_) + ("<" * self.mem_size_))

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
            return self.offset(0)
        if value == "last":
            return self.offset(self.mem_size_ - 1)

        if self._main.is_val(value):
            idx = self._main.valueof(value)

            if idx in range(self.mem_size_):
                return self.offset(idx)

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

            def put_read(n: int, dsts: list, copy: bool, tmp_addr: int):
                if "print" in dsts:
                    pn = dsts.count("print")

                    self._main.put_at(self.offset(), (">" * n) + ("." * pn) + ("<" * n))

                    dsts = [dst for dst in dsts if dst != "print"]

                if len(dsts) == 0:
                    return

                for dst in dsts:
                    sign, v = separate_sign(dst)

                    if not self._main.is_var(v):
                        raise Exception(f"[fastmem:{name}] took unknown arg")

                    dst_addr = self._main.addressof(v)

                    if sign == "":
                        self._main.put_at(dst_addr, "[-]")

                self._main.put_at(self.offset(n), "[")

                if copy:
                    self._main.put_at(tmp_addr, "+")

                for dst in dsts:
                    sign, v = separate_sign(dst)
                    addr = self._main.addressof(v)

                    if sign == "":
                        sign = "+"

                    self._main.put_at(addr, sign)

                self._main.put_at(self.offset(n), "-]")

                if copy:
                    self._main.put_at(tmp_addr, "[")
                    self._main.put_at(self.offset(n), "+")
                    self._main.put_at(tmp_addr, "-]")


            sign, v = separate_sign(src)

            if self._main.is_val(v):
                n = self._main.valueof(v)

                put_read(n, dsts, copy, 0)
            elif self._main.is_var(v):
                addr = self._main.addressof(v)

                tmp = self._main.get_nearest_tmp(tmps, [v])
                tmps.remove(tmp)

                tmp2 = -1
                if sign != "-":
                    tmp2 = self._main.get_nearest_tmp(tmps, [v])
                    tmps.remove(tmp2)

                for i in range(self.mem_size_):
                    self._main.put_at(tmp, "+")
                    self._main.put_at(addr, "[-")
                    self._main.put_at(tmp, "-")

                for i in range(self.mem_size_ - 1, -1, -1):
                    self._main.put_at(addr, "[-]]")

                    self._main.put_at(tmp, "[")
                    put_read(i, dsts, copy, addr)

                    if sign != "-":
                        self._main.put_at(tmp2, "+" * i)

                    self._main.put_at(tmp, "[-]]")


                if sign != "-":
                    self._main.put_move(tmp2, [f"+#{addr}"])

                    tmps.append(tmp2)
    
                tmps.append(tmp)

            return

        if name == "@w_move":
            src = args[0]
            dsts = args[1:]

            sign, v = separate_sign(src)

            if self._main.is_val(v):
                # [?] = imm
                n = self._main.valueof(v)

                for dst in dsts:
                    dst_sign, dst = separate_sign(dst)

                    if self._main.is_val(dst):
                        # [imm] = imm
                        m = self._main.valueof(dst)

                        if name_suffix == "":
                            o = "[-]" + ("+" * n)
                        else:
                            o = "+" if name_suffix == "add" else "-"
                            o = (o * n)

                        self._main.put_at(self.offset(m), o)
                    elif self._main.is_var(dst):
                        # [var] = imm
                        dst_addr = self._main.addressof(dst)

                        tmp = self._main.get_nearest_tmp(tmps, [dst, self.offset()])
                        tmps.remove(tmp)

                        tmp2 = -1

                        if dst_sign != "-":
                            tmp2 = self._main.get_nearest_tmp(tmps, [dst, self.offset()])
                            tmps.remove(tmp2)

                        for i in range(self.mem_size_):
                            self._main.put_at(tmp, "+")
                            self._main.put_at(dst_addr, "[-")
                            self._main.put_at(tmp, "-")

                        for i in range(self.mem_size_ - 1, -1, -1):
                            self._main.put_at(dst_addr, "[-]]")

                            self._main.put_at(tmp, "[")

                            if name_suffix == "":
                                o = "[-]" + ("+" * n)
                            else:
                                o = "+" if name_suffix == "add" else "-"
                                o = (o * n)

                            self._main.put_at(self.offset(i), o)

                            if dst_sign != "-":
                                self._main.put_at(tmp2, "+" * i)

                            self._main.put_at(tmp, "[-]]")

                        if dst_sign != "-":
                            self._main.put_move(tmp2, [f"+#{dst_addr}"])

                            tmps.append(tmp2)

                        tmps.append(tmp)
            elif self._main.is_var(v):
                # [?] = var
                addr = self._main.addressof(v)

                for i in range(len(dsts)):
                    dst = dsts[i]
                    dst_sign, dst = separate_sign(dst)

                    if self._main.is_val(dst):
                        # [imm] = var
                        n = self._main.valueof(dst)
                        tmp = self._main.get_nearest_tmp(tmps, [v, self.offset()])

                        if name_suffix == "":
                            self._main.put_at(self.offset(n), "[-]")

                        self._main.put_at(addr, "[")

                        if copy or i < len(dsts) - 1:
                            self._main.put_at(tmp, "+")

                        self._main.put_at(self.offset(n), "-" if name_suffix == "sub" else "+")
                        self._main.put_at(addr, "-]")

                        if copy or i < len(dsts) - 1:
                            self._main.put_move(tmp, [f"+#{addr}"])

                        continue

                    if self._main.is_var(dst):
                        # [var] = var
                        tmp = self._main.get_nearest_tmp(tmps, [dst, self.offset()])
                        tmps.remove(tmp)

                        tmp_for_src = -1
                        tmp_for_dst_ptr = -1

                        if copy or len(dsts) > 1:
                            tmp_for_src = self._main.get_nearest_tmp(tmps, [dst, self.offset()])
                            tmps.remove(tmp_for_src)
                        if dst_sign != "-":
                            tmp_for_dst_ptr = self._main.get_nearest_tmp(tmps, [dst, self.offset()])
                            tmps.remove(tmp_for_dst_ptr)

                        dst_addr = self._main.addressof(dst)

                        for j in range(self.mem_size_):
                            self._main.put_at(tmp, "+")
                            self._main.put_at(dst_addr, "[-")
                            self._main.put_at(tmp, "-")

                            if dst_sign != "-":
                                self._main.put_at(tmp_for_dst_ptr, "+")

                        for j in range(self.mem_size_ - 1, -1, -1):
                            self._main.put_at(dst_addr, "[-]]")

                            self._main.put_at(tmp, "[")

                            if name_suffix == "":
                                self._main.put_at(self.offset(j), "[-]")

                            self._main.put_at(addr, "[")

                            if copy or i < len(dsts) - 1:
                                self._main.put_at(tmp_for_src, "+")

                            self._main.put_at(self.offset(j), "-" if name_suffix == "sub" else "+")
                            self._main.put_at(addr, "-]")

                            if copy or i < len(dsts) - 1:
                                self._main.put_move(tmp_for_src, [f"+#{addr}"])

                            self._main.put_at(tmp, "[-]]")

                        if dst_sign != "-":
                            self._main.put_move(tmp_for_dst_ptr, [f"+#{dst_addr}"])

                        tmps.append(tmp)

                        if tmp_for_src != -1:
                            tmps.append(tmp_for_src)
                        if tmp_for_dst_ptr != -1:
                            tmps.append(tmp_for_dst_ptr)

            return

        raise Exception(f"wnknown ins: {name} {args}")
