#include <iostream>
#include <string>
#include <vector>

#include "../src/common.hh"
#include "../src/read.hh"

int main(int argc_, char **argv_) {
    std::vector<std::string> argv(argv_, argv_ + argc_);

    if (argv.size() >= 2 and argv[1] == "mandelbrot") {
        if (argv.size() >= 3 and argv[2] == "-c") {
            render_colour(mandelbrot_c(256), complex(-2.15, -1), complex(0.85, 1));
        } else {
            render(mandelbrot(256), complex(-2, -1), complex(1, 1));
        }
        exit(0);
    }

    if (argv.size() >= 4 and argv[1] == "julia") {
        complex c(read<double>(argv[2]), read<double>(argv[3]));
        if (argv.size() >= 5 and argv[4] == "-c") {
            render_colour(julia_c(c, 256), complex(-2, -1.2), complex(2, 1.2));
        } else {
            render(julia(c, 256), complex(-2, -1.2), complex(2, 1.2));
        }
        exit(0);
    }

    std::cout << "Toy fractal renderer." << std::endl;
    std::cout << "usage: " << argv[0] << " mandelbrot [-c] | julia <real> <imag> [-c]" << std::endl;
    std::cout << "The '-c' option adds colour; have fun!" << std::endl;
}

