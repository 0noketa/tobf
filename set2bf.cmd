@setlocal
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:main
    @if "%~1"=="-help" @(
        @echo set2bf options ^< src ^> dst
        @goto :eof
    )

    @python "%TOBF_DIR%\tools\set2tobf.py"  %2 %3 %4 %5 %6 %7 %8 %9 < "%~1" > "%~pd1\tmp.txt"
    @python "%TOBF_DIR%\tobf" "%~pd1\tmp.txt" "-I%TOBF_DIR%\lib" -o- | @python "%TOBF_DIR%\tobf\bfopt.py" -O1 > "%~1.bf"
    @goto :eof
