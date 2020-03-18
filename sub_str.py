
# zasciiz string (no size-limitation)
# tmp, BOS, ...str, EOS, tmp
# init n
#   initializes for n bytes string
# clean
#   cleans all
# @clear
#   removes all chars
# @set ...literal
#   stores chars in every literal (can not include any of spaces. will be joined by single space)
# @+set literal
#   alias of @set+ . any of them will be renamed or removed.
# @set+ literal
#   appends chars in literal (can not include any of spaces)
# @readln
#   reads string ends with EOL and set it without EOL. unsafe as gets() in C.
# @readln+
#   reads string ends with EOL and append it without EOL. unsafe as gets() in C.
# @readln n
#   safe version. input size is upto n bytes. not implemented.
# @readln+ n
#   safe version. input size is upto n bytes. not implemented.
# @write
#   writes string
# @writeln
#   writes string with EOL
# @write reversed
#   writes reversed string
# @writeln reversed
#   writes reversed string with EOL
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
# @len ...out_vars
#   count chars in bytes. result is uint(<256).



from base import separate_sign, calc_small_pair, SubsystemBase, Mainsystem


class Subsystem_Str(SubsystemBase):
    def __init__(self, _name="str"):
        super().__init__(_name)
        self._str_initialized = False
        self._str_size = 0
    def copy(self, _name):
        r = super().copy(_name)
        r._str_initialized = self._str_initialized
        r._str_size = self._str_size

        return r

    def str_init(self, _ssize=16):
        if not self._str_initialized:
            self._str_size = _ssize
            self.resize(self._str_size + 4)
            self._str_initialized = True

    def str_clean(self):
        if self._str_initialized:
            self._main.put_with(self.offset(), ">>[>]<[[-]<]<")

    def put_init(self, args: list):
        if len(args) > 0:
            _size = self._main.valueof(args[0])
            self.str_init(int(_size))
        else:
            self.str_init()

    def put_set_char(self, v: int):
        """current_addr+1 as workspace. and moves to current_addr+1"""

        n, m = calc_small_pair(v, 1)

        if m == 1 or n * m < n + m + 5:
            self._main.put("+" * n + ">")
        else:
            self._main.put(">" + "+" * n + "[<" + "+" * m + ">-]")


    def has_ins(self, name: str, args: list) -> bool:
        return (name in [
                "init", "clean",
                "@clear",
                "@readln", "@readln+", "@+readln", "@write", "@writeln",
                "@pop", "@drop"]
            or len(args) > 0
                and name in ["@push", "@copypush", "@set", "@set+", "@+set", "@len"]
            or super().has_ins(name, args))

    def put(self, name: str, args: list):
        if name == "init":
            self.put_init(args)
            return

        if name == "clean":
            self.str_clean()
            return

        if name == "@set":
            self.put("@clear", [])
            name = "@+set"

        if name in "@+set":
            self._main.put(">" * self.offset() + ">>[>]")

            _first = True
            for arg in args:
                if _first:
                    arg2 = arg
                    _first = False
                else:
                    arg2 = " " + arg

                for c in arg2:
                    self.put_set_char(ord(c))

            self._main.put("<[<]<" + "<" * self.offset())

            return

        if name == "@clear":
            self._main.put_with(self.offset(), ">>[>]<[[-]<]<")

            return

        if name == "@readln":
            self.put("@clear", [])
            name = "@+readln"

        if name in "@+readln":
            if len(args) == 0:
                self._main.put_with(self.offset(), ">>[>],----------[++++++++++>,----------]<[<]<")

                return

            raise Exception("str:@readln/1 is stub")

            for arg in args:
                if self._main.is_var(arg):
                    pass

            return

        if name == "@write":
            if len(args) > 0 and args[0] == "reversed":
                self._main.put_with(self.offset(), ">>[>]<[.<]<")
            else:
                self._main.put_with(self.offset(), ">>[.>]<[<]<")

            return

        if name == "@writeln":
            if len(args) > 0 and args[0] == "reversed":
                self._main.put_with(self.offset(), ">>[>]<[.<]++++++++++.[-]<")
            else:
                self._main.put_with(self.offset(), ">>[.>]++++++++++.[-]<[<]<")

            return

        if name in ["@push", "@copypush"]:
            if len(args) == 0:
                raise Exception("str:@push requires 1 arg")

            for arg in args:
                if arg == "input":
                    self._main.put_with(self.offset(), ">>[>],<<[<]<")

                    continue

                if self._main.is_var(arg):
                    addr = self._main.addressof(arg)

                    self._main.put_with(addr, "[")

                    if name == "@copypush":
                        self._main.put("+")

                    self._main.put_with(self.offset(), ">>[>]>+<<[<]<")
                    self._main.put_with(addr, "-]")
                    self._main.put_with(self.offset(), ">>[>]>[<+>-]<<[<]<")

                    if name == "@copypush":
                        self._main.put("[")
                        self._main.put_with(addr, "+")
                        self._main.put("-]")

                    continue

                v = self._main.valueof(arg)

                self._main.put(">" * self.offset() + ">>[>]")
                self.put_set_char(v)
                self._main.put("<<[<]<" + "<" * self.offset())

            return
        
        if name == "@pop":
            if len(args) == 0:
                self._main.put_with(self.offset(), ">>[>]<[[-]<[<]]<")

                return

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                if sign == "":
                    self._main.put_with(addr, "[-]")

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_with(self.offset(), ">>[>]<[[>+<-]>[<<[<]<+>>[>]>-]<<[<]]<")
                self._main.put_with(self.offset(), "[")
                self._main.put_with(addr, "-" if sign == "-" else "+")
                self._main.put_with(self.offset(), "-]")

            return

        if name == "@drop":
            if len(args) == 0:
                self._main.put_with(self.offset(), ">>[-]>[[<+>-]>]<<[<]<")

                return

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                if sign == "":
                    self._main.put_with(addr, "[-]")

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_with(self.offset(), ">>[<<+>>-]>[[<+>-]>]<<[<]<")
                self._main.put_with(self.offset(), "[")
                self._main.put_with(addr, "-" if sign == "-" else "+")
                self._main.put_with(self.offset(), "-]")

            return

        if name == "@len":
            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                if sign == "":
                    self._main.put_with(addr, "[-]")

            self._main.put_with(self.offset(), ">>[[>]<[>+<-]<[<]<+>>]>[[<+>-]>]<<[<]<[")

            for arg in args:
                sign, addr0 = separate_sign(arg)
                addr = self._main.addressof(addr0)

                self._main.put_with(addr, "-" if sign == "-" else "+")

            self._main.put_with(self.offset(), "-]")

            return

        raise Exception(f"wnknown ins: {name} {args}")
