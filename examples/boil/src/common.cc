#include "types.hh"

function f(complex c) {
    return [c] (complex z) {
        return z*z + c;
    };
}

bool pred(complex z) {
    return std::norm(z) < 4.0;
}

