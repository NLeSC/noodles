#!/usr/bin/env python

"""
Setup script for Noodles.
"""

from pathlib import Path
from setuptools import setup, find_packages

# Get the long description from the README file
here = Path(__file__).parent.absolute()
with (here / 'README.rst').open(encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='Noodles',
    version='0.3.1',
    description='Workflow Engine',
    long_description=long_description,
    author='Johan Hidding',
    url='https://github.com/NLeSC/noodles',
    packages=find_packages(exclude=['test*']),
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Distributed Computing'],

    install_requires=['graphviz', 'ujson'],
    extras_require={
        'xenon': ['pyxenon'],
        'numpy': ['numpy', 'h5py', 'filelock'],
        'develop': [
            'pytest', 'pytest', 'coverage', 'pep8', 'numpy', 'tox',
            'sphinx', 'sphinx_rtd_theme', 'nbsphinx', 'flake8'],
    },
)
