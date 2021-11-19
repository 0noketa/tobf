@setlocal
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:help
    @echo bfopt src options
    @echo options:
    @echo   -main   input is not partial
    @echo   -mem?   select size of memory
    @echo   -O?     select optimization level
    @goto :eof

:main
    @if "%~1"=="" @goto :help
    @if "%~1"=="-h" @goto :help
    @if "%~1"=="-help" @goto :help
    @python "%TOBF_DIR%\tobf\bfopt.py" %2 %3 %4 %5 %6 %7 %8 %9 < "%~1" > "%~dpn1.o.bf"
    @goto :eof
