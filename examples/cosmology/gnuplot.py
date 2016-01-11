# -*- coding: utf-8 -*-
# module that plots gnuplot to IPython notebook

import sys
from subprocess import Popen, PIPE
# from functools import reduce, partial
import numpy as np


class Gnuplot:
    """Create an instance of the Gnuplot process. If dummy is given, the
    process will just print to stdout in stead of running Gnuplot."""
    def __init__(self, persist=False, dummy=False, binary=True):
        if dummy:
            self.f = sys.stdout
        elif persist:
            self.p = Popen(["gnuplot", "-persist"], stdin=PIPE)
            self.f = self.p.stdin
        else:
            self.p = Popen("gnuplot", stdin=PIPE)
            self.f = self.p.stdin

        if binary:
            self.put_array = self.put_array_binary
        else:
            self.put_array = self.put_array_text

    def __call__(self, *args):
        """Send commands to Gnuplot. If an instance of a numpy array is given,
        it is converted to inline data. You can use this if you give a
        'plot '-' ... ' command just before the data."""
        for a in args:
            if isinstance(a, bytes):
                self.f.write(a)
                self.f.flush()

            if isinstance(a, str):
                self.f.write(a.encode())
                self.f.write('\n'.encode())
                self.f.flush()

            if isinstance(a, np.ndarray):
                self.put_array(a)

            if isinstance(a, list):
                for i in a:
                    self(i)

    def flush(self):
        self.f.flush()

    def terminate(self):
        """Close the Gnuplot input pipe, and wait for the process to exit."""
        self.f.close()
        self.p.wait()

    def put_array_binary(self, data):
        self.f.write(data.tostring())

    def put_array_text(self, data):
        """Print array data such that Gnuplot understands it as inlined data entries.
        Doesn't work with matrix data yet, since Gnuplots protocol for entering
        matrix data by text is different from other data."""
        if len(data.shape) > 3:
            raise

        if len(data.shape) == 1:
            for x in data:
                self(str(x))

        if len(data.shape) == 2:
            for x in data:
                self(" ".join([str(l) for l in x]))

        if len(data.shape) == 3:
            for x in data:
                for y in x:
                    self(" ".join([str(l) for l in y]))
                self("")

        self("EOF")


class Multiplot:
    def __init__(self, w, h, n, m):
        self.w = w
        self.h = h
        self.n = n
        self.m = m
        self.set_margin(0.1, 0.1, 0.8, 0.3)

    def set_margin(self, t, r, b, l):
        "set margins (clockwise: t, r, b, l) and recalculate plot positions"
        self.margin_left = l
        self.margin_bottom = b
        self.margin_top = t
        self.margin_right = r

        self.fw = self.w*self.n + self.margin_left + self.margin_right
        self.fh = self.h*self.m + self.margin_top + self.margin_bottom

        self.ml = self.margin_left / self.fw
        self.mr = self.margin_right / self.fw
        self.mt = self.margin_top / self.fh
        self.mb = self.margin_bottom / self.fh

        self.ew = (1 - (self.ml + self.mr)) / self.n
        self.eh = (1 - (self.mt + self.mb)) / self.m

    def set_term(self, term="pdf"):
        return "set term {2} size {0:f},{1:f} " \
               "font 'Bitstream Charter, 10'".format(
                   self.fw, self.fh, term)

    def subplot(self, i, j):
        left = self.ml + self.ew * i
        right = self.ml + self.ew * (i+1)
        bottom = self.mb + self.eh * (self.m - j - 1)
        top = self.mb + self.eh * (self.m - j)
        return "set l{0} {1:f}; set r{0} {2:f}; " \
               "set b{0} {3:f} ; set t{0} {4:f}".format(
                   "margin at screen", left, right, bottom, top)

    def left(self, i):
        return self.ml + self.ew * i

    def bottom(self, j):
        return self.mb + self.eh * (self.m - j - 1)


def matrix(data, using=None):
    plot_using = ""
    d = np.zeros([s+1 for s in data.shape], dtype='float32')
    plot_cmd = "binary matrix"
    d[1:, 1:] = data
    d[1:, 0] = np.arange(data.shape[0])
    d[0, 1:] = np.arange(data.shape[1])
    d[0, 0] = data.shape[1]

    n = np.ones(1, dtype='int32') * data.shape[1]
    if using is not None:
        plot_using += " "
        plot_using += using

    return (plot_cmd + plot_using, n.tostring() + d.flat[1:].tostring())


def array(data, using=None):
    plot_cmd = "binary array={0} format='%{1}'".format(data.shape, data.dtype)
    plot_using = ""
    if using is not None:
        plot_using += " "
        plot_using += using
    plot_data = data.tostring()
    return (plot_cmd + plot_using, plot_data)


def record(data, using=None):
    plot_cmd = "binary record={0} format='{1}'".format(
        data.shape[0], ("%" + str(data.dtype)) * data.shape[1])
    plot_using = ""
    if using is not None:
        plot_using += " "
        plot_using += using
    plot_data = data
    return (plot_cmd + plot_using, plot_data)


def plot_data(*args):
    plot_cmd = "plot '-' " + args[0][0] + ", '' ".join(a[0] for a in args[1:])
    plot_data = [a[1] for a in args]
    return [plot_cmd] + plot_data


def splot_data(*args):
    plot_cmd = "splot '-' " + ", '' ".join(a[0] for a in args)
    plot_data = [a[1] for a in args]
    return [plot_cmd] + plot_data


default_palette = """# default blue to red palette
rcol(x) = 0.237 - 2.13*x + 26.92*x**2 - 65.5*x**3 + 63.5*x**4 - 22.36*x**5
gcol(x) = ((0.572 + 1.524*x - 1.811*x**2)/(1 - 0.291*x + 0.1574*x**2))**2
bcol(x) = 1/(1.579 - 4.03*x + 12.92*x**2 - 31.4*x**3 + 48.6*x**4 - 23.36*x**5)
set palette model RGB functions rcol(gray), gcol(gray), bcol(gray)
"""
