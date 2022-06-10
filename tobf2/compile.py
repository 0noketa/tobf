
#stub
#everything will be changed
#
# scope:
#   # every scope deallocates variables and unloads modules at its "end"
#   # does not clean its area
#   scope
#      ...
#   end
# macro:
#   # every variable declared in macro has unique name
#   :name param0 param1 ...
#      ...
#   end
# macro with scope:
#   macro name param0 param1 ...
#      ...
#   end
# module:
#   module Name field0 field1 ...
#     ...
#   end
#   AncestorName Name additional_field0 additional_field1 ...
#     ...
#   end
#
# bugs:
#   do not use modules in modules. no way to search them was implemented.
#   local macro is not a bug. but they can not use members of parent macro.
#   nothing have been prepared for builtin structures.
#   language forces to write many redundant things.
#   modules can be imported from ancestors.

from typing import cast, Union, List, Dict
import sys
import io


class Locatable:
    def __init__(self, range_: range, name_="", is_scope_=False, parent_=None) -> None:
        self.name_ = name_
        self.range_ = range_
        self.is_scope_ = is_scope_
        self.parent_: Locatable = parent_
        self.subareas_: List[Locatable] = []

    # area information

    def name(self):
        return self.name_

    def has_parent(self):
        return self.parent_ is not None

    def parent(self):
        return self.parent_

    def parent_address(self):
        return self.parent_.absolute_address() if self.has_parent() else 0

    def address_range(self):
        return self.range_

    def address(self):
        return self.range_.start

    def last_address(self):
        return self.range_.stop - 1 if self.size() else self.range_.start

    def contains_address(self, addr_: int):
        return addr_ in self.range_

    def absolute_address(self):
        return self.parent_address() + self.address()

    def absolute_last_address(self):
        return self.parent_address() + self.last_address()

    def absolute_address_range(self):
        return range(self.absolute_address(), self.absolute_last_address() + 1)

    def size(self):
        return len(self.range_)

    def resize(self, size_: int):
        if size_ > self.size():
            if self.absolute_address() + size_ - 1 not in self.parent().absolute_address_range():
                raise Exception(f"failed to resize. parent area has not enough size.")
            if size_ < self.least_size():
                raise Exception(f"failed to resize. members require more cells.")

        self.range_ = range(self.range_.start, self.range_.start + size_)

    def optimize_layout(self, keep_addresses_=False):
        addr_ = 0

        for i in self.subareas_:
            i.optimize_layout(keep_addresses_=keep_addresses_)
            least_size_ = i.least_size()

            if least_size_ < i.size():
                i.resize(least_size_)

            if not keep_addresses_ and addr_ < i.address():
                i.relocate(addr_)

            addr_ = i.last_address() + 1

    def least_size(self):
        if self.size() == 0:
            return 0
        elif len(self.subareas_):
            return max(map(Locatable.last_address, self.subareas_)) + 1
        else:
            return 1

    def relocate(self, addr_: int, new_parent_=None):
        if self.has_parent() and addr_ > self.parent().size():
            raise Exception(f"failed to relocate. new address is outside of parent area")

        if new_parent_ is not None:
            self.parent_ = new_parent_

        self.range_ = range(addr_, addr_ + self.size())

    # members

    def search(self, qname: str):
        return self.subareas_[int(qname)] if qname.isdigit() else None

    def has_subarea(self, area_: object):
        return area_ in self.subareas_

    def indexof_subarea(self, area_: object):
        return self.subareas_.index(area_) if self.has_subarea(area_) else -1

    def subareas(self):
        return self.subareas_

    def subarea(self, idx: int):
        if idx not in range(self.subareas_):
            raise Exception(f"subarea {idx} does not exist")

        return self.subarea_[idx]

    def append_subarea(self, area_: object):
        area_ = cast(Locatable, area_)

        self.subareas_.sort(key=Locatable.address)

        addr_ = 0

        for i in self.subareas_:
            if addr_ + area_.size() < i.address():
                break

            addr_ = i.address() + i.size()

        if area_.size() <= self.size() - addr_:
            area_.relocate(addr_, self)
            self.subareas_.append(area_)
            self.subareas_.sort(key=Locatable.address)
        else:
            raise Exception(f"failed to allocate {area_.size()} cells")

    def pop_subarea(self, area_: object):
        area_ = cast(Locatable, area_)

        self.subareas_.remove(area_)

        area_.relocate(0, None)

        return area_


    # optimization hints

    def skipr(self):
        return ">" * self.size()

    def skipl(self):
        return "<" * self.size()


