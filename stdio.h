#ifdef __C2BF__
#ifndef stdio__h__included
#define stdio__h__included

#include "c2bf.inc"

int stdin, stdout, stderr;
int c2bf_eof;
int EOF = 255;

feof(file) {
    c2bf_eof;
}

getchar() {
    int c;

    if (c2bf_eof == 1) {
        c = EOF;
    } else {
        c = __c2bf_input;

        if (c == 0) { c = EOF; }
        else if (c == 26) { c = EOF; }

        if (c == EOF) { c2bf_eof = 1; }
    }

    c;
}

putchar(c) {
    __c2bf_print(c);
}


#endif
#endif
