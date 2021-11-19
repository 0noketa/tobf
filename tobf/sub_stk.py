
# stack (no size-limitation)
#   default: 0, v0, used?, v1, used?, ..., tmps
#   reversed: tmps, ..., used?, v1, used?, v0, 0
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
#   initializes for n cells with 2 tmps.
# init n dynamic
#   initializes for n cells with 4 tmps (instructions for unknown range require).
# init n m
#   initializes for n cells with m(>=2) tmps.
# init n dynamic reversed
# init n m reversed
#   not implemented.
#   uses reversed structure that reduces code when memory layout is something like below
#     stack1(reversed), vars, stack2
#   in optimized code, any address in "vars" becomes base address.
# clean
#   cleans all
# @clear
#   drops all
# @copypush ...in_vals
#   appends copied values to last.
#   this instruction will be removed.
# @push ...in_vals
#   appends values to last.
#   breaks variable when prefixed with "-".
#   keyword "input" can be included in args. they pushes input instead of variable.
# @pop
#   removes last value
# @pop ...out_vars
#   removes last values. and stores to out_vars
#   keyword "print" can be included in args. they prints poped value instead of assignment.
# @dup
# @dup imm_element_size
# @dup imm_element_size imm_n_times
# @dup imm_element_size var_n_times
#   not implemented
# @dup imm_element_size -var_n_times
#   not implemented
# @swap
# @swap imm_element_size
# @rot
# @rot imm_element_size
# @rot imm_element_size imm_n_range
# @rot imm_element_size var_n_range
# @rot imm_element_size -var_n_range
# @over
# @over imm_element_size
# @add
# @sub
# @inc
# @dec
#   stack jugglers.
#   remove last value(s) and stores calulated value(s) 
#   calculations are same as in concatenative languages
#   -var versions break variables
# @calc ...stack_juggling_code
#   inline rpn claculator.
#   accepts any of [dup swap rot over drop + - 1+ 1- , . <anynumber> <anychar>]
#   and digit-prefixed tuple-juggling operators such as
#     2dup (a b -- a b  a b)
#     3swap (a b c  d e f -- d e f  a b c)
#     4rot (a b c d  e f g h  i j k l -- e f g h  i j k l  a b c d)
#     5over (a b c d e  f g h i j -- a b c d e  f g h i j  a b c d e)
#   currently Ndrop is not implemented
# @juggle imm_src_range ...imm_indices
#   pop values and push copied values.
#   ex:
#     # a b c d -- a b c d  c b a d
#     @juggle 4  0 1 2 3  2 1 0 3
# @empty out_var
#   1 if stack is empty

from typing import cast, Union, List, Dict, Callable
from tobf import Tobf
from base import Subsystem, separate_sign, calc_small_pair, SubsystemBase


