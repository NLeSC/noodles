#include "test.hh"
#include "../src/read.hh"

Test test_read("src/read.hh", [] () {
    assert(read<int>("15") == 15);
    assert(read<double>("3.1415") == 3.1415);
    return true;
});
