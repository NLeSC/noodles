#include <cmath>
#include "common.hh"

predicate mandelbrot(int maxit) {
    return [maxit] (complex c) {
        return iterate(f(c), pred, complex(0, 0), maxit) == maxit;
    };
}

unit_map mandelbrot_c(int maxit) {
    return [maxit] (complex c) {
        return sqrt(double(iterate(f(c), pred, complex(0, 0), maxit)) / maxit);
    };
}