class Subsystem_Stk(SubsystemBase):
    def __init__(self, tobf: Tobf, _name: str, args: List[Union[str, int]], instantiate: Callable[[int, Subsystem], int]):
        super().__init__(tobf, _name)
        self._main = cast(Tobf, self._main)

        if len(args) > 0:
            self._stk_size = self._main.valueof(args[0])

            if len(args) == 1:
                self.stk_tmps_ = 2
            elif args[1] == "dynamic":
                self.stk_tmps_ = 4
            else:
                self.stk_tmps_ = max(2, self._main.valueof(args[1]))

            self.reversed_ = "reversed" in args[2:]
        else:
            self._stk_size = 8
            self.stk_tmps_ = 2
            self.reversed_ = False

        self.resize(1 + self._stk_size * 2 + self.stk_tmps_)

        instantiate(self.size(), self)

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
            n = n * m
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
                "@pop", "@dup", "@swap", "@rot", "@over", "@add", "@sub", "@inc", "@dec",
                "@calc"]
            or len(args) > 0
                and name in [
                    "@push", "@copypush", "@pop",
                    "@juggle"]
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

    def put_juggling_dup(self, n: int = 1, c: int = 1, first=False, last=False):
        """starts and ends at first unused value.
           n: number of copies\n
           c: size of value
        """

        if c * 2 > self.size() - self._stk_size * 2:
            raise Exception(f"[stk:@calc {c}dup] requires {c * 2} stack-embedded tmps (currently {self.stk_tmps_})")

        m = n + 1

        if first and last and c == 1:
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

        # self._main.put("<<[" + (">>+" * m) + ("<<" * m) + "-]>" + (">>+" * n) + ">[" + ("<<" * m) + "+" + (">>" * m) + "-]")

        self._main.put(
            ("<<" + "[" + ((">>" * c + "+") * m) + ("<<" * c * m) + "-]") * c
            + (">>" * (c - 1)) + ">" + (">>+" * c * n) + ">" + (">>" * c)
            + ("<<" + "[" + ("<<" * c * m) + "+" + (">>" * c * m) + "-]") * c)

        if last:
            self.put_juggling_end()

    def put_juggling_rot(self, n: int = 3, c: int = 1, first=False, last=False):
        """starts and ends at first unused value.
           n: size of range\n
           c: size of value
        """

        if c * 2 > self.size() - self._stk_size * 2:
            raise Exception(f"[stk:@calc {c}rot] requires {c * 2} stack-embedded tmps (currently {self.stk_tmps_})")

        m = n - 1

        if first and last and c == 1:
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

        # self._main.put("<" + ("<<" * m) + "<[" + (">>" * n) + "+" + ("<<" * n) + "-]" + (">>[<<+>>-]" * n))

        self._main.put(
            # 2rot
            # 1 2  3 4  5 6 *x y
            ("<<" * c * n)
            #*1 2  3 4  5 6  x y
            # 1*2  3 4  5 6  x y
            + ("[" + (">>" * c * n) + "+" + ("<<" * c * n) + "-]" + ">>") * c
            # 1 2 *3 4  5 6  x y
            # 1 2  3*4  5 6  x y
            + ((("[" + ("<<" * c) + "+" + (">>" * c) + "-]" + (">>" * c)) * n) + ("<<" * (c * n - 1))) * c
            # 1 2  3*4  5 6  x y
            )

        if last:
            self.put_juggling_end()

    def put_juggling_over(self, c: int = 1, first=False, last=False):
        """starts and ends at first unused value.\n
           c: size of value
        """

        if c <= 0:
            args = ["0"]
        else:
            args = [str(c * 2)] + [str(i) for i in range(c * 2)] + [str(i) for i in range(c)]

        self.put_juggling_juggle(args, first=first, last=last)

    def put_juggling_juggle(self, args: List[str], first=False, last=False):
        """starts and ends at first unused value."""

        if len(args) == 0 or int(args[0]) == 0:
            if first and not last:
                self.put_juggling_start()

            if last and not first:
                self.put_juggling_end()

            return

        if len(list(filter(self._main.is_val, args))) != len(args):
            raise Exception(f"currently [stk:@juggle] accept only immediates.")

        src_size = self._main.valueof(args[0])

        if src_size <= 0:
            return

        src_stack = list(range(src_size))
        dst_stack = list(map(self._main.valueof, args[1:]))
        n_affected = max(len(src_stack), len(dst_stack)) + 2

        # current stack
        stack = list(src_stack) +  [-1] * (n_affected - len(src_stack))


        def clear():
            # clear values
            for i, v in enumerate(src_stack):
                if v not in dst_stack:
                    # ..., *v(N-size), 1, ..., at v(N-size + i), 1, ..., v(N)=empty, 0
                    self._main.put_at(i * 2, "[-]")
                    stack[i] = -1

        def is_placed(v: int) -> bool:
            """True if v does not require any additional move/copy.\n
                v: index in source as variable name.
            """

            if v not in dst_stack:
                return True

            for i, v2 in enumerate(dst_stack):
                if v2 == v and stack[i] != v:
                    return False

            return len(dst_stack) == n_affected - 1 or (v not in stack[len(dst_stack):])

        def get_tmps(excludes: List[int] = []) -> List[int]:
            """returns list of index"""
            return [i for i, v in enumerate(stack) if v == -1 and i not in excludes]

        def put_move(from_: int, to_: List[int]):
            """generates code and updates stack state\n
                from_, to_: index of stack starts at top.
            """

            self._main.put_move(f"#{from_ * 2}", [f"+#{i * 2}" for i in to_])

            v = stack[from_]
            
            for i in to_:
                stack[i] = v

            stack[from_] = -1

        def put_move_to_tmps(srcs: List[int], tmps_excludes: List[int] = []):
            for i, v in enumerate(srcs):
                tmps = get_tmps(tmps_excludes)
                put_move(v, [tmps[i]])

        def main():
            for v in src_stack:
                if is_placed(v):
                    continue

                dst_idxs = [i for i, v2 in enumerate(dst_stack) if v2 == v]
                dst_idxs_with_value = [i for i in dst_idxs if stack[i] != -1]

                # any destination address has value. copy required.
                if len(dst_idxs_with_value) != 0:
                    tmps = get_tmps(dst_idxs)

                    # not enough temporary space exist. never happen?
                    if len(tmps) < len(dst_idxs_with_value):
                        raise Exception(f"not implemented")

                    put_move_to_tmps(dst_idxs_with_value, tmps_excludes=dst_idxs)

                src_idx = stack.index(v)

                put_move(src_idx, dst_idxs)

        # end local funcs

        # ..., v(N-1), 1, *v(N)=empty, 0
        if first:
            self.put_juggling_start()

        # ..., *v(N-size), 1, ..., v(N)=empty, 0
        self._main.put("<" * src_size * 2)

        clear()
        main()

        # ..., *v(sizeof src), 1, ..., v(sizeof dst)=empty, 0
        # or
        # ..., v(sizeof dst), 1, ..., *v(sizeof src), 1, ..., v(N)=empty, 0
        self._main.put(">" * src_size * 2)

        if src_size < len(dst_stack):
            d = len(dst_stack) - src_size

            self._main.put(">+>" * d)

        if src_size > len(dst_stack):
            d = src_size - len(dst_stack)

            self._main.put("<-<" * d)

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

            for i, arg in enumerate(args):
                first = i == 0
                last = i + 1 == len(args)

                if arg in ["0dup", "0swap", "0rot", "0drop"]:
                    pass
                elif arg == "swap":
                    self.put_juggling_rot(2, 1, first=first, last=last)
                elif arg[1:] == "swap" and arg[0].isdigit():
                    self.put_juggling_rot(2, int(arg[0]), first=first, last=last)
                elif arg == "dup":
                    self.put_juggling_dup(1, 1, first=first, last=last)
                elif arg[1:] == "dup" and arg[0].isdigit():
                    self.put_juggling_dup(1, int(arg[0]), first=first, last=last)
                elif arg == "rot":
                    self.put_juggling_rot(3, 1, first=first, last=last)
                elif arg[1:] == "rot" and arg[0].isdigit():
                    self.put_juggling_rot(3, int(arg[0]), first=first, last=last)
                elif arg == "drop":
                    self.put_juggling_pop(None, first=first, last=last)
                elif arg == "over":
                    self.put_juggling_over(1, first=first, last=last)
                elif arg[1:] == "over" and arg[0].isdigit():
                    self.put_juggling_over(int(arg[0]), first=first, last=last)
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

            for i, arg in enumerate(args):                
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
            m = 1
            if len(args) > 0:
                if self._main.is_var(args[0]):
                    raise Exception(f"[stk:@dup] accepts only immediates for element size")

                m = self._main.valueof(args[0])

            if len(args) > 1:
                if self._main.is_var(args[1]):
                    raise Exception(f"[stk:@dup] for dynamic range is not implemented")

                n = self._main.valueof(args[1])

            if n <= 0 or m <= 0:
                return

            self.put_juggling_dup(n, m, first=True, last=True)

            return

        if name == "@swap":
            # self._main.put_at(self.offset(), ">>[>>]<<[<[>>+<<-] <<[>>+<<-] >>>>[<<<<+>>>>-] <[<<]]")
            # return

            if len(args) > 1:
                raise Exception(f"[stk:@swap/{len(args)}] is not implemented")

            name = "@rot"

            if len(args) == 1:
                args = [args[0], "2"]
            else:
                args = ["1", "2"]

        if name == "@rot":
            n = 3
            m = 1

            if len(args) > 0:
                if self._main.is_var(args[0]):
                    raise Exception(f"[stk:@rot] accepts only immediates for element size")

                m = self._main.valueof(args[0])

                args = args[1:]

                if m <= 0:
                    return

            if len(args) > 0:
                sign, arg = separate_sign(args[0])

                if self._main.is_var(arg):
                    if self.stk_tmps_ < 4:
                        raise Exception(f"[{self.name()}:@rot] for dynamic range requires at least 4 stack-embedded tmps")

                    if m != 1:
                        raise Exception(f"[{self.name()}:@rot] for dynamic range is implemented only for element_size=1")

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

            self.put_juggling_rot(n, m, first=True, last=True)

            return

        if name == "@over":
            if len(args) > 1:
                raise Exception(f"[stk:@over/{len(args)}] is not implemented")

            m = self._main.valueof(args[0]) if len(args) > 0 else 1

            self.put_juggling_over(m, first=True, last=True)

            return

        if name in ["@inc", "@dec"]:
            self.put_juggling_inc(name == "@dec", first=True, last=True)

            return

        if name == "@juggle":
            if len(args) == 0:
                raise Exception(f"[stk:@juggle/0] is not implemented")

            self.put_juggling_juggle(args, first=True, last=True)

            return

        raise Exception(f"wnknown ins: {name} {args}")
