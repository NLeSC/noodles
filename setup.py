#!/usr/bin/env python

from distutils.core import setup

setup(
    name='Noodles',
    version='0.1.0',
    description='Workflow Engine',
    author='Johan Hidding',
    url='https://github.com/NLeSC/noodles',
    packages=['noodles'],

    classifiers=[
        'License :: OSI Approved :: '
        'GNU Lesser General Public License v3 or later (LGPLv3+)',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Environment :: Console',
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.5',
        'Topic :: System :: Distributed Computing'],

    install_requires=[],
    tests_require=['nose', 'coverage', 'pyflakes', 'pep8'])
