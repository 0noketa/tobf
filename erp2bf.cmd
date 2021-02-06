@setlocal
@call "%~pd0\prepare_tobf.cmd"
@python "%TOBF_DIR%\tobf\erp2tobf.py"  "-I%TOBF_DIR%\lib_erp" < "%~1" > "%~pd1\tmp.txt"
@python "%TOBF_DIR%\tobf" "%~pd1\tmp.txt" "-I%TOBF_DIR%\lib" %2 %3 %4 %5 %6 %7 %8 %9 -o- > "%~pd1\tmp.bf"
@python "%TOBF_DIR%\tobf\bfopt.py" -O1 < "%~pd1\tmp.bf" > "%~1.bf"
@endlocal
