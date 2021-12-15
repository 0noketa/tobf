@setlocal
@call "%~pd0\prepare_tobf.cmd"
@call :main %*
@endlocal

@goto :eof

:main
    @python "%TOBF_DIR%\tools\set2tobf.py"  %1 %2 %3 %4 %5 %6 %7 %8 %9
    @goto :eof
