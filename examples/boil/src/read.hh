#pragma once

#include <string>
#include <sstream>

template <typename T>
T read(std::string s) {
    T v;
    std::istringstream iss(s);
    iss >> v;
    return v;
}

