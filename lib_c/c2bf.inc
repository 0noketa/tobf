#ifndef c2bf__included
#define c2bf__included

#ifndef __TOBF_C2BF__
    #include <stdio.h>

    #define __c2bf_debug() fputs("debug dump at here\n", stderr)
    #define __c2bf_input (getchar() & 0xFF)
    #define __c2bf_print(arg) putchar(arg)
#endif


input_int() {
    int i = 0, c;

    c = __c2bf_input;
    while (c != 10) {
        i = i * 10;
        i += c - 48;

        c = __c2bf_input;
    }

    return i;
}

print_int(n) {
    int i = 0, j = 0, k = 0;

    while (n) {
        i += 1;
        if (i == 10) {
            i = 0;
            j += 1;
            if (j == 10) {
                j = 0;
                k += 1;
            }
        }

        n -= 1;
    }

    #ifdef __TOBF_C2BF__
    __c2bf_moveadd('0', i, j, k);
    __c2bf_print(k, j, i);
    #else
    __c2bf_print(k + '0');
    __c2bf_print(j + '0');
    __c2bf_print(i + '0');
    #endif
}

println_int(n) {
    print_int(n);
    __c2bf_print('\n');
}

#endif
