#include <stdio.h>
#include "c2bf.inc"

int f, b;

fizz(i) {
    int m = 1;

    if (f == 3) {
        fputs("FIZZ", stdout);
        f = 0;
        m = 0;
    }

    if (b == 5) {
        fputs("BUZZ", stdout);
        b = 0;
        return;
    }

    if (m) {
        print_int(i);
    }

    // currently, compiler does not generate any [return].
    // all path should have [return].
    return;
}

main() {
    int i = 0;
    int n = input_int();

    while (i < n) {
        fizz(i);
        putchar('\n');

        i += 1;
        f += 1;
        b += 1;
    }
}
