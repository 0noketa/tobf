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
# AssemblerFuck
# https://esolangs.org/wiki/AssemblerFuck
# AssemblerFuck++
# https://esolangs.org/wiki/AssemblerFuck%2B%2B
import sys
import re


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
    if cmd == "MOVE":
        arg0 = getreg(args, 0, istarget=True)
        arg1 = getreg(args, 1)

        return arg0 == "OUT" and arg1 == "IN"

    return False

def compile(src):
    with_tmp = False
    src2 = []
    for line in src:
        line: str = line
        try:
            line2 = line.strip().split(" ", maxsplit=1)
            cmd = line2[0].strip()
            args = list(map(str.strip, line2[1].split(","))) if len(line2) > 1 else []
            src2.append((cmd, args))

            if not with_tmp and uses_tmp(cmd, args):
                with_tmp = True
        except:
            sys.stderr.write(f"error: {line}\n")
            break

    blocks = []
    dst = ""
    for (cmd, args) in src2:
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
            elif cmd == "IF":
                arg0 = getnum(args)
                # v _ v2 _
                dst += "[>+>>+<<<-]>[<+>-]+>>" + "-" * arg0 + "[<<->>[-]]<<[[-]<"
                blocks.append("IF")
            elif cmd == "DO":
                nesting_depth = len([1 for i in blocks if i == "DO"])
                arg0 = getnum(args)
                # v0 _ v1 i v2 j v3 k
                dst += ">>>" + ">>" * nesting_depth + "<<[>>+<<-]" * nesting_depth 
                if arg0 == 0:
                    dst += "+[<<<"
                else:
                    dst += "+" * arg0 + "[-<<<"
                blocks.append("DO")
            elif cmd == "END":
                nesting_depth = len([1 for i in blocks if i == "DO"])
                block = blocks.pop()
    
                if block == "UNTIL":
                    dst += "]"
                elif block == "IF":
                    dst += ">]<"
                elif block == "DO":
                    dst += ">>>]" + ">>[<<+>>-]" * nesting_depth + "<<" * nesting_depth 
                    dst += "<<<"    
            elif cmd == "MOV":
                arg0 = getreg(args, 0, istarget=True)
                arg1 = getreg(args, 1)

                if arg0 == arg1:
                    continue
                
                nesting_depth = len([1 for i in blocks if i == "DO"])

                if arg0 == "LEFT":
                    if with_tmp and arg1 != "IN":
                        dst += ">" + ">>[<<+>>-]" * nesting_depth + "<<" * nesting_depth + "<" 

                    dst += "<<" if with_tmp else "<"
                    if arg1 == "IN":
                        dst += ","
                        dst += ">>" if with_tmp else ">"  # required?
                elif arg0 == "RIGHT":
                    dst += ">>" if with_tmp else ">"
                    if arg1 == "IN":
                        dst += ","
                        dst += "<<" if with_tmp else "<"  # required?

                    if with_tmp and arg1 != "IN":
                        dst += ">" + ">>" * nesting_depth + "<<[>>+<<-]" * nesting_depth + "<" 
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
