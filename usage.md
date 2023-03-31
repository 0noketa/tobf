# usage

this repository contains some programs for Brainfuck-concerned languages.  
every program listed below has its own entry-point.

## part of tobf

### tobf/

compiler of assembly-level language for Brainfuck.
this directory can be passed to python.
usage of language is [here](./tobf/tobf.py) this language is not so usable.

``` sh
python tobf [options] [source]
```

options

* -Idirname  
  selects additional include directory. default is none.  
  library directories should be passed manually.
* -ofilename  
  selects destination file.
* -o-  
  selects stdout as destination file.
* -fast  
  generates fast (on BFI with no optimization) code.
  for example: almost all text message uses no loops.
* -no_tmp  
  disables default temporary variables. implicit assignment is required for some instruction.

### tobf/bfopt.py

Brainfuck optimizer (usable stub).  
requires tobf/const_replacer.py, tobf/base.py .

### gen/gen_mod_dec.py

generates fixed-columns decimal-integer module for tobf

``` sh
python gen_mod_dec.py columns > program
```

### tobf/erp2tobf.py

B-level RPN language (with labels, anonymous functions and goto) to tobf compiler.  

### tobf/c2bf.py

almost abandoned stub.

---

## atdbf and its front-end

compiler/interpreter for 2D Brainfuck (without something such as self-modification) languages (currently 10 languages are implemented).  
this implementation uses 1D intermediate language for fast and short output.  

every program requires tools/atdbf.py .  
almost all program can be used like below.

``` sh
# compiler
python tools/pathc.py [options] src > dst
python tools/pathc.py [options] < src > dst
# interpreter
python tools/pathc.py [options] -run src < input_data > output_data
```

options:

* -lang=name  
  select target language
* -tname  
  select target language
* -run  
  passes code to interpreter
* -mem_size=N  
  select memory size

stable targets are:

* asm2bf
* Brainfuck
* [BrainfuckAsmCompiler](https://github.com/esovm/BrainfuckAsmCompiler)
* C
* Enigma2D
* Generic2DBrainfuck
* PATH
* x86 (in NASM, on PC)

### tools/pathc.py

PATH compiler/interpreter.

### tools/semopathc.py

SeMo-PATH compiler/interpreter.

### tools/snuspc.py

SNUSP(Core SNUSP) compiler/interpreter.

### tools/mtdc.py

Minimal-2D compiler/interpreter.

### tools/enigmatdc.py

Enigma-2D compiler/interpreter.

### tools/gtdbfc.py

Generic 2D Brainfuck compiler/interpreter.

### tools/brainspacec.py

BrainSpace compiler/interpreter.

### tools/aassc.py

"Around and around, sleeping sound" compiler/interpreter.

### tools/regiminc.py

Regimin compiler/interpreter.  
compiler target languages are only C and Brainfuck.

### tools/clockwisec.py

Clockwise compiler/interpreter.  
compiler target languages are only C.

### tools/twolangc.py

2L compiler/interpreter (stub).  
compiler target languages are only C.

---

## standalone programs

### tools/set2tobf.py

Set to tobf compiler.  
language Set this compiler uses is [this language](https://esolangs.org/wiki/Set).  
program addresses (line numbers) are limited (<256).  

### tools/mtd2path.py

Minimal-2D to PATH compiler.  
for short output, use "tools/mtdc.py -tPATH" instead of this compiler.

### tools/path2mtd.py

PATH to Minimal-2D compiler.
for short output, use "tools/pathc.py -tbf" and any Brainfuck->Minimal-2D compiler instead of this compiler.

### tools/txt2aass.py

this program gernerates "Around and around, sleeping sound" program that generates text passed to this program. non-ASCII characters will be broken.

### tools/tocw.py

compiler of high-level language for Clockwise.

### tools/echolangc.py

[EchoLang](https://esolangs.org/wiki/EchoLang) to Python compiler and executor(works as interpreter).  
every undefined part may be incorrect that will be changed.
