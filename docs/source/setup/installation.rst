Installation instructions
=========================
The easiest way to install the ``pyjobshop`` package is through ``pip``.
To install it, simply run:

.. code-block:: shell

   pip install pyjobshop


Installing from source¶
----------------------
To install the latest version of ``pyjobshop`` directly from the GitHub repository, run the following:

.. code-block:: shell

   pip install 'pyjobshop @ git+https://github.com/PyJobShop/PyJobShop

This can be useful to get features that have not yet made it to the Python package index.


Installing CP Optimizer
-----------------------
By default, PyJobShop comes with OR-Tools' CP-SAT solver, which is an open-source constraint programming solver.
PyJobShop also implements the IBM ILOG CP Optimizer, which is a commercial constraint programming solver.
To use PyJobShop with CP Optimizer, you can install PyJobShop with the optional `cpoptimizer` dependency as follows:

.. code-block:: shell

   pip install pyjobshop[cpoptimizer]

This installation comes with the free community edition of CP Optimizer, which solves models with up to 1000 variables and 1000 constraints.
Models beyond that size require a paid version or academic version of CP Optimizer.

If you are a student or researcher, you can get a free academic version of CP Optimizer for non-commercial purposes.
The steps below describe how you can install CP Optimizer through their academic program.

- Register at [ibm.com/academic](https://ibm.com/academic) and log in.
- Go to [academic.ibm.com/a2mt/downloads/data_science](https://academic.ibm.com/a2mt/downloads/data_science) and download CP Optimizer.
- Follow the installation instructions and make sure to follow the Python installation instructions at the end.
- Ensure that the path to `cpoptimizer(.exe)` is accessible and properly set in your system path.
