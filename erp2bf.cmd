@setlocal
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:main
    @if "%~1"=="-help" @(
        @echo erp2tobf src options
        @goto :eof
    )

    @python "%TOBF_DIR%\tobf\erp2tobf.py"  "-I%TOBF_DIR%\lib_erp" %2 %3 %4 %5 %6 %7 %8 %9 < "%~1" > "%~pd1\tmp.txt"
    @python "%TOBF_DIR%\tobf" "%~pd1\tmp.txt" "-I%TOBF_DIR%\lib" -o- > "%~pd1\tmp.bf"
    @python "%TOBF_DIR%\tobf\bfopt.py" -O1 < "%~pd1\tmp.bf" > "%~1.bf"
    @goto :eof
