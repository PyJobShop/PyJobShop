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

    .. autoclass:: StartBeforeStart

    .. autoclass:: StartBeforeEnd

    .. autoclass:: EndBeforeStart

    .. autoclass:: EndBeforeEnd

    .. autoclass:: IdenticalResources

    .. autoclass:: DifferentResources

    .. autoclass:: Consecutive

    .. autoclass:: SameSequence
       :exclude-members: tasks1, tasks2

    .. autoclass:: SetupTime

    .. autoclass:: ModeDependency

    .. autoclass:: Constraints
       :members:

    .. autoclass:: Objective
       :members:

.. automodule:: pyjobshop.Solution

   .. autoclass:: Solution

   .. autoclass:: TaskData

   .. autoclass:: JobData

.. automodule:: pyjobshop.Result

   .. autoclass:: Result

   .. class:: SolveStatus

      Enum representing the termination status of the solver run.

      .. attribute:: OPTIMAL
         :value: "Optimal"

         Solution is proven optimal.

      .. attribute:: FEASIBLE
         :value: "Feasible"

         A feasible solution was found.

      .. attribute:: INFEASIBLE
         :value: "Infeasible"

         Problem is proven infeasible.

      .. attribute:: TIME_LIMIT
         :value: "Time-limit"

         Solver terminated due to time limit.

      .. attribute:: UNKNOWN
         :value: "Unknown"

         Solver terminated with unknown status.

.. automodule:: pyjobshop.solve
   :members:

.. automodule:: pyjobshop.constants
   :members:
