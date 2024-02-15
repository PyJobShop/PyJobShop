from collections import defaultdict
from typing import Iterable, Optional

import numpy as np
from docplex.cp.solution import CpoSolveResult

from .cp import default_model, result2solution
from .ProblemData import (
    AssignmentPrecedence,
    Job,
    Machine,
    Objective,
    Operation,
    ProblemData,
    TimingPrecedence,
)
from .Result import Result


class Model:
    """
    Model class to build a problem instance step-by-step.
    """

    def __init__(self):
        self._jobs = []
        self._machines = []
        self._operations = []
        self._job2ops: dict[int, list[int]] = defaultdict(list)
        self._processing_times: dict[tuple[int, int], int] = {}
        self._timing_precedences: dict[
            tuple[int, int], list[tuple[TimingPrecedence, int]]
        ] = defaultdict(list)
        self._assignment_precedences: dict[
            tuple[int, int], list[AssignmentPrecedence]
        ] = defaultdict(list)
        self._setup_times: dict[tuple[int, int, int], int] = {}
        self._process_plans: list[list[list[int]]] = []
        self._planning_horizon: Optional[int] = None
        self._objective: Objective = Objective.MAKESPAN

        self._id2job: dict[int, int] = {}
        self._id2machine: dict[int, int] = {}
        self._id2op: dict[int, int] = {}

    @property
    def jobs(self) -> list[Job]:
        return self._jobs

    @property
    def machines(self) -> list[Machine]:
        return self._machines

    @property
    def operations(self) -> list[Operation]:
        return self._operations

    @property
    def objective(self) -> Objective:
        return self._objective

    def data(self) -> ProblemData:
        """
        Returns a ProblemData object containing the problem instance.
        """
        num_jobs = len(self.jobs)
        num_ops = len(self.operations)
        num_machines = len(self.machines)

        job2ops = [self._job2ops[idx] for idx in range(num_jobs)]

        # Convert setup times into a 3D array with zero as default.
        setup_times = np.zeros((num_machines, num_ops, num_ops), dtype=int)
        for (machine, op1, op2), duration in self._setup_times.items():
            setup_times[machine, op1, op2] = duration

        return ProblemData(
            jobs=self.jobs,
            machines=self.machines,
            operations=self.operations,
            job2ops=job2ops,
            processing_times=self._processing_times,
            timing_precedences=self._timing_precedences,
            assignment_precedences=self._assignment_precedences,
            setup_times=setup_times,
            process_plans=self._process_plans,
            planning_horizon=self._planning_horizon,
            objective=self._objective,
        )

    def add_job(
        self,
        weight: int = 1,
        release_date: int = 0,
        due_date: Optional[int] = None,
        deadline: Optional[int] = None,
        name: str = "",
    ) -> Job:
        """
        Adds a job to the model.

        Parameters
        ----------
        weight
            The job importance weight, used as multiplicative factor in the
            objective function.
        release_date
            The earliest time that the job may start. Default is zero.
        due_date
            The latest time that the job should be completed before incurring
            penalties. Default is None, meaning that there is no due date.
        deadline
            The latest time by which the job must be completed. Note that a
            deadline is different from a due date; the latter does not restrict
            the latest completion time. Default is None, meaning that there is
            no deadline.
        name
            Name of the job.

        Returns
        -------
        Job
            The created job.
        """
        job = Job(weight, release_date, due_date, deadline, name)

        self._id2job[id(job)] = len(self.jobs)
        self._jobs.append(job)

        return job

    def add_machine(
        self,
        downtimes: Iterable[tuple[int, int]] = (),
        allow_overlap: bool = False,
        name: str = "",
    ) -> Machine:
        """
        Adds a machine to the model.

        Parameters
        ----------
        downtimes
            List of downtimes for the machine. A downtime is a time interval
            [start, end) during which the machine is unavailable for
            processing. Defaults to no downtimes.
        allow_overlap
            Whether it is allowed to schedule multiple operations on the
            machine at the same time. Default ``False``.
        name
            Name of the machine.

        Returns
        -------
        Machine
            The created machine.
        """
        machine = Machine(
            downtimes=downtimes,
            allow_overlap=allow_overlap,
            name=name,
        )

        self._id2machine[id(machine)] = len(self.machines)
        self._machines.append(machine)

        return machine

    def add_operation(
        self,
        job: Optional[Job] = None,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
        fixed_duration: bool = True,
        optional: bool = False,
        name: str = "",
    ) -> Operation:
        """
        Adds an operation to the model.

        Parameters
        ----------
        job
            The job that the operation belongs to.
        earliest_start
            Earliest start time of the operation.
        latest_start
            Latest start time of the operation.
        earliest_end
            Earliest end time of the operation.
        latest_end
            Latest end time of the operation.
        fixed_duration
            Whether the duration of the operation is fixed. Defaults to True.
        optional
            Whether processing this operation is optional. Defaults to False.
        name
            Name of the operation.

        Returns
        -------
        Operation
            The created operation.
        """
        operation = Operation(
            earliest_start,
            latest_start,
            earliest_end,
            latest_end,
            fixed_duration,
            optional,
            name,
        )

        op_idx = len(self.operations)
        self._id2op[id(operation)] = op_idx
        self._operations.append(operation)

        if job is not None:
            job_idx = self._id2job[id(job)]
            self._job2ops[job_idx].append(op_idx)

        return operation

    def add_processing_time(
        self, machine: Machine, operation: Operation, duration: int
    ):
        """
        Adds a processing time for a machine and operation combination.

        Parameters
        ----------
        machine
            The machine on which the operation is processed.
        operation
            An operation.
        duration
            Processing time of the operation on the machine.
        """
        if duration < 0:
            raise ValueError("Processing time must be non-negative.")

        machine_idx = self._id2machine[id(machine)]
        op_idx = self._id2op[id(operation)]
        self._processing_times[machine_idx, op_idx] = duration

    def add_timing_precedence(
        self,
        operation1: Operation,
        operation2: Operation,
        constraint: TimingPrecedence = TimingPrecedence.END_BEFORE_START,
        delay: int = 0,
    ):
        """
        Adds a timing precedence constraint between two operations.

        Parameters
        ----------
        operation1
            First operation.
        operation2
            Second operation.
        constraint
            Timing precedence constraint between the first and the second
            operation. Defaults to ``END_BEFORE_START``, meaning that the first
            operation must end before the second operation starts.
        delay
            Delay between the first and the second operation. Defaults to
            zero (no delay).
        """
        op1 = self._id2op[id(operation1)]
        op2 = self._id2op[id(operation2)]
        self._timing_precedences[op1, op2].append((constraint, delay))

    def add_assignment_precedence(
        self,
        operation1: Operation,
        operation2: Operation,
        assignment_precedence: AssignmentPrecedence,
    ):
        """
        Adds an assignment precedence constraints between two operations.

        Parameters
        ----------
        operation1
            First operation.
        operation2
            Second operation.
        assignment_precedence
            Assignment precedence relation between the first and the second
            operation.

        """
        op1 = self._id2op[id(operation1)]
        op2 = self._id2op[id(operation2)]
        self._assignment_precedences[op1, op2].append(assignment_precedence)

    def add_setup_time(
        self,
        machine: Machine,
        operation1: Operation,
        operation2: Operation,
        duration: int,
    ):
        """
        Adds a setup time between two operations on a machine.

        Parameters
        ----------
        machine
            Machine on which the setup time occurs.
        operation1
            First operation.
        operation2
            Second operation.
        duration
            Duration of the setup time when switching from the first operation
            to the second operation on the machine.
        """
        machine_idx = self._id2machine[id(machine)]
        op_idx1 = self._id2op[id(operation1)]
        op_idx2 = self._id2op[id(operation2)]

        self._setup_times[machine_idx, op_idx1, op_idx2] = duration

    def add_process_plan(self, *plans: list[Operation]):
        """
        Adds one or multiple process plans. Each plan is a list of operations.
        Exactly one process plan is selected, meaning that all operations in
        the selected plan are required to be processed.

        Parameters
        ----------
        plans
            The plans to be added. Each plan is a list of operations. Multiple
            plans can be passed as separate arguments.
        """
        ids = [[self._id2op[id(op)] for op in plan] for plan in plans]
        self._process_plans.append(ids)

    def set_planning_horizon(self, horizon: int):
        """
        Sets the planning horizon of the model.

        Parameters
        ----------
        horizon
            The planning horizon.
        """
        self._planning_horizon = horizon

    def set_objective(self, objective: Objective):
        """
        Sets the objective to be minimized in this model.

        Parameters
        ----------
        objective
            An objective function.
        """
        self._objective = objective

    def solve(
        self, log: bool = False, time_limit: Optional[int] = None
    ) -> Result:
        """
        Solves the problem data instance created by the model.

        Parameters
        ----------
        log
            Whether to log the solver output. Defaults to False.
        time_limit
            Time limit in seconds for the solver, defaults to None. If set to
            None, the solver will run until an optimal solution is found.

        Returns
        -------
        Result
            A Result object containing solver results.
        """
        data = self.data()
        cp_model = default_model(data)

        log_verbosity = "Terse" if log else "Quiet"
        kwargs = {"TimeLimit": time_limit, "LogVerbosity": log_verbosity}
        cp_result: CpoSolveResult = cp_model.solve(**kwargs)  # type: ignore

        solve_status = cp_result.get_solve_status()
        runtime = cp_result.get_solve_time()

        if solve_status == "Infeasible":
            solution = None
            objective_value = None
        else:
            solution = result2solution(self.data(), cp_result)
            objective_value = cp_result.get_objective_value()

        return Result(solve_status, runtime, solution, objective_value)
