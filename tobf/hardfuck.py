
# ZaYen's Hardfuck(https://esolangs.org/wiki/Hardfuck) to Brainfuck compiler
# warrning:
#   currently, behavior of "@" is unclear. this implementation should be incorrect. do not use this.
#
#   this compiler stores result of '@' at current position and no other behavior exists. can not run Helloworld.
#   maybe "/" is correct. use only this.
# memory layout:
#   [0] * size  # data
#   + [(i * 4) & 0xFF for i in range(size)]  # plane for pre-calculated results of "@"
#   + [0] * size  # plane for temporaly used for copying results of "@"
#   + [0] + [1] * (size - 1)  # plane for "/"
import io


class Hardfuck:
    @classmethod
    def compile(self, src: io.TextIOWrapper, dst: io.TextIOWrapper, mem_size: int = 0x100, clean = True, short = True) -> int:
        """returns memory size in bf"""
        s = "".join([c for c in src.read() if c in "><+-,.[]@/"])

        # "," <-> "."
        s = s.replace(",", " ").replace(".", ",").replace(" ", ".")

        rewind_plane_idx = -1
        const_plane_idx = -1
        tmp_plane_idx = -1

        current_plane = 0

        # init plane for @
        if "@" in s:
            dst.write(">" * mem_size)

            for i in range(mem_size):
                j = (i * 4) & 0xFF
                dst.write(("+" * j) + ">")

            current_plane += 1
            const_plane_idx = current_plane
            current_plane += 1
            tmp_plane_idx = current_plane

        # init plane for /
        if "/" in s:
            dst.write(">" * mem_size)

            if short and mem_size >= 256:
                mem_size2 = mem_size - 1
                n = mem_size2 // 255 - 1
                m = mem_size2 % 255 + 1

                dst.write("++++ ++++ ++++ +++[>++++ ++++ ++++ ++++ +<-]>[-[>+<-]+>]<-")
                dst.write(">++++ ++++ ++++ +++[<++++ ++++ ++++ ++++ +>-]<[-[>+<-]+>]" * n)
                dst.write("+>" * m)
            else:
                dst.write(">+" * (mem_size - 1) + ">")

            current_plane += 1
            rewind_plane_idx = current_plane

        used_memory = mem_size * (current_plane + 1)

        if short:
            if rewind_plane_idx != -1:
                dst.write("<[<]")
                dst.write("<" * mem_size)
            if const_plane_idx != -1:
                dst.write("<" * mem_size * 2)
        else:
            dst.write("<" * used_memory)



        while len(s):
            const = s.find("@")
            rewind = s.find("/")

            if const != -1 and (rewind == -1 or const < rewind):
                dst.write(s[:const])
                dst.write((">" * mem_size * const_plane_idx) + "["
                    + (">" * mem_size) + "+"
                    + ("<" * mem_size * tmp_plane_idx) + "+"
                    + (">" * mem_size * const_plane_idx) + "-]"
                    + (">" * mem_size) + "["
                    + ("<" * mem_size) + "+"
                    + (">" * mem_size) + "-]"
                    + ("<" * mem_size * tmp_plane_idx))
                s = s[const + 1:]
            elif rewind != -1:
                dst.write(s[:rewind])
                dst.write((">" * mem_size * rewind_plane_idx) + "[<]" + ("<" * mem_size * rewind_plane_idx))
                s = s[rewind + 1:]
            else:
                dst.write(s)
                s = ""

        if clean:
            # init plane for /
            if rewind_plane_idx != -1:
                dst.write(">" * mem_size * rewind_plane_idx)
                dst.write(">" * mem_size)
                dst.write("<[<]")
                dst.write("<" * mem_size * rewind_plane_idx)

            # clean plane for @
            if const_plane_idx != -1:
                dst.write(">" * mem_size * const_plane_idx)
                dst.write("[-]>" * mem_size)
                dst.write("<" * mem_size)
                dst.write("<" * mem_size * const_plane_idx)

        return used_memory

    def __init__(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, mem_size: int = 0x100, clean = True, short = True) -> None:
        self.src = src
        self.dst = dst
        self.mem_size = mem_size
        self.clean = clean
        self.short = short

    def compile_file(self, src: io.TextIOWrapper = None, dst: io.TextIOWrapper = None, mem_size: int = None, clean: bool = None, short: bool = None) -> int:
        if src == None and self.src != None:
            src = self.src
        if dst == None and self.dst != None:
            dst = self.dst
        if mem_size == None:
            mem_size = self.mem_size
        if clean == None:
            clean = self.clean
        if short == None:
            short = self.short

        if src == None and dst == None:
            raise Exception(f"any of input and ouput was None")

        return Hardfuck.compile(src, dst, mem_size, clean, short)


if __name__ == "__main__":
    import sys

    min_width = 4

    width = 256
    short = True
    clean = False

    for i in sys.argv:
        if i.startswith("-size"):
            width = max(min_width, int(i[5:]))
        if i == "-clean":
            clean = True
        if i == "-short":
            short = True
        if i == "-fast":
            short = False
        if i in ["-?", "-help"]:
            sys.stderr.write("Hardfuck to Brainfuck compiler\n")
            sys.stderr.write(f"python {sys.argv[0]} [options] < src > dst\n")
            sys.stderr.write(f"  -sizeN  select memory size (default: {width})\n")
            sys.stderr.write(f"  -clean  clear workspace of simulator at the end of program\n")
            sys.stderr.write(f"  -fast   generates simple long code\n")
            sys.stderr.write(f"  -short  generates short code\n")
            sys.exit(0)

    af = Hardfuck(sys.stdin, sys.stdout, width, clean, short)

    af.compile_file()

