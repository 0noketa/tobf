@setlocal
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:help
    @echo Minimal-2D to Brainfuck compiler
    @echo mtd2bf src
    @goto :eof

:main
    @if "%~1"=="" @goto :help
    @if "%~1"=="-h" @goto :help
    @if "%~1"=="-help" @goto :help

    @python "%TOBF_DIR%\tools\mtdc.py"  -tbf %2 %3 %4 %5 %6 %7 %8 %9 < "%~1" | @python "%TOBF_DIR%\tobf\bfopt.py" -O1 > "%~1.bf"
    @goto :eof
