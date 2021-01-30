
# stack (no size-limitation)
#   default: 0, v0, used?, v1, used?, ..., 0, 0
#   dynamic: 0, v0, used?, v1, used?, ..., 0, 0, 0, 0
# consts:
#   is_arraylike: 0
#   is_stacklike: 1
#   readable: 1
#   writable: 0
#   prefix: 1
#   suffix: 4 if dynamic else 2 
#   cells: n
#   cell_prefix: 0 
#   cell_suffix: 1 
# init n
#   initializes for n cells
# init n dynamic
#   initializes for n cells. with instructions for unknown range
# clean
#   cleans all
# @clear
#   drops all
# @copypush ...in_vals
#   appends copied values to last.
# @push ...in_vals
#   appends values to last.
# @pop
#   removes last value
# @pop ...out_vars
#   removes last values. and stores to out_vars
# @dup
# @dup imm_n_times
# @swap
# @rot
# @rot imm_n_range
# @rot var_n_range
# @rot -var_n_range
# @add
# @sub
# @inc
# @dec
#   stack jugglers.
#   remove last value(s) and stores calulated value(s) 
#   calculations are same as concatenative languages
#   -var versions break variables
# @calc ...stack_jaggling_code
#   inline rpn claculator. accepts any of [dup swap rot + - 1+ 1- , . <anynumber> <anychar>]
# @empty out_var

from typing import cast, Union, List, Dict, Callable
from tobf import Tobf
from base import separate_sign, calc_small_pair, SubsystemBase


