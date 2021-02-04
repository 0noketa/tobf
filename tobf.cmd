@python ..\tobf %1 %2 %3 %4 %5 %6 %7 %8 %9 -o- > tmp.bf
@python ..\tobf\bfopt.py -O1 < tmp.bf > "%~1.bf"
