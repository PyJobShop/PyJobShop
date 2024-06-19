> [!NOTE]
> This package is under development. Expect things to break significantly in versions ``v0.0.*``.


# PyJobShop
[![PyPI](https://img.shields.io/pypi/v/PyJobShop?style=flat-square)](https://pypi.org/project/pyjobshop/)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](https://github.com/PyJobShop/PyJobShop/)
[![CI](https://img.shields.io/github/actions/workflow/status/PyJobShop/PyJobShop/.github%2Fworkflows%2FCI.yml?style=flat-square)](https://github.com/PyJobShop/PyJobShop/)
[![DOC](https://img.shields.io/readthedocs/pyjobshop?style=flat-square)](https://pyjobshop.readthedocs.io/)
[![Codecov](https://img.shields.io/codecov/c/github/PyJobShop/PyJobShop?style=flat-square)](https://app.codecov.io/gh/PyJobShop/PyJobShop/)

PyJobShop is a Python package for solving scheduling problems with constraint programming.
It currently supports the following scheduling problems:

- **Machine environments:** single machine, parallel machines, hybrid flow shops, open shops, and flexible job shops.
- **Constraints:** release dates, deadlines, sequence-dependent setup times, no-wait, blocking, and precedence constraints.
- **Objective functions:** minimizing makespan, total completion time, number of tardy jobs, and total tardiness.

You can find PyJobShop on the Python Package Index under the name `pyjobshop`. 
To install it, simply run:

``` shell
pip install pyjobshop
```

The documentation is available [here](https://pyjobshop.readthedocs.io/).


## Constraint programming solvers
PyJobShop uses [OR-Tools'](https://github.com/google/or-tools) CP-SAT solver as its default constraint programming solver.
CP-SAT is an open-source constraint programming solver and encompasses other technologies such as satisfiability and mixed-integer linear programming solvers.
CP-SAT has consistently won the annual [MiniZinc Challenge](https://www.minizinc.org/challenge/), demonstrating its superior performance on constraint programming models.

> [!TIP]
> If you are new to scheduling or constraint programming, you might benefit from first reading the TODO and TODO pages.

Besides OR-Tools' CP-SAT solver, PyJobShop also implements the IBM ILOG CP Optimizer, which is a commercial and very effective constraint programming solver.
To use CP Optimizer, you have to install PyJobShop with the optional `cpoptimizer` dependency as follows: 

``` shell
pip install pyjobshop[cpoptimizer]
```

This installation comes with the free community edition of CP Optimizer, but it only solves models with up to 1000 variables and 1000 constraints.
Models beyond that size require a paid version or an academic version.
See [their documentation](http://ibmdecisionoptimization.github.io/docplex-doc/getting_started.html#setting-up-an-optimization-engine) for more details on how to obtain such version.

TODO: refer to documentation on how to get an academic version of CP Optimizer.

## Examples
We provide example notebooks that show how PyJobShop may be used to solve scheduling problems.

- TODO

## Contributing
TODO

## Getting help
TODO
