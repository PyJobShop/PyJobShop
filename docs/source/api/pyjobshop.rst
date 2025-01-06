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

    .. autoclass:: Machine
       :members:

    .. autoclass:: Renewable
       :members:

    .. autoclass:: NonRenewable
       :members:

    .. autoclass:: Task
       :members:

    .. autoclass:: Mode
       :members:

    .. autoclass:: Constraints
        :members:

    .. autoclass:: StartBeforeStart
        :exclude-members: count, index

    .. autoclass:: StartBeforeEnd
        :exclude-members: count, index

    .. autoclass:: EndBeforeStart
        :exclude-members: count, index

    .. autoclass:: EndBeforeEnd
        :exclude-members: count, index

    .. autoclass:: IdenticalResources
        :exclude-members: count, index

    .. autoclass:: DifferentResources
        :exclude-members: count, index

    .. autoclass:: Consecutive
        :exclude-members: count, index

    .. autoclass:: SetupTime
        :exclude-members: count, index

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
