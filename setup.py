#!/usr/bin/env python

from setuptools import setup
from os import path
from codecs import open

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Noodles',
    version='0.3.0',
    description='Workflow Engine',
    long_description=long_description,
    author='Johan Hidding',
    url='https://github.com/NLeSC/noodles',
    packages=[
        'noodles', 'noodles.serial', 'noodles.run', 'noodles.run.xenon',
        'noodles.run.remote',
        'noodles.display',
        'noodles.patterns',
        'noodles.interface', 'noodles.workflow', 'noodles.files',
        'noodles.prov', 'noodles.draw_workflow'],
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Distributed Computing'],

    install_requires=['graphviz', 'ujson'],
    extras_require={
        'xenon': ['pyxenon'],
        'numpy': ['numpy', 'h5py', 'filelock'],
        'develop': [
            'pytest', 'pytest', 'coverage', 'pep8', 'numpy', 'tox',
            'sphinx', 'sphinx_rtd_theme', 'nbsphinx'],
    },
)
