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
    version='0.2.3',
    description='Workflow Engine',
    author='Johan Hidding',
    url='https://github.com/NLeSC/noodles',
    packages=[
        'noodles', 'noodles.serial', 'noodles.run', 'noodles.run.xenon',
        'noodles.run.remote',
        'noodles.display',
        'noodles.interface', 'noodles.workflow', 'noodles.files',
        'noodles.prov'],

    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Distributed Computing'],

    install_requires=[],
    extras_require={
        'prov': ['tinydb', 'ujson'],
        'xenon': ['pyxenon'],
        'numpy': ['numpy', 'h5py', 'msgpack-python', 'filelock'],
        'test': ['nose', 'coverage', 'pyflakes', 'pep8', 'docker-py']
    },
)
