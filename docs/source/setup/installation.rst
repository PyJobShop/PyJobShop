Installation instructions
=========================
The easiest way to install the ``pyjobshop`` package is through ``pip``.
To install it, simply run:

.. code-block:: shell

   pip install pyjobshop


Installing from source
----------------------
To install the latest version of ``pyjobshop`` directly from the GitHub repository, run the following:

.. code-block:: shell

   pip install 'pyjobshop @ git+https://github.com/PyJobShop/PyJobShop'

This can be useful to get features that have not yet made it to the Python package index.


Installing CP Optimizer
-----------------------
By default, PyJobShop comes with OR-Tools' CP-SAT solver, which is an open-source constraint programming solver.
PyJobShop can also be used with IBM ILOG CP Optimizer, which is a commercial constraint programming solver.
To use PyJobShop with CP Optimizer, there are two different ways, depending on whether you have CP Optimizer installed or not.

If you already have CP Optimizer installed, then you only need the additional `docplex` dependency which can be installed together with PyJobShop as follows:

.. code-block:: shell

   pip install pyjobshop[docplex]

If you don't have CP Optimizer, then you can install PyJobShop with the free community edition of CP Optimizer.
This free edition is able to solve models with up to 1000 variables and 1000 constraints, beyond that size you need a paid version or academic version of CP Optimizer.

.. code-block:: shell

   pip install pyjobshop[docplex,cplex]


If you are a student or researcher, you can get a free academic version of CP Optimizer for non-commercial purposes.
The steps below describe how you can install CP Optimizer through their academic program.

- Register at [ibm.com/academic](https://ibm.com/academic) and log in.
- Go to [academic.ibm.com/a2mt/downloads/data_science](https://academic.ibm.com/a2mt/downloads/data_science) and download ILOG CPLEX Optimization Studio, which comes with CP Optimizer.
- Follow the installation instructions and make sure to follow the Python installation instructions at the end.
- Ensure that the path to `cpoptimizer(.exe)` is accessible and properly set in your system path.
