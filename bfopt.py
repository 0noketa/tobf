

def optimize(s: str) -> str:
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

    return s

if __name__ == "__main__":
    import sys

    src = optimize("".join(map(optimize, sys.stdin.readlines())))

    w = 80
    for i in range(0, len(src), w):
        print(src[i:i+80])
