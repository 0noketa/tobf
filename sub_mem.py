
# subsystem mem
# init imm
#   initialize imm bytes of random-access memory. only once works. imm <= 256.
# clean imm
#   works only after init. clean random-access memory area.
#   init and resb can be used after clean again.
# clean imm fast
#   fast and short version.
#   doesnt clear values. clears just 1 byte in every cell.
#   works when every values stored in memory was 0.
#   on highly optimized bf implementations, this version will not be fast. just short.
# @set imm_value ...addresses
#   set constant or use command to random-access memory 
#   imm_value:
#     any digits
#       set constant
#     input
#       set input data. 
#     print
#       print data.
#   address:
#     +address or -address
#       add or sub. sign can exists only once and works only with digits value.
#     digits
#       address
#     var_name
#       uses pointer variable
# @w_move in_var ...addresses
#   set value from variable to random-access memory. currently addresses accept only variable.
# @w_moveadd in_var ...addresses
# @w_movesub in_var ...addresses
# @w_copy in_var ...addresses
# @w_copyadd in_var ...addresses
# @w_copysub in_var ...addresses
# @r_move in_var ...addresses
#   move value from  random-access memory to variable. address is the same as @w_move.
# @r_moveadd address ...out_vars
# @r_movesub address ...out_vars
# @r_copy address ...out_vars
# @r_copyadd address ...out_vars
# @r_copysub address ...out_vars

from typing import cast, Union, List, Tuple, Dict, Callable
from tobf import Tobf
from base import separate_sign, SubsystemBase


