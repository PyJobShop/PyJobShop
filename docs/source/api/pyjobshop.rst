.. module:: pyjobshop
   :synopsis: PyJobShop


PyJobShop
=========

.. automodule:: pyjobshop.Model

   .. autoclass:: Model
      :members:

.. automodule:: pyjobshop.ProblemData

    .. autoclass:: ProblemData
       :members:

    .. autoclass:: Job
       :members:

    .. autoclass:: Resource
       :members:

    .. autoclass:: Machine
       :members:

    .. autoclass:: Task
       :members:

    .. autoclass:: Mode
       :members:

    .. autoenum:: Constraint

    .. autoclass:: Objective
       :members:


.. automodule:: pyjobshop.Solution

   .. autoclass:: Solution

   .. autoclass:: TaskData

.. automodule:: pyjobshop.Result

   .. autoclass:: Result

   .. autoclass:: SolveStatus


.. automodule:: pyjobshop.solve
   :members:

.. automodule:: pyjobshop.constants
   :members:


.. module:: pyjobshop.plot
   :synopsis: Plotting tools

Plotting tools
--------------

The :mod:`pyjobshop.plot` module contains various functions for plotting solutions.

.. automodule:: pyjobshop.plot.plot_machine_gantt

   .. autofunction:: plot_machine_gantt

.. automodule:: pyjobshop.plot.plot_task_gantt

   .. autofunction:: plot_task_gantt

.. automodule:: pyjobshop.plot.plot_resource_usage

   .. autofunction:: plot_resource_usage

.. automodule:: pyjobshop.plot.plot_resource_gantt

   .. autofunction:: plot_resource_gantt
