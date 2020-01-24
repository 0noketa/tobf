
# a to-bf compiler for small outouts
# abi:
#   dynamic_addressing: every address is 8bits. only 256 bytes.
#     16bits addressing is planned as that cant be used both systems in once.
#     ex: initialize as 8bit addrs -> use -> clean -> initialize as 16bit addrs.
#   pointer: always points address 0 with value 0 at the beggining and the end
#   memory: temporary, ...vars, dynamic_memory
#     area of vars has no hidden workspace expects address 0).
#     dynamic_memory is optional. nothing exists until initialized manually. and can be cleaned up.
# linking(not yet):
#   sequencial or macro-injection.
#   linkers are required to read only first lines of every source.
# syntax:
#   program: var_decl "\n" instructions "end" "\n"
#   var_decl: id (" " id)*
#   instructions: (id (" " id)* "\n")*
# instructions:
# set imm ...out_vars_with_sign
#   every destination can starts with "+" or "-", they means add or sub instead of set 
#   aliases_with_inplicit_signs:
#     add imm ...out_vars
#     sub imm ...out_vars
#     clear ...out_vars
#       imm as 0 and no sign
#     inc ...out_vars
#       imm as 1 and sign as "+"
#     dec ...out_vars
#       imm as 1 and sign as "-"
# move in_var ...out_vars_with_sign
#   in_var becomes to 0
#   aliases_with_inplicit_signs:
#     moveadd in_var ...out_vars 
#     movesub in_var ...out_vars 
# copy in_var ...out_vars_with_sign
#   aliases_with_inplicit_signs:
#     copyadd in_var ...out_vars 
#     copysub in_var ...out_vars 
# resb imm
#   declare size of static memory. default=number of vars. only once works.
# mem_init imm
#   initialize imm bytes of dynamic memory. only once works.
# mem_clean imm
#   works only after mem_init. clean dynamic memory area.
#   mem_init and resb can be used after mem_clean again.
# mem_clean imm fast
#   fast and short version.
#   doesnt clear values. clears just 1 byte in every cell.
#   works when all values stored in memory was 0.
#   on highly optimized bf implementations, this version will not be fast. just short.
# mem_set imm_value ...addresses
#   set constant or use command to dynamic memory 
#   imm_value:
#     any digits
#       set constant
#     input
#       set input data. 
#     print
#       print data.
#   address:
#     +address or -address
#       add or sub. can exists only once and works only with digits value.
#     digits
#       address
#     var_name
#       uses pointer variable
# mem_w_move in_var ...addresses
#   set value from variable to dynamic memory. addresses are the same as mem_set.
# mem_w_moveadd in_var ...addresses
# mem_w_movesub in_var ...addresses
# mem_w_copy in_var ...addresses
# mem_w_copyadd in_var ...addresses
# mem_w_copysub in_var ...addresses
# mem_r_move in_var ...addresses
#   move value from  dynamic memory to variable. addresses are the same as mem_set.
# mem_r_moveadd address ...out_vars
# mem_r_movesub address ...out_vars
# mem_r_copy address ...out_vars
# mem_r_copyadd address ...out_vars
# mem_r_copysub address ...out_vars
# if cond_var
# endif cond_var
#   like "next i" in basic. this rule simplifies compiler.
#   currently compiler disallows no cond_var instructions.
# ifelse cond_var work_var
#   work_var carries run_else flag
# else cond_var work_var
# endifelse cond_var work_var
# while cond_var
# endwhile cond_var
# end
#   can not be omitted

idt = 0
def put(s):
    global idt
    print("  " * idt + s)
def uplevel():
    global idt
    idt += 1
def downlevel():
    global idt
    idt = idt - 1 if idt > 0 else 0

def begin_global(i):
    put(">" * int(i))
    
def end_global(i):
    put("<" * int(i))

def begin(i):
    put(">" * int(i + 1))
    
def end(i):
    put("<" * int(i + 1))

