from collections import defaultdict
from typing import Optional

import numpy as np
from docplex.cp.solution import CpoSolveResult

from .cp import default_model
from .ProblemData import (
    AssignmentPrecedence,
    Job,
    Machine,
    Operation,
    ProblemData,
    TimingPrecedence,
)

MAX_VALUE = 2**25


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
        self._access_matrix: dict[tuple[int, int], bool] = {}
        self._setup_times: dict[tuple[int, int, int], int] = {}

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

    def data(self) -> ProblemData:
        """
        Returns a ProblemData object containing the problem instance.
        """
        num_jobs = len(self.jobs)
        num_ops = len(self.operations)
        num_machines = len(self.machines)

        job2ops = [self._job2ops[idx] for idx in range(num_jobs)]

        # Convert access matrix into a 2D array with True as default.
        access_matrix = np.full((num_machines, num_machines), True)
        for (machine1, machine2), is_accessible in self._access_matrix.items():
            access_matrix[machine1, machine2] = is_accessible

        # Convert setup times into a 3D array with zero as default.
        setup_times = np.zeros((num_machines, num_ops, num_ops), dtype=int)
        for (machine, op1, op2), duration in self._setup_times.items():
            setup_times[machine, op1, op2] = duration

        return ProblemData(
            self.jobs,
            self.machines,
            self.operations,
            job2ops,
            self._processing_times,
            self._timing_precedences,
            self._assignment_precedences,
            access_matrix,
            setup_times,
        )

    def add_job(
        self,
        release_date: int = 0,
        deadline: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Job:
        """
        Adds a job to the model.

        Parameters
        ----------
        release_date: int
            Release date of the job. Defaults to 0.
        deadline: Optional[int]
            Optional deadline of the job.
        name: Optional[str]
            Optional name of the job.

        Returns
        -------
        Job
            The created job.
        """
        job = Job(release_date, deadline, name)

        self._id2job[id(job)] = len(self.jobs)
        self._jobs.append(job)

        return job

    def add_machine(self, name: Optional[str] = None) -> Machine:
        """
        Adds a machine to the model.

        Parameters
        ----------
        name: Optional[str]
            Optional name of the machine.

        Returns
        -------
        Machine
            The created machine.
        """
        machine = Machine(name)

        self._id2machine[id(machine)] = len(self.machines)
        self._machines.append(machine)

        return machine

    def add_operation(
        self,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Operation:
        """
        Adds an operation to the model.

        Parameters
        ----------
        earliest_start: Optional[int]
            Earliest start time of the operation.
        latest_start: Optional[int]
            Latest start time of the operation.
        earliest_end: Optional[int]
            Earliest end time of the operation.
        latest_end: Optional[int]
            Latest end time of the operation.
        name: Optional[str]
            Name of the operation.

        Returns
        -------
        Operation
            The created operation.
        """
        operation = Operation(
            earliest_start, latest_start, earliest_end, latest_end, name
        )

        self._id2op[id(operation)] = len(self.operations)
        self._operations.append(operation)

        return operation

    def assign_job_operations(self, job: Job, operations: list[Operation]):
        """
        Assigns operations to a job.

        Parameters
        ----------
        job: Job
            The job to which the operations are added.
        operations: list[Operation]
            The operations to add to the job.
        """
        job_idx = self._id2job[id(job)]
        op_idcs = [self._id2op[id(op)] for op in operations]

        self._job2ops[job_idx].extend(op_idcs)

    def add_processing_time(
        self, machine: Machine, operation: Operation, duration: int
    ):
        """
        Adds a processing time for a machine and operation combination.

        Parameters
        ----------
        machine: Machine
            The machine on which the operation is processed.
        operation: Operation
            An operation.
        duration: int
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
        timing_precedence: TimingPrecedence,
        delay: int = 0,
    ):
        """
        Adds a timing precedence constraint between two operations.

        Parameters
        ----------
        operation1: Operation
            First operation.
        operation2: Operation
            Second operation.
        timing_precedence: TimingPrecedence
            Timing precedence constraint between the first and the second
            operation.
        delay: int
            Delay between the first and the second operation. Defaults to
            zero (no delay).
        """
        op1 = self._id2op[id(operation1)]
        op2 = self._id2op[id(operation2)]
        self._timing_precedences[op1, op2].append((timing_precedence, delay))

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
        operation1: Operation
            First operation.
        operation2: Operation
            Second operation.
        assignment_precedence: AssignmentPrecedence
            Assignment precedence relation between the first and the second
            operation.

        """
        op1 = self._id2op[id(operation1)]
        op2 = self._id2op[id(operation2)]
        self._assignment_precedences[op1, op2].append(assignment_precedence)

    def add_access_constraint(
        self, machine1: Machine, machine2: Machine, is_accessible: bool = False
    ):
        """
        Adds an access constraint between two machines.

        Parameters
        ----------
        machine1: Machine
            First machine.
        machine2: Machine
            Second machine.
        is_accessible: bool
            Whether the second machine is accessible from the first machine.
            Defaults to False.
        """
        idx1 = self._id2machine[id(machine1)]
        idx2 = self._id2machine[id(machine2)]
        self._access_matrix[idx1, idx2] = is_accessible

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
        machine: Machine
            Machine on which the setup time occurs.
        operation1: Operation
            First operation.
        operation2: Operation
            Second operation.
        duration: int
            Duration of the setup time when switching from the first operation
            to the second operation on the machine.
        """
        machine_idx = self._id2machine[id(machine)]
        op_idx1 = self._id2op[id(operation1)]
        op_idx2 = self._id2op[id(operation2)]

        self._setup_times[machine_idx, op_idx1, op_idx2] = duration

    def solve(self, time_limit: Optional[int] = None) -> CpoSolveResult:
        """
        Solves the problem data instance created by the model.

        Parameters
        ----------
        time_limit: Optional[int]
            Time limit in seconds for the solver, defaults to None. If set to
            None, the solver will run until an optimal solution is found.

        Returns
        -------
        Result
            A results object containing solver result.
        """
        data = self.data()
        cp_model = default_model(data)
        return cp_model.solve(TimeLimit=time_limit)
