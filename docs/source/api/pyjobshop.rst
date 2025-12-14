.. module:: pyjobshop
   :synopsis: PyJobShop


PyJobShop
=========

.. automodule:: pyjobshop.Model

   .. autoclass:: Model
      :members:

      .. rubric:: Methods

      .. autosummary::
         :nosignatures:

         ~Model.add_job
         ~Model.add_machine
         ~Model.add_renewable
         ~Model.add_consumable
         ~Model.add_task
         ~Model.add_mode
         ~Model.add_start_before_start
         ~Model.add_start_before_end
         ~Model.add_end_before_start
         ~Model.add_end_before_end
         ~Model.add_identical_resources
         ~Model.add_different_resources
         ~Model.add_consecutive
         ~Model.add_same_sequence
         ~Model.add_setup_time
         ~Model.add_mode_dependency
         ~Model.add_select_all_or_none
         ~Model.add_select_at_least_one
         ~Model.add_select_exactly_one
         ~Model.remove_mode
         ~Model.remove_modes
         ~Model.set_objective
         ~Model.summary
         ~Model.from_data
         ~Model.data
         ~Model.solve

.. automodule:: pyjobshop.ProblemData

    .. autoclass:: ProblemData
       :members:

    .. autoclass:: Job
       :members:

    .. autoclass:: Machine
       :members:

    .. autoclass:: Renewable
       :members:

    .. autoclass:: Consumable
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

    .. autoclass:: SelectAllOrNone
       :exclude-members: condition_task

    .. autoclass:: SelectAtLeastOne
       :exclude-members: condition_task

    .. autoclass:: SelectExactlyOne
       :exclude-members: condition_task

    .. autoclass:: Constraints
       :exclude-members: __len__
       :members:

    .. autoclass:: Objective
       :members:

.. automodule:: pyjobshop.Solution

   .. autoclass:: Solution

   .. autoclass:: TaskData

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
