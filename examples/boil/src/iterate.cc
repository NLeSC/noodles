#include "types.hh"

int iterate(function f, predicate pred, complex z, unsigned maxit) {
    unsigned i = 0;

    while (pred(z) && i < maxit) {
        z = f(z);
        ++i;
    }

    return i;
}

