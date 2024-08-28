> [!NOTE]
> This package is under development. Expect things to break significantly in versions ``v0.0.*``.

![PyJobShop logo](docs/source/assets/images/logo.svg)

[![PyPI](https://img.shields.io/pypi/v/PyJobShop?style=flat-square)](https://pypi.org/project/pyjobshop/)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](https://github.com/PyJobShop/PyJobShop/)
[![CI](https://img.shields.io/github/actions/workflow/status/PyJobShop/PyJobShop/.github%2Fworkflows%2FCI.yml?style=flat-square)](https://github.com/PyJobShop/PyJobShop/)
[![DOC](https://img.shields.io/readthedocs/pyjobshop?style=flat-square)](https://pyjobshop.readthedocs.io/)
[![Codecov](https://img.shields.io/codecov/c/github/PyJobShop/PyJobShop?style=flat-square)](https://app.codecov.io/gh/PyJobShop/PyJobShop/)

PyJobShop is a Python library for solving scheduling problems with constraint programming.
It currently supports the following scheduling problems:

- **Machine environments:** single machine, parallel machines, hybrid flow shops, open shops, job shops, and flexible job shops.
- **Constraints:** release dates, deadlines, due dates, sequence-dependent setup times, no-wait, blocking, and precedence constraints.
- **Objective functions:** minimizing makespan, total completion time, number of tardy jobs, and total tardiness.

You can find PyJobShop on the Python Package Index under the name `pyjobshop`. 
To install it, simply run:

``` shell
pip install pyjobshop
```

The documentation is available [here](https://pyjobshop.readthedocs.io/).

> [!TIP]
> If you are new to scheduling or constraint programming, you might benefit from first reading the [introduction to scheduling](https://pyjobshop.readthedocs.io/en/stable/setup/intro_to_scheduling.html) and [introduction to CP](https://pyjobshop.readthedocs.io/en/stable/setup/intro_to_cp.html) pages.

## Constraint programming solvers
PyJobShop uses [OR-Tools'](https://github.com/google/or-tools) CP-SAT solver as its default constraint programming solver.
We also support CP Optimizer - see [our documentation](https://pyjobshop.readthedocs.io/en/stable/setup/installation.html) for instructions on how to install PyJobShop with CP Optimizer.

## Examples
We provide example notebooks that show how PyJobShop may be used to solve scheduling problems.

- TODO

## Contributing
We are very grateful for any contributions you are willing to make. 
Please have a look [here](https://pyjobshop.readthedocs.io/en/stable/contributing.html) to get started. 
If you aim to make a large change, it is helpful to discuss the change first in a new GitHub issue. Feel free to open one!

## Getting help
Feel free to open an issue or a new discussion thread here on GitHub.
Please do not e-mail us with questions, modelling issues, or code examples.
Those are much easier to discuss via GitHub than over e-mail.
When writing your issue or discussion, please follow the instructions [here](https://pyjobshop.readthedocs.io/en/stable/setup/getting_help.html).
