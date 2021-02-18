
# usage:
#   python gen_mod_dec.py 6 > mod_dec6.txt
# limitation: 3 <= cols < any_large_number_your_computer_can_not_manage
import sys


n_cols = 3

if len(sys.argv) > 1:
    n_cols2 = int(sys.argv[1])

    n_cols = max(n_cols, n_cols2)

def cols(fmt=" {0}") -> str:
    return "".join([fmt.format(i) for i in range(n_cols)])

def rcols(fmt=" {0}") -> str:
    return "".join([fmt.format(i) for i in range(n_cols - 1, -1, -1)])

def shl(fmt="move col{0} col{1}\n") -> str:
    return "".join([fmt.format(i - 1, i) for i in range(n_cols - 1, 0, -1)])

def shr(fmt="move col{1} col{0}") -> str:
    return " ".join([fmt.format(i, i + 1) for i in range(n_cols - 1)])

print(f"""n m o z

# {n_cols} columns decimal integer

:init
    !$ dec{n_cols}_interface {cols(" col{0}")}
    set '0 z
:clean
    clear z
:@check v
    is_var{rcols(" v:col{0}")}
:@set{rcols(" col{0}")} v
    @check v""")
print(rcols("""
    set col{0} v:col{0}"""))
print("""
:@w_move_str s v
    @check v
    # is str s

    @clear v

    s:@drop n
    while n
        @shl v
        copysub z n
        @w_movelowest n +v:col0
        s:@drop +n
    endwhile n

:@shl v
    @check v""")
print(shl("""
    move v:col{0} v:col{1}"""))
print("""
    clear v:col0
:@shr v
    @check v""")
print(shr("""
    move v:col{1} v:col{0}"""))

print(f"""
    clear v:col{n_cols - 1}
:@r_copylowest v out
    @check v
    is_var out
    copy v:col0 out
:@r_movelowest v out
    @check v
    is_var out
    move v:col0 out
:@w_copylowest in v
    @check v
    is_var in
    copy in v:col0
:@w_movelowest in v
    @check v
    is_var in
    move in v:col0

:@clear v
    @set{" 0" * n_cols} v
:_@move _f x *
    @check x
    @check *""")
print(rcols("""
    _f x:col{0} *:col{0}"""))

print(f"""
:@move x *
    _@move move x *
:@copy x *
    _@move _copy x *

 # via o
:_copyadd x *
    move x o
    moveadd o x *
:_copyadd{n_cols} x{rcols(" y{0}")}
    move x o
    moveadd o x{rcols(" y{0}")}
:_copy x *
    clear y
    _copyadd x *
:_copysub x *
    move x o
    movesub o x *
:_copysub{n_cols} x{rcols(" y{0}")}
    move x o
    move o +x{rcols(" -y{0}")}
:_copyneg x y
    clear y
    _copysub x y


:_nop4 x _m _n _f
:_inc x _m _n  _f v  _next
    _copyadd v n
    sub _m n
    ifelse n o
        _f v
    else n -o
        set _n v
        _next x _m _n _f
    endifelse n o""")
print(shl("""
:_inc_col{0} x _m _n _f
    _inc x _m _n  _f x:col{0}  _inc_col{1}"""))
print(f"""
:_inc_col{n_cols - 1} x _m _n _f
    _inc x _m _n  _f x:col{n_cols - 1}  _nop4

:@inc x
    @check x
    _inc_a x 9 0 inc
:@dec x
    @check x
    _inc_a x 0 9 dec

:_copyifgt9 v n o
    _copy v n
    set 9 m
    ifgt n m o

:_endifgt9 n o
    endifgt n m o

:_moveadd_dec _f_sub _f_inc _f_copyadd x y
    @check x
    @check y""")
print(shr("""
    _f_copyadd x:col{0} y:col{0}
    _copyifgt9 y:col{0} n o
        _f_sub 10 y:col{0}
        _f_inc y:col{1}
    _endifgt9 n o"""))
print(f"""
    _f_copyadd x:col{n_cols - 1} y:col{n_cols - 1}
    _copyifgt9 y:col{n_cols - 1} n o
        _f_sub 10 y:col{n_cols - 1}
    _endifgt9 n o


:@moveadd x y
    _moveadd_dec sub inc moveadd  x y
:@copyadd x y
    _moveadd_dec sub inc _copyadd  x y
:@movesub x y
    _movesub_dec add dec movesub  x y
:@copysub x y
    _movesub_dec add dec _copysub  x y

# breaks x
:@movemul x y z
    @check x
    @check y
    @check z

    @while x
        @copyadd y z
        @dec x
    @endwhile x

:_copyifelse x n o
    _copyadd x n
    ifelse n o

:_copyif x n
    _copyadd x n
    if n

:@read x
    @check x
    input{rcols(" x:col{0}")}
    _copysub{n_cols} z{rcols(" x:col{0}")}

:@write0 x
    @check x
    _copyadd{n_cols} z{rcols(" x:col{0}")}
    print{rcols(" x:col{0}")}
    _copysub{n_cols} z{rcols(" x:col{0}")}

:@read_until tail x
    @check x
    @clear x
    input n
    sub tail n
    while n
        add tail n
        sub '0 n""")
print(shl("""
        move x:col{0} x:col{1}"""))
print(f"""
        move n x:col0

        input n
        sub tail n
    endwhile n

:@readln x
    @read_until 10 x

:@writeln0 x
    @write0 x
    set 10 n
    print n
    clear n

:_write_n
    _copyadd z n
    print n
:_write1 x
    _copy x n
    _write_n

:@write x
    @check x
    _copy x:col{n_cols - 1} n
    ifelse n m
        _write_n
""")

for i in range(n_cols - 2, 0, -1):
    print(f"        _write1 x:col{i}")

print("""    else n m
        _@write_0 x
    endifelse n m

    _copy x:col0 n
    _write_n

    clear n
""")

for i in range(0, n_cols - 4):
    print(f"""
:_@write_{i} x
    _copy x:col{n_cols - 2 - i} n
    ifelse n m
        _write_n
""")

    for j in range(n_cols - 3 - i, 0, -1):
        print(f"        _write1 x:col{j}")

    print(f"""    else n m
        _@write_{i + 1} x
    endifelse n m
    """)

print(f"""
:_@write_{max(0, n_cols - 4)} x
    _copy x:col2 n
    ifelse n m
        _write_n
        _write1 x:col1
    else n m
        _copy x:col1 n
        if n
            _write_n
        endif n
    endifelse n m

:@writeln x
    @write x
    set 10 n
    print n
    clear n

# moveadd to :f
:_movefold x
    @check x""")
print(rcols("""
    moveadd x:col{0} """ + f"x:col{n_cols}"))
print("""

:_copyfold x n
    @check x""")
print(rcols("""
    _copyadd x:col{0} n"""))
print("""

:@if x
    @check x
    _copyfold x n
    if n
:@endif x
    @check x
    _copyfold x n
    endif n
    @clear x

:@ifelse x y
    @check x
    _copyfold x n
    ifelse n y
:@else x y
    @check x
    else n y
:@endifelse x y
    @check x
    endifelse n y
    @clear x

:@while x
    @check x
    _copyfold x n
    while n
    clear n
:@endwhile x
    @check x
    clear n
    _copyfold x n
    endwhile n

:@pushto v stk""")
print(cols("""
    stk:@push v:col{0}"""))

print("""
:@popfrom v stk""")
print(rcols("""
    stk:@pop v:col{0}"""))

print("""
end
""")
