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

if __name__ == "__main__":
    import sys

    comment = len(sys.argv) > 1 and sys.argv[1] == "-keep_source"

    src = input().strip()
    vrs = list(filter(len, map(str.strip, src.split())))

    if comment:
        put(src)

    while True:
        src = input().strip()
        cod = list(filter(len, map(str.strip, src.split())))

        if len(cod) == 0:
            continue

        if comment:
            put(src)

        if cod[0] == "#":
            if comment:
                put(src)
            continue

        if len(cod) < 2 or cod[0] == "end":
            break

        if cod[0] in ["set", "add", "sub"]:
            if len(cod) < 3:
                print("error:", cod)
                break

            n = int(cod[1])
            v = vrs.index(cod[2])

            begin(v)
            if cod[0] == "set":
                put("[-]")
            
            if cod[0] == "sub":
                dec(n)
            else:
                inc(n)
    
            end(v)

            continue

        if cod[0] in ["copy", "copyadd", "copysub"]:
            if len(cod) < 3:
                print("error:", cod)
                break

            v_from = vrs.index(cod[1])

            # clear dst
            if cod[0] == "copy":
                for name in cod[2:]:
                    v_to = vrs.index(name)

                    begin(v_to)
                    put("[-]")
                    end(v_to)

            # to it
            begin(v_from)
            put("[")
            end(v_from)
            put("+")
            begin(v_from)
            put("-]")
            end(v_from)

            put("[")

            v_to = vrs.index(cod[1])

            begin(v_to)
            put("+")
            end(v_to)


            for name in cod[2:]:
                v_to = vrs.index(name)

                begin(v_to)
                put("+" if cod[0] != "copysub" else "-")
                end(v_to)

            put("-]")

            continue


        if cod[0] in ["move", "moveadd", "movesub"]:
            if len(cod) < 3:
                print("error:", cod)
                break

            v_from = vrs.index(cod[1])

            begin(v_from)
            put("[")
            end(v_from)

            for name in cod[2:]:
                v_to = vrs.index(name)

                begin(v_to)

                if cod[0] == "move":
                    put("[-]")

                put("-" if cod[0] == "movesub" else "+")
                end(v_to)

            begin(v_from)
            put("-]")
            end(v_from)

            continue

        if cod[0] in ["if", "while"]:
            if len(cod) < 2:
                print("error:", cod)
                break

            v_from = vrs.index(cod[1])

            begin(v_from)
            put("[")
            end(v_from)

            uplevel()

            continue

        if cod[0] in ["endif", "endwhile"]:
            if len(cod) < 2:
                print("error:", cod)
                break

            v_from = vrs.index(cod[1])

            downlevel()

            begin(v_from)
            put("[-]]" if cod[0] == "endif" else "]")
            end(v_from)

            continue

        if cod[0] == "ifelse":
            if len(cod) < 3:
                print("error:", cod)
                break

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
            if len(cod) < 3:
                print("error:", cod)
                break

            v_then = vrs.index(cod[1])
            v_else = vrs.index(cod[2])

            downlevel()

            begin(v_else)
            put("[-]")
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
            if len(cod) < 3:
                print("error:", cod)
                break

            v_from = vrs.index(cod[2])

            downlevel()

            begin(v_from)
            put("[-]]")
            end(v_from)

            continue

        if cod[0] in ["inc", "dec", "input", "print", "clear"]:
            if len(cod) < 2:
                print("error:", cod)
                break

            tbl = {
                "inc": "+",
                "dec": "-",
                "input": ",",
                "print": ".",
                "clear": "[-]"
            }

            v_from = vrs.index(cod[1])

            begin(v_from)
            put(tbl[cod[0]])
            end(v_from)

            continue

        if cod[0] in ["inc", "dec"]:
            if len(cod) < 2:
                print("error:", cod)
                break

            v_from = vrs.index(cod[1])

            begin(v_from)
            put("+" if cod[0] == "inc" else "-")
            end(v_from)

            continue

        print("error unknown:", cod)
        break
