.. figure:: assets/images/logo.svg
   :alt: PyVRP logo
   :figwidth: 100%

.. note::

   This project is under active development. Expect things to break significantly in versions ``v0.0.*``.


PyJobShop is a Python library for solving scheduling problems with constraint programming.
It currently supports the following scheduling problems:

- **Machine environments:** single machine, parallel machines, hybrid flow shops, open shops, and flexible job shops.
- **Constraints:** release dates, deadlines, sequence-dependent setup times, no-wait, blocking, and precedence constraints.
- **Objective functions:** minimizing makespan, total completion time, number of tardy jobs, and total tardiness.

You can find PyJobShop on the Python Package Index under the name ``pyjobshop``.
To install it, simply run::

  pip install pyjobshop


.. hint::

    If you are new to scheduling or constraint programming, you might benefit from first reading the :doc:`introduction to scheduling <setup/introduction_to_scheduling>` and :doc:`introduction to CP <setup/introduction_to_cp>`.
    To set up an installation from source, or to run the examples listed below yourself, please have a look at the :doc:`installation instructions <setup/installation>`.

Contents
--------

.. toctree::
   :maxdepth: 1
   :caption: Getting started

   setup/intro_to_scheduling
   setup/intro_to_cp
   setup/installation
   setup/getting_help

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/simple_example
   examples/hybrid_flow_shop
   examples/flexible_job_shop

.. toctree::
   :maxdepth: 1
   :caption: API reference

   api/pyjobshop

.. toctree::
   :maxdepth: 1
   :caption: Developing PyJobShop

   dev/contributing
   dev/new_variants
