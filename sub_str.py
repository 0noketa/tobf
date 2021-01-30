
# zasciiz string (no size-limitation)
# tmp, BOS, ...str, EOS, tmp, tmp, tmp, tmp
# init n
#   initializes for n bytes string
# clean
#   cleans all
# @clear
#   removes all chars
# @set ...literal
#   stores chars in every literal (can not include any of spaces. will be joined by single space)
# @+set literal
#   appends chars in literal (can not include any of spaces)
# @readln
#   reads string ends with EOL and set it without EOL. unsafe as gets() is.
# @+readln
#   reads string ends with EOL and append it without EOL. unsafe as gets() is.
# @readln n
# @+readln n
#   a bit safe version. input size is upto n bytes. currently does not stop at EOF.
# @write
#   writes string
# @writeln
#   writes string with EOL
# @write reversed
#   writes reversed string
# @writeln reversed
#   writes reversed string with EOL
# @=write ...literals
# @=write ...literals
# @=+write ...literals
# @=+write ...literals
#   set and writes string
# @copypush ...in_vals
#   appends copied chars to last.
# @push ...in_vals
#   appends chars to last.
# @pop
#   removes last char
# @pop ...out_vars
#   removes last chars. and stores to out_vars
# @drop
#   removes first char
# @drop ...out_vars
#   removes first chars. and stores to out_vars
# @move ...out_strs
#   moves all chars to out_strs
# @+move_reversed ...out_strs
#   moves all chars to out_strs in reversed order
# @len ...out_vars
#   count chars in bytes. result is uint(<256).


from typing import cast, Union, List, Tuple, Dict, Callable
from tobf import Tobf
from base import separate_sign, calc_small_pair, SubsystemBase