class Area(Locatable):
    def __init__(self, range_: range, name_="", is_scope_=False, parent_=None) -> None:
        super().__init__(range_, name_, is_scope_, parent_)
        self.member_by_name_: Dict[str, List[Locatable]] = {}


    # members

    def members(self):
        return list(filter(lambda x: x.name != "", self.subareas()))

    def member(self, name: str):
        return self.member_by_name_[name][-1] if self.has_member(name) else None

    def member_index(self, name: str):
        return self.indexof_subarea(self.member(name)) if self.has_member(name) else -1

    def has_member(self, member_: Union[str, Locatable]):
        if type(member_) == str:
            return member_ in self.member_by_name_
        else:
            return member_ in self.subareas()

    def add_member(self, member_: Locatable):
        self.append_subarea(member_)

        name = member_.name()
        if name not in self.member_by_name_:
            self.member_by_name_[name] = []

        self.member_by_name_[name].append(member_)

    def create_member(self, name: str, size_: int) -> Locatable:
        member_ = Area(range(size_), name)

        self.add_member(member_)

    def remove_member(self, member_: Union[str, Locatable]) -> Locatable:
        if not self.has_member(member_):
            return

        if type(member_) == str:
            name_ = member_
        else:
            name_ = member_.name()

        member_ = self.member_by_name_[name_][-1]
        self.member_by_name_[name_].pop()

        if len(self.member_by_name_[name_]) == 0:
            self.member_by_name_.pop(name_)

        return self.pop_subarea(member_)

    def search(self, qname: str):
        nodes = qname.split(".")

        if self.is_scope_:
            node, *nodes = nodes

            if self.has_member(node):
                v = self.member(node)
            elif self.has_parent():
                return self.parent().search(qname)
            else:
                return None
                raise Exception(f"unknown name {qname}")
        else:
            v = self

        for node in nodes:
            if v.has_member(node):
                v = v.member(node)
            else:
                return None

        return v

class CodeGenerator:
    def __init__(self) -> None:
        pass

    @classmethod
    def put_select(self, from_: int, to_: int):
        if from_ < to_:
            sys.stdout.write(">" * (to_ - from_))
        else:
            sys.stdout.write("<" * (from_ - to_))

    @classmethod
    def put_move(self, src_addr: int, dsts_addrs: int, base_=0, last_=0):
        self.put_select(base_, src_addr)
        sys.stdout.write("[")

        addr = src_addr
        for dst_addr in sorted(dsts_addrs):
            self.put_select(addr, dst_addr)
            sys.stdout.write("+")
            addr = dst_addr

        self.put_select(addr, src_addr)

        sys.stdout.write("-]")
        self.put_select(src_addr, last_)


