#include "test.hh"
#include "../src/common.hh"

Test test_mandel("src/mandel.cc", [] () {
    assert(mandelbrot(256)(complex(0,0)));
    assert(!mandelbrot(256)(complex(2,2)));
    return true;
});

Test test_julia("src/julia.cc", [] () {
    assert(julia(complex(0,0), 256)(complex(0,0)));
    assert(!julia(complex(0,0), 256)(complex(2,2)));
    return true;
});
