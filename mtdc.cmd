@setlocal
@call "%~pd0\prepare_tobf.cmd"
@python "%TOBF_DIR%\tools\mtdc.py" %1 %2 %3 %4 %5 %6 %7 %8 %9
@endlocal
