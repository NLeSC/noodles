#include "common.hh"
#include <cmath>

predicate julia(complex c, int maxit) {
    return [c, maxit] (complex z) {
        return iterate(f(c), pred, z, maxit) == maxit;
    };
}

unit_map julia_c(complex c, int maxit) {
    return [c, maxit] (complex z) {
        return sqrt(double(iterate(f(c), pred, z, maxit)) / maxit);
    };
}
