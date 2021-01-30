import sys

def check_balanced_loop(s: str, ptr: int = 0, from_: int = 0, to_: int = -1, mask: list = [], max_mem_size: int = -1) -> bool:
    """s[from_:to_] as loop excludes []\n
       mask: in/out. memory constraint. element is True if cell was broken by this loop.
       result: False if loop is not balanced
    """
    if to_ == -1:
        to_ = len(s)

    ptr0 = ptr

    i = from_
    while i < to_:
        if s[i] == "]":
            raise Exception(f"error")

        if s[i] == "[":
            j = skip_loop(s, i)
            
            if not check_balanced_loop(s, ptr, i + 1, j - 1, mask, max_mem_size):
                return False
            
            i = j
            continue

        if s[i] == ">":
            ptr += 1
            if ptr >= len(mask):
                if max_mem_size != -1:
                    raise Exception(f"error")

                mask.extend([False for i in range(len(mask))])
        elif s[i] == "<":
            ptr -= 1
        elif s[i] in ["+", "-", ","]:
            mask[ptr] = True
 
        i += 1

    return ptr == ptr0

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

def remove_deadloops(s: str, is_main=False, max_mem_size=-1) -> str:
    i = 0
    while i < len(s):
        if i + 1 < len(s) and s[i] == "]" and s[i + 1] == "[":
            j = skip_loop(s, i + 1)
            s = s[:i + 1] + s[j:]
        else:
            i += 1

    if is_main:
        if max_mem_size == -1:
            mem_size = 0x10000
        else:
            mem_size = max_mem_size

        ptr = 0
        mask = [False for i in range(mem_size)]
        i = 0
        while i < len(s):
            if s[i] == "[":
                j = skip_loop(s, i)

                if mask[ptr]:
                    if not check_balanced_loop(s, ptr, i + 1, j - 1, mask, max_mem_size):
                        # stops at live unbalanced loop
                        break

                    mask[ptr] = False
                    i = j
                else:
                    s = s[:i] + s[j:]

                continue

            if s[i] == ">":
                ptr += 1
                if ptr >= mem_size:
                    if max_mem_size != -1:
                        raise Exception(f"error")

                    mask += [False for i in range(mem_size)]
                    mem_size *= 2
            elif s[i] == "<":
                ptr -= 1
            elif s[i] in ["+", "-", ","]:
                mask[ptr] = True

            i += 1

    return s

def optimize(s: str, is_partial=True, is_main=False, max_mem_size=-1) -> str:
    tbl = {
        "<>": "",
        "><": "",
        "[+]": "[-]",
        "+[-]": "[-]",
        "-[-]": "[-]",
        "[[-]]": "[-]",
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

        if not is_partial:
            s0 = s
            s = remove_deadloops(s, is_main, max_mem_size)
            if s != s0:
                replaced = True

    if is_main:
        if max_mem_size == -1:
            mem_size = 0x10000
        else:
            mem_size = max_mem_size

        i = 0
        while i < len(s):
            i = s.find("]", i + 1)

            if i == -1:
                break

            ptr = mem_size
            mask = [True for _ in range(mem_size * 2)]
            mask[ptr] = False

            j = i + 1
            while j < len(s):
                if s[j] == "]":
                    break

                if s[j] == "[":
                    k = skip_loop(s, j)

                    if mask[ptr]:
                        if not check_balanced_loop(s, ptr, j + 1, k - 1, mask, mem_size * 2):
                            break

                        mask[ptr] = False
                        j = k
                    else:
                        s = s[:j] + s[k:]

                    continue

                if s[j] in ["+", "-", ","]:
                    mask[ptr] = True
                elif s[j] == ">":
                    ptr += 1
                elif s[j] == "<":
                    ptr -= 1

                j += 1


    return s

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] in ["-?", "/?", "-help", "--help"]:
        print(f"python {sys.argv[0]} [-main [memory_size]] < input.bf > output.bf")
        print(f"  -main  ignores initial data")

        sys.exit(0)

    is_main = len(sys.argv) > 1 and sys.argv[1] == "-main"
    memory_size = int(sys.argv[2]) if is_main and len(sys.argv) > 2 else -1

    src = optimize("".join(map(optimize, sys.stdin.readlines())), is_partial=False, is_main=is_main, max_mem_size=memory_size)

    w = 80
    for i in range(0, len(src), w):
        print(src[i:i+w])

    sys.exit(0)
