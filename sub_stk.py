
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
# @empty out_var

from base import separate_sign, calc_small_pair, SubsystemBase, Mainsystem


class Subsystem_Stk(SubsystemBase):
    def __init__(self, _name="stk"):
        super().__init__(_name)
        self._stk_initialized = False
        self._stk_size = 0
    def copy(self, _name):
        r = super().copy(_name)
        r._stk_initialized = self._stk_initialized
        r._stk_size = self._stk_size

        return r

    def stk_init(self, _ssize=16, dyn=False):
        if not self._stk_initialized:
            self._stk_size = _ssize
            self.resize(self._stk_size * 2 + (5 if self.dyn else 3))
            self._stk_initialized = True

    def stk_clean(self):
        if self._stk_initialized:
            self._main.put_at(self.offset(), ">>[>>]<<[-<[-]<]")

    def put_init(self, args: list):
        if len(args) > 0:
            _size = self._main.valueof(args[0])
            self.dyn = len(args) > 1 and args[1] == "dynamic"
            self.stk_init(int(_size))
        else:
            self.stk_init()

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
                "@pop", "@dup", "@swap", "@rot", "@add", "@sub", "@inc", "@dec"]
            or len(args) > 0
                and name in [
                    "@push", "@copypush", "@pop"]
            or super().has_ins(name, args))

    def put(self, name: str, args: list):
        if name == "init":
            self.put_init(args)
            return

        if name == "clean":
            self.stk_clean()
            return

        if name == "@clear":
            self._main.put_at(self.offset(), ">>[>>]<<[-<[-]<]")

            return

        if name in ["@push", "@copypush"]:
            if len(args) == 0:
                raise Exception("str:@push requires 1 arg")

            for arg in args:
                if arg == "input":
                    self._main.put_at(self.offset(), ">>[>>]+<,<[<<]")

                    continue

                if self._main.is_var(arg):
                    addr = self._main.addressof(arg)

                    self._main.put_at(addr, "[")

                    if name == "@copypush":
                        self._main.put("+")

                    self._main.put_at(self.offset(), ">>[>>]<+<[<<]")
                    self._main.put_at(addr, "-]")

                    self._main.put_at(self.offset(), ">>[>>]+[<<]")

                    if name == "@copypush":
                        self._main.put("[")
                        self._main.put_at(addr, "+")
                        self._main.put("-]")

                    continue

                v = self._main.valueof(arg)

                self._main.put(">" * self.offset() + ">>[>>]<")
                self.put_set_char(v)
                self._main.put("+[<<]" + "<" * self.offset())

            return

        if name == "@pop":
            if len(args) == 0:
                self._main.put_at(self.offset(), ">>[>>]<<[-<[-]<[<<]]")

                return

            self.put_clear_dsts(args)

            for arg in args:
                if arg == "print":
                    self._main.put_at(self.offset(), ">>[>>]<<[-<.[-]<[<<]]")

                    continue

                if not self._main.is_var(arg):
                    raise Exception(f"[@pop/n] with unknown arg")

                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(self.offset(), ">>[>>]<<[ <[ >[<<]")
                self._main.put_at(addr, "-" if sign == "-" else "+")
                self._main.put_at(self.offset(), ">>[>>]<<<-] >-<<[<<]]")

            return

        if name == "@empty":
            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(addr, "[-]+")

            self._main.put_at(self.offset(), ">>[<<")
            self._main.put("+")
            self._main.put_at(self.offset(), ">>-]<<")

            self._main.put("[")

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_at(addr, "-")

            self._main.put_at(self.offset(), ">>+<<")

            self._main.put("-]")

            return

        if name in ["@add", "@sub"]:
            o = "+" if name == "@add" else "-"
            self._main.put_at(self.offset(), ">>[>>]<<[<[<<" + o + ">>-]>-<<[<<]]")

            return

        if name == "@dup":
            n = 1
            if len(args) == 1:
                if self._main.is_var(args[0]):
                    raise Exception(f"[stk:@dup] for dynamic range is not implemented")

                n = self._main.valueof(args[0])
            elif len(args) > 0:
                raise Exception(f"[stk:@dup/{len(args)}] is not implemented")


            if n < 1:
                return

            m = n + 1
            self._main.put_at(self.offset(), ">>[>>]<<[ <[" + (">>+" * m) + ("<<" * m) + "-]>" + (">>+" * n) + ">[" + ("<<" * m) + "+" + (">>" * m) + "-]< [<<]]")
            # self._main.put_at(self.offset(), ">>[>>]<<[ [>>+>>+<<<< <[>>+>>+<<<<-]>-] >>>>[<<<<+>>>> <[<<<<+>>>>-]>-] <<<<[<<] ]")

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

                    self._main.put_at(addr, "[-[+ [")

                    if sign != "-":
                        self._main.put("+")

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
                        self._main.put("[")
                        self._main.put_at(addr, "+")
                        self._main.put("-]")

                    return

                n = self._main.valueof(arg)

            if n < 2:
                return
            m = n - 1
            self._main.put_at(self.offset(), ">>[>>]<<[" + ("<<" * m) + "<[" + (">>" * n) + "+" + ("<<" * n) + "-]" + (">>[<<+>>-]" * n) + "<[<<]]")
            # self._main.put_at(self.offset(), ">>[>>]<<[ << << <[>> >> >>+<< << <<-] >>[<<+>>-] >>[<<+>>-] >>[<<+>>-] <[<<]]")

            return

        if name in ["@inc", "@dec"]:
            o = "+" if name == "@inc" else "-"
            self._main.put_at(self.offset(), ">>[>>]<<[<" + o + ">[<<]]")

            return

        raise Exception(f"wnknown ins: {name} {args}")
