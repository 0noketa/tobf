
# yet another implementation of Clifford Wolf's BFA
# something i could not understand ("/debug/" and "(local:parent)") are not implemented

import sys
import io


class Bfa:
    def __init__(self, src) -> None:
        self.src = src
        self.varss = []
        self.base_addr = 0
        self.vars = []
        self.block_stack = []
        self.block_it = 0
        self.current_addr = 0
        self.max_mem = 0

    def get_address(self, name):
        if name in self.vars:
            return self.base_addr + self.vars.index(name)

        stack = self.varss.copy()
        current = self.vars
        base_addr2 = self.base_addr

        for i in range(len(stack)):
            current = stack.pop()
            base_addr2 = base_addr2 - len(current)

            if name in current:
                return base_addr2 + current.index(name)

        raise Exception(f"{name} is not defined")

    def select_addr(self, addr, out=sys.stdout):
        addr2 = addr - self.current_addr

        if addr2 < 0:
            out.write("<" * -addr2)
        else:
            out.write(">" * addr2)

        self.current_addr = addr

    def compile(self, out=sys.stdout) -> int:
        """out: file-like\n
           returns memory size to run safe
        """

        while True:
            self.src = self.src.strip()

            if len(self.src) == 0:
                self.select_addr(0, out)

                break

            if self.src[0] == "'":
                j = self.src[1:].index("'")
                bf = self.src[1:j + 1]
                self.src = self.src[j + 2:]

                out.write(bf)

                continue

            if self.src[0] == "(":
                j = self.src.index(")")
                name = self.src[1:j]
                self.src = self.src[j + 1:]

                if name in self.vars:
                    raise Exception(f"error: {name} was defined twice")

                self.vars.append(name)

                addr = self.get_address(name)
                if addr + 1 > self.max_mem:
                    self.max_mem = addr + 1

                continue

            if self.src[0] == "<":
                j = self.src.index(">")
                name = self.src[1:j]
                self.src = self.src[j + 1:]

                addr = self.get_address(name)

                self.select_addr(addr, out)

                continue

            if self.src[0] == "[":
                self.src = self.src[1:]

                self.block_stack.append(self.block_it)
                self.block_it = self.current_addr

                out.write("[\n")

                continue

            if self.src[0] == "]":
                self.src = self.src[1:]

                if self.block_it == -1:
                    raise Exception(f"[ does not exists")

                self.select_addr(self.block_it, out)
                self.block_it = self.block_stack.pop()

                out.write("]\n")

                continue

            if self.src[0] == "{":
                self.src = self.src[1:]

                self.base_addr += len(self.vars)
                self.varss.append(self.vars)
                self.vars = []

                continue

            if self.src[0] == "}":
                self.src = self.src[1:]

                addr0 = self.current_addr

                for v in self.vars:
                    addr = self.get_address(v)
                    self.select_addr(addr, out)
                    out.write("[-]\n")

                self.select_addr(addr0, out)

                self.vars = self.varss.pop()
                self.base_addr -= len(self.vars)

                continue

            if self.src[0] in ["#", ";"]:
                try:
                    j = self.src[1:].index("\n")
                    self.src = self.src[j + 2:]
                except Exception:
                    self.src = ""

                continue

            if self.src[0] in ["+", "-", ",", "."]:
                out.write(self.src[0])

                self.src = self.src[1:]

                continue

        return self.max_mem

    @classmethod
    def from_filename(self, filename: str):
        with io.open(filename, "r") as f:
            bfa = Bfa.from_file(f)

        return bfa

    @classmethod
    def from_file(self, file):
        src = file.read()

        return Bfa(src)


def main(argv):
    if len(argv) < 2:
        print("yet another implementation of Clifford Wolf's BFA")
        print(f"  python {argv[0]} src.bfa")

        return 0

    try:
        bfa = Bfa.from_file(argv[1])

        with io.open(argv[1] + ".bf", "w") as f:
            bfa.compile(f)

    except Exception as e:
        sys.stdout.write(e)

        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv))
