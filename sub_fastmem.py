
# smallest array with fast & largest code (<=256 elements)
#   currently fastmem is more orthogonal than mem. every combination of args work fine. mem should be rewritten.
#   do not use for large(>=16) array. code size will easily become *10 .. *100 or more.
#   will not be fast on optimized envirionments.
# init n
#   initializes for n cells
# init n n_tmps
#   uses additional workspace (some instruction require upto 2 cells)
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

from base import separate_sign, calc_small_pair, SubsystemBase, Mainsystem


class Subsystem_FastMem(SubsystemBase):
    def __init__(self, _name="fastmem"):
        super().__init__(_name)
        self._mem_initialized = False
        self._mem_size = 0
        self.tmps = 0
    def copy(self, _name):
        r = super().copy(_name)
        r._stk_initialized = self._mem_initialized
        r._mem_size = self._mem_size

        return r

    def mem_init(self, _size=16):
        if not self._mem_initialized:
            self._mem_size = _size
            self.resize(self._mem_size + self.tmps)
            self._mem_initialized = True

    def mem_clean(self):
        if self._mem_initialized:
            self._main.put_at(self.offset(), "[-]>" * self._size)

    def put_init(self, args: list):
        if len(args) > 0:
            _size = self._main.valueof(args[0])
            self.tmps = int(args[1]) if len(args) > 1 else 0
            self.mem_init(int(_size))
        else:
            self.tmps = 0
            self.mem_init()

    def put_clear_dsts(self, out_vars: list):
        """clear destinations without sign."""

        for out_var in out_vars:
            sign, addr0 = separate_sign(out_var)
            addr = self._main.addressof(addr0)

            if sign == "":
                self._main.put_at(addr, "[-]")

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

    def put(self, name: str, args: list):
        name0 = name

        if name == "init":
            self.put_init(args)
            return

        if name == "clean":
            self.mem_clean()
            return

        if name == "@clear":
            self._main.put_at(self.offset(), ("[-]>" * self._size) + ("<" * self._size))

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

                if sign != "-" and self.tmps == 0:
                    raise Exception(f"tryed to copy both mem-cell and index but additional workspace was disabled")

                for i in range(self._size):
                    self._main.put("+")
                    self._main.put_at(addr, "[-")
                    self._main.put("-")

                for i in range(self._size - 1, -1, -1):
                    self._main.put_at(addr, "[-]]")

                    self._main.put("[")
                    put_read(i, dsts, copy, addr)

                    if sign != "-":
                        self._main.put_at(self.offset(self._size), "+" * i)

                    self._main.put("[-]]")


                if sign != "-":
                    self._main.put_at(self.offset(self._size), "[")
                    self._main.put_at(addr, "+")
                    self._main.put_at(self.offset(self._size), "-]")

            return

        if name == "@w_move":
            src = args[0]
            dsts = args[1:]

            sign, v = separate_sign(src)

            if self._main.is_val(v):
                n = self._main.valueof(v)

                for dst in dsts:
                    dst_sign, dst = separate_sign(dst)

                    if self._main.is_val(dst):
                        m = self._main.valueof(dst)

                        if name_suffix == "":
                            o = "[-]" + ("+" * n)
                        else:
                            o = "+" if name_suffix == "add" else "-"
                            o = (o * n)

                        self._main.put_at(self.offset(m), o)
                    elif self._main.is_var(dst):
                        dst_addr = self._main.addressof(dst)

                        if dst_sign != "-" and self.tmps == 0:
                            raise Exception(f"at [fastmem:{name0}]. tryed to save destination pointer. but no workstpace enabled.")

                        for i in range(self._size):
                            self._main.put("+")
                            self._main.put_at(dst_addr, "[-")
                            self._main.put("-")

                        for i in range(self._size - 1, -1, -1):
                            self._main.put_at(dst_addr, "[-]]")

                            self._main.put("[")

                            if name_suffix == "":
                                o = "[-]" + ("+" * n)
                            else:
                                o = "+" if name_suffix == "add" else "-"
                                o = (o * n)

                            self._main.put_at(self.offset(i), o)

                            if dst_sign != "-":
                                self._main.put_at(self.offset(self._size), "+" * i)

                            self._main.put("[-]]")

                        if dst_sign != "-":
                            self._main.put_at(self.offset(self._size), "[")
                            self._main.put_at(dst_addr, "+")
                            self._main.put_at(self.offset(self._size), "-]")

            elif self._main.is_var(v):
                addr = self._main.addressof(v)

                for i in range(len(dsts)):
                    dst = dsts[i]
                    dst_sign, dst = separate_sign(dst)

                    if self._main.is_val(dst):
                        n = self._main.valueof(dst)

                        if name_suffix == "":
                            self._main.put_at(self.offset(n), "[-]")

                        self._main.put_at(addr, "[")

                        if copy or i < len(dsts) - 1:
                            self._main.put("+")

                        self._main.put_at(self.offset(n), "-" if name_suffix == "sub" else "+")
                        self._main.put_at(addr, "-]")

                        if copy or i < len(dsts) - 1:
                            self._main.put("[")
                            self._main.put_at(addr, "+")
                            self._main.put("-]")

                        continue

                    if int(dst_sign != "-") + int(copy or len(dsts) > 1) > self.tmps:
                        raise Exception(f"requires more workspaces")

                    tmp_for_src = -1
                    tmp_for_dst_ptr = -1

                    if copy or len(dsts) > 1:
                        tmp_for_src = self.offset(self._size)
                    if dst_sign != "-":
                        tmp_for_dst_ptr = self.offset(self._size + int(copy or len(dsts) > 1))

                    if self._main.is_var(dst):
                        dst_addr = self._main.addressof(dst)

                        for j in range(self._size):
                            self._main.put("+")
                            self._main.put_at(dst_addr, "[-")
                            self._main.put("-")

                            if dst_sign != "-":
                                self._main.put_at(tmp_for_dst_ptr, "+")

                        for j in range(self._size - 1, -1, -1):
                            self._main.put_at(dst_addr, "[-]]")

                            self._main.put("[")

                            if name_suffix == "":
                                self._main.put_at(self.offset(j), "[-]")

                            self._main.put_at(addr, "[")

                            if copy or i < len(dsts) - 1:
                                self._main.put_at(tmp_for_src, "+")

                            self._main.put_at(self.offset(j), "-" if name_suffix == "sub" else "+")
                            self._main.put_at(addr, "-]")

                            if copy or i < len(dsts) - 1:
                                self._main.put_at(tmp_for_src, "[")
                                self._main.put_at(addr, "+")
                                self._main.put_at(tmp_for_src, "-]")

                            self._main.put("[-]]")

                        if dst_sign != "-":
                            self._main.put_at(tmp_for_dst_ptr, "[")
                            self._main.put_at(dst_addr, "+")
                            self._main.put_at(tmp_for_dst_ptr, "-]")

            return

        raise Exception(f"wnknown ins: {name} {args}")
