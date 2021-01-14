#include "c2bf.inc"


main() {
    int i = 0;
    int j = 0;

    while (i < 10) {
        i += 1;

        if (i >= 5) break;

        j += 1;
    }

    println_int(i);
    println_int(j);

    i = 0;
    j = 0;

    while (i < 10) {
        i += 1;

        if (i >= 5) continue;

        j += 1;
    }

    println_int(i);
    println_int(j);
}