class Subsystem_Stk(SubsystemBase):
    def __init__(self, tobf: Tobf, _name: str, args: List[Union[str, int]], get_addr: Callable[[int], int]):
        super().__init__(tobf, _name)
        self._main = cast(Tobf, self._main)

        if len(args) > 0:
            size = self._main.valueof(args[0])
            self.dyn = len(args) > 1 and args[1] == "dynamic"
            self._stk_size = size
        else:
            self.dyn = False
            self._stk_size

        self.resize(self._stk_size * 2 + (5 if self.dyn else 3))

    def put_clean(self, args: List[Union[str, int]]):
        if len(args) > 0 and args[0] == "fast":
            return

        self._main.put_at(self.offset(), ">>[>>]<<[-<[-]<]")

    def put_set_char(self, v: int):
        """current_addr+1 as workspace. and moves to current_addr+1"""

        if v == 0:
            self._main.put(">")
            return

        n, m = calc_small_pair(v, 1)

        if m == 1 or n * m < n + m + 5:
            self._main.put("+" * n + ">")
        else:
            self._main.put(">" + "+" * n + "[<" + "+" * m + ">-]")

    def put_clear_dsts(self, out_vars: list):
        """clear destinations without sign."""

        for out_var in out_vars:
            sign, addr0 = separate_sign(out_var)
            addr = self._main.addressof(addr0)

            if sign == "":
                self._main.put_at(addr, "[-]")

    def has_ins(self, name: str, args: list) -> bool:
        return (name in [
                "init", "clean",
                "@clear", "@empty",
                "@pop", "@dup", "@swap", "@rot", "@add", "@sub", "@inc", "@dec",
                "@calc"]
            or len(args) > 0
                and name in [
                    "@push", "@copypush", "@pop"]
            or super().has_ins(name, args))

    def skip_args(self, args: list, i: int, pred: str) -> int:
        while (i < len(args)
                and (args[i] == pred if type(pred) == str
                    else pred(args[i]))):
            i += 1

        return i

    def put_juggling_start(self):
        self._main.put((">" * self.offset()) + ">>[>>]<")

    def put_juggling_end(self):
        """at first unused value"""
        self._main.put("<[<<]" + ("<" * self.offset()))

    def put_juggling_push(self, value: str, first=False, last=False, tmps: List[int] = None):
        """starts and ends at first unused value"""

        sign, value = separate_sign(value)

        if self._main.is_var(value):
            addr = self._main.addressof(value)
            tmp = -1

            if sign != "-":
                tmp = self._main.get_nearest_tmp(tmps, [addr])

            if not first:
                self.put_juggling_end()

            self._main.put_at(addr, "[")

            if sign != "-":
                self._main.put_at(tmp, "+")

            self._main.put_at(self.offset(), ">>[>>]<+<[<<]")
            self._main.put_at(addr, "-]")

            self._main.put_at(self.offset(), ">>[>>]+[<<]")

            if sign != "-":
                self._main.put_move(tmp, [f"+#{addr}"])

            if not last:
                self.put_juggling_start()

            return

        if first:
            self.put_juggling_start()

        if value == "input":
            self._main.put(",>+>")
        elif self._main.is_val(value):
            v = self._main.valueof(value)
            self.put_set_char(v)
            self._main.put("+>")
        else:
            raise Exception(f"unknown args{value}")

        if last:
            self.put_juggling_end()

    def put_juggling_pop(self, value: str = None, first=False, last=False):
        """starts and ends at first unused value"""

        if first:
            self.put_juggling_start()

        if value == None:
            self._main.put("<-<[-]")
        elif value == "print":
            self._main.put("<-<.[-]")

        if last:
            self.put_juggling_end()

    def put_juggling_add(self, sub=False, first=False, last=False):
        """starts and ends at first unused value"""

        if first:
            self.put_juggling_start()

        o = "-" if sub else "+"

        if first and last:
            self._main.put("<[<[<<" + o + ">>-]>-<<[<<]]" + ("<" * self.offset()))

            return

        self._main.put("<<[<<" + o + ">>-]>-<")

        if last:
            self.put_juggling_end()

    def put_juggling_inc(self, dec=False, first=False, last=False):
        """starts and ends at first unused value"""

        if first:
            self.put_juggling_start()

        o = "-" if dec else "+"

        if first and last:
            self._main.put("<[<" + o + ">[<<]]" + ("<" * self.offset()))

            return

        self._main.put("<<" + o + ">>")

        if last:
            self.put_juggling_end()

    def put_juggling_dup(self, n: int = 1, first=False, last=False):
        """starts and ends at first unused value"""

        m = n + 1

        if first and last:
            if n < 1:
                return

            self.put_juggling_start()
            self._main.put("<[ <[" + (">>+" * m) + ("<<" * m) + "-]>" + (">>+" * n) + ">[" + ("<<" * m) + "+" + (">>" * m) + "-]< [<<]]")
            self._main.put("<" * self.offset())

            return

        if n < 1:
            if last: 
                self.put_juggling_end()

            return

        if first:
            self.put_juggling_start()

        self._main.put("<<[" + (">>+" * m) + ("<<" * m) + "-]>" + (">>+" * n) + ">[" + ("<<" * m) + "+" + (">>" * m) + "-]")

        if last:
            self.put_juggling_end()

    def put_juggling_rot(self, n: int = 3, first=False, last=False):
        """starts and ends at first unused value"""

        m = n - 1

        if first and last:
            if n < 2:
                return

            self.put_juggling_start()
            self._main.put("<[" + ("<<" * m) + "<[" + (">>" * n) + "+" + ("<<" * n) + "-]" + (">>[<<+>>-]" * n) + "<[<<]]")
            self._main.put("<" * self.offset())

            return

        if n < 2:
            if last: 
                self.put_juggling_end()

            return

        if first:
            self.put_juggling_start()

        self._main.put("<" + ("<<" * m) + "<[" + (">>" * n) + "+" + ("<<" * n) + "-]" + (">>[<<+>>-]" * n))

        if last:
            self.put_juggling_end()

    def put(self, name: str, args: list, tmps: List[int] = None):
        if name == "init":
            return

        if name == "clean":
            self.put_clean()
            return

        if name == "@clear":
            self._main.put_at(self.offset(), ">>[>>]<<[-<[-]<]")

            return

        if name == "@calc":
            if len(args) == 0:
                return

            for i in range(len(args)):
                arg = args[i]
                first = i == 0
                last = i + 1 == len(args)

                if arg == "swap":
                    self.put_juggling_rot(2, first=first, last=last, tmps=tmps)
                elif arg == "dup":
                    self.put_juggling_dup(1, first=first, last=last, tmps=tmps)
                elif arg == "rot":
                    self.put_juggling_rot(3, first=first, last=last)
                elif arg == "drop":
                    self.put_juggling_pop(None, first=first, last=last)
                elif arg == "+":
                    self.put_juggling_add(sub=False, first=first, last=last)
                elif arg == "-":
                    self.put_juggling_add(sub=True, first=first, last=last)
                elif arg == "1+":
                    self.put_juggling_inc(dec=False, first=first, last=last)
                elif arg == "1-":
                    self.put_juggling_inc(dec=True, first=first, last=last)
                elif arg == ".":
                    self.put_juggling_pop("print", first=first, last=last)
                elif arg == ",":
                    self.put_juggling_push("input", first=first, last=last, tmps=tmps)
                elif arg.isdigit():
                    self.put_juggling_push(str(int(arg)), first=first, last=last, tmps=tmps)
                elif arg == "'":
                    self.put_juggling_push("32", first=first, last=last)
                elif arg.startswith("'"):
                    self.put_juggling_push(str(ord(arg[1])), first=first, last=last)
                else:
                    raise Exception(f"[stk:calc] can not compile [{arg}]")

            return

        if name in ["@push", "@copypush"]:
            if len(args) == 0:
                raise Exception("stk:@push requires 1 arg")

            for i in range(len(args)):
                arg = args[i]
                
                self.put_juggling_push(arg, i == 0, i + 1 == len(args), tmps=tmps)

            return

        if name == "@pop":
            if len(args) == 0:
                self._main.put_at(self.offset(), ">>[>>]<<[-<[-]<[<<]]")

                return

            self.put_clear_dsts(list(filter(self._main.is_var, args)))

            for arg in args:
                if arg == "print":
                    self._main.put_at(self.offset(), ">>[>>]<<[-<.[-]<[<<]]")

                    continue

                sign, arg = separate_sign(arg)

                if not self._main.is_var(arg):
                    raise Exception(f"[@pop/n] with unknown arg")

                addr = self._main.addressof(arg)

                self._main.put_at(self.offset(), ">>[>>]<<[ <[ >[<<]")
                self._main.put_at(addr, "-" if sign == "-" else "+")
                self._main.put_at(self.offset(), ">>[>>]<<<-] >-<<[<<]]")

            return

        if name == "@empty":
            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(addr, "[-]+")

            tmp = self._main.get_nearest_tmp(tmps, args)

            self._main.put_at(self.offset(), ">>[<<")
            self._main.put_at(tmp, "+")
            self._main.put_at(self.offset(), ">>-]<<")

            self._main.put_at(tmp, "[")

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(addr, "-")

            self._main.put_at(self.offset(), ">>+<<")

            self._main.put_at(tmp, "-]")

            return

        if name in ["@add", "@sub"]:
            self.put_juggling_add(name == "@sub", first=True, last=True)

            return

        if name == "@dup":
            n = 1
            if len(args) == 1:
                if self._main.is_var(args[0]):
                    raise Exception(f"[stk:@dup] for dynamic range is not implemented")

                n = self._main.valueof(args[0])
            elif len(args) > 0:
                raise Exception(f"[stk:@dup/{len(args)}] is not implemented")

            self.put_juggling_dup(n, first=True, last=True)

            return

        if name == "@swap":
            # self._main.put_at(self.offset(), ">>[>>]<<[<[>>+<<-] <<[>>+<<-] >>>>[<<<<+>>>>-] <[<<]]")
            # return
            args = [2]
            name = "@rot"

        if name == "@rot":
            n = 3
            if len(args) > 0:
                sign, arg = separate_sign(args[0])

                if self._main.is_var(arg):
                    if not self.dyn:
                        raise Exception(f"[{self.name()}:@rot] for dynamic range is not enabled in source code")

                    addr = self._main.addressof(arg)
                    tmp = -1

                    if sign != "-":
                        tmp = self._main.get_nearest_tmp(tmps, [addr])

                    self._main.put_at(addr, "[-[+ [")

                    if sign != "-":
                        self._main.put_at(tmp, "+")

                    # makes: ..., 0, 0, 0, n_range
                    self._main.put_at(self.offset(), ">>[>>]>>+<<<<[<<]")

                    self._main.put_at(addr, "-]")

                    # makes: ..., v[N-2], 1, v[N-1], *n_range-1, 0, 0, 0, 0
                    self._main.put(">" * self.offset() + ">>[>>]>>[<<<<+>>>>-]<<<<--")

                    # makes: ..., v[N-n_range], *0, v[N-n_range+1], 1, v[N-n_range+2], 1, 0, 0, 0, 0
                    self._main.put("[[<<+>>-]+<<--]")

                    # makes: ..., 0, *0, v[N-n_range+1], 1, v[N-n_range+2], 1, v[N-n_range], 0, 0, 0
                    self._main.put("<[>>>[>>]<+<[<<]<-]>")

                    # makes: ..., v[N-n_range+1], 1, v[N-n_range+2], 1, v[N-n_range], 1, 0, *0
                    self._main.put("+[>[<<+>>-]>]")

                    self._main.put("<<[<<]" + "<" * self.offset())

                    self._main.put_at(addr, "]]")

                    if sign != "-":
                        self._main.put_move(tmp, [f"+#{addr}"])

                    return

                if self._main.is_val(arg):
                    n = self._main.valueof(arg)

            self.put_juggling_rot(n, first=True, last=True)

            return

        if name in ["@inc", "@dec"]:
            self.put_juggling_inc(name == "@dec", first=True, last=True)

            return

        raise Exception(f"wnknown ins: {name} {args}")