class Subsystem_Memory(SubsystemBase):
    """random-access memory area"""

    def addressof(self, addr):
        return self._main.addressof(addr) if type(addr) == str else addr


    def inc_or_dec(self, c, n):
        for i in range(n // 16):
            self._main.put(c * 8 + " " + c * 8)

        m = n % 16
        if m == 0:
            pass
        elif m > 8:
            m = m % 8
            self._main.put(c * 8 + " " + c * m)
        else:
            self._main.put(c * m)

    def inc(self, n):
        self.inc_or_dec("+", n)

    def dec(self, n):
        self.inc_or_dec("-", n)

    def clear(self, v):
        self._main.put_at(v, "[-]")

    def moveadd_global(self, in_addr, out_addrs):
        self._main.put_at(in_addr, "[")

        for out_addr in out_addrs:
            self._main.put_at(out_addr, "+")

        self._main.put_at(in_addr, "-]")

    def load_global(self, addr):
        self._main.put_at(addr, "[")
        self._main.put("+")
        self._main.put_at(addr, "-]")

    def store_it(self, out_globals, out_vars):
        for out_var in out_vars:
            sign, out_var = separate_sign(out_var)

            if sign == "":
                v = self._main.addressof(out_var)

                self.clear(v)

        self._main.put("[")

        for out_global in out_globals:
            self._main.put_at(out_global, "+")

        for out_var in out_vars:
            sign, out_var = separate_sign(out_var)
            
            addr = self._main.addressof(out_var)

            self._main.put_at(addr, "-" if sign == "-" else "+")

        self._main.put("-]")

    def mem2_clean(self, fast=False):
        if not self._mem_initialized:
            return

        # + eos
        size = self._mem_size + 2

        if fast:
            return

        self._main.put(">" * self.offset())

        for i in range(size):
            self._main.put("[-]>" * 2)

        self._main.put("<" * self.offset(size * 2))

    def __init__(self, tobf: Tobf, _name: str, args: List[Union[str, int]], instantiate: Callable[[int, SubsystemBase], int]):
        super().__init__(tobf, _name)
        self._main = cast(Tobf, self._main)

        if len(args) > 0:
            _cells = self._main.valueof(args[0])
        else:
            _cells = 16

        self._mem_size = _cells
        _size = (_cells + 2) * 2
        self.resize(_size)

        instantiate(self.size(), self)

        self.def_const("size", self._mem_size)

    def has_ins(self, name: str, args: list) -> bool:
        return (name in [
                "clean",
                "@clear"]
            or len(args) == 1
                and name == "init"
            or len(args) > 1
                and name in [
                    "@set",
                    "@w_copy", "@w_move",
                    "@r_copy", "@r_move",
                    "@w_copy", "@w_copyadd", "@w_copysub",
                    "@w_move", "@w_moveadd", "@w_movesub",
                    "@r_copy", "@r_copyadd", "@r_copysub",
                    "@r_move", "@r_moveadd", "@r_movesub"]
            or super().has_ins(name, args))

    def put_clean(self, args: list):
        if len(args) > 0 and self._main.valueof(args[0]) != self._mem_size:
            raise Exception(f"error: mem:@clean with different size")
            return

        self.mem2_clean(len(args) > 1 and args[1] == "fast")

    def put(self, ins_name: str, args: list, tmps: List[int]):
        if ins_name == "init":
            return

        if ins_name == "clean":
            self.put_clean(args)
            return

        if ins_name == "@clear":
            self.mem2_clean(args)
            return

        if (len(args) < 2
            and ins_name in [
                "@set", "@w_copy", "@w_move",
                "@w_copy", "@w_copyadd", "@w_copysub",
                "@w_move", "@w_moveadd", "@w_movesub",
                "@r_copy", "@r_copyadd", "@r_copysub",
                "@r_move", "@r_moveadd", "@r_movesub"
                ]):
            raise Exception(f"error: {ins_name} {args}")

        # aliases
        if ins_name in ["@w_copy", "@w_move"]:
            if self._main.is_val(args[0]):
                ins_name = "@set"

        if ins_name in ["@w_copyadd", "@w_copysub"]:
            sign = "+" if ins_name == "@w_copyadd" else "-"
            ins_name = "@w_copy"
            args = [args[0]] + [sign + x for x in args[1:]]

        if ins_name in ["@w_moveadd", "@w_movesub"]:
            sign = "+" if ins_name == "@w_moveadd" else "-"
            ins_name = "@w_move"
            args = [args[0]] + [sign + x for x in args[1:]]

        if ins_name in ["@r_copyadd", "@r_copysub"]:
            sign = "+" if ins_name == "@r_copyadd" else "-"
            ins_name = "@r_copy"
            args = [args[0]] + [sign + x for x in args[1:]]

        if ins_name in ["@r_moveadd", "@r_movesub"]:
            sign = "+" if ins_name == "@r_moveadd" else "-"
            ins_name = "@r_move"
            args = [args[0]] + [sign + x for x in args[1:]]

        if ins_name == "@set":
            if self._main.is_var(args[0]):
                raise Exception("[mem:@set var ...out] is not implemented")

            def put_value(value):
                if value == "input":
                    self._main.put(",")
                elif value == "print":
                    self._main.put(".")
                else:
                    if sign == "":
                        self._main.put("[-]")

                    value = int(value)
                    if sign == "-":
                        self.dec(value)
                    else:
                        self.inc(value)

            value = self._main.valueof(args[0])

            for address in args[1:]:
                sign, address = separate_sign(address)

                if not self._main.is_var(address):
                    address = self._main.valueof(address)

                    self._main.put(">" + self.offset(address * 2 + 1))

                    put_value(value) 
                    
                    self._main.put("<" * self.offset(address * 2 + 1))
                else:
                    addr = self._main.addressof(address)
                    tmp = self._main.get_nearest_tmp(tmps, [self.offset()])

                    self._main.put_move(addr, [f"+#{tmp}"])

                    self._main.put_at(tmp, "[")
                    self._main.put_at(addr, "+")

                    self._main.put_at(self.offset(2), "+")
                    self._main.put_at(tmp, "-]")

                    self._main.put(">" * self.offset())
                    self._main.put(""">>[[>>+<<-]+>>-]<""")
                    put_value(value)
                    self._main.put("""<[-<<]""")
                    self._main.put("<" * self.offset())

            return

        if ins_name in ["@w_move", "@w_copy"]:
            if not self._main.is_var(args[0]):
                raise Exception(f"[mem:{ins_name} val ...out] is not implemented")

            addr = self._main.addressof(args[0])

            if ins_name == "@w_copy":
                self.load_global(addr)

                self.store_it([self.offset(4)], ["+" + args[0]])
            else:
                self._main.put_at(addr, "[")
                self._main.put_at(self.offset(4), "+")
                self._main.put_at(addr, "-]")

            out_vars = args[1:]

            for i in range(len(out_vars)):
                name = out_vars[i]
                sign, name = separate_sign(name)

                addr = self._main.addressof(name)
                self.load_global(addr)

                self.store_it([self.offset(2)], ["+" + name])

                # for next destination
                if i < len(out_vars) - 1:
                    self.moveadd_global(self.offset(4), [self.offset()])
                    self.moveadd_global(self.offset(), [0, self.offset(4)])

                self._main.put(">" * self.offset())
                self._main.put(""">>[->>[>>+<<-]<<[>>+<<-]+>>]""")
                if sign == "":
                    self._main.put("""<[-]>""")
                self._main.put(""">>[<<<""")
                self._main.put("-" if sign == "-" else "+")
                self._main.put(""">>>-]<<<<[-<<]""")
                self._main.put("<" * self.offset())

                if i < len(out_vars) - 1:
                    self.moveadd_global(0, [self.offset(4)])

            return

        if ins_name in ["@r_move", "@r_copy"]:
            address = args[0]

            # clear dst of move/copy
            for name in args[1:]:
                sign, name = separate_sign(name)

                if sign == "":
                    v = self._main.addressof(name)

                    self.clear(v)

            # static addressing
            if not self._main.is_var(address):
                address = self._main.addressof(address)
                address = self.offset(address * 2 + 1)

                if ins_name == "@r_copy":
                    out_globals = [address]
                    out_vars = args[1:]
                    last = ""
                else:
                    out_globals = []
                    out_vars = args[1:-1]
                    last = args[-1]

                # copy
                if len(out_vars) > 1:
                    self.load_global(address)

                    self.store_it(out_globals, out_vars)

                # move                
                if last != "":
                    sign, name = separate_sign(last)

                    v = self._main.addressof(name)

                    self._main.put_at(address, "[")
                    self._main.put_at(v, "-" if sign == "-" else "+")
                    self._main.put_at(address, "-]")
            else:
                v = self._main.addressof(address)

                self.load_global(v)

                self.store_it([self.offset(2)], ["+" + address])

                self._main.put(">" * self.offset())
                self._main.put(""">>[[>>+<<-]+>>-]""")
                if ins_name == "@r_copy":
                    self._main.put("""<[>>>+<<<-]>>>[<<+<+>>>-]<<""")
                else:
                    self._main.put("""<[>+<-]>""")
                self._main.put("""<<[->>>>[<<+>>-]<<<<<<]>>>>[<<+>>-]<<<<""")
                self._main.put("<" * self.offset())

                if False:  # ex: from set
                    self._main.put(">" * self.offset())
                    self._main.put(""">>[[>>+<<-]+>>-]<""")
                    put_value(value)
                    self._main.put("""<[-<<]""")
                    self._main.put("<" * self.offset())


                self._main.put_at(self.offset(2), "[")

                for name in args[1:]:
                    sign, name = separate_sign(name)
                    addr = self._main.addressof(name)

                    self._main.put_at(addr, "-" if sign == "-" else "+")

                self._main.put_at(self.offset(2), "-]")

            return

        raise Exception(f"error unknown: {ins_name} {args}")

