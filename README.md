---
title: Noodles - parallel programming in Python
---

[![Travis](https://travis-ci.org/NLeSC/noodles.svg?branch=master)](https://travis-ci.org/NLeSC/noodles)
[![Zenodo DOI](https://zenodo.org/badge/45391130.svg)](https://zenodo.org/badge/latestdoi/45391130)
[![Code coverage](https://codecov.io/gh/NLeSC/noodles/branch/master/graph/badge.svg)](https://codecov.io/gh/NLeSC/noodles)
[![Documentation](https://readthedocs.org/projects/noodles/badge/?version=latest)](https://noodles.readthedocs.io/en/latest/?badge=latest)

::: {.splash}
* Write readable code
* Parallelise with a dash of Noodle sauce!
* Scale your applications from laptop to HPC using Xenon
    + [Learn more about Xenon](https://xenon-middleware.github.io/xenon)
* Read our [documentation](https://noodles.rtfd.io/), including tutorials on:
    + [Creating parallel programs](https://noodles.readthedocs.io/en/latest/poetry_tutorial.html)
    + [Circumventing the global interpreter lock](https://noodles.readthedocs.io/en/latest/prime_numbers.html)
    + [Handling errors in a meaningful way](https://noodles.readthedocs.io/en/latest/errors.html)
    + [Serialising your data](https://noodles.readthedocs.io/en/latest/serialisation.html)
    + [Functional programming and flow control](https://noodles.readthedocs.io/en/latest/control_your_flow.html)
:::

# What is Noodles?

Noodles is a task-based parallel programming model in Python that offers the same intuitive interface when running complex workflows on your laptop or on large computer clusters.

# Installation
To install the latest version from PyPI:

```
pip install noodles
```

To enable the Xenon backend for remote job execution,

```
pip install noodles[xenon]
```

This requires a Java Runtime to be installed, you may check this by running

```
java --version
```

which should print the version of the currently installed JRE.


# Documentation
All the latest documentation is available on [Read the Docs](https://noodles.rtfd.io/).

