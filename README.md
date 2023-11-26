[![CI](https://github.com/leonlan/PyJobShop/actions/workflows/CI.yml/badge.svg?branch=main)](https://github.com/leonlan/PyJobShop/actions/workflows/CI.yml/badge.svg)
[![codecov](https://codecov.io/gh/leonlan/PyJobShop/graph/badge.svg?token=5WZK5HW1FI)](https://codecov.io/gh/leonlan/PyJobShop)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


# Flexible Job Shop Problem
This repository implements a constraint programming (CP) model for the flexible job shop problem (FJSP).
We consider a rich variant of the FJSP with many different constraints, such as arbitrary operations precedence relations, sequence-dependent setup times, and many more.
The implementation is currently work in progress and V1 is planned to be finished in 2024 Q2.
Feel free to open an issue if you have any questions.

We use IBM ILOG CP Optimizer to implement the CP model.
Contributions to migrate the CP Optimizer model to OR-Tools are welcome.


## Installation
First, clone this repository to your local setup and `cd` into it. 
Then, make sure you have [Poetry](https://python-poetry.org/) version 1.2+ installed, and run the following command:

``` shell
poetry install
```

This will set-up a virtual environment and install all necessary dependencies. 
Running the following script should work now:

``` shell
poetry run python flowshop.py
```

### Installing CPLEX
Running the CP model and solving it requires the optimization engine from IBM CPLEX. 
See [their documentation](http://ibmdecisionoptimization.github.io/docplex-doc/getting_started.html#setting-up-an-optimization-engine) for more details.
If you install the free community edition, you can only solve models with up to 1000 variables and 1000 constraints.
Models beyond that size require a paid version or an academic version.
