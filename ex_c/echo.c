#include <stdio.h>

main() {
    while (!feof(stdin)) {
        int c = getchar();

        if (c != EOF) { putchar(c); }
    }
}