def inc_or_dec(c, n):
    for i in range(n // 16):
        put(c * 8 + " " + c * 8)

    m = n % 16
    if m == 0:
        pass
    elif m > 8:
        m = m % 8
        put(c * 8 + " " + c * m)
    else:
        put(c * m)

def inc(n):
    inc_or_dec("+", n)

def dec(n):
    inc_or_dec("-", n)

def clear(v):
    begin(v)
    put("[-]")
    end(v)

def move(in_var, out_vars, vrs):
    in_var = vrs.index(in_var)

    for out_var in out_vars:
        sign, out_var = separate_sign(out_var)
        out_var = vrs.index(out_var)

        if sign == "":
            clear(out_var)

    begin(in_var)
    put("[")
    end(in_var)

    for out_var in out_vars:
        sign, out_var = separate_sign(out_var)
        out_var = vrs.index(out_var)

        begin(out_var)
        put("-" if sign == "-" else "+")
        end(out_var)

    begin(in_var)
    put("-]")
    end(in_var)

def move_global(in_addr, out_addrs):
    for out_addr in out_addrs:
        begin_global(out_addr)
        put("[-]")
        end_global(out_addr)

    moveadd_global(in_addr, out_addrs)

def moveadd_global(in_addr, out_addrs):
    begin_global(in_addr)
    put("[")
    end_global(in_addr)

    for out_addr in out_addrs:
        begin_global(out_addr)
        put("+")
        end_global(out_addr)

    begin_global(in_addr)
    put("-]")
    end_global(in_addr)


def load_var(in_var):
    begin(in_var)
    put("[")
    end(in_var)
    put("+")
    begin(in_var)
    put("-]")
    end(in_var)

def load_global(addr):
    begin_global(addr)
    put("[")
    end_global(addr)
    put("+")
    begin_global(addr)
    put("-]")
    end_global(addr)

def store_it(out_globals, out_vars, vrs=[]):
    for out_var in out_vars:
        sign, out_var = separate_sign(out_var)

        if sign == "":
            v = vrs.index(out_var)

            clear(v)

    put("[")

    for out_global in out_globals:
        begin_global(out_global)
        inc(1)
        end_global(out_global)

    for out_var in out_vars:
        sign, out_var = separate_sign(out_var)
        
        v = vrs.index(out_var)

        begin(v)
        put("-" if sign == "-" else "+")
        end(v)

    put("-]")

def calc_small_pair(n, vs):
    """vs: num of vars"""
    """+{result0}[>+{result1}<-]"""

    n = n % 256
    x = 256
    y = 256
    s = 256
    for i in range(1, 256):
        if n % i == 0:
            j = n // i
            s2 = int(i + j * vs)

            if s2 < s:
                x = i
                y = j
                s = s2

    return max(x, y), min(x, y)

def separate_sign(name):
    if len(name) > 0 and name[0] in ["+", "-"]:
        return name[0], name[1:]
    else:
        return "", name

# memory
# current layout: it rope address flagEnd flagContinue carried value
cell_layout = {
    # "it": 0,
    "rope": 1,
    "address": 2,
    "flagEnd": 3,
    "flagContinue": 4,
    "carried": 5,
    "value": 6
}
_vars_size = 256
_vars_limited = False
def limit_vars(n=256):
    global _vars_size, _vars_limited

    if not _vars_limited:
        # contains inplicit it
        _vars_size = n + 1
        _vars_limited = True
def vars_size():
    """registers"""
    global _vars_size
    return _vars_size

def memcell_size(n_bytes=1):
    return len(cell_layout.keys()) + n_bytes

_mem_initialized = False
_mem_size = 0

def mem2_init(size=16):
    global cell_layout, _mem_initialized, _mem_size

    if not _mem_initialized:
        _mem_initialized = True
        _mem_size = int(cod[1])

def mem_init(size=16):
    global cell_layout, _mem_initialized, _mem_size

    if _mem_initialized:
        return

    _mem_initialized = True
    _mem_size = size

    # + eos
    size = size + 1
    rope = cell_layout["rope"]

    put(">" * vars_size())
    put(">" * rope)
    
    for i in range(size):
        put(">" * memcell_size())
        inc(1)

    put("<" * (vars_size() + memcell_size() * size + rope))

def mem_clean(fast=False):
    global cell_layout, _mem_initialized, _mem_size, _vars_limited

    if not _mem_initialized:
        return

    # + eos
    size = _mem_size + 2

    _vars_limited = False
    _mem_initialized = False
    _mem_size = 0

    # with large memory, loop with rope should be better than this.

    put(">" * vars_size())

    if fast:
        put(">" * cell_layout["rope"])
        for i in range(size):
            put(">" * memcell_size() + "[-]")
        put("<" * cell_layout["rope"])
    else:
        for i in range(size):
            put("[-]>" * memcell_size())

    put("<" * (vars_size() + memcell_size() * size))

def mem2_clean(fast=False):
    global cell_layout, _mem_initialized, _mem_size, _vars_limited

    if not _mem_initialized:
        return

    # + eos
    size = _mem_size + 2

    _vars_limited = False
    _mem_initialized = False
    _mem_size = 0

    if fast:
        return

    # with large memory, loop with rope should be better than this.

    put(">" * vars_size())

    for i in range(size):
        put("[-]>" * 2)

    put("<" * (vars_size() + size * 2))


def mem_set(value="1", address=0, vrs=[]):
    sign, address = separate_sign(address)

    # should check chars at here
    if not (address in vrs):
        address = int(address)

    if type(address) == str:
        v = vrs.index(address)
        load_var(v)

        put("[")
        begin(v)
        put("+")
        end(v)
        begin_global(vars_size() + cell_layout["address"])
        inc(1)
        end_global(vars_size() + cell_layout["address"])
        put("-]")

    begin_global(vars_size())

    if type(address) == int:
        begin_global(cell_layout["address"])
        inc(address)
        end_global(cell_layout["address"])

    put(""">>>>+[<<[>>>>>>>+<<<<<+<<-]>>>>>>>-<<<<<<+>[<->[-]]>>>>>>>+<<<<<<<<[>>>""")

    if value == "input":
        put(",")
    elif value == "print":
        put(".")
    else:
        if sign == "":
            put("[-]")

        value = int(value)
        if sign == "-":
            dec(value)
        else:
            inc(value)
    put(""">>>>>-<<[-]<<<<<<[-]]>>>>>>>>]+[-<<<<<<<<<<[>>>+<<<[-]]>>+>[<-<<+>>>[-]]+<[>-<[-]]>]<<<<""")

    end_global(vars_size())

def mem_w_move(value="1", address=0, vrs=[], copy=False):
    sign, address = separate_sign(address)

    # should check chars at here
    if not (address in vrs):
        address = int(address)
    if not (value in vrs):
        value = int(value)

    if type(address) == str:
        v = vrs.index(address)

        load_var(v)

        put("[")
        begin(v)
        put("+")
        end(v)
        begin_global(vars_size() + cell_layout["address"])
        inc(1)
        end_global(vars_size() + cell_layout["address"])
        put("-]")

    if type(value) == str:
        v = vrs.index(value)

        if copy:
            load_var(v)

            put("[")
            begin(v)
            put("+")
            end(v)
            begin_global(vars_size() + cell_layout["carried"])
            inc(1)
            end_global(vars_size() + cell_layout["carried"])
            put("-]")
        else:
            begin(v)
            put("[")
            end(v)
            begin_global(vars_size() + cell_layout["carried"])
            inc(1)
            end_global(vars_size() + cell_layout["carried"])
            begin(v)
            put("-]")
            end(v)

    begin_global(vars_size())

    if type(address) == int:
        begin_global(cell_layout["address"])
        inc(address)
        end_global(cell_layout["address"])

    # warrning: use mem_set instead of this.
    if type(value) == int:
        begin_global(cell_layout["carried"])
        inc(value)
        end_global(cell_layout["carried"])

    put(""">>>>+[>[>>>>>>>+<<<<<<<-]<<<[>>>>>>>+<<<<<+<<-]>>>>>>>-<<<<<<+>[<->[-]]>>>>>>>+<<<<<<<<[>>>""")
    if sign == "":
        put("[-]")
    put(""">>>>>>[<<<<<<""")
    if sign == "-":
        dec(1)
    else:
        inc(1)
    put(""">>>>>>-]<-<<[-]<<<<<<[-]]>>>>>>>>]""")
    put("""+[-<<<<<<<<<<[>>>+<<<[-]]>>+>[<-<<+>>>[-]]+<[>-<[-]]>]<<<<""")

    end_global(vars_size())

def mem_r_move(address=0, out_vars=[], vrs=[], copy=False):
    # should check chars at here
    if not (address in vrs):
        address = int(address)

    if type(address) == str:
        v = vrs.index(address)

        load_var(v)

        put("[")
        begin(v)
        put("+")
        end(v)
        begin_global(vars_size() + cell_layout["address"])
        inc(1)
        end_global(vars_size() + cell_layout["address"])
        put("-]")

    begin_global(vars_size())

    if type(address) == int:
        begin_global(cell_layout["address"])
        inc(address)
        end_global(cell_layout["address"])

    put(""">>>>+[<<[>>>>>>>+<<<<<+<<-]>>>>>>>-<<<<<<+>[<->[-]]>>>>>>>+<<<<<<<<[<<<""")

    if copy:
        put(""">>>>>>[<<<<<<+>>>>>>-]<<<<<<[>>>>>>+>>>>>>+<<<<<<<<<<<<-]""")
    else:
        put(""">>>>>>[>>>>>>+<<<<<<-]<<<<<<""")

    put(""">>>>>>>>>>>-<<[-]<<<<<<[-]]>>>>>>>>]""")
    put("""+[-<<<<<<[-]>>>>>>>[<<<<<<<+>>>>>>>-]<<<<<<<<<<<[>>>+<<<[-]]>>+>[<-<<+>>>[-]]+<[>-<[-]]>]<<<<""")

    end_global(vars_size())

    # load carried to it
    load_global(vars_size() + cell_layout["carried"])

    store_it([], out_vars, vrs)

def put_peek(address=0, is_imm=True):
    pass

if __name__ == "__main__":
    import sys

    comment = len(sys.argv) > 1 and sys.argv[1] == "-v"

    src = input().strip()
    vrs = list(filter(len, map(str.strip, src.split())))

    if comment:
        put(src)

    while True:
        src = input().strip()
        cod = list(filter(len, map(str.strip, src.split())))

        if len(cod) == 0:
            continue

        if cod[0] == "#":
            if comment:
                put(src)
            continue
        elif comment:
            put(src)

        if len(cod) > 0 and cod[0] == "end":
            put("[-]")
            break

        if len(cod) < 2:
            print("error:", cod)
            break

        if cod[0] == "bf":
            put(cod[1])

            continue

        if (len(cod) < 3
            and cod[0] in [
                "set", "add", "sub",
                "copy", "copyadd", "copysub",
                "move", "moveadd", "movesub",
                "mem_w_copy", "mem_w_copyadd", "mem_w_copysub",
                "mem_w_move", "mem_w_moveadd", "mem_w_movesub",
                "mem_r_copy", "mem_r_copyadd", "mem_r_copysub",
                "mem_r_move", "mem_r_moveadd", "mem_r_movesub",
                "mem2_w_copy", "mem2_w_copyadd", "mem2_w_copysub",
                "mem2_w_move", "mem2_w_moveadd", "mem2_w_movesub",
                "mem2_r_copy", "mem2_r_copyadd", "mem2_r_copysub",
                "mem2_r_move", "mem2_r_moveadd", "mem2_r_movesub",
                "ifelse", "else", "endifelse"]):
            print("error:", cod)
            break

        # aliases
        if cod[0] == "clear":
            cod = ["set", "0"] + cod[1:]

        if cod[0] in ["inc", "dec"]:
            sign = "+" if cod[0] == "inc" else "-"
            cod = ["set", "1"] + [sign + x for x in cod[1:]]

        if cod[0] in ["add", "sub"]:
            sign = "+" if cod[0] == "add" else "-"
            cod = ["set", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["copyadd", "copysub"]:
            sign = "+" if cod[0] == "copyadd" else "-"
            cod = ["copy", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["moveadd", "movesub"]:
            sign = "+" if cod[0] == "moveadd" else "-"
            cod = ["move", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem_w_copyadd", "mem_w_copysub"]:
            sign = "+" if cod[0] == "mem_w_copyadd" else "-"
            cod = ["mem_w_copy", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem_w_moveadd", "mem_w_movesub"]:
            sign = "+" if cod[0] == "mem_w_moveadd" else "-"
            cod = ["mem_w_move", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem_r_copyadd", "mem_r_copysub"]:
            sign = "+" if cod[0] == "mem_r_copyadd" else "-"
            cod = ["mem_r_copy", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem_r_moveadd", "mem_r_movesub"]:
            sign = "+" if cod[0] == "mem_r_moveadd" else "-"
            cod = ["mem_r_move", cod[1]] + [sign + x for x in cod[2:]]
            
        if cod[0] in ["mem2_w_copyadd", "mem2_w_copysub"]:
            sign = "+" if cod[0] == "mem2_w_copyadd" else "-"
            cod = ["mem2_w_copy", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem2_w_moveadd", "mem2_w_movesub"]:
            sign = "+" if cod[0] == "mem2_w_moveadd" else "-"
            cod = ["mem2_w_move", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem2_r_copyadd", "mem2_r_copysub"]:
            sign = "+" if cod[0] == "mem2_r_copyadd" else "-"
            cod = ["mem2_r_copy", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] in ["mem2_r_moveadd", "mem2_r_movesub"]:
            sign = "+" if cod[0] == "mem2_r_moveadd" else "-"
            cod = ["mem2_r_move", cod[1]] + [sign + x for x in cod[2:]]

        if cod[0] == "resb":
            size = int(cod[1])
            limit_vars(size)

            continue

        if cod[0] == "mem_init":
            # default
            limit_vars(len(vrs))

            size = int(cod[1])
            mem_init(size)

            continue

        if cod[0] == "mem2_init":
            # default
            limit_vars(len(vrs))

            size = int(cod[1])
            mem2_init(size)

            continue

        if cod[0] == "mem_clean":
            mem_clean(len(cod) > 2 and cod[2] == "fast")

            continue

        if cod[0] == "mem2_clean":
            mem2_clean(len(cod) > 2 and cod[2] == "fast")

            continue

        if cod[0] == "mem_set":
            # default
            limit_vars(len(vrs))
            mem_init(32)

            value = cod[1]

            for address in cod[2:]:
                mem_set(value, address, vrs)

            continue

        if cod[0] == "mem2_set":
            def put_value(value):
                if sign == "" and value.isdigit():
                    put("[-]")

                if value == "input":
                    put(",")
                elif value == "print":
                    put(".")
                else:
                    value = int(value)
                    if sign == "-":
                        dec(value)
                    else:
                        inc(value)

            # default
            limit_vars(len(vrs))
            mem_init(32)

            value = cod[1]

            for address in cod[2:]:
                sign, address = separate_sign(address)

                if not (address in vrs):
                    address = int(address)

                    begin_global(vars_size() + address * 2 + 1)

                    put_value(value) 
                    
                    end_global(vars_size() + address * 2 + 1)
                else:
                    v = vrs.index(address)

                    load_var(v)

                    put("[")
                    begin(v)
                    put("+")
                    end(v)

                    begin_global(vars_size() + 2)
                    inc(1)
                    end_global(vars_size() + 2)
                    put("-]")

                    begin_global(vars_size())
                    put(""">>[[>>+<<-]+>>-]<""")
                    put_value(value)
                    put("""<[-<<]""")
                    end_global(vars_size())

            continue

        if cod[0] in ["mem2_w_move", "mem2_w_copy"]:
            # default
            limit_vars(len(vrs))
            mem2_init(32)

            v = vrs.index(cod[1])

            if cod[0] == "mem2_w_copy":
                load_var(v)

                store_it([vars_size() + 4], ["+" + cod[1]], vrs)
            else:
                begin(v)
                put("[")
                end(v)
                begin_global(vars_size() + 4)
                put("+")
                end_global(vars_size() + 4)
                begin(v)
                put("-]")
                end(v)

            out_vars = cod[2:]

            for i in range(len(out_vars)):
                name = out_vars[i]
                sign, name = separate_sign(name)

                v = vrs.index(name)
                load_var(v)

                store_it([vars_size() + 2], ["+" + name], vrs)

                # for next destination
                if i < len(out_vars) - 1:
                    moveadd_global(vars_size() + 4, [vars_size()])
                    moveadd_global(vars_size(), [0, vars_size() + 4])

                begin_global(vars_size())
                put(""">>[->>[>>+<<-]<<[>>+<<-]+>>]""")
                if sign == "":
                    put("""<[-]>""")
                put(""">>[<<<""")
                put("-" if sign == "-" else "+")
                put(""">>>-]<<<<[-<<]""")
                end_global(vars_size())

                if i < len(out_vars) - 1:
                    moveadd_global(0, [vars_size() + 4])

            continue

        if cod[0] in ["mem2_r_move", "mem2_r_copy"]:
            # default
            limit_vars(len(vrs))
            mem2_init(32)

            address = cod[1]

            # clear dst of move/copy
            for name in cod[2:]:
                sign, name = separate_sign(name)

                if sign == "":
                    v = vrs.index(name)

                    clear(v)

            # static addressing
            if not (address in vrs):
                address = int(address)
                address = vars_size() + address * 2 + 1

                if cod[0] == "mem2_r_copy":
                    out_globals = [address]
                    out_vars = cod[2:]
                    last = ""
                else:
                    out_globals = []
                    out_vars = cod[2:-1]
                    last = cod[-1]

                # copy
                if len(out_vars) > 1:
                    load_global(address)

                    store_it(out_globals, out_vars, vrs)

                # move                
                if last != "":
                    sign, name = separate_sign(last)

                    v = vrs.index(name)

                    begin_global(address)
                    put("[")
                    end_global(address)
                    begin(v)
                    put("-" if sign == "-" else "+")
                    end(v)
                    begin_global(address)
                    put("-]")
                    end_global(address)
            else:
                v = vrs.index(address)

                load_var(v)

                store_it([vars_size() + 2], ["+" + address], vrs)

                begin_global(vars_size())
                put(""">>[[>>+<<-]+>>-]""")
                if cod[0] == "mem2_r_copy":
                    put("""<[>>>+<<<-]>>>[<<+<+>>>-]<<""")
                else:
                    put("""<[>+<-]>""")
                put("""<<[->>>>[<<+>>-]<<<<<<]>>>>[<<+>>-]<<<<""")
                end_global(vars_size())

                if False:  # ex: from set
                    begin_global(vars_size())
                    put(""">>[[>>+<<-]+>>-]<""")
                    put_value(value)
                    put("""<[-<<]""")
                    end_global(vars_size())


                begin_global(vars_size() + 2)
                put("[")
                end_global(vars_size() + 2)

                for name in cod[2:]:
                    sign, name = separate_sign(name)
                    v = vrs.index(name)

                    begin(v)
                    put("-" if sign == "-" else "+")
                    end(v)

                begin_global(vars_size() + 2)
                put("-]")
                end_global(vars_size() + 2)

            continue

        if cod[0] == "mem_w_copy":
            # default
            limit_vars(len(vrs))
            mem_init(32)

            value = cod[1]

            for address in cod[2:]:
                mem_w_move(value, address, vrs, True)

            continue

        if cod[0] == "mem_w_move":
            # default
            limit_vars(len(vrs))
            mem_init(32)

            value = cod[1]


            for address in cod[2:-1]:
                mem_w_move(value, address, vrs, True)

            mem_w_move(value, cod[-1], vrs, False)

            continue

        if cod[0] == "mem_r_copy":
            # default
            limit_vars(len(vrs))
            mem_init(32)

            address = cod[1]

            mem_r_move(address, cod[2:], vrs, True)

            continue

        if cod[0] == "mem_r_move":
            # default
            limit_vars(len(vrs))
            mem_init(32)

            address = cod[1]

            mem_r_move(address, cod[2:], vrs, False)

            continue

        if cod[0] == "set":
            n = int(cod[1])

            vs = len(cod) - 2
            if vs == 1 or n <= 8:
                for name in cod[2:]:
                    sign, name = separate_sign(name)

                    v = vrs.index(name)
                    begin(v)

                    if sign == "":
                        put("[-]")
                    
                    if sign == "-":
                        dec(n)
                    else:
                        inc(n)
            
                    end(v)
            else:
                n, m = calc_small_pair(n, vs)

                for name in cod[2:]:
                    sign, name = separate_sign(name)

                    if sign != "":
                        continue

                    v = vrs.index(name)

                    clear(v)

                inc(n)
                put("[")
                uplevel()

                for name in cod[2:]:
                    sign, name = separate_sign(name)

                    v = vrs.index(name)

                    begin(v)
                    if sign == "-":
                        dec(m)
                    else:
                        inc(m)
            
                    end(v)

                downlevel()
                put("-]")

            continue

        if cod[0] in "copy":
            v_from = vrs.index(cod[1])

            # move to it
            load_var(v_from)

            # copy and restore
            store_it([], cod[2:] + ["+" + cod[1]], vrs)

            continue


        if cod[0] in "move":
            move(cod[1], cod[2:], vrs)

            continue

        if cod[0] in ["if", "while"]:
            v_from = vrs.index(cod[1])

            begin(v_from)
            put("[")
            end(v_from)

            uplevel()

            continue

        if cod[0] in ["endif", "endwhile"]:
            v_from = vrs.index(cod[1])

            downlevel()

            begin(v_from)
            put("[-]]" if cod[0] == "endif" else "]")
            end(v_from)

            continue

        if cod[0] == "ifelse":
            v_then = vrs.index(cod[1])
            v_else = vrs.index(cod[2])

            begin(v_else)
            put("[-]+")
            end(v_else)

            begin(v_then)
            put("[")
            end(v_then)

            uplevel()

            continue

        if cod[0] == "else":
            v_then = vrs.index(cod[1])
            v_else = vrs.index(cod[2])

            downlevel()

            begin(v_else)
            put("-")
            end(v_else)

            begin(v_then)
            put("[-]]")
            end(v_then)

            begin(v_else)
            put("[")
            end(v_else)

            uplevel()

            continue

        if cod[0] == "endifelse":
            v_from = vrs.index(cod[2])

            downlevel()

            begin(v_from)
            put("-]")
            end(v_from)

            continue

        if cod[0] in ["input", "print"]:
            tbl = {
                "input": ",",
                "print": ".",
            }

            for name in cod[1:]:
                v_from = vrs.index(name)

                begin(v_from)
                put(tbl[cod[0]])
                end(v_from)

            continue

        print("error unknown:", cod)
        break