class Macro:
    def __init__(self,
            name: str, params: List[str] = None,
            code: List[List[str]] = None,
            is_reentrant=True,
            is_module=False,
            module_=None,
            global_module: object = None) -> None:
        """extern: external modules"""
        self.name_ = name
        self.params_ = params if params is not None else []
        self.code_ = code if code is not None else []
        self.macs_: Dict[str, Macro] = {}
        self.mods_: Dict[str, Macro] = {}
        self.is_reentrant_ = is_reentrant
        self.is_module_ = is_module
        self.module_: Macro = module_
        self.global_module_: Macro = global_module

    def mod_name(self):
        return self.module_.name_ if self.module_ is not None else ""
    def create_copy_macro(self, new_mod):
        new_mod = cast(Macro, new_mod)

        mac = Macro(name=self.name_, params=self.params_,
                code=self.code_,
                is_module=self.is_module_,
                is_reentrant=self.is_reentrant_,
                module_=new_mod,
                global_module=self.global_module_)

        macs_ = {}
        for name in self.macs_:
            macs_[name] = mac.macs_[name].create_copy_macro(new_mod)

        mac.macs_ = macs_

        return mac
    def inherit_macro(self, mac):
        mac = cast(Macro, mac)
        self.macs_[mac.name_] = mac.create_copy_macro(self)

    def search(self, qname: str):
        node, *nodes = qname.split(".", maxsplit=1)

        if node in self.macs_:
            mac = self.macs_[node]
            if len(nodes) > 0:
                return mac.search(nodes[0])
        else:
            mac = None
            
        return mac

    def load(self, file: io.TextIOWrapper = None, linked_file_names: List[str] = None, file_extension=".txt"):
        dpt = 1
        heads = ["scope", "if", "while", "do"]
        linked_file_names = [] if linked_file_names is None else linked_file_names
        files = []
        file = sys.stdin if file is None else file
        extern_mods = self.mods_ if self.global_module_ is None else self.global_module_.mods_

        while True:
            line = file.readline()
            if line == "":
                if len(files):
                    file.close()
                    file = files.pop()
                else:
                    break

            src = line.strip()
            if src.startswith("#"):
                continue

            src = list(map(str.strip, src.split()))
            if len(src) == 0:
                continue

            op, *args = src

            # sys.stderr.write(f"# {op} {args}\n")

            if op == "link":
                file_name = args[0] + file_extension
                if file_name not in linked_file_names:
                    linked_file_names.append(file_name)
                    files.append(file)
                    file = io.open(file_name, "r")

                continue

            mac_is_reentrant = True
            mac_is_module = False
            mod_base: Macro = None
            if op.startswith(":"):
                args = [op[1:]] + args
                op = "macro"
                mac_is_reentrant = False

            if op in extern_mods:
                mod_base = extern_mods[op]
                op = "macro"
                mac_is_reentrant = False
                mac_is_module = True

            if op == "module":
                op = "macro"
                mac_is_reentrant = False
                mac_is_module = True

            if op == "macro":
                name, *params = args

                if self.global_module_ is None:
                    extern = self
                else:
                    extern = self.global_module_

                if self.is_module_:
                    if mod_base is not None:
                        params = mod_base.params_ + params

                    mac = Macro(name, params,
                            is_reentrant=mac_is_reentrant,
                            is_module=mac_is_module,
                            module_=self,
                            global_module=extern)

                    if mod_base is not None:
                        for sub_mac in mod_base.macs_:
                            mac.inherit_macro(mod_base.macs_[sub_mac])
                else:
                    mac = Macro(name, params,
                            is_reentrant=mac_is_reentrant, is_module=mac_is_module,
                            module_=self,
                            global_module=extern)

                mac.load(file=file,
                        linked_file_names=linked_file_names,
                        file_extension=file_extension)

                if mac_is_module:
                    self.mods_[name] = mac
                else:
                    self.macs_[name] = mac

                continue
            elif op in heads:
                dpt += 1
            elif op == "end":
                dpt -= 1

            if dpt == 0:
                break
            elif op != "":
                self.code_.append([op] + args)

    def create_vars(self, parent):
        vs = Area(range(len(self.params_)), name_=self.name_, parent_=parent)

        for name in self.params_:
            vs.create_member(name, 1)

        return vs

    def code(self, args):
        vars_ = []

        if self.is_reentrant_:
            yield ["scope"]

        for i in self.code_:
            op, *i_args = i
            is_decl = False

            if op == "":
                continue

            if self.is_reentrant_ and not self.is_module_:
                if op in ["int", "long"]:
                    vars_.extend(i_args)
                    i = [op] + list(map(self.mangle, i_args))
                    is_decl = True
                elif op in ["struct"]:
                    vars_.append(i_args[0])
                    i = [op, self.mangle(i_args[0])] + i_args[1:]
                    is_decl = True
                elif op == "undef":
                    _ = list(map(vars_.remove, i_args))
                    i = [op] + list(map(self.mangle, i_args))
                    is_decl = True
                elif op in ["typedef", "const", "macro", "module"] or op.startswith(":"):
                    is_decl = True

            if is_decl:
                yield i
            else:
                yield [self.export_qname(j, args, vars_) for j in i]

        if self.is_reentrant_:
            yield ["end"]
        yield [" endmacro"]

    def mangle(self, name):
        s = name
        o = self

        while o is not None:
            s = o.name_ + "_" + s
            o = o.module_

        return "__auto_var__" + s

    def export_qname(self, qname: str, args: List[str], vars: List[str]=None):
        nodes = qname.split(".")

        for i, node in enumerate(nodes):
            param = ""
            local = ""

            if i == 0 and node in self.params_:
                param = node
            elif i == 0 and node in self.macs_ and not self.is_module_:
                local = self.name_ + "." + node
            elif i == 0 and node in vars and not self.is_module_:
                local = self.mangle(node)
            elif node.startswith("$") and node[1:] in self.params_:
                param = node[1:]

            if param != "":
                nodes[i] = args[self.params_.index(param)]
            elif local != "":
                nodes[i] = local

        return ".".join(nodes)




