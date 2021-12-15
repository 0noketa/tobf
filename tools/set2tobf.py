# Set to tobf compiler
#
# Set:
# https://esolangs.org/wiki/Set
from typing import Tuple, List
import re


class Set2TobfInstruction:
    VARS = "".join([f("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for f in [str, str.lower]]) + "?!"

    def __init__(self, line=None, args=[], co=None, o=None) -> None:
        """args should be sorted and padded as [left, right, right_right, cond_left, cond_right]"""
        self.line = line
        self.args = args
        self.co = co
        self.o = o

    def has_cond(self):
        return self.co is not None

    def has_op(self):
        return self.o is not None
    
    def is_nop(self):
        return len([True for i in self.args if i is not None]) == 0

    def uses_var(self, v):
        return len([True for i in self.args if i == v]) != 0

    @classmethod
    def load(self, i: int, src: str):
        m: re.Match = re.match(
                """(?:\[(v)(c)(v)\]\s+|)set\s+(v)\s+(?:(v)|\((v)(o)(v)\))"""
                    .replace("c", """(?:/|=)""")
                    .replace("o", """(?:\+|\-)""")
                    .replace("v", """(?:[a-zA-Z]|\d+|!|\?)"""),
                src)

        if m is None:
            return None

        c0, co, c1,  a0,  a1,  a2, o, a3 = m.groups()

        # check args
        if (a0 is None or (a2 is None) != (a3 is None) or (a2 is None) != (a3 is None)):
            return None

        # check cond
        if (c0 is None) != (c1 is None) or (c0 is None) != (co is None):
            return None

        if a1 is None:
            a1 = a2
            a2 = a3

        return Set2TobfInstruction(i, [a0, a1, a2, c0, c1], co, o)

class Set2Tobf:
    def __init__(self, src: List[str] = None, argv: List[str] = []) -> None:
        self.src = src
        self.code: List[Set2TobfInstruction] = None
        self.error_line = -1
        self.error_src = ""
        # does not remove not used vars
        self.keep_vars = False
        # does not remove not used vars
        self.keep_chars = False
        self.help = False

        for arg in argv:
            if arg == "-help":
                self.help = True
            if arg == "-keep_vars":
                self.keep_vars = True
            if arg == "-keep_chars":
                self.keep_chars = True

    def load(self, src: List[str]):
        self.code = []

        for i, s in enumerate(src):
            if ">" in s:
                s = s.split(">")[0]
            
            s = s.strip()

            if len(s) == 0:
                self.code.append(Set2TobfInstruction(i + 1))

                continue

            step = Set2TobfInstruction.load(i + 1, s)

            if step is None:
                self.error_line = i + 1
                self.error_src = s

                return False

            self.code.append(step)

    def get_used_vars(self) -> List[str]:
        f = lambda x: len([True for step in self.code if step.uses_var(x)]) > 0

        return [c for c in Set2TobfInstruction.VARS if f(c)]

    def esc(self, v):
        if v == "?":
            return "local:lbls:next_label"
        elif v == "!":
            return "input"
        else:
            return v

    def compile_load(self, v, val, add=""):
        dst = []

        if val == "!":
            dst.append(f"input {add}{v}")
        elif val == "?":
            dst.append(f"copy local:lbls:next_label {add}{v}")
        elif val in Set2TobfInstruction.VARS or val.startswith("_"):
            dst.append(f"copy {val} {add}{v}")
        else:
            dst.append(f"set {val} {add}{v}")

        return dst

    def compile_store(self, v, val, add="", brk=False):
        dst = []

        if val == "!":
            dst.append(f"print {v}")
        elif brk:
            dst.append(f"move {v} {val}")
        else:
            dst.append(f"copy {v} {val}")

        return dst

    def compile(self, src: List[str] = None) -> List[str]:
        if self.help:
            return [
                "python set2tobf.py [options] < src > dst",
                "options:",
                "  -keep_chars  compiler always generates all of A-Z",
                "  -keep_vars   compiler always generates all of a-z"
            ]

        src0 = src

        if src is None:
            src = self.src

        if self.code is None or src0 is not None:
            self.load(src)

        dst = []
        used = self.get_used_vars()

        if self.keep_vars and self.keep_chars:
            vars_0 = list(Set2TobfInstruction.VARS)
        elif self.keep_chars:
            vars_0 = [c for c in list(Set2TobfInstruction.VARS) if c.isupper()] + [c for c in used if c.islower()]
        elif self.keep_vars:
            vars_0 = [c for c in used if c.isupper()] + [c for c in list(Set2TobfInstruction.VARS) if c.islower()]
        else:
            vars_0 = used
        
        vars_ = [i for i in vars_0 if i not in "?!"] + "_x _y".split(" ")

        dst.extend([
            " ".join(vars_) + " _",
            "public " + " ".join(vars_0),
        ])
       
        if "?" in used:
            dst.extend([
                ":init",
                "tmp _",
                "init_vars",
                "init_chars",
                "loadas local:lbls code mod_jump2",
                ":clean",
                "tmp -_",
                "clean_vars",
                "clean_chars",
                "unload local:lbls"
            ])
        else:
            dst.extend([
                ":init",
                "tmp _",
                "init_vars",
                "init_chars",
                ":clean",
                "tmp -_",
                "clean_vars",
                "clean_chars"
            ])

        dst.append(":init_chars")

        if len([True for c in vars_ if c.isupper()]) == 26:
            dst.append("bf_at A ++++++++++++++++++++++++++"
                    + "[[>>+>+<<<-]+>++++++++++[<+++++++++>-]>[<<->>-]>[<<+>>-]<<-]"
                    + "<<<<<<<<<<<<<<<<<<<<<<<<<<")
        else:
            for c in vars_:
                if c.isupper():
                    dst.append(f"set {ord(c)} {c}")

        dst.append(":init_vars")

        for c in vars_:
            if c.islower():
                dst.append(f"clear {c}")

        dst.append(":clean_chars")

        for c in vars_:
            if c.isupper():
                dst.append(f"clear {c}")

        dst.extend([
            ":clean_vars",
            "init_vars",
            ":main",
            "init",
            "run",
            "clean",
            ":run"
        ])

        if "?" in used:
            dst.append(f"local:lbls:@begin {len(self.code)}")

        for i, step in enumerate(self.code):
            if "?" in used:
                dst.append(f"local:lbls:@at {i}")

            if step.is_nop():
                continue

            if step.args[0] == "?" and step.args[1] == "?":
                    raise Exception(f"infinite loop at {i + 1}\n")


            if step.args[0] == "?":
                if step.args[1].isdigit() and not step.has_op():
                    set_label = f"set {int(step.args[1]) - 1}"
                else:
                    dst.extend(self.compile_load("_x", step.args[1]))

                    if step.has_op():
                        dst.extend(self.compile_load("_x", step.args[2], step.o))

                    dst.append(f"dec _x")

                    set_label = "move _x"

                if step.has_cond():
                    dst.extend(self.compile_load("_y", step.args[3]))
                    dst.extend(self.compile_load("_y", step.args[4], "-"))

                    if step.co == "/":
                        dst.append(f"local:lbls:@goto_if _y {set_label}")
                    else:
                        dst.append(f"local:lbls:@goto_ifn _y {set_label}")
                else:
                    dst.append(f"local:lbls:@goto {set_label}")
            else:
                if step.has_cond():
                    dst.extend(self.compile_load("_y", step.args[3]))
                    dst.extend(self.compile_load("_y", step.args[4], "-"))

                    if step.co == "=":
                        dst.append(f"not _y")

                    dst.append(f"if _y")

                if step.args[0] == "!":
                    left = "_x"
                else:
                    left = step.args[0]

                if step.args[0] == "!" and not step.has_op():
                    if step.args[0] != step.args[1]:
                        dst.extend(self.compile_store(step.args[1], step.args[0]))
                else:
                    if step.args[0] != step.args[1]:
                        dst.extend(self.compile_load(left, self.esc(step.args[1])))

                    if step.has_op():
                        if step.args[0] != step.args[2]:
                            dst.extend(self.compile_load(left, self.esc(step.args[2]), step.o))
                        else:
                            dst.extend(self.compile_load("_x", self.esc(step.args[2])))
                            dst.extend(self.compile_store(left, "_x", step.o, brk=True))

                    if step.args[0] == "!":
                        dst.extend(self.compile_store("_x", step.args[0], brk=True))

                if step.has_cond():
                    dst.append(f"endif _y")

        if "?" in used:
            dst.append(f"local:lbls:@end")

        dst.append(f"end")

        return dst

if __name__ == "__main__":
    import sys

    src = sys.stdin.readlines()
    comp = Set2Tobf(src, sys.argv[1:])

    dst = comp.compile()

    list(map(print, dst))

    sys.exit(0)

