@setlocal
@set ext=m2d
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:help
    @echo PATH to Minimal-2D compiler
    @echo path2mtd src
    @goto :eof

:main
    @if "%~1"=="" @goto :help
    @if "%~1"=="-h" @goto :help
    @if "%~1"=="-help" @goto :help

    @python "%TOBF_DIR%\tools\path2mtd.py"  %2 %3 %4 %5 %6 %7 %8 %9 < "%~1" > "%~1.%ext%"
    @goto :eof
