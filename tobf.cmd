@python ..\tobf %1 %2 %3 %4 %5 %6 %7 %8 %9 > tmp.bf
@python ..\tobf\bfopt.py < tmp.bf > %~dpn1.bf

