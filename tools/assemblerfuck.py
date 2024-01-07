# AssemblerFuck/AssemblerFuck++ to Brainfuck assembler
#
# limitation:
#   OBJECT/TARGET validation is AssemblerFuck++
#   implements "MOV LEFT|RIGHT, IN" as "<,>|>,<"
#
#   maybe Helloworld is incorrect
#
# layout:
#   v0, ...tmps, v1, ...tmps, v2, ...tmps, ...
#
#   instructions below require temporaries.
#     "IF", "DO", "MOV OUT, IN"
#
# additional instructions:
#  BREAK          exit from current DO block.
#
# AssemblerFuck
# https://esolangs.org/wiki/AssemblerFuck
# AssemblerFuck++
# https://esolangs.org/wiki/AssemblerFuck%2B%2B
import sys
import re

ENABLE_EXTENSIONS = True


def getnum(a: list[str], idx=0):
    if len(a) <= idx:
        raise Exception()
    s = a[idx]
    if s is None or not s.isdigit():
        raise Exception()

    return int(s)

def getreg(a: list[str], idx=0, istarget=False):
    if len(a) <= idx:
        raise Exception()
    s = a[idx]
    cmds = [
        ["P", "IN"],
        ["P", "RIGHT", "LEFT", "OUT"]
    ][int(istarget)]
    if s is None or s not in cmds:
        raise Exception()

    return s

def uses_tmp(cmd, args):
    if cmd in ["IF", "DO"]:
        return True
    if cmd == "MOV":
        arg0 = getreg(args, 0, istarget=True)
        arg1 = getreg(args, 1)

        return arg0 == "OUT" and arg1 == "IN"

    return False

