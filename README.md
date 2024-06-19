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
PyJobShop uses [OR-Tools](https://github.com/google/or-tools) as the default constraint programming solver.

TODO


### Installing CPLEX
Running the CP model and solving it requires the optimization engine from IBM CPLEX. 
See [their documentation](http://ibmdecisionoptimization.github.io/docplex-doc/getting_started.html#setting-up-an-optimization-engine) for more details.
If you install the free community edition, you can only solve models with up to 1000 variables and 1000 constraints.
Models beyond that size require a paid version or an academic version.

## Examples
We provide example notebooks that show how PyJobShop may be used to solve scheduling problems.

- TODO

## Contributing
TODO

## Getting help
TODO
