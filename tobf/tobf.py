
# a to-bf compiler for small programs
# abi:
#   dynamic_addressing: none.
#   pointer: always points address 0 at the beggining and the end
#   memory: ...vars, ...extensions
#     area of vars has no hidden workspace excepts default 1 cell at address 0 (can be omitted).
#   workspaces: [copy] and some instruction require workspaces.
#     any variable can be workspace.
#     variables for workspace should be 0 when registered/unregistered.
#     no workspace can be modified explicitly.
# syntax:
#   program: var_decl "\n" instructions "end" "\n"
#   var_decl: id (" " val)*
#   instructions: instruction*
#   instruction: qid (" " val)* "\n" | qid (|" " space_separated) "\n"
#   val: digits | "'" | "'" char | qid | sign qid
#   sign: "+" | "-"
#   qid: id ":" id | id
# signed args:
#   if instruction is just for modifing passed variable, "+" means "+=" in C, and "-" means "-=".
#   if instruction is not just for modifing passed variable (ex: variable as pointer), "-" means breakable variable, and "+" will be ignored.
#   some instruction ignores this rule for more prior intent (bug of language).
#   ex: "copy -x ..." and "add ... -x" ignores "-" because "copy" should copy, "add" should add.
# local names:
#   if id has prefix "local:", it will be replaced with instance-specific name.
#   it can be used for instance name (currently no other purpose exists).
# instructions:
# public ...vars
#   do nothing in main program.
#   declares variables as public.
#   public variables can be copied/moved from/to objects with similar interface via copy/move instruction.
# bool io_var
# not io_var
#   required tmps: 1
#   io_var becomes to 1 or 0.
# bool -in_var ...out_vars
# not -in_var ...out_vars
#   add/sub/move 1 or 0 to out_vars. breaks in_var.
# bool in_var ...out_vars
# not in_var ...out_vars
#   required tmps: 2
#   add/sub/move 1 or 0 to out_vars.
# set imm ...out_vars_with_sign
#   every destination can starts with "+" or "-", they means add or sub instead of set.
#   this description is avairable in arguments for instructions below:
#     bool, not, copy, move
#   aliases_with_inplicit_signs:
#     add imm ...out_vars
#     sub imm ...out_vars
#     clear ...out_vars
#       imm as 0 and no sign
#     inc ...out_vars
#       imm as 1 and sign as "+"
#     dec ...out_vars
#       imm as 1 and sign as "-"
# eq imm ...out_vars
# moveeq in_var ...out_vars
# copyeq in_var ...out_vars
#   similer to eq
# and in_var out_var
# nand in_var out_var
# or in_var ...out_vars
# nor in_var ...out_vars
#   similer to eq. breaks in_var
# move in_var ...out_vars_with_sign
#   in_var becomes to 0.
#   if out_vars contains in_var, requires 1 tmp. 
#   aliases_with_implicit_signs:
#     moveadd in_var ...out_vars
#     movesub in_var ...out_vars
# copy in_sub ...out_subs_with_sign
#   if sub was arraylike, move entire array. or move members.
# copy in_var ...out_vars_with_sign
#   required tmps: 1
#   aliases_with_inplicit_signs:
#     copyadd in_var ...out_vars
#     copysub in_var ...out_vars
# copy in_sub ...out_subs_with_sign
#   if sub was arraylike, copy entire array. or copy members.
# add in_var ...out_vars
# sub in_var ...out_vars
#   alias of copyadd/copysub
# add -in_var ...out_vars
# sub -in_var ...out_vars
#   alias of moveadd/movesub
# tmp addr
#   register variable to implicit workspace.
#   variable should be stored zero.
#   variable should not be used until unregistered.
# tmp -addr
#   unregister variable from implicit workspace.
# load subsystem_name ...args
#   loads subsystem after reserved vars and subsystems already loaded
# loadas alias_name subsystem_name ...args
#   loads and names as alias_name
# unload subsysten_name
#   unloads a subsystem. subsystem_name can be alias_name
# subsystem_name:any_name ...args
#   invokes a feature of subsystem
# if cond_var
#   cond_var is avarable until endif
# endif cond_var
#   like "next i" in basic. this rule simplifies compiler.
#   currently compiler disallows no cond_var instructions.
#   breaks cond_var
# ifelse cond_var work_var
#   work_var carries run_else flag
#   cond_var is avarable until "else"
# ifelse cond_var +work_var
#   notices work_var as zero
# else cond_var work_var
# else cond_var -work_var
#   notices work_var as not touched
# endifelse cond_var work_var
# ifgt var0 var1 tmp_var0 tmp_var2
# iflt var0 var1 tmp_var0 tmp_var2
#   skips block if var1 > var0.
#   breaks vars. no variable in args can not be used in this block.
# ifgt var0 var1 tmp_var
# iflt var0 var1 tmp_var
#   required tmps: 1
#   block instruction with tmps are unsafe when block contain [tmp] instruction.
# ifgt var0 var1
# iflt var0 var1
#   required tmps: 2
# endifgt var0 var1 tmp_var0 tmp_var1
# endiflt var0 var1 tmp_var0 tmp_var1
#   breaks vars.
# endifgt var0 var1 tmp_var
# endiflt var0 var1 tmp_var
#   required tmps: 1
# endifgt var0 var1
# endiflt var0 var1
#   required tmps: 2
# ifnotin cond_var ...imms
# endifnotin cond_var ...imms
#   skips block if any immediate equals to cond_var.
#   breaks cond_var
# while cond_var
# endwhile cond_var
# every ins0 ...args0 | ins1 ...args1 | ... <- ...sub_args0 | ...sub_args1 | ...
# ! ins0 ...args0 | ins1 ...args1 | ... <- ...sub_args0 | ...sub_args1 | ...
#   invoke every instruction with args + every sub_args
#   ex:
#       ! a | b x <- c | d
#     means:
#       a c
#       b x c
#       a d
#       b x d
#     does not mean(for usability):
#       a c
#       a d
#       b x c
#       b x d
# !!
#   remove all macro. no purpose.
# !$ name ...
#   define macro. macro is avairable as $!name in args of !
# bf src
#   inline brainfuck.
# include_bf file_name mem_size
#   injects brainfuck code from file. included code should not leave changed pointer.
#   can be used to include something such as output of very smart txt2bf.
#   maybe some compiler generates includable code.
# include_bf file_name mem_size ...io_vars
#   before bf, copies io_vars to bf_memory_area.
#   after bf, moves bf_memory_area to variables.
# include_bf file_name
#   bf code uses only 1 cell.
# include_bf file_name io_var
#   runs at selected var. uses only 1 cell.
# include_arrowfuck file_name mem_width mem_height ...io_vars
#   injects compiled ArrowFuck code.
# include_4dchess file_name mem_size0 mem_size1 mem_size2 mem_size3 ...io_vars
#   injects compiled 4DChess code.
# include_c file_name stack_size function_name ...in_vars out_var
#   uses C function.
# write_lit ...literals
# writeln_lit ...literals
#   required tmps: 1 or 2
# end
#   can not be omitted

