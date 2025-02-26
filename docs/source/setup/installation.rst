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

PyJobShop includes OR-Tools' CP-SAT solver by default, an open-source constraint programming solver.
Additionally, PyJobShop can be integrated with IBM ILOG CP Optimizer, a commercial constraint programming solver.

To use PyJobShop with CP Optimizer, take one of the following two steps:

1. **If you already have CP Optimizer installed:**

   Install the additional ``docplex`` dependency together with PyJobShop as follows:

   .. code-block:: shell

      pip install pyjobshop[docplex]


   ``docplex`` is the Python modeling interface for CPLEX and CP Optimizer. It allows users to model constraint programming problems in Python. It looks for a local installation of CP Optimizer to solve these models.

2. **If you don't have CP Optimizer installed:**

   You can install PyJobShop with the free community edition of CP Optimizer by including the ``cplex`` dependency.

   .. code-block:: shell

      pip install pyjobshop[docplex,cplex]

   The ``cplex`` library installs a free edition of CP Optimizer that is capable of solving models with up to 1000 variables and 1000 constraints. For larger models, you need a paid or academic version of CP Optimizer.

Obtaining the academic version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you are a student or researcher, you can get the free academic version of CP Optimizer for non-commercial purposes by following these steps:

- Register at `ibm.com/academic <https://ibm.com/academic>`_ and log in.
- Go to `academic.ibm.com/a2mt/downloads/data_science <https://academic.ibm.com/a2mt/downloads/data_science>`_ and download ILOG CPLEX Optimization Studio, which includes CP Optimizer.
- Follow the installation instructions, making sure to complete the Python installation steps at the end.
- Ensure that the path to ``cpoptimizer(.exe)`` is accessible and properly set in your system path.
