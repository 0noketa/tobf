# Linefuck6 to Brainfuck compiler
#
# Linefuck6
# https://esolangs.org/wiki/Linefuck6

# charset(0..):
# a-z A-Z 0-9 spc


def compile(src: str):
    data = [0 for _ in range(10)]
    ptr = 0
    # layout: 0,_, 0,_, 0,_, 0,_,  0,*v0, 0,v1, 0, ..., v8, 0,v9, 1
    dst = ">>>>>>>>"
    dst += (">>" * 10) + "+" + ("<<" * 10)
    dst += ">"

    for c in src:
        if c == "-":
            if ptr != -1 and data[ptr] != -1:
                if data[ptr] < 62:
                    dst += "+"
                    data[ptr] += 1
                else:
                    while dst.endswith("+"):
                        dst = dst[:-1]
                    data[ptr] = 0
            else:
                dst += "+" + ("-" * 63) + "[[<+>-]<" + ("+" * 63) + ">]<[>+<-]>"
        elif c == "\u2013":
            if ptr != -1:
                dst += ">>"
                ptr += 1
                if ptr == 9:
                    ptr = -1
            else:
                dst += "> <<+>>[<<->> " + ("<<" * 10) + ">>] <<[->>] >"
        elif c == "_":
            dst += "[<+<<<<<<<<+>>>>>>>>>-]"
            dst += "<[>+<-]>"
            dst += "<+<<+<<+<<+>>>>>>>"
            dst += ("[" + ("-[" * 25)
                        + ("-[" * 26)
                            + ("-[" * 10)
                                + ("-[" * 1)
                                + "[-]<<<<<<<->>>>>>>"
                                + ("]" * 1)
                            + "<<<<<->>>>>"
                            + ("]" * 10)
                        + "<<<->>>"
                        + ("]" * 26)
                    + "<->"
                    + ("]" * 25) + "]")
            dst += "<<<<<<<<<[>>>>>>>>>+<<<<<<<<<-]>>>>>>>>>"
            dst += "<[>" + ("+" * 97) + "." + ("-" * 97) + "<-<<-<<-<<->>>>>>]>"
            dst += "<<<[>>>" + ("+" * (65 - 26)) + "." + ("-" * (65 - 26)) + "<<<-<<-<<->>>>]>>>"
            dst += "<<<<<[>>>>>" + ("-" * (52 - 48)) + "." + ("+" * (52 - 48)) + "<<<<<-<<->>]>>>>>"
            dst += "<<<<<<<[>>>>>>>" + ("-" * 30) + "." + ("+" * 30) + "<<<<<<<-]>>>>>>>"
            # dst += "."
        elif c == "~":
            dst += ","
            if ptr != -1:
                data[ptr] = -1
        elif c == "'":
            dst += "["
            ptr = -1
        elif c == "\"":
            dst += "]"

    return dst


if __name__ == "__main__":
    import sys
    import io
    import encodings

    encoding = "utf-8"
    file_name = ""

    for arg in sys.argv[1:]:
        if arg.startswith("-e"):
            encoding = arg[2:]
        elif not arg.startswith("-"):
            file_name = arg

    src = ""    
    if file_name == "":
        if sys.stdin.encoding != encoding:
            sys.stderr.write(f"stdin is encoded as {encodings.normalize_encoding(sys.stdin.encoding)}.\n")
            sys.exit(1)
        else:
            src = sys.stdin.read()
    else:
        with io.open(file_name, "r", encoding=encoding) as f:
            src = f.read()

    dst = compile(src)

    print(dst)
