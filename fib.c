#include "c2bf.inc"


print_fib(n) {
    int i = 1;
    int j = 0;

    while (n) {
        println_int(i);

        #ifdef __C2BF_TUPLES__
            // asignment with temporaly tuples
            [i, j] = [i + j, i];
        #else
            {
                int k = i;
                i = i + j;
                j = k;
            }
        #endif

        n -= 1;
    }
}

main() {
    int n = input_int();

    print_fib(n);
}