if __name__ == "__main__":
    # main-loop with flattened recursive-calls that should be rewritten
    root = Area(range(65536), is_scope_=True)
    areas_ = [root]
    types_ = {}
    opts_ = {"CELL_SIZE": 1}
    module_instances: Dict[str, Area] = {}
    # modules that should be deallocated at end of scope
    modscopes: List[List[str]] = [[]]
    # stack that indicates either current macro is module_member or not?
    mods: List[str] = [""]

    for arg in sys.argv:
        sep = ""
        if arg.startswith("-"):
            sep = "="
            arg = arg[1:]
        elif arg.startswith("/"):
            sep = ":"
            arg = arg[1:]

        if arg.startswith("D"):
            name, value = arg[1:].split(sep)

            if value == "":
                value = "1"

            opts_[name] = value

    # pass config at here
    prog = Macro("", sorted(opts_.keys()), is_module=True)
    prog.load()
    root_prog = prog
    codes = [(prog, prog.code([opts_[i] for i in sorted(opts_)]))]
    macs = [prog.macs_]

    def in_mod_mac():
        return len(mods) and mods[-1] != ""

    def get_mac(name):
        mac = prog.search(name)
        if mac is not None:
            return mac

        mac = root_prog.search(name)
        if mac is not None:
            return mac

        return None
    def qualify_var_name(qname):
        if qname.startswith(".") and in_mod_mac():
            mod_name = mods[-1]
            mod_vars = module_instances[mod_name]

            v = mod_vars.search(qname[1:])
            if v is not None:
                return mod_name + qname

        return qname

    def get_var(qname, allow_none=False):
        # if current scope is inside module member macro
        if qname.startswith("."):
            if in_mod_mac():
                mod_vars = module_instances[mods[-1]]

                v = mod_vars.search(qname[1:])
                if v is not None:
                    return v
        else:
            for i in reversed(areas_):
                v = i.search(qname)
                if v is not None:
                    return v

        if allow_none:
            return None

        raise Exception(f"unknown {qname}")

    def is_var(qname):
        return get_var(qname, allow_none=True) is not None

    def load_module(name):
        if name in module_instances:
            return None

        if name not in root_prog.mods_:
            raise Exception(f"undefined module {name}")

        mod = root_prog.mods_[name]
        mod_fields = mod.create_vars(area_)
        module_instances[name] = mod_fields
        area_.add_member(mod_fields)
        modscopes[-1].append(name)

        if "init" in mod.macs_:
            return mod.macs_["init"]

        return None

    def unload_module(name):
        if name not in module_instances:
            raise Exception(f"module {name} is not loaded")

        if name not in root_prog.mods_:
            raise Exception(f"undefined module {name}")

        mod_fields = module_instances.pop(name)
        scope = cast(Area, mod_fields.parent())
        scope.remove_member(name)
        modscopes[-1].remove(name)

    def dump_macro(mac: Macro, dpt=0):
        tab = "  " * dpt
        sys.stderr.write(tab + mac.name_ + f"({mac.mod_name()}) [{mac.params_}]\n")

        if mac.name_ in module_instances:
            vs = module_instances[mac.name_]
            sys.stderr.write(tab + f"at: {vs.absolute_address()} size:{vs.size()}\n")


        if len(mac.mods_):
            sys.stderr.write(tab + "modules:\n")
            for m in mac.mods_:
                dump_macro(mac.mods_[m], dpt + 1)

        if len(mac.macs_):
            sys.stderr.write(tab + "macros:\n")
            for m in mac.macs_:
                dump_macro(mac.macs_[m], dpt + 1)


    # dump_macro(prog)

    block_heads = []

    skip = 0
    while len(codes):
        prog, prog_code = codes.pop()

        if not len(areas_):
            raise Exception("no scope! maybe any bug")

        for code in prog_code:
            area_ = areas_[-1]
            op, *args = code

            # print(f"## {op} {args}")

            if skip > 0:
                if op in ["is_var", "isn_var", "is_val", "isn_val"]:
                    skip += 1
                if op == "endis":
                    skip -= 1

                continue
            if op == "endis":
                continue
            elif op in ["is_var", "isn_var"]:
                n_defined = list(filter(is_var, args))
                if op == "is_var":
                    cond = len(n_defined) == len(args)
                else:
                    cond = len(n_defined) == 0
                skip = int(not cond)
                continue
            elif op in ["is_val", "isn_val"]:
                n_defined = list(filter(str.isdigit, args))
                if op == "is_val":
                    cond = len(n_defined) == len(args)
                else:
                    cond = len(n_defined) == 0
                skip = int(not cond)

                continue


            mac = get_mac(op)
            if mac is not None:
                codes.append((prog, prog_code))
                codes.append((mac, mac.code(list(map(qualify_var_name, args)))))
                macs.append(mac.macs_)
                mods.append(mac.mod_name())
                break
            elif op == "import":
                mod_name = args[0]
                mac = load_module(mod_name)
                if mac is not None:
                    codes.append((prog, prog_code))
                    codes.append((mac, mac.code(list(map(qualify_var_name, args[1:])))))
                    macs.append(mac.macs_)
                    mods.append(mod_name)
                    break
            elif op == "log":
                sys.stderr.write(" ".join(args) + "\n")
            elif op == "log_dump":
                dump_macro(root_prog)
            elif op == " endmacro":
                macs.pop()
                mods.pop()
                break
            elif op == "end":
                block_type, block_arg = block_heads.pop()

                if block_type == "scope":
                    scope = areas_.pop()

                    for member in scope.members():
                        if member.name() in module_instances:
                            print(f"unload {member.name()}")
                            unload_module(member.name())

                    if area_.has_parent():
                        area_.parent().pop_subarea(area_)

                    area_ = areas_[-1]
                elif block_type in ["if", "while"]:
                    CodeGenerator.put_select(0, block_arg)
                    print("[-]]" if block_type == "if" else "]")
                    CodeGenerator.put_select(block_arg, 0)
            elif op == "typedef":
                members_ = []
                types_[args[0]] = members_

                i = 0
                args = args[1:]
                while i < len(args):
                    if args[i] == "extend":
                        i += 1

                        for j in types_[args[i]]:
                            members_.append(j)
                    elif args[i] == "typeof":
                        i += 1

                        if i >= len(args):
                            break

                        template = list(area_.search(args[i]).members())

                        for j in template:
                            members_.append(j.name())

                    else:
                        members_.append(args[i])

                    i += 1
            elif op == "struct":
                area_.create_member(args[0], 256)
                v = area_.member(args[0])

                member_size_ = 1
                i = 0
                args = args[1:]
                while i < len(args):
                    if args[i] == "extends":
                        i += 1

                        if args[i] not in types_:
                            raise Exception(f"unknown type {args[i]}")

                        for j in types_[args[i]]:
                            v.create_member(j, 1)
                    elif args[i] == "typeof":
                        i += 1

                        if i >= len(args):
                            break

                        template = list(area_.search(args[i]).members())

                        for j in template:
                            v.create_member(j.name(), j.size())

                    # elif args[i] == "long":
                    #     member_size_ = 2
                    elif args[i] == "int":
                        member_size_ = 1
                    else:
                        v.create_member(args[i], member_size_)

                    i += 1

                v.optimize_layout()
                v.resize(v.least_size())

            elif op == "int":
                for i in args:
                    area_.create_member(i, 1)

            elif op == "long":
                for i in args:
                    area_.create_member(i, 2)

            elif op == "undef":
                for i in args:
                    area_.remove_member(i)

            elif op == "moveadd":
                from_ = get_var(args[0])

                if len(list(from_.members())):
                    for member_ in from_.members():
                        name = member_.name()
                        dsts = [v.member(name).absolute_address()
                                    for v in map(get_var, args[1:]) if v.has_member(name)]

                        CodeGenerator.put_move(member_.absolute_address(), dsts)
                elif from_.size() > 1:
                    src_base = from_.absolute_address()
                    for i in range(from_.size()):
                        dsts = [v.absolute_address() + i
                                    for v in map(get_var, args[1:]) if i < v.size()]

                        CodeGenerator.put_move(src_base + i, dsts)
                else:
                    CodeGenerator.put_move(
                            from_.absolute_address(),
                            map(Locatable.absolute_address, map(get_var, args[1:])))

                print("")
            elif op in ["input", "print"]:
                addr = 0
                for arg in args:
                    v = get_var(arg)

                    for addr2 in v.absolute_address_range():
                        CodeGenerator.put_select(addr, addr2)
                        print("." if op == "print" else ",")
                        addr = addr2

                CodeGenerator.put_select(addr, 0)

            elif op in ["set", "clear", "add", "sub"]:
                if op == "clear":
                    args = [0] + args

                op1 = "[-]" if op in ["set", "clear"] else ""
                op2 = "-" if op == "sub" else "+"

                src = int(args[0])
                addr = 0

                for dst in args[1:]:
                    v = get_var(dst)
                    addr2 = v.absolute_address()
                    CodeGenerator.put_select(addr, addr2)
                    print(op1 + op2 * src)
                    addr = addr2
                CodeGenerator.put_select(addr, 0)
            elif op == "scope":
                area_.optimize_layout(keep_addresses_=True)
                area2_ = Area(range(area_.size() - area_.least_size()), is_scope_=True, parent_=area_)

                area_.append_subarea(area2_)
                areas_.append(area2_)

                area_ = area2_

                block_heads.append(("scope", None))
            elif op in ["if", "while"]:
                v = get_var(args[0])

                CodeGenerator.put_select(0, v.absolute_address())
                print("[")
                CodeGenerator.put_select(v.absolute_address(), 0)

                block_heads.append((op, v.absolute_address()))
            else:
                sys.stderr.write(f"unknown op {op}\n")



