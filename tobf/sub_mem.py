
# subsystem mem
# memory layout:
#   0, value0, 0, value1, ..., value(N-1), 0, 0, 0, 0
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



    def mem2_clean(self, fast=False):
        # + eos
        size = self.mem_size_ + 2

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

        self.mem_size_ = _cells
        _size = (_cells + 2) * 2
        self.resize(_size)

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
            return self.offset(1)
        if value == "last":
            return self.offset(1 + (self.mem_size_ - 1) * 2)

        if self._main.is_val(value):
            idx = self._main.valueof(value)

            if idx in range(self.mem_size_):
                return self.offset(1 + idx * 2)

        raise Exception(f"can not get address of {value}")

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
        if len(args) > 0 and self._main.valueof(args[0]) != self.mem_size_:
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

            value = self._main.valueof(args[0])

            for dst in args[1:]:
                dst_sign, dst = separate_sign(dst)

                if self._main.is_val(dst):
                    idx = self._main.valueof(dst)
                    dst_addr = self.offset(idx * 2 + 1)

                    self._main.put_set(value, f"{dst_sign}#{dst_addr}")
                elif self._main.is_var(dst):
                    dst_addr = self._main.addressof(dst)
                    tmp = self._main.get_nearest_tmp(tmps, [self.offset()])

                    self._main.put_copy(dst_addr, [f"+#{self.offset(2)}"])

                    self._main.put(">" * self.offset())
                    self._main.put(""">>[[>>+<<-]+>>-]<""")

                    self._main.put_set(value, f"{dst_sign}#0")

                    self._main.put("""<[-<<]""")
                    self._main.put("<" * self.offset())

            return

        if ins_name in ["@w_move", "@w_copy"]:
            if not self._main.is_var(args[0]):
                raise Exception(f"[mem:{ins_name} val ...out] is not implemented")

            addr = self._main.addressof(args[0])

            if ins_name == "@w_copy":
                self._main.put_copy(addr, [f"+#{self.offset(4)}"])
            else:
                self._main.put_move(addr, [f"+#{self.offset(4)}"])

            out_vars = args[1:]
            tmp = self._main.get_nearest_tmp(tmps, [addr])

            for i in range(len(out_vars)):
                name = out_vars[i]
                sign, name = separate_sign(name)

                if self._main.is_var(name):
                    dst_addr = self._main.addressof(name)

                    self._main.put_copy(dst_addr, [f"+#{self.offset(2)}"])

                    # for next destination
                    if i < len(out_vars) - 1:
                        self._main.put_copy(self.offset(4), [f"+#{self.offset()}"])

                    self._main.put(">" * self.offset())
                    self._main.put(""">>[->>[>>+<<-]<<[>>+<<-]+>>]""")
                    if sign == "":
                        self._main.put("""<[-]>""")
                    self._main.put(""">>[<<<""")
                    self._main.put("-" if sign == "-" else "+")
                    self._main.put(""">>>-]<<<<[-<<]""")
                    self._main.put("<" * self.offset())

                    if i < len(out_vars) - 1:
                        self._main.put_move(tmp, [f"+#{self.offset(4)}"])

                    continue

                if self._main.is_val(name):
                    dst_idx = self._main.valueof(name)

                    self._main.put_at(self.offset(4), "[")
                    self._main.put_at(self.offset(1 + dst_idx * 2), "+")

                    if i + 1 < len(out_vars): 
                        self._main.put_at(self.offset(2), "+")

                    self._main.put_at(self.offset(4), "-]")

                    if i + 1 < len(out_vars): 
                        self._main.put_move(self.offset(2), [f"+#{self.offset(4)}"])

                    continue

            return

        if ins_name in ["@r_move", "@r_copy"]:
            src = args[0]

            if len(list(filter(self._main.is_var, args[1:]))) != len(args[1:]):
                raise Exception(f"unknown instruction: [mem:{ins_name}] with non-variable destinations")

            # static addressing
            if self._main.is_val(src):
                idx = self._main.valueof(src)
                addr = self.offset(idx * 2 + 1)

                if ins_name == "@r_copy":
                    self._main.put_copy(addr, args[1:])
                else:
                    self._main.put_move(addr, args[1:])
            elif self._main.is_var(src):
                idx_addr = self._main.addressof(src)

                self._main.put_copy(idx_addr, [f"+#{self.offset(2)}"])

                self._main.put(">" * self.offset())
                self._main.put(""">>[[>>+<<-]+>>-]""")
                if ins_name == "@r_copy":
                    self._main.put("""<[>>>+<<<-]>>>[<<+<+>>>-]<<""")
                else:
                    self._main.put("""<[>+<-]>""")
                self._main.put("""<<[->>>>[<<+>>-]<<<<<<]>>>>[<<+>>-]<<<<""")
                self._main.put("<" * self.offset())

                self._main.put_move(self.offset(2), args[1:])

            return

        raise Exception(f"error unknown: {ins_name} {args}")

