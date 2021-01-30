
# a to-bf compiler for small programs
# abi:
#   dynamic_addressing: every address is 8bits. only 256 bytes.
#     16bits addressing is planned as that cant be used both systems in once.
#     ex: initialize as 8bit addrs -> use -> clean -> initialize as 16bit addrs.
#   pointer: always points address 0 with value 0 at the beggining and the end
#   memory: temporary, ...vars, dynamic_memory
#     area of vars has no hidden workspace expects address 0).
#     dynamic_memory is optional. nothing exists until initialized manually. and can be cleaned up.
# linking(not yet):
#   sequencial or macro-injection.
#   linkers are required to read only first lines of every source.
# syntax:
#   program: var_decl "\n" instructions "end" "\n"
#   var_decl: id (" " id)*
#   instructions: (id (" " id)* "\n")*
# instructions:
# set imm ...out_vars_with_sign
#   every destination can starts with "+" or "-", they means add or sub instead of set 
#   aliases_with_inplicit_signs:
#     add imm ...out_vars
#     sub imm ...out_vars
#     clear ...out_vars
#       imm as 0 and no sign
#     inc ...out_vars
#       imm as 1 and sign as "+"
#     dec ...out_vars
#       imm as 1 and sign as "-"
# move in_var ...out_vars_with_sign
#   in_var becomes to 0
#   aliases_with_inplicit_signs:
#     moveadd in_var ...out_vars 
#     movesub in_var ...out_vars 
# copy in_var ...out_vars_with_sign
#   aliases_with_inplicit_signs:
#     copyadd in_var ...out_vars 
#     copysub in_var ...out_vars 
# resb imm
#   declare size of static memory. default=number of vars. works when no subsystem was loaded.
# load subsystem_name ...args
#   loads subsystem after reserved vars and subsystems already loaded
# loadas alias_name subsystem_name ...args
#   loads and names as alias_name
# unload subsysten_name
#   unloads a subsystem. subsystem_name can be alias_name
# subsystem_name.any_name ...args
#   invokes a feature of subsystem
# if cond_var
# endif cond_var
#   like "next i" in basic. this rule simplifies compiler.
#   currently compiler disallows no cond_var instructions.
# ifelse cond_var work_var
#   work_var carries run_else flag
# else cond_var work_var
# endifelse cond_var work_var
# while cond_var
# endwhile cond_var
# end
#   can not be omitted

from base import SubsystemBase, InstructionBase, split
from tobf import Tobf
from subsystems import Subsystem_ConstSet, Subsystem_Consts, Subsystem_Enums, Subsystem_Vars, Subsystem_Code
from sub_mem import Subsystem_Memory
from sub_fastmem import Subsystem_FastMem
from sub_str import Subsystem_Str
from sub_stk import Subsystem_Stk


if __name__ == "__main__":    
    import sys

    verbose = False
    fast = False
    tmps = ["tmp"]
    args = sys.argv[1:]

    if len(args) == 0:
        print("py tobf source [options]")
        exit(0)

    src = args[0]

    for arg in args[1:]:
        if arg == "-v":
            verbose = True
        if arg == "-f":
            fast = True
        if arg == "-no_tmp":
            tmps = []

    compiler = Tobf(sys.stdout, list(range(len(tmps))), tmps, fast)
    compiler.install_subsystem("enums", Subsystem_Enums)
    compiler.install_subsystem("consts", Subsystem_Consts)
    compiler.install_subsystem("constset", Subsystem_ConstSet)
    compiler.install_subsystem("vars", Subsystem_Vars)
    compiler.install_subsystem("code", Subsystem_Code)
    compiler.install_subsystem("mem", Subsystem_Memory)
    compiler.install_subsystem("fastmem", Subsystem_FastMem)
    compiler.install_subsystem("str", Subsystem_Str)
    compiler.install_subsystem("stk", Subsystem_Stk)

    compiler.compile_file(src, verbose)

