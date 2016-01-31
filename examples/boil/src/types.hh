#pragma once

#include <complex>
#include <functional>

using complex = std::complex<double>;
using function = std::function<complex (complex)>;
using predicate = std::function<bool (complex)>;
using unit_map = std::function<double (complex)>;

