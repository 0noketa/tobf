

def skip_loop(s: str, i: int = 0) -> int:
    if s[i] != "[":
        return i + 1

    d = 0
    for j in range(i + 1, len(s)):
        if s[j] == "[":
            d += 1
        elif s[j] == "]":
            if d == 0:
                return j + 1
            d -= 1

    return len(s)

def remove_deadloops(s: str, is_main=False) -> str:
    i = 0
    while i < len(s) - 1:
        if s[i] == "]" and s[i + 1] == "[":
            j = skip_loop(s, i + 1)
            s = s[:i + 1] + s[j:]
        else:
            i += 1

    if is_main:
        i = 0
        while i < len(s) - 1:
            if s[i] == "[":
                j = skip_loop(s, i)
                s = s[:i] + s[j:]
            elif s[i] in "+-,":
                break
            else:
                i += 1

    return s

def optimize(s: str, is_main=False) -> str:
    tbl = {
        "<>": "",
        "><": "",
        "][-]": "]",
        "+-": "",
        "-+": ""
    }

    s = "".join(filter(lambda x: x in "><+-[],.", s))

    replaced = True
    while replaced:
        replaced = False

        for key in tbl.keys():
            if key in s:
                s = s.replace(key, tbl[key])
                replaced = True

        s0 = s
        s = remove_deadloops(s, is_main)
        if s != s0:
            replaced = True

    return s

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-?", "/?", "-help", "--help"]:
        print(f"python {sys.argv[0]} [-main] < input.bf > output.bf")
        print(f"  -main  ignores initial data")

        sys.exit(0)

    is_main = len(sys.argv) > 1 and sys.argv[1] == "-main"

    src = optimize("".join(map(optimize, sys.stdin.readlines())), is_main=is_main)

    w = 80
    for i in range(0, len(src), w):
        print(src[i:i+w])

    sys.exit(0)
