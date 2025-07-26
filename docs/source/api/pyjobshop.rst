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
       :inherited-members:
       :show-inheritance:
       :exclude-members: capacity

    .. autoclass:: Renewable
       :members:
       :inherited-members:
       :show-inheritance:

    .. autoclass:: NonRenewable
       :members:
       :inherited-members:
       :show-inheritance:

    .. autoclass:: Task
       :members:

    .. autoclass:: Mode
       :members:

    .. autoclass:: StartBeforeStart

    .. autoclass:: StartBeforeEnd

    .. autoclass:: EndBeforeStart

    .. autoclass:: EndBeforeEnd

    .. autoclass:: IdenticalResources

    .. autoclass:: DifferentResources

    .. autoclass:: Consecutive

    .. autoclass:: SetupTime

    .. autoclass:: ModeDependency

    .. autoclass:: Constraints
       :members:

    .. autoclass:: Objective
       :members:

.. automodule:: pyjobshop.Solution

   .. autoclass:: Solution

   .. autoclass:: TaskData

.. automodule:: pyjobshop.Result

   .. autoclass:: Result

   .. autoclass:: SolveStatus
      :members:

.. automodule:: pyjobshop.solve
   :members:

.. automodule:: pyjobshop.constants
   :members:
