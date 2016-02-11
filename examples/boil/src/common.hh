#pragma once

#include "types.hh"

extern int iterate(function f, predicate pred, complex z, unsigned maxint);
extern bool pred(complex z);
extern function f(complex c);
extern void render(predicate pred, complex a, complex b, unsigned width);
extern void render_double_colour(unit_map f, complex a, complex b, unsigned width);

extern predicate mandelbrot(int maxit);
extern predicate julia(complex c, int maxit);
extern unit_map mandelbrot_c(int maxit);
extern unit_map julia_c(complex c, int maxit);
