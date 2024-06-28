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
Besides OR-Tools' CP-SAT solver, PyJobShop also implements the IBM ILOG CP Optimizer, which is a commercial constraint programming solver.
To try out CP Optimizer, you can install PyJobShop with the optional `cpoptimizer` dependency as follows:

.. code-block:: shell

   pip install pyjobshop[cpoptimizer]

This installation comes with the free community edition of CP Optimizer, which only solves models with up to 1000 variables and 1000 constraints.
Models beyond that size require the paid version or academic version.

If you are a student or researcher working academia, you can get a free academic version of CP Optimizer for non-commericial purposes.
The steps below describe how you can install CP Optimizer through their academic program.

- Visit [ibm.com/academic](https://ibm.com/academic) and register and log in.
- Navigate to [academic.ibm.com/a2mt/downloads/data_science](https://academic.ibm.com/a2mt/downloads/data_science) and download CP Optimizer.
- Follow the installation instructions and make sure to follow the Python installation instructions at the end.
- Ensure the solver executable is found by adding its directory to the PATH. Add the following line to your shell configuration file (``~/.bashrc`, `~/.zshrc`, etc.):
- Ensure that the path to `cpoptimizer(.exe)` is accessible and properly set in your system path.


To check that your installation was successful, run the following command:


.. code-block:: shell

   poetry run pytest --solvers cpoptimizer
