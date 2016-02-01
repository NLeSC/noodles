#include <iostream>
#include <string>
#include <vector>
#include <unistd.h>

#include "../src/common.hh"
#include "../src/read.hh"

int main(int argc_, char **argv_) {
    std::vector<std::string> argv(argv_, argv_ + argc_);

    int columns = 80;
    bool use_colour = false;
    int opt;
    if (argv.size() >= 2 and argv[1] == "mandelbrot") {
        while ((opt = getopt(argc_, argv_, "cw:")) != -1) {
            switch (opt) {
                case 'c': use_colour = true; break;
                case 'w': columns = read<int>(optarg);
            }
        }

        if (use_colour) {
            render_double_colour(mandelbrot_c(256),
                complex(-2.15, -1), complex(0.85, 1),
                columns);
        } else {
            render(mandelbrot(256),
                complex(-2, -1), complex(1, 1),
                columns);
        }
        exit(0);
    }

    if (argv.size() >= 4 and argv[1] == "julia") {
        complex c(read<double>(argv[2]), read<double>(argv[3]));
        while ((opt = getopt(argc_ - 3, argv_ + 3, "cw:")) != -1) {
            switch (opt) {
                case 'c': use_colour = true; break;
                case 'w': columns = read<int>(optarg);
            }
        }

        if (use_colour) {
            render_double_colour(julia_c(c, 256),
                complex(-2, -1.2), complex(2, 1.2),
                columns);
        } else {
            render(julia(c, 256),
                complex(-2, -1.2), complex(2, 1.2),
                columns);
        }
        exit(0);
    }

    std::cout << "Toy fractal renderer." << std::endl;
    std::cout << "usage: " << argv[0] << " mandelbrot [-c] [-w <n>] | julia <real> <imag> [-c] [-w <n>]\n\n";
    std::cout << "Some nice coordinates for the Julia set: \n"
              << "    0.26, -1, -0.123+0.745i, -1+0.29i, -0.03+0.7i, etc. \n"
              << "Pro tip: set your terminal to fullscreen and tiny font, \n"
              << "    then run with '-w $COLUMNS'.\n";
    std::cout << "The '-c' option adds colour; have fun!" << std::endl;
}