def compile(src):
    with_tmp = False
    with_break = False
    src2 = []
    for line in src:
        line: str = line
        try:
            line2 = line.strip().split(" ", maxsplit=1)
            cmd = line2[0].strip()
            if cmd == "":
                continue

            args = list(map(str.strip, line2[1].split(","))) if len(line2) > 1 else []
            src2.append((cmd, args))

            if not with_tmp and uses_tmp(cmd, args):
                with_tmp = True            

            if cmd == "BREAK":
                with_break = True
        except:
            sys.stderr.write(f"error: {line}\n")
            break

    blocks = []
    i = 0
    while i < len(src2):
        cmd, _ = src2[i]
        if cmd in ["DO", "IF", "UNTIL"]:
            blocks.append(cmd)
        if cmd == "END":
            blocks.pop()

        if cmd == "BREAK":
            j = i + 1
            src2.insert(j, ("BREAK_skip", []))
            j += 1
            i += 1

            blocks2 = blocks.copy()
            depth = 0
            while j < len(src2):
                cmd2, _ = src2[j]
                if cmd2 in ["DO", "IF", "UNTIL"]:
                    depth += 1
                    blocks2.append(cmd2)
                elif cmd2 == "END":
                    depth -= 1
                    block = blocks2.pop()

                    if depth == -1:
                        depth = 0
                        src2.insert(j, ("BREAK_endskip", []))

                        if src2[j - 1][0] == "BREAK_skip":
                            src2.pop(j)
                            src2.pop(j - 1)

                            j -= 1
                        else:
                            j += 1

                        if block == "DO":
                            src2.insert(j + 1, ("BREAK_clean", []))
                            break
                        else:
                            src2.insert(j + 1, ("BREAK_skip", []))

                            j += 1

                j += 1
            
        i += 1

    blocks = []
    until_nums = []
    nesting_depth = 0
    dst = ""
    for (cmd, args) in src2:
        # dst += f"\n{cmd} "
        try:
            if cmd == "SET":
                arg0 = getnum(args)
                dst += "[-]" + "+" * arg0
            elif cmd == "ADD":
                arg0 = getnum(args)
                dst += "+" * arg0
            elif cmd == "SUB":
                arg0 = getnum(args)
                dst += "-" * arg0
            elif cmd == "UNTIL":
                arg0 = getnum(args)
                dst += "-" * arg0 + "[" + "+" * arg0
                blocks.append("UNTIL")
                until_nums.append(arg0)
            elif cmd == "IF":
                arg0 = getnum(args)
                # v _ v2 _
                dst += "[>+>>+<<<-]>[<+>-]+>>" + "-" * arg0 + "[<<->>[-]]<<[[-]<"
                blocks.append("IF")
            elif cmd == "DO":
                arg0 = getnum(args)
                # v0 _ v1 _ v2 i v3 j
                if with_break:
                    dst += ">>"
                dst += ">>>>>" + ">>" * nesting_depth + "<<[>>+<<-]" * nesting_depth 
                if arg0 == 0:
                    dst += "+[<<<<<"
                else:
                    dst += "+" * arg0 + "[-<<<<<"
                if with_break:
                    dst += "<<"

                blocks.append("DO")
                nesting_depth += 1
            elif cmd == "BREAK" and ENABLE_EXTENSIONS:
                nesting_depth = len([1 for i in blocks if i == "DO"])
                break_depth = 1

                # if len(args) > 0:
                #     break_depth = getnum(args, 0)
                # if break_depth > nesting_depth:
                #     break_depth = nesting_depth

                dst += ">>>+>>" + ">>" * break_depth + "[-]<<" * break_depth + "<<<<<"
            elif cmd == "BREAK_skip" and ENABLE_EXTENSIONS:
                dst += ">+>>[<<->>>>+<<-]>>[<<+>>-]<<<<[-<"
            elif cmd == "BREAK_endskip" and ENABLE_EXTENSIONS:
                dst += ">]<"
            elif cmd == "BREAK_clean" and ENABLE_EXTENSIONS:
                dst += ">>>[-]<<<"
            elif cmd == "END":
                block = blocks.pop()

                if block == "UNTIL":
                    n = until_nums.pop()
                    dst += "-" * n + "]" + "+" * n
                elif block == "IF":
                    dst += ">]<"
                elif block == "DO":
                    if with_break:
                        dst += ">>"

                    dst += ">>>>>]" + ">>[<<+>>-]" * nesting_depth + "<<" * nesting_depth 
                    dst += "<<<<<"

                    if with_break:
                        dst += "<<"

                    nesting_depth -= 1               
            elif cmd == "MOV":
                arg0 = getreg(args, 0, istarget=True)
                arg1 = getreg(args, 1)

                if arg0 == arg1:
                    continue
                
                nesting_depth = len([1 for i in blocks if i == "DO"])

                if arg0 == "LEFT":
                    if with_tmp and arg1 != "IN" and nesting_depth > 0:
                        if with_break:
                            dst += ">>"
                        dst += ">>>" + ">>[<<+>>-]" * nesting_depth + "<<" * nesting_depth + "<<<" 
                        if with_break:
                            dst += "<<"

                    dst += "<<" if with_tmp else "<"
                    if arg1 == "IN":
                        dst += ","
                        dst += ">>" if with_tmp else ">"  # required?
                elif arg0 == "RIGHT":
                    dst += ">>" if with_tmp else ">"
                    if arg1 == "IN":
                        dst += ","
                        dst += "<<" if with_tmp else "<"  # required?

                    if with_tmp and arg1 != "IN" and nesting_depth > 0:
                        if with_break:
                            dst += ">>"
                        dst += ">>>" + ">>" * nesting_depth + "<<[>>+<<-]" * nesting_depth + "<<<" 
                        if with_break:
                            dst += "<<"
                elif arg0 == "OUT":
                    if arg1 == "IN":
                        dst += ">,.[-]<"
                    else:
                        dst += "."
                elif arg0 == "P" and arg1 == "IN":
                    dst += ","
                else:
                    raise Exception()
        except:
            sys.stderr.write(f"error: {cmd} {','.join(args)}\n")
            break

    return dst


if __name__ == "__main__":
    src = sys.stdin.readlines()
    dst = compile(src)
    print(dst)
