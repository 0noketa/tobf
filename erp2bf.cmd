@setlocal
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:help
    @echo erp2bf src options
    @echo options:
    @echo   -Idir  add include/import search directory
    @echo   -dsN   select size of data stack
    @echo   -rsN   select size of call stack
    @goto :eof

:main
    @if "%~1"=="" @goto :help
    @if "%~1"=="-h" @goto :help
    @if "%~1"=="-help" @goto :help

    @python "%TOBF_DIR%\tobf\erp2tobf.py"  "-I%TOBF_DIR%\lib_erp" %2 %3 %4 %5 %6 %7 %8 %9 < "%~1" > "%~pd1\tmp.txt"
    @python "%TOBF_DIR%\tobf" "%~pd1\tmp.txt" "-I%TOBF_DIR%\lib" -o- > "%~pd1\tmp.bf"
    @python "%TOBF_DIR%\tobf\bfopt.py" -O1 < "%~pd1\tmp.bf" > "%~1.bf"
    @goto :eof
