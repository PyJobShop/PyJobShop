# PyJobShop
[![pyjobshop](https://github.com/leonlan/pyjobshop/actions/workflows/CI.yml/badge.svg)](https://github.com/leonlan/pyjobshop/actions/workflows/CI.yml)
[![codecov](https://codecov.io/gh/leonlan/PyJobShop/graph/badge.svg?token=5WZK5HW1FI)](https://codecov.io/gh/leonlan/PyJobShop)

PyJobShop is a package for implementing scheduling models in Python.
It supports the classically known *flexible job shop problem* (FJSP) and many of its extensions such as arbitrary precedence relations, sequence-dependent setup times, and many more!
The implementation is currently work in progress and V1 is planned to be finished in by April 2024.
Feel free to open an issue if you have any questions.


## Installation
First, clone this repository to your local setup and `cd` into it. 
Then, make sure you have [Poetry](https://python-poetry.org/) version 1.2+ installed, and run the following command:

``` shell
poetry install
```

This will set-up a virtual environment and install all necessary dependencies. 

### Installing CPLEX
Running the CP model and solving it requires the optimization engine from IBM CPLEX. 
See [their documentation](http://ibmdecisionoptimization.github.io/docplex-doc/getting_started.html#setting-up-an-optimization-engine) for more details.
If you install the free community edition, you can only solve models with up to 1000 variables and 1000 constraints.
Models beyond that size require a paid version or an academic version.