from __future__ import annotations
from typing import cast, Union, List, Tuple, Set, Dict, Type
import io
import statistics
import os
import hashlib

from base import Subsystem, split, split_list, separate_sign, calc_small_pair, calc_small_triple, MacroProc

from brainfuck_with_mdm import ArrowFuck, FDChess
from bfa import Bfa
from c2bf import C2bf


class Tobf:
    def __init__(self,
            dst: io.TextIOWrapper,
            tmps: List[int] = [0],
            vars: List[str] = ["__default_tmp"],
            inc_dirs: List[str] = [],
            fast=False):
        """tmps: addresses of workspaces.\n
           vars: implicitly declared variables.\n
           inc_dirs: any of include/import/load/... uses these directries\n
           fast: if True, does not generate "++[>++<-]" for initialization. just generate ">++++<"\n
        """
        self.dst_ = dst
        self.tmps_ = tmps.copy()
        self.base_vars_ = vars.copy()
        self.vars_ = vars.copy()
        self.fast_ = fast

        self.cwd_ = os.getcwd()
        self.inc_dirs_ = inc_dirs + [self.cwd_]

        self.subsystem_templates_: Dict[str, Subsystem] = {}
        self.subsystem_instances_: List[Subsystem] = []
        self.subsystem_instances_by_name_: Dict[str, Subsystem] = {}
        self.concatnative_macros_: Dict[str, str] = {}
        self.macros_: Dict[str, MacroProc] = {}

        # unique file number
        self.n_files = 0

    def fast(self) -> bool:
        return self.fast_

    def install_subsystem(self, name: str, subsystem: Type[Subsystem]):
        self.subsystem_templates_[name] = subsystem

    def addressof_instance(self, name) -> int:
        if not (name in self.subsystem_instances_by_name_.keys()):
            raise Exception(f"subsystem {name} is not instantiated")

        return self.subsystem_instances_by_name_[name].offset(0)

    def addressof_free_area(self, size: int) -> int:
        """malloc() for subsystems"""
        if len(self.subsystem_instances_) > 0:
            self.subsystem_instances_.sort()

        base = len(self.vars_)

        for sub in self.subsystem_instances_:
            addr = sub.offset(0)

            if addr - base >= size:

                return base

            base = addr + sub.size()

        return base

    def get_template(self, name) -> Type[Subsystem]:
        """returns subsystem template"""
        if not (name in self.subsystem_templates_.keys()):
            raise Exception(f"subsystem {name} is not installed")

        return self.subsystem_templates_[name]

    def get_instance(self, name) -> Subsystem:
        """returns subsystem instance"""

        if not (name in self.subsystem_instances_by_name_.keys()):
            raise Exception(f"subsystem aliased as {name} is not loaded")

        return self.subsystem_instances_by_name_[name]

    def load(self, name:str, args:list, alias=""):
        if alias == "":
            alias = name

        if not (name in self.subsystem_templates_.keys()):
            raise Exception(f"subsystem {name} is not installed")

        if alias in self.subsystem_instances_by_name_.keys():
            raise Exception(f"subsystem aliased as {alias} is already loaded.")

        template = self.get_template(name)

        def instantiate(size: int, instance: Subsystem = None, args: List[str] = None):
            addr = self.addressof_free_area(size)

            self.subsystem_instances_.append(instance)
            self.subsystem_instances_by_name_[alias] = instance

            instance.set_base(addr)

            if instance != None:
                instance.put_init(args)

            return addr

        instance = template(self, alias, args=args, instantiate=instantiate)

    def unload(self, name: str, args: list) -> bool:
        subsystem = self.get_instance(name)

        if subsystem == None:
            return False

        subsystem.put_clean(args)

        self.subsystem_instances_by_name_.pop(name)
        self.subsystem_instances_.remove(subsystem)

    """int: addr\n
       str, (\+|-|)(/'.*|\d+/): imm\n
       str, (\+|-|)(#\d+): addr\n
       str, (\+|-|)([\w_][\w\d_]*(?::[\w_][\w\d_]*)): name\n
    """
    def is_signed(self, value) -> bool:
        """is valid signed(intent dscripted) value"""
        return (type(value) == str and len(value) > 1
            and value[0] in ["+", "-"])
    def is_val(self, value: Union[int, str]) -> bool:
        """is valid immediate"""
        if type(value) == int:
            return True

        if type(value) != str:
            raise Exception(f"bad arg: {value}: {type(value)}")

        sign, value = separate_sign(value)
        if value.isdigit() or len(value) > 0 and value[0] == "'":
            return True
        elif ":" in value:
            sub, value2 = value.split(":", maxsplit=1)

            sub = self.get_instance(sub)

            return sub.has_const(value2) or sub.has_enum(value2)
        else:
            return False

    def is_val_or_input(self, value) -> bool:
        return value == "input" or self.is_val(value)

    def is_var(self, value: Union[str, int]) -> bool:
        if type(value) == int:
            return True
        elif type(value) != str:
            raise Exception(f"bad arg: {value}: {type(value)}")
        elif self.is_signed(value):
            sign, value2 = separate_sign(value)

            return self.is_var(value2)
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.get_instance(sub_name)

            return sub.has_var(name)
        elif value.startswith("#") and value[1:].isdigit():
            return True
        else:
            return self.has_var(value)

    def has_var(self, name: str) -> bool:
        return (name in self._vars) or name.startswith("#")

    def is_sub(self, value: str, typ="") -> bool:
        sign, value = separate_sign(value)

        if not (value in self.subsystem_instances_by_name_.keys()):
            return False

        if typ == "":
            return True

        sub = self.get_instance(value)

        return isinstance(sub, self.get_template(typ))

    def addressof(self, value: Union[str, int], allow_tmps=True) -> int:
        if type(value) == int:
            r = value
        elif type(value) != str:
            raise Exception(f"bad arg: {value}: {type(value)}")
        elif self.is_signed(value):
            sign, value2 = separate_sign(value)

            if self.is_signed(value2):
                raise Exception(f"invalid value: {value}")

            r = self.addressof(value2)
        elif self.is_sub(value):
            r = self.addressof_instance(value)
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.get_instance(sub_name)

            r = sub.addressof(name)
        elif value.startswith("#") and value[1:].isdigit():
            r = int(value[1:])
        elif self.has_var(value):
            r = self.vars_.index(value)
        elif value.isdigit():
            raise Exception(f"can not get address of immediate:{value}")
        else:
            raise Exception(f"failed to get address of {value}")

        if not allow_tmps and (r in self.tmps_):
            raise Exception(f"workspace con not be used")

        return r

    def byteof(self, value, byte=False) -> int:
        return self.valueof(value, byte=True)

    def valueof(self, value: Union[int, str], byte=False) -> int:
        if type(value) == int:
            return value
        elif type(value) != str:
            raise Exception(f"bad arg: {value}: {type(value)}")
        elif ":" in value:
            sub_name, name = split(value, sep=":", maxsplit=1)
            sub = self.get_instance(sub_name)

            return sub.valueof(name)
        elif value == "'":
            return 32
        elif value.startswith("'"):
            return ord(value[1])
        elif value.isdigit():
            return int(value)
        else:
            raise Exception(f"bad value")
            return value

    def put(self, s):
        self.dst_.write(s + "\n")

    def put_at(self, addr: Union[int, str], s:str):
        if not self.is_var(addr):
            raise Exception(f"{addr}: {type(addr)} is not valid address")

        if type(addr) == int and addr < 0:
            self.put("<" * abs(addr))
            self.put(s)
            self.put(">" * abs(addr))
        else:
            self.put(">" * self.addressof(addr))
            self.put(s)
            self.put("<" * self.addressof(addr))

    def put_at_every(self, addrs: List[Union[str, int]], s: str, unique=True):
        used = []

        addrs = self.get_addresses(addrs)
        for sign, addr in addrs:
            if unique:
                if addr in used:
                    continue

                used.append(addr)

            self.put_at(addr, s)

    def has_var(self, name: str) -> bool:
        return name in self.vars_

    def put_inc_or_dec(self, c: str, n: int):
        for i in range(n // 16):
            self.put(c * 8 + " " + c * 8)

        m = n % 16
        if m == 0:
            pass
        elif m > 8:
            m = m % 8
            self.put(c * 8 + " " + c * m)
        else:
            self.put(c * m)

    def put_inc(self, n):
        self.put_inc_or_dec("+", n)

    def put_dec(self, n):
        self.put_inc_or_dec("-", n)

    def get_addresses(self, addrs: List[Union[int, str]], unique: bool = False, sorted: bool = True) -> List[Tuple[str, int]]:
        """returns list of (sign, addr)\n
           ignores "print" and "input"
        """

        r = []
        addrs = addrs.copy()

        i = 0
        while i < len(addrs):
            addr = addrs[i]

            if addr in ["input", "print"]:
                i += 1
                continue

            sign, addr = separate_sign(addr)

            if self.is_sub(addr):
                sub = self.get_instance(addr)
                sub_addrs = [f"{sign}{sub.name()}:{name}" for name in sub.get_vars()]

                addrs = addrs[:i] + sub_addrs + addrs[i + 1:]

                continue

            addr = self.addressof(addr)

            if not (unique or (addr in r)):
                r.append((sign, addr))

            i += 1

        if sorted:
            r.sort(key=(lambda x: x[1]))

        return r
    def get_nearest_tmp(self, tmps: List[int], targets: List[Union[str, int]]) -> int:
        if len(tmps) == 0:
            raise Exception(f"requires more workspace")

        if len(targets) == 0:
            return tmps[0]

        targets = list(map(self.addressof, targets))
        target = statistics.mean(targets)
        distances = [(tmp, abs(tmp - target)) for tmp in tmps]

        distances.sort(key=(lambda x: x[1]))

        return distances[0][0]
    def get_unsigned_target(self, targets: List[Union[str, int]]) -> int:
        """any breakable destination as temporary"""

        tmps = [addr for sign, addr in self.get_addresses(targets) if sign == ""]

        return self.get_nearest_tmp(tmps, targets)

    def put_clear(self,
            out_addrs: Union[Union[str, int], List[Union[str, int]]],
            without: List[Union[str, int]] = [],
            ignore_signed=False):
        if type(out_addrs) != list:
            self.put_clear([out_addrs], ignore_signed=True)
            return

        cleared = [self.addressof(i) for i in without]

        for addr in out_addrs:
            sign, addr = separate_sign(addr)
            addr = self.addressof(addr)

            if addr in cleared:
                continue

            if ignore_signed and sign != "":
                continue

            cleared.append(addr)

            self.put_at(addr, "[-]")

    def make_signed_addr(self, sign: str, addr: Union[str, int]) -> str:
        if type(addr) == int:
            addr = "#" + str(addr)

        return sign + addr

    def is_sortable_args(self, args: List[Union[str, int]]) -> bool:
        return ("input" not in args) and ("output" not in args)

    def has_self_reassignment(self, in_addr: int, out_addrs: List[Union[str, int]]) -> bool:
        for addr in out_addrs:
            sign, addr = separate_sign(addr)
            addr = self.addressof(addr)

            if in_addr == addr:
                return True

        return False

    def sign_replaced_args(self, args: List[str, int], old_sign: str, new_sign: str) -> List[str]:
        r = []

        for arg in args:
            if type(arg) == int:
                sign = ""
                arg = f"#{arg}"
            else:
                sign, arg = separate_sign(arg)

            if sign == old_sign:
                sign = new_sign
        
            r.append(sign + arg)

        return r

    def put_move(self, in_addr: Union[int, str], out_addrs: List[Union[int, str]], tmps: List[int] = None, as_bool=False, append=True):
        """as_bool: carries just once\n
           append: if False, increment becomes decrement\n
        """
        if tmps == None:
            tmps = self.tmps_

        if self.has_self_reassignment(in_addr, out_addrs):
            raise Exception(f"[move from to itself]")

        if self.is_sub(in_addr):
            in_sub = self.get_instance(in_addr)

            if not self.fast() and in_sub.has_short_move(out_addrs):
                in_sub.put_short_array_move(out_addrs)
            else:
                self.put_move_array(in_addr, out_addrs, tmps)
                self.put_move_record(in_addr, out_addrs, tmps)

            return

        in_addr = self.addressof(in_addr)
        out_addrs = self.get_addresses(out_addrs)
        out_addrs = [self.make_signed_addr(sign, addr) for sign, addr in out_addrs]

        self.put_clear(out_addrs, without=[in_addr], ignore_signed=True)

        self.put_at(in_addr, "[")

        for out_addr in out_addrs:
            sign, out_addr = separate_sign(out_addr)
            
            if in_addr == out_addr:
                raise Exception(f"move from and to {in_addr}")

            self.put_at(out_addr, "-" if (sign == "-") == append else "+")

        if as_bool:
            self.put_at(in_addr, "[-]]")
        else:
            self.put_at(in_addr, "-]")

    def put_copy(self, in_addr: Union[int, str], out_addrs: List[Union[int, str]], tmps: List[int] = None):
        if tmps == None:
            tmps = self.tmps_

        if len(tmps) == 0:
            raise Exception(f"tryed to copy. but no workspace avairable")

        if self.is_sub(in_addr):
            in_sub = self.get_instance(in_addr)

            if not self.fast() and in_sub.has_short_copy(out_addrs):
                in_sub.put_short_array_copy(out_addrs)
            else:
                self.put_move_array(in_addr, out_addrs, tmps, copy=True)
                self.put_move_record(in_addr, out_addrs, tmps, copy=True)

            return

        in_addr = self.addressof(in_addr)
        tmp = self.get_nearest_tmp(tmps, [in_addr] + out_addrs)
        tmps.remove(tmp)

        self.put_move(in_addr, [f"+#{tmp}"], tmps=tmps)
        self.put_move(tmp, [f"+#{in_addr}"] + out_addrs, tmps=tmps)

        tmps.append(tmp)

    def put_move_record(self, in_addr: str, out_addrs: List[Union[int, str]], tmps: List[int] = None, copy = False):
        """currently in_addr should be name."""

        if not self.is_sub(in_addr):
            raise Exception(f"{in_addr} is not a record")

        sub = self.get_instance(in_addr)

        for v in sub.readable_vars():
            addr = sub.addressof(v)

            dsts = []
            for dst in out_addrs:
                if not self.is_sub(dst):
                    raise Exception(f"can not copy record({in_addr}) to variable({dst})")

                dst_sign, dst = separate_sign(dst)
                dst_sub = self.get_instance(dst)

                if v not in dst_sub.writable_vars():
                    continue

                # avoid to break copoyed array by aliases of any index
                if sub.is_readable_array() and dst_sub.is_writable_array():
                    continue

                dst_addr = dst_sub.addressof(v)
                dsts.append(f"{dst_sign}#{dst_addr}")

            if len(dsts):
                if copy:
                    self.put_copy(addr, dsts, tmps)
                else:
                    self.put_move(addr, dsts, tmps)

    def put_move_array(self, in_addr: str, out_addrs: List[Union[int, str]], tmps: List[int] = None, copy = False):
        """currently in_addr should be name."""

        if not self.is_sub(in_addr):
            raise Exception(f"{in_addr} is not an array")

        sub = self.get_instance(in_addr)

        if sub.is_readable_array():
            for i in range(sub.array_size()):
                addr = sub.addressof(str(i))

                dsts = []
                for dst in out_addrs:
                    if not self.is_sub(dst):
                        raise Exception(f"can not copy array to variable")

                    dst_sign, dst = separate_sign(dst)
                    dst_sub = self.get_instance(dst)

                    if not dst_sub.is_writable_array() or i >= dst_sub.array_size():
                        continue

                    dst_addr = dst_sub.addressof(str(i))
                    dsts.append(f"{dst_sign}#{dst_addr}")

                if len(dsts):
                    if copy:
                        self.put_copy(addr, dsts, tmps)
                    else:
                        self.put_move(addr, dsts, tmps)

    def put_print_or_input(self, addrs: List[Union[str, int]], print=False, tmps: List[int] = []):
        tmp = -1

        if len(list(filter(self.is_val, addrs))) > 0:
            if print:
                var_addrs = list(filter(self.is_var, addrs))
                tmp = self.get_nearest_tmp(tmps, var_addrs)
            else:
                raise Exception(f"unknown instruction [input imm]")

        current_value = 0

        for addr in addrs:
            sign, addr = separate_sign(addr)

            if print:
                if self.is_val(addr):
                    v = self.valueof(addr)
                    d = v - current_value
                    o = "+" if d >= 0 else "-"

                    self.put_at(tmp, (o * abs(d)) + ".")

                    current_value = v
                elif self.is_sub(addr):
                    sub = self.get_instance(addr)

                    if sub.is_readable_array():
                        for i in range(sub.array_size()):
                            self.put_at(sub.addressof(str(i)), ".")
                    elif len(sub.readable_vars()):
                        for i in sub.readable_vars():
                            self.put_at(sub.addressof(i), ".")
                    else:
                        raise Exception(f"non-printable object was passed to [print]")

                else:
                    self.put_at(addr, ".")
            else:
                def print_(sign: str, addr: int):
                    if sign == "":
                        self.put_at(addr, ",")
                    else:
                        if len(tmps) == 0:
                            raise Exception(f"tryed to add input but no workspace avairable")

                        tmp = self.get_nearest_tmp(tmps, [addr])
                        self.put_at(tmp, ",")
                        self.put_move(tmp, [f"{sign}#{addr}"])

                if self.is_var(addr):
                    print_(sign, self.addressof(addr))
                elif self.is_sub(addr):
                    sub = self.get_instance(addr)

                    if not sub.is_writable_array():
                        raise Exception(f"non-writable object was passed to [input]")

                    for i in range(sub.array_size()):
                        print_(sign, sub.addressof(str(i)))

        if current_value != 0:
            self.put_at(tmp, "[-]")

    def put_set(self, value: Union[str, int], out_addrs: List[Union[str, int]], tmps: List[int] = []):
        if value in ["input", "print"]:
            self.put_print_or_input(out_addrs, print=(value == "print"), tmps=tmps)

            return

        self.put_clear(out_addrs, ignore_signed=True)

        n = 1
        m = self.valueof(value)
        tmp = -1

        if m == 0:
            return

        if not self.fast_ and len(tmps) > 0:
            if type(m) != int:
                raise Exception(f"{type(m)}{m} <={value}")
            n, m = calc_small_pair(m, len(out_addrs))
            tmp = self.get_nearest_tmp(tmps, out_addrs)

            if n > 1 and n * m * len(out_addrs) <= n + 3 + m * len(out_addrs):
                m = int(n * m)
                n = 1

        if n > 1:
            self.put_at(tmp, ("+" * n) + "[")

        for addr in out_addrs:
            sign, addr = separate_sign(addr)
            addr = self.addressof(addr)
            o = "-" if sign == "-" else "+"

            self.put_at(addr, o * m)

        if n > 1:
            self.put_at(tmp, "-]")

    def put_invoke(self, name: str, args: List[Union[str, int]], tmps: List[int] = None):
        if tmps == None:
            tmps = self.tmps_

        if ":" in name:
            sub_name, name = name.split(":", maxsplit=1)

            sub = self.get_instance(sub_name)

            if sub == None:
                raise Exception(f"subsystem {sub_name} is not loaded")
            if not sub.has_ins(name, args):
                raise Exception(f"{sub.name()} hasnt {name}")

            return sub.put(name, args, tmps)

        if name == "bf":
            self.put("".join(args))

            return True

        # aliases
        if name in ["inc", "dec"]:
            sign = "+" if name == "inc" else "-"
            name = "set"
            args = ["1"] + [sign + arg for arg in args]
        if name == "clear":
            name = "set"
            args = ["0"] + args
        if name in ["print", "input"]:
            args = [name] + args
            name = "set"
        if name in ["add", "sub"]:
            sign = "+" if name == "add" else "-"
            name = "set"
            args = [args[0]] + [sign + x for x in args[1:]]
        if name in ["copyadd", "copysub"]:
            sign = "+" if name == "copyadd" else "-"
            name = "copy"
            args = [args[0]] + [sign + x for x in args[1:]]
        if name in ["moveadd", "movesub"]:
            sign = "+" if name == "moveadd" else "-"
            name = "move"
            args = [args[0]] + [sign + x for x in args[1:]]


        # ducktype checker (maybe doesnt work well)
        if name == "is_var":
            for arg in args:
                if not self.is_var(arg):
                    raise Exception(f"type check failed: {arg} should be variable")

            return True

        if name == "is_val":
            for arg in args:
                if self.is_var(arg) or self.is_sub(arg):
                    raise Exception(f"type check failed: {arg} should be value")

            return True

        if name == "is_sub":
            for arg in args:
                if not self.is_sub(arg):
                    raise Exception(f"type check failed: {arg} should be subsystem")

            return True

        if name == "is":
            if len(args) == 0:
                raise Exception("is/0 is not implemented")

            typ = args[0]
            for arg in args[1:]:
                if not self.is_sub(arg, typ):
                    raise Exception(f"type check failed: {arg} should be subsystem {typ}")

            return True

        if name == "is_tmp":
            for arg in args:
                addr = self.addressof(arg)

                if addr not in self.tmps_:
                    raise Exception(f"type check failed: {arg} should be workspace")

            return True

        if name == "tmp":
            for arg in args:
                sign, arg = separate_sign(arg)
                addr = self.addressof(arg)

                if sign == "-":
                    self.tmps_.remove(addr)
                else:
                    self.tmps_.append(addr)

            return True

        if name == "load":
            self.load(args[0], args[1:])

            return True

        if name == "loadas":
            self.load(args[1], args[2:], alias=args[0])

            return True

        if name == "unload":
            self.unload(args[0], args[1:])

            return True

        if name in ["add", "sub"]:
            sign, arg = separate_sign(args[0])

            if self.is_var(arg):
                if sign == "-":
                    name = "move" + name
                else:
                    name = "copy" + name

        if name == "swap":
            if len(tmps) == 0:
                raise Exception(f"[swap] requires 1 workspace")

            tmp = self.get_nearest_tmp(tmps, args)
            addr0 = self.addressof(args[0])
            addr1 = self.addressof(args[1])

            self.put_move(addr0, [f"+#{tmp}"])
            self.put_move(addr1, [f"+#{addr0}"])
            self.put_move(tmp, [f"+#{addr1}"])

            return True

        if name in ["bool", "not"]:
            sign, addr = separate_sign(args[0])
            addr = self.addressof(addr)

            if sign != "" and len(args) == 1:
                raise Exception(f"[bool/1] with signed arg is unknown instruction")

            if sign == "-" and not self.has_self_reassignment(addr, args[1:]):
                if name == "bool":
                    self.put_move(addr, args[1:], as_bool=True)
                else:
                    self.put_set("1", args[1:])
                    self.put_move(addr, self.sign_replaced_args(args[1:], "", "+"), as_bool=True, append=False)

                return True

            tmp = self.get_nearest_tmp(tmps, args)
            tmps.remove(tmp)

            tmp2 = -1
            if len(args) > 1:
                tmp2 = self.get_nearest_tmp(tmps, args)
            tmps.append(tmp)

            if name == "bool":
                if len(args) == 1:
                    self.put_move(addr, [f"+#{tmp}"])
                    self.put_move(tmp, [f"+#{addr}"], as_bool=True)
                else:
                    self.put_move(addr, [f"+#{tmp}", f"+#{tmp2}"])
                    self.put_move(tmp, args[1:], as_bool=True)
                    self.put_move(tmp2, [f"+#{addr}"])
            else:
                if len(args) == 1:
                    self.put_move(addr, [f"+#{tmp}"])
                    self.put_at(addr, "+")
                    self.put_move(tmp, [f"-#{addr}"], as_bool=True)
                else:
                    self.put_move(addr, [f"+#{tmp}", f"+#{tmp2}"])
                    self.put_move(tmp, [f"+#{addr}"])
                    self.put_set("1", [f"+#{tmp}"])
                    self.put_move(tmp2, [f"-#{tmp}"], as_bool=True)
                    self.put_clear(args[1:], ignore_signed=True)
                    self.put_move(tmp, self.sign_replaced_args(args[1:], "", "-"), append=False)
    
            return True

        if name == "eq":
            sign, value = separate_sign(args[0])

            if self.is_val(value):
                v = self.valueof(value)

                for arg in args[1:]:
                    addr = self.addressof(arg)
                    tmp = self.get_nearest_tmp(tmps, [addr])

                    self.put_at(tmp, "+")
                    self.put_at(addr, ("-" * v))
                    self.put_move(addr, [f"-#{tmp}"], as_bool=True)
                    self.put_move(tmp, [f"+#{addr}"])

            return True

        if name in ["moveeq", "copyeq"]:
            addr0 = self.addressof(args[0])

            for arg in args[1:]:
                addr = self.addressof(arg)
                tmp = self.get_nearest_tmp(tmps, [addr0, addr])

                self.put_move(addr, tmp)

                self.put_at(addr0, "[")
                self.put_at(tmp, "-")
                if name == "copyeq" or len(args) > 2:
                    self.put_at(addr, "+")
                self.put_at(addr0, "-]")

                if name == "copyeq" or len(args) > 2:
                    self.put_move(addr, addr0)

                self.put_at(addr, "+")

                self.put_move(tmp, [f"-#{addr}"], as_bool=True)

            if name == "moveeq" or len(args) > 2:
                self.put_clear(addr0)

            return True

        if name in ["or", "nor"]:
            if len(args) < 2:
                raise Exception(f"[{name}/{len(args)}] is not implemented")

            addr0 = self.addressof(args[0])

            for arg in args[1:]:
                addr = self.addressof(arg)
                tmp = self.get_nearest_tmp(tmps, [addr0, addr])

                # move v?  bool(it)
                # move v0  +bool(it) bool(v?)
                # move v?  v0
                # if it  inc v?

                self.put_move(addr, [f"+#{tmp}"], as_bool=True)

                self.put_move(addr0, [f"+#{tmp}", f"+#{addr}"], as_bool=True)
                self.put_move(addr, [f"+#{tmp}"], as_bool=True)

                self.put_move(addr, [f"+#{addr0}"])

                if name == "nor":
                    self.put_at(addr, "+")

                    self.put_move(tmp, [f"-#{addr}"])
                else:
                    self.put_move(tmp, [f"+#{addr}"])

            self.put_at(addr0, "-")

            return True

        if name in ["and", "nand"]:
            if len(args) != 2:
                raise Exception(f"[{name}/{len(args)}] is not implemented")

            addr0 = self.addressof(args[0])

            for arg in args[1:]:
                addr = self.addressof(arg)
                tmp = self.get_nearest_tmp(tmps, [addr0, addr])

                # breaks args[0]

                self.put_move(addr, [f"+#{tmp}"], as_bool=True)

                if name == "nand":
                    self.put_at(addr, "+")

                o = "+" if name == "and" else "-"
                self.put_at(tmp, "[")
                self.put_move(addr0, [f"{o}#{addr}"], as_bool=True)
                self.put_at(tmp, "-]")

            return True

        if name == "!$":
            if len(args) == 0:
                self.concatnative_macros_ = {}
                return

            self.concatnative_macros_[args[0]] = args[1:]

            return

        if name in ["every", "!"]:
            if not ("<-" in args):
                raise Exception(f"[every] requires <-")

            args2 = []
            for arg in args:
                if arg.startswith("$!"):
                    args2.extend(self.concatnative_macros_[arg[2:]])
                else:
                    args2.append(arg)
            args = args2

            inss = split_list(args[:args.index("<-")], "|")
            argss = split_list(args[args.index("<-") + 1:], "|")

            for args2 in argss:
                for ins in inss:
                    ins2, *prefix = ins

                    self.put_invoke(ins2, prefix + args2, tmps)

            return True

        if name == "set":
            self.put_set(args[0], args[1:], tmps)

            return True

        if name == "copy":
            self.put_copy(args[0], args[1:], tmps)

            return True


        if name == "move":
            self.put_move(args[0], args[1:], tmps)

            return True

        if name in ["if", "while"]:
            addr = self.addressof(args[0])

            self.put_at(addr, "[")

            return True

        # validation
        if name in ["ifnotin", "endifnotin"]:
            if not self.is_var(args[0]):
                raise Exception(f"first arg of [{name}] should be variable")

            if len(list(filter(None, map(self.is_val, args[1:])))) != len(args[1:]):
                raise Exception(f"currently [{name}] accepts only one variable and immediates")

        if name == "ifnotin":
            addr = self.addressof(args[0])

            args2 = args[1:]
            args2 = set(map(self.byteof, args2))
            args2 = sorted(args2)

            base = 0
            for i in args2:
                j = i - base
                base = i

                self.put_at(addr, "-" * j + "[")


            return True

        if name == "endifnotin":
            addr = self.addressof(args[0])

            self.put_at(addr, "[-]" + "]" * (len(args) - 1))

            return True

        if name in ["endif", "endwhile"]:
            sign, v = separate_sign(args[0])
            addr = self.addressof(v)


            self.put_at(addr,
                "]" if name == "endwhile"
                else "-]" if sign == "-"
                else "[-]]")

            return True

        if name == "ifelse":
            a_then = self.addressof(args[0])
            s_else, v_else = separate_sign(args[1])
            a_else = self.addressof(v_else)

            self.put_at(a_else, "+" if s_else == "+" else "[-]+")
            self.put_at(a_then, "[")

            return True

        if name == "else":
            s_then, v_then = separate_sign(args[0])
            s_else, v_else = separate_sign(args[1])
            a_then = self.addressof(v_then)
            a_else = self.addressof(v_else)

            self.put_at(a_else, "-" if s_else == "-" else "[-]")
            self.put_at(a_then, "-]" if s_then == "-" else "[-]]")
            self.put_at(a_else, "[")

            return True

        if name == "endifelse":
            sign, v = separate_sign(args[1])
            addr = self.addressof(v)

            self.put_at(addr, "-]" if sign == "-" else "[-]]")

            return True

        if name in ["iflt", "endiflt"]:
            name = "ifgt" if name == "iflt" else "endifgt"
            right = args[0]
            left = args[1]
            args[0] = left
            args[1] = right

        if name == "ifgt":
            a_left = self.addressof(args[0])
            a_right = self.addressof(args[1])

            if len(args) > 2:
                a_tmp = self.addressof(args[2])
            else:
                a_tmp = self.get_nearest_tmp(tmps, [a_left, a_right])
                tmps.remove(a_tmp)

            if len(args) > 3:
                a_tmp2 = self.addressof(args[3])
            else:
                a_tmp2 = self.get_nearest_tmp(tmps, [a_left, a_right])

            if len(args) < 3:
                tmps.append(a_tmp)

            self.put_at(a_left, "[")

            self.put_move(a_right, [f"+#{a_tmp}", f"+#{a_tmp2}"])

            self.put_move(a_tmp, [f"+#{a_right}"])

            self.put_at(a_tmp, "+")
            self.put_move(a_tmp2, [f"-#{a_tmp}"], as_bool=True)
            self.put_at(a_tmp, "[[-]")

            return True

        if name == "endifgt":
            a_left = self.addressof(args[0])
            a_right = self.addressof(args[1])

            if len(args) > 2:
                a_tmp = self.addressof(args[2])
            else:
                # should not load vars without unload in block.
                # should not (un)register workspaces in block.
                # variables and tmps should be the same as at block head. 
                a_tmp = self.get_nearest_tmp(tmps, [a_left, a_right])

            self.put_at(a_left, "[-]+")
            self.put_at(a_tmp, "[-]]")

            self.put_at(a_right, "-")
            self.put_at(a_left, "-]")
            self.put_at(a_right, "[-]")

            return True

        if name in ["include_bf", "include_arrowfuck", "include_4dchess"]:
            args0 = args

            clean = True
            mem_size = [1, 1, 1, 1]

            if len(args) and args[0] == "fast":
                clean = False
                args = args[1:]

            for i in range(4):
                if len(args) > 1 and args[1].isdigit():
                    mem_size[i] = int(args[1])
                    args = args[:1] + args[2:]

            if len(args) < 1:
                raise Exception(f"[{name}/{len(args0)}] is not implemented")

            try:
                with io.open(args[0]) as bff:
                    bf = bff.read()
            except Exception:
                raise Exception(f"failed to open {args[0]}")

            if name == "include_arrowfuck":
                src = io.StringIO(bf)
                dst = io.StringIO()

                mem_size = ArrowFuck(src, dst, mem_size[:2]).compile()
                bf = dst.getvalue()

            elif name == "include_4dchess":
                src = io.StringIO(bf)
                dst = io.StringIO()

                mem_size = FDChess(src, dst, mem_size[:4]).compile()
                bf = dst.getvalue()

            else:
                mem_size = mem_size[0]

            if len(args[1:]) > mem_size:
                raise Exception("variables [include_bf] passed can not be stored to bf memory area.")

            vs = args[1:]

            if mem_size < len(vs):
                mem_size = len(vs)

            if mem_size <= 1 and len(vs) == 0:
                tmp = tmps[0] if len(tmps) else self.addressof_free_area(1)

                self.put_at(tmp, bf + "[-]")

                return True

            if len(vs) == mem_size:
                direct_io = True

                p = -1
                for i in vs:
                    addr = self.addressof(i)

                    if p == -1:
                        p = addr
                    elif p + 1 == addr:
                        p += 1
                    else:
                        direct_io = False
                        break

                if direct_io:
                    self.put_at(self.addressof(vs[0]), bf)

                    return True

            bf_ptr = self.addressof_free_area(mem_size)

            for i in range(len(vs)):
                addr = self.addressof(vs[i])

                self.put_move(addr, [f"#{bf_ptr + i}"])

            self.put_at(bf_ptr, bf)

            for i in range(len(vs)):
                addr = self.addressof(vs[i])

                self.put_move(bf_ptr + i, [f"#{addr}"])

            if clean:
                mem_size -= len(vs)

                self.put_at(bf_ptr + len(vs), ("[-]>" * mem_size) + ("<" * mem_size))

            return True

        if name == "include_c":
            if len(args) < 4:
                raise Exception(f"[include_c/{len(args)}] is not implemented")

            c_file_name = args[0]
            c_stack_size = int(args[1])
            c_func_name = args[2]
            c_func_args_and_result = args[3:]
            c_func_args = c_func_args_and_result[:-1]

            shared_vars = [f"__tobf_shared{i}" for i in range(len(c_func_args))]

            try:
                c = C2bf(c_file_name, shared_vars=shared_vars, stack_size=c_stack_size)
                c_func_args2 = [f"__tobf_shared{i}" for i in range(len(c_func_args))]
                c_startup = f"""{{ __tobf_shared0 = {c_func_name}({",".join(c_func_args2)}); }}"""
                bf, c_mem_size = c.compile_to_bf(c_startup)
                c_base_ptr = self.addressof_free_area(c_mem_size)
            except Exception:
                raise Exception(f"failed to open {c_file_name}")

            for i in range(len(c_func_args)):
                arg = c_func_args[i]

                if self.is_var(arg):
                    addr = self.addressof(arg)

                    self.put_move(addr, [f"+#{c_base_ptr + i}"])
                else:
                    v = self.valueof(arg)
                    self.put_at(c_base_ptr + i, "+" * v)

            self.put_at(c_base_ptr, bf)

            addr = self.addressof(c_func_args_and_result[-1])

            self.put_move(c_base_ptr, [f"+#{addr}"])

            return True

        if name in ["write_lit", "writeln_lit"]:
            tail = "\n" if name == "writeln_lit" else ""
            tmp = self.get_nearest_tmp(tmps, [0])

            if not self.fast() and len(tmps) > 1:
                tmps.remove(tmp)
                tmp2 = self.get_nearest_tmp(tmps, [tmp])
                tmps.append(tmp)

                if abs(tmp - tmp2) > 1:
                    tmp2 = -1 
            else:
                tmp2 = -1

            self.put(">" * tmp)

            c0 = 0
            for c in [ord(s) for s in " ".join(args) + tail]:
                if c > c0:
                    o = "+"
                    d = c - c0
                else:
                    o = "-"
                    d = c0 - c

                if tmp2 != -1:
                    n, m, d2 = calc_small_triple(d)

                    # 7: len(">[<>-]<")
                    if d > n + m + 7 + d2:
                        self.put("<" * tmp)
                        self.put(">" * tmp2)

                        self.put(("+" * n) + "[")
                        self.put("<" * tmp2)
                        self.put(">" * tmp)

                        self.put(o * m)

                        self.put("<" * tmp)
                        self.put(">" * tmp2)
                        self.put("-]")

                        self.put("<" * tmp2)
                        self.put(">" * tmp)

                        self.put(o * d2)
                    else:
                        self.put(o * d)
                else:
                    self.put(o * d)

                self.put(".")

                c0 = c

            self.put("[-]")
            self.put("<" * tmp)

            return True

        if name in self.macros_.keys():
            proc = self.macros_[name]

            def put_(name, args):
                self.put_invoke(name, args, tmps=tmps)

            proc.put(name, args, put_, [])

            return


        raise Exception(f"unknown instruction {name}")

    def compile_instruction(self, src: Union[str, List[str]]):
        if type(src) == str:
            src = split(src)

        name, *args = src

        return self.put_invoke(name, args, self.tmps_)

    def escape_comment(self, s: str) -> str:
        for from_, to_ in [
                [">", "{INC_PTR}"],
                ["<", "{DEC_PTR}"],
                ["+", "{INC}"],
                ["-", "{DEC}"],
                [",", "{IN}"],
                [".", "{OUT}"],
                ["[", "{LEFT}"],
                ["]", "{RIGHT}"]]:
            s = s.replace(from_, to_)

        return s

    def compile_all(self, src: List[List[str]], comments=False):
        for i in src:
            if comments:
                self.put(self.escape_comment(" ".join(i)))

            self.compile_instruction(i)

    def compile_file(self, file_name, comments=False):
        pub_vars, vars, macros = self.read_file(file_name)

        in_subdir = os.path.sep in file_name

        if in_subdir:
            self.inc_dirs_.append(os.path.dirname(file_name))

        self.vars_ = self.base_vars_ + vars
        self.macros_ = macros
        self.compile_all(macros["main"].codes, comments)

        if in_subdir:
            self.inc_dirs_.pop()

    def find_dir(self, file: str) -> str:
        for d in reversed(self.inc_dirs_):
            if os.path.isfile(os.path.join(d, file)):
                return d

        raise Exception(f"failed to open {file}")

    def read_file(self, file: str) -> Tuple[List[str], List[str], Dict[str, MacroProc]]:
        """returns (public_vars, vars, macros)"""

        self.n_files += 1

        file_dir = self.find_dir(file)
        file = os.path.abspath(os.path.join(file_dir, file))
        
        local_pfx = f"__tobf_local_{self.n_files}__"

        pub_vs = set([])
        vs = []
        ms = {"main": MacroProc("main", [], [])}

        src: List[str] = []

        with io.open(file, "r") as f:
            src = f.read().splitlines()

        label = "main"

        vs = split(src[0])

        for line in src[1:]:
            line = line.strip()

            if line == "":
                continue
            if line.startswith("#"):
                continue

            cod = []
            
            for tkn in split(line):
                if tkn.startswith("local:"):
                    tkn = local_pfx + tkn[6:]

                cod.append(tkn)

            if cod[0] == "public":
                pub_vs |= set(cod[1:])

                continue

            if cod[0].startswith(":"):
                label = cod[0][1:]

                if not (label in ms.keys()):
                    ms[label] = MacroProc(label, [], [])

                if len(ms[label].params) == 0:
                    if len(cod) > 0 and cod[-1] == "*":
                        ms[label].has_va = True
                        ms[label].params = cod[1:-1]
                    else:
                        ms[label].params = cod[1:]

                continue

            if cod[0] == "end":
                break

            ms[label].codes.append(cod)


        pub_vs = [v for v in vs if v in pub_vs]

        return (pub_vs, vs, ms)
