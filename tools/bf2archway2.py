# Brainfuck to Archway2 compiler (stub)

def compile(input_file, output_file):
    dpt = 0
    put = lambda s: output_file.write(("   " * dpt) + s + "\n")

    put("/")
    put("+ \\")
    put(" -")
    while True:
        c = input_file.read(1)
        if len(c) == 0:
            break

        if c in "><+-,.":
            put(f" {c}")
        elif c == "[":
            put("  /")
            put("     \\")
            put(" \\")
            dpt += 1
        elif c == "]":
            dpt -= 1
            put(" \\")
            put("    /")
            put(" +  +")
            put("/")
            put(" -  /")

    put("-\\")
    put("+/")

if __name__ == "__main__":
    import sys

    compile(sys.stdin, sys.stdout)
