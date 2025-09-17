.. figure:: assets/images/logo.svg
   :alt: PyJobShop logo
   :figwidth: 100%


PyJobShop is a Python library for solving scheduling problems with constraint programming.
It currently supports the following scheduling problems:

- **Resource environments:** single machines, parallel machines, hybrid flow shops, open shops, job shops, flexible job shops, distributed shops, renewable resources and non-renewable resources.
- **Constraints:** release dates, deadlines, due dates, multiple modes, permutations, sequence-dependent setup times, no-wait, no-idle, blocking, breaks, optional task selection, and arbitrary precedence constraints.
- **Objective functions:** minimizing makespan, total flow time, number of tardy jobs, total tardiness, total earliness, maximum tardiness, and total setup times.

You can find PyJobShop on the Python Package Index under the name ``pyjobshop``.
To install it, simply run:

.. code-block:: shell

   pip install pyjobshop


.. hint::

    If you are new to scheduling or constraint programming, you might benefit from first reading the :doc:`introduction to scheduling <setup/intro_to_scheduling>` and :doc:`introduction to CP <setup/intro_to_cp>` pages.
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
   setup/citing

.. toctree::
   :maxdepth: 1
   :caption: Examples

   examples/simple_example
   examples/flexible_job_shop
   examples/hybrid_flow_shop
   examples/permutation_flow_shop
   examples/project_scheduling
   examples/optional_tasks
   examples/breaks
   examples/objectives
   examples/quick_examples

.. toctree::
   :maxdepth: 1
   :caption: API reference

   api/pyjobshop
   api/plot

.. toctree::
   :maxdepth: 1
   :caption: Developing PyJobShop

   dev/contributing
   dev/resources
