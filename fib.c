#include "c2bf.inc"


print_fib(n) {
    int i = 1;
    int j = 0;

    while (n) {
        println_int(i);

        int k = i;
        i = i + j;
        j = k;

        n -= 1;
    }
}

main() {
    int n = input_int();

    print_fib(n);
}
