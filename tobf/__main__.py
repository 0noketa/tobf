
# a to-bf compiler for small programs

from base import SubsystemBase, InstructionBase, split
from tobf import Tobf
from subsystems import Subsystem_ConstSet, Subsystem_Consts, Subsystem_Enums, Subsystem_Vars, Subsystem_Code
from sub_mem import Subsystem_Memory
from sub_fastmem import Subsystem_FastMem
from sub_slowmem import Subsystem_SlowMem
from sub_str import Subsystem_Str
from sub_stk import Subsystem_Stk


if __name__ == "__main__":    
    import sys
    import io

    verbose = False
    fast = False
    tmps = ["__default_tmp"]
    inc_dirs = []
    args = sys.argv[1:]

    if len(args) == 0:
        print("py tobf source [options]")
        exit(0)

    src_name = ""
    dst_name = ""
    dst = None

    for arg in args:
        if arg == "-v":
            verbose = True
        elif arg == "-f":
            fast = True
        elif arg == "-no_tmp":
            tmps = []
        elif arg.startswith("-I"):
            d = arg[2:]

            if d not in inc_dirs:
                inc_dirs.append(d)
        elif arg.startswith("-o-"):
            dst = sys.stdout
        elif arg.startswith("-o"):
            dst_name = arg[2:]
        elif not arg.startswith("-"):
            src_name = arg

    if dst_name == "":
        dst_name = src_name + ".bf"

    if dst == None:
        dst = io.open(dst_name, "w")

    compiler = Tobf(dst=dst, tmps=list(range(len(tmps))), vars=tmps, inc_dirs=inc_dirs, fast=fast)
    compiler.install_subsystem("enums", Subsystem_Enums)
    compiler.install_subsystem("consts", Subsystem_Consts)
    compiler.install_subsystem("constset", Subsystem_ConstSet)
    compiler.install_subsystem("vars", Subsystem_Vars)
    compiler.install_subsystem("code", Subsystem_Code)
    compiler.install_subsystem("mem", Subsystem_Memory)
    compiler.install_subsystem("fastmem", Subsystem_FastMem)
    compiler.install_subsystem("slowmem", Subsystem_SlowMem)
    compiler.install_subsystem("str", Subsystem_Str)
    compiler.install_subsystem("stk", Subsystem_Stk)

    compiler.compile_file(src_name, verbose)

    if dst_name != "":
        dst.close()
