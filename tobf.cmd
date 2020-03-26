@py ..\tobf %1 > tmp.bf
@py ..\tobf\bfopt.py < tmp.bf > %~dpn1.bf

