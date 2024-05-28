from collections import defaultdict
from typing import Optional

import numpy as np
from docplex.cp.solution import CpoSolveResult

import pyjobshop.cpoptimizer as cpoptimizer
import pyjobshop.ortools as ortools
from ortools.sat.python.cp_model import CpSolver
from pyjobshop.constants import MAX_VALUE
from pyjobshop.ProblemData import (
    Constraint,
    Job,
    Machine,
    Objective,
    Operation,
    ProblemData,
)
from pyjobshop.Result import Result


class Model:
    """
    Model class to build a problem instance step-by-step.
    """

    def __init__(self):
        self._jobs: list[Job] = []
        self._machines: list[Machine] = []
        self._operations: list[Operation] = []
        self._job2ops: dict[int, list[int]] = defaultdict(list)
        self._processing_times: dict[tuple[int, int], int] = {}
        self._constraints: dict[tuple[int, int], list[Constraint]] = (
            defaultdict(list)
        )

        self._setup_times: dict[tuple[int, int, int], int] = {}
        self._planning_horizon: int = MAX_VALUE
        self._objective: Objective = Objective.MAKESPAN

        self._id2job: dict[int, int] = {}
        self._id2machine: dict[int, int] = {}
        self._id2op: dict[int, int] = {}

    @property
    def jobs(self) -> list[Job]:
        """
        Returns the list of jobs in the model.
        """
        return self._jobs

    @property
    def machines(self) -> list[Machine]:
        """
        Returns the list of machines in the model.
        """
        return self._machines

    @property
    def operations(self) -> list[Operation]:
        """
        Returns the list of operations in the model.
        """
        return self._operations

    @property
    def objective(self) -> Objective:
        """
        Returns the objective function to be minimized in this model.
        """
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
            constraints=self._constraints,
            setup_times=setup_times,
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
        self, allow_overlap: bool = False, name: str = ""
    ) -> Machine:
        """
        Adds a machine to the model.

        Parameters
        ----------
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
        machine = Machine(allow_overlap=allow_overlap, name=name)

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

    def add_constraint(
        self,
        first: Operation,
        second: Operation,
        constraint: Constraint,
    ):
        """
        Adds a precedence constraint between two operations.

        Parameters
        ----------
        first
            First operation.
        second
            Second operation.
        constraint
            Constraint between the first and the second operation.
        """
        op1 = self._id2op[id(first)]
        op2 = self._id2op[id(second)]
        self._constraints[op1, op2].append(constraint)

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
        self,
        solver: str = "cpoptimizer",
        log: bool = False,
        time_limit: Optional[int] = None,
    ) -> Result:
        """
        Solves the problem data instance created by the model.

        Parameters
        ----------
        solver
            The CP solver to use, one of ['ortools', 'cpoptimzer']. Default
            'ortools'.
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

        if solver == "ortools":
            ort_model, op_vars, assign_vars = ortools.default_model(data)

            cp_solver = CpSolver()

            if time_limit is not None:
                cp_solver.parameters.max_time_in_seconds = time_limit

            status_code = cp_solver.Solve(ort_model)
            status = cp_solver.StatusName(status_code)
            objective = cp_solver.ObjectiveValue()
            print(f"Solve status: {status}")
            print(f"Optimal objective value: {objective}")

            if status != "INFEASIBLE":
                solution = ortools.result2solution(
                    data, cp_solver, assign_vars
                )
            else:
                solution = None

            return Result(
                status.capitalize(),
                cp_solver.WallTime(),
                solution,
                objective,
            )

        elif solver == "cpoptimizer":
            cp_model = cpoptimizer.default_model(data)

            log_verbosity = "Terse" if log else "Quiet"
            kwargs = {"TimeLimit": time_limit, "LogVerbosity": log_verbosity}
            cp_result: CpoSolveResult = cp_model.solve(**kwargs)  # type: ignore

            solve_status = cp_result.get_solve_status()
            runtime = cp_result.get_solve_time()

            if solve_status == "Infeasible":
                solution = None
                objective_value = None
            else:
                solution = cpoptimizer.result2solution(self.data(), cp_result)
                objective_value = cp_result.get_objective_value()

            return Result(solve_status, runtime, solution, objective_value)

        else:
            raise ValueError(f"Unknown solver: {solver}.")
