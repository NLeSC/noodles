#include "types.hh"
#include <iostream>

void render(predicate pred, complex a, complex b, int width) {
    int height = width/3;
    double scale_real = (b.real() - a.real()) / width;
    double scale_imag = (b.imag() - a.imag()) / height;

    for (unsigned j = 0; j < height; ++j) {
        for (unsigned i = 0; i < width; ++i) {
            complex c = a + complex(i * scale_real, j * scale_imag);

            if (pred(c))
                std::cout << '#';
            else
                std::cout << ' ';
        }
        std::cout << std::endl;
    }
}

struct Colour {
    int r, g, b;

    Colour(int r_, int g_, int b_):
        r(r_), g(g_), b(b_) {}
};

Colour colour_map(double x) {
    double r = (0.472-0.567*x+4.05*pow(x, 2))
                /(1.+8.72*x-19.17*pow(x, 2)+14.1*pow(x, 3)),
           g = 0.108932-1.22635*x+27.284*pow(x, 2)-98.577*pow(x, 3)
                +163.3*pow(x, 4)-131.395*pow(x, 5)+40.634*pow(x, 6),
           b = 1./(1.97+3.54*x-68.5*pow(x, 2)+243*pow(x, 3)
                -297*pow(x, 4)+125*pow(x, 5));

    return Colour(int(r*255), int(g*255), int(b*255));
}

void render_double_colour(unit_map f, complex a, complex b, int width) {
    int height = (width * 10) / 16;
    double scale_real = (b.real() - a.real()) / width;
    double scale_imag = (b.imag() - a.imag()) / height;

    for (unsigned j = 0; j < height; j += 2) {
        for (unsigned i = 0; i < width; ++i) {
            complex c1 = a + complex(i * scale_real, j * scale_imag);
            complex c2 = a + complex(i * scale_real, (j+1) * scale_imag);
            auto clr1 = colour_map(f(c1)),
                 clr2 = colour_map(f(c2));

            std::cout << "\033[38;2;" << clr1.r << ";"
                      << clr1.g << ";" << clr1.b << "m"
                      << "\033[48;2;" << clr2.r << ";"
                      << clr2.g << ";" << clr2.b << "m▀";
        }
        std::cout << "\033[m\n";
    }
}

