# Stable interpreter
#
# this language seems unable to push any non-zero value over 0
#
# Stable
# https://esolangs.org/wiki/Stable


def run(src: str, out):
    stk = [1]

    i = 0
    while i < len(src):
        c = src[i]

        if len(stk) < 2 and c in "+-*/":
            return (stk, (i, "empty stack"))

        if c == "~":
            stk.append(0)
        elif c == "+":
            stk.append(stk.pop() + stk.pop())
        elif c == "-":
            b = stk.pop()
            a = stk.pop()
            stk.append(a - b)
        elif c == "*":
            stk.append(stk.pop() * stk.pop())
        elif c == "/":
            b = stk.pop()
            a = stk.pop()
            if b == 0:
                return (stk, (i, "div by 0"))

            stk.append(a // b)
        elif c == ":":
            stk.append(stk[-1])
        elif c == ".":
            # out.write(ord(stk[-1]))
            print(stk[-1])
        elif c == "(":
            if stk[-1] == 0:
                d = 0
                i += 1
                while i < len(src) and (d > 0 or src[i] != ")"):
                    if src[i] == "(":
                        d += 1
                    if src[i] == ")":
                        d -= 1
                    i += 1
        elif c == ")":
            if stk[-1] != 0:
                d = 0
                i -= 1
                while i < len(src) and (d > 0 or src[i] != "("):
                    if src[i] == "(":
                        d -= 1
                    if src[i] == ")":
                        d += 1
                    i -= 1
        i += 1

    return (stk, None)


if __name__ == "__main__":
    import sys

    src = sys.stdin.read()

    results, error = run(src, sys.stdout)

    sys.stderr.write("stack: " + ", ".join(map(str, results)) + "\n")

    if error is not None:
        i, msg = error

        sys.stderr.write(
            f"error: {msg}\n\n"
            + src[max(0, i - 16):i] + "\n"
            + f"`{src[i]}` <-- error\n"
            + src[i + 1:i + 16] + "\n")