class Subsystem_Str(SubsystemBase):
    def __init__(self, tobf: Tobf, _name: str, args: List[Union[str, int]], get_addr: Callable[[int], int]):
        super().__init__(tobf, _name)
        self._main = cast(Tobf, self._main)

        if len(args) > 0:
            self._str_size = self._main.valueof(args[0])
        else:
            self._str_size = 16

        self.resize(self._str_size + 6)
        self.set_base(get_addr(self.size()))

        self.def_const("size", self._str_size)

    def put_clean(self, args: List[str]):
        if len(args) > 0 and args[0] == "fast":
            return

        self._main.put_at(self.offset(), ">>[>]<[[-]<]<")

    def put_set_char(self, v: int):
        """current_addr+1 as workspace. and moves to current_addr+1"""

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
                "@clear",
                "@readln", "@+readln", "@read", "@+read", "@write", "@writeln",
                "@pop", "@drop"]
            or len(args) > 0
                and name in [
                    "@push", "@copypush", "@set", "@+set", "@len",
                    "@move", "@+move", "@move_reversed", "@+move_reversed",
                    "@=write", "@=writeln", "@=+write", "@=+writeln",]
            or len(args) > 1
                and name in [
                    "@split", "@+split"]
            or super().has_ins(name, args))

    def put(self, name: str, args: List[Union[int, str]], tmps: List[int] = None):
        if name == "init":
            return

        if name == "clean":
            self.put_clean()
            return

        if name in ["@=write", "@=writeln"]:
            self.put("@set", args)
            self.put(f"@{name[2:]}", [])
            return

        if name in ["@=+write", "@=+writeln"]:
            self.put("@+set", args)
            self.put(f"@{name[3:]}", [])
            return

        if name == "@set":
            self.put("@clear", [])
            name = "@+set"

        if name in "@+set":
            self._main.put(">" * self.offset() + ">>[>]")

            for c in " ".join(args):
                self.put_set_char(ord(c))

            self._main.put("<[<]<" + "<" * self.offset())

            return

        if name == "@clear":
            self._main.put_at(self.offset(), ">>[>]<[[-]<]<")

            return

        if name in ["@readln", "@read"]:
            self.put("@clear", [])
            name = "@+readln"

        if name == "@+readln":
            if len(args) == 0:
                self._main.put_at(self.offset(), ">>[>],----------[++++++++++>,----------]<[<]<")

                return

            arg = args[0]

            if self._main.is_var(arg):
                self._main.put_at(arg, "[")
                self._main.put_at(self.offset(), ">>[>]>+<[<]<")
                self._main.put_at(arg, "-]")
            else:
                size = self._main.valueof(arg)
                self._main.put_at(self.offset(), ">>[>]>" + "+" * size +"<<[<]<")

            self._main.put_at(self.offset(),
                ">>[>]>[->>>+<<<<,"
                # 255
                + "+[-"
                # 26
                + ("----- ----- ----- ----- ----- -["
                    + "+++++ +++++ +++++ +++++ +++++ +") 
                + "----------[>>+>+<<<-]"
                # 26
                + "]"
                # 255
                + "]"
                + ">>[<<+>>-]>[<<<++++++++++>>>>-<[-]]>[<<<[-]>>>-]<<<[>+<-]>]<<<[<]<")

            return

        # uses 2 right tmp
        if name == "@+read":
            if len(args) == 0:
                self._main.put_at(self.offset(), ">>[>]>+<<[<]<")
            else:
                arg = args[0]

                if self._main.is_var(arg):
                    self._main.put_at(arg, "[")
                    self._main.put_at(self.offset(), ">>[>]>+<[<]<")
                    self._main.put_at(arg, "-]")
                else:
                    size = self._main.valueof(arg)
                    self._main.put_at(self.offset(), ">>[>]>" + "+" * size +"<<[<]<")

            self._main.put_at(self.offset(), ">>[>]>[-[>+<-]<,>>]<<[<]<")

            return

        if name == "@write":
            if len(args) > 0 and args[0] == "reversed":
                self._main.put_at(self.offset(), ">>[>]<[.<]<")
            else:
                self._main.put_at(self.offset(), ">>[.>]<[<]<")

            return

        if name == "@writeln":
            if len(args) > 0 and args[0] == "reversed":
                self._main.put_at(self.offset(), ">>[>]<[.<]++++++++++.[-]<")
            else:
                self._main.put_at(self.offset(), ">>[.>]++++++++++.[-]<[<]<")

            return

        if name in ["@push", "@copypush"]:
            if len(args) == 0:
                raise Exception("str:@push requires 1 arg")

            for arg in args:
                if arg == "input":
                    self._main.put_at(self.offset(), ">>[>],<<[<]<")

                    continue

                if self._main.is_var(arg):
                    addr = self._main.addressof(arg)

                    self._main.put_at(addr, "[")

                    if name == "@copypush":
                        self._main.put("+")

                    self._main.put_at(self.offset(), ">>[>]>+<<[<]<")
                    self._main.put_at(addr, "-]")
                    self._main.put_at(self.offset(), ">>[>]>[<+>-]<<[<]<")

                    if name == "@copypush":
                        self._main.put("[")
                        self._main.put_at(addr, "+")
                        self._main.put("-]")

                    continue

                v = self._main.valueof(arg)

                self._main.put(">" * self.offset() + ">>[>]")
                self.put_set_char(v)
                self._main.put("<<[<]<" + "<" * self.offset())

            return
        
        if name == "@pop":
            if len(args) == 0:
                self._main.put_at(self.offset(), ">>[>]<[[-]<[<]]<")

                return

            self.put_clear_dsts(args)

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(self.offset(), ">>[>]<[[>+<-]>[<<[<]<+>>[>]>-]<<[<]]<")
                self._main.put_at(self.offset(), "[")
                self._main.put_at(addr, "-" if sign == "-" else "+")
                self._main.put_at(self.offset(), "-]")

            return

        if name == "@drop":
            if len(args) == 0:
                self._main.put_at(self.offset(), ">>[-]>[[<+>-]>]<<[<]<")

                return

            self.put_clear_dsts(args)

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(self.offset(), ">>[<<+>>-]>[[<+>-]>]<<[<]<")
                self._main.put_at(self.offset(), "[")
                self._main.put_at(addr, "-" if sign == "-" else "+")
                self._main.put_at(self.offset(), "-]")

            return

        if name in ["@move", "@move_reversed", "@split"]:
            if name == "@split":
                args2 = args[1:]
            else:
                args2 = args

            for arg in args2:
                if not self._main.is_sub(arg, "str"):
                    raise Exception(f"[str:{name}] takes only str")

                arg_str: SubsystemBase = self._main.subsystem_by_alias(arg)

                arg_str.put("@clear", [])

            name = "@+" + name[1:]

        if name in ["@+move", "@+move_reversed"]:
            ins_pop = "@drop" if name == "@+move" else "@pop"

            self.put(ins_pop, [0])
            self._main.put("[")

            self._main.put("[")

            if len(set(args)) != len(args):
                raise Exception(f"[str:{name}] takes every str only once")

            for arg in args:
                if not self._main.is_sub(arg, "str"):
                    raise Exception(f"[str:{name}] takes only str")

                arg_str: SubsystemBase = self._main.subsystem_by_alias(arg)
        
                if arg_str == self:
                    raise Exception("[str:@move] can not move to the same str")

                self._main.put_at(arg_str.offset(), ">>[>]>+<<[<]<")

            self._main.put("-]")

            for arg in args:
                arg_str: SubsystemBase = self._main.subsystem_by_alias(arg)
        
                self._main.put_at(arg_str.offset(), ">>[>]>[<+>-]<[<]<")

            self.put(ins_pop, [0])
            self._main.put("]")

            return

        if name == "@+split":
            sep = args[0]

            if not self._main.is_val(sep):
                raise Exception(f"first arg of [str:{name}] should be immediate")

            n_sep = self._main.valueof(sep)
            args = args[1:]

            for arg in args:
                arg_str: SubsystemBase = self._main.subsystem_by_alias(arg)

                arg_str.put("@clear", [])

            for arg in args:
                arg_str: SubsystemBase = self._main.subsystem_by_alias(arg)

                """
                inc it
                while it
                    clear it
                    self:drop self:tmp_L
                    if self:L
                        sub self:L sep
                        if self:L
                            add self:L sep
                            self:@push self:L
                            inc it
                """
                self._main.put("+[[-]")

                # safe version of self.put("@drop", [self.offset()])
                self._main.put_at(self.offset(), "[-]>>[<<+>>-]>[[<+>-]>]<<[<]<")

                n, m = calc_small_pair(n_sep, 1)
                if m == 1:
                    self._main.put_at(self.offset(), "[" + ("-" * n) + "[" + ("+" * n))
                else:
                    self._main.put_at(self.offset(), "[>" + ("+" * n) + "[<" + ("-" * m) + ">-]<[>" + ("+" * n) + "[<" + ("+" * m) + ">-]<" )

                # safe version of arg_str.put("@push", [self.offset()])
                self._main.put_at(self.offset(), "[")
                self._main.put_at(arg_str.offset(), ">>[>]>+<<[<]<")
                self._main.put_at(self.offset(), "-]")
                self._main.put_at(arg_str.offset(), ">>[>]>[<+>-]<<[<]<")

                self._main.put("+")
                self._main.put_at(self.offset(), "[-]]]")
                self._main.put("]")

            return

        if name == "@len":
            self.put_clear_dsts(args)

            self._main.put_at(self.offset(), ">>[[>]<[>+<-]<[<]<+>>]>[[<+>-]>]<<[<]<[")

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(addr, "-" if sign == "-" else "+")

            self._main.put_at(self.offset(), "-]")

            return

        raise Exception(f"wnknown ins: {name} {args}")
