from collections import defaultdict
from typing import Optional

import numpy as np

from pyjobshop.constants import MAX_VALUE
from pyjobshop.ProblemData import (
    Constraint,
    Job,
    Machine,
    Objective,
    ProblemData,
    Task,
)
from pyjobshop.Result import Result
from pyjobshop.solve import solve


class Model:
    """
    Model class to build a problem instance step-by-step.
    """

    def __init__(self):
        self._jobs: list[Job] = []
        self._machines: list[Machine] = []
        self._tasks: list[Task] = []
        self._processing_times: dict[tuple[int, int], int] = {}
        self._constraints: dict[tuple[int, int], list[Constraint]] = (
            defaultdict(list)
        )

        self._setup_times: dict[tuple[int, int, int], int] = {}
        self._horizon: int = MAX_VALUE
        self._objective: Objective = Objective.MAKESPAN

        self._id2job: dict[int, int] = {}
        self._id2machine: dict[int, int] = {}
        self._id2task: dict[int, int] = {}

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
    def tasks(self) -> list[Task]:
        """
        Returns the list of tasks in the model.
        """
        return self._tasks

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
        num_tasks = len(self.tasks)
        num_machines = len(self.machines)

        # Convert setup times into a 3D array with zero as default.
        setup_times = np.zeros((num_machines, num_tasks, num_tasks), dtype=int)
        for (machine, task1, task2), duration in self._setup_times.items():
            setup_times[machine, task1, task2] = duration

        return ProblemData(
            jobs=self.jobs,
            machines=self.machines,
            tasks=self.tasks,
            processing_times=self._processing_times,
            constraints=self._constraints,
            setup_times=setup_times,
            horizon=self._horizon,
            objective=self._objective,
        )

    def add_job(
        self,
        weight: int = 1,
        release_date: int = 0,
        deadline: int = MAX_VALUE,
        due_date: Optional[int] = None,
        name: str = "",
    ) -> Job:
        """
        Adds a job to the model.

        Parameters
        ----------
        weight
            The job importance weight, used as multiplicative factor in the
            objective function. Default 1.
        release_date
            The earliest time that the job may start. Default 0.
        deadline
            The latest time by which the job must be completed. Note that a
            deadline is different from a due date; the latter does not restrict
            the latest completion time. Default ``MAX_VALUE``.
        due_date
            The latest time that the job should be completed before incurring
            penalties. Default is None, meaning that there is no due date.
        name
            Name of the job.

        Returns
        -------
        Job
            The created job.
        """
        job = Job(weight, release_date, deadline, due_date, name=name)

        self._id2job[id(job)] = len(self.jobs)
        self._jobs.append(job)

        return job

    def add_machine(self, name: str = "") -> Machine:
        """
        Adds a machine to the model.

        Parameters
        ----------
        name
            Name of the machine.

        Returns
        -------
        Machine
            The created machine.
        """
        machine = Machine(name=name)

        self._id2machine[id(machine)] = len(self.machines)
        self._machines.append(machine)

        return machine

    def add_task(
        self,
        job: Optional[Job] = None,
        earliest_start: int = 0,
        latest_start: int = MAX_VALUE,
        earliest_end: int = 0,
        latest_end: int = MAX_VALUE,
        fixed_duration: bool = True,
        name: str = "",
    ) -> Task:
        """
        Adds a task to the model.

        Parameters
        ----------
        job
            The job that the task belongs to. Default None.
        earliest_start
            Earliest start time of the task. Default 0.
        latest_start
            Latest start time of the task. Default ``MAX_VALUE``.
        earliest_end
            Earliest end time of the task. Default 0.
        latest_end
            Latest end time of the task. Default ``MAX_VALUE``.
        fixed_duration
            Whether the duration of the task is fixed. Default True.
        name
            Name of the task.

        Returns
        -------
        Task
            The created task.
        """
        task = Task(
            earliest_start,
            latest_start,
            earliest_end,
            latest_end,
            fixed_duration,
            name,
        )

        task_idx = len(self.tasks)
        self._id2task[id(task)] = task_idx
        self._tasks.append(task)

        if job is not None:
            job_idx = self._id2job[id(job)]
            self._jobs[job_idx].add_task(task_idx)

        return task

    def add_processing_time(self, task: Task, machine: Machine, duration: int):
        """
        Adds a processing time for a given task on a machine.

        Parameters
        ----------
        task
            The task to be processed.
        machine
            The machine on which the task is processed.
        duration
            Processing time of the task on the machine.
        """
        if duration < 0:
            raise ValueError("Processing time must be non-negative.")

        task_idx = self._id2task[id(task)]
        machine_idx = self._id2machine[id(machine)]
        self._processing_times[task_idx, machine_idx] = duration

    def add_start_at_start(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must start at the same time as
        the second task starts.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.START_AT_START)

    def add_start_at_end(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must start at the same time as
        the second task ends.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.START_AT_END)

    def add_start_before_start(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must start before the second task
        starts.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.START_BEFORE_START)

    def add_start_before_end(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must start before the second task
        ends.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.START_BEFORE_END)

    def add_end_at_end(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must end at the same time as the
        second task ends.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.END_AT_END)

    def add_end_at_start(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must end at the same time as the
        second task starts.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.END_AT_START)

    def add_end_before_start(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must end before the second task
        starts.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.END_BEFORE_START)

    def add_end_before_end(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must end before the second task
        ends.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.END_BEFORE_END)

    def add_previous(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must be scheduled right before
        the second task, if they are scheduled on the same machine.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.PREVIOUS)

    def add_same_machine(self, first: Task, second: Task):
        """
        Adds a constraint that two tasks must be scheduled on the same machine.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.SAME_MACHINE)

    def add_different_machine(self, first: Task, second: Task):
        """
        Adds a constraint that the two tasks must be scheduled on different
        machines.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.DIFFERENT_MACHINE)

    def add_setup_time(
        self, machine: Machine, task1: Task, task2: Task, duration: int
    ):
        """
        Adds a setup time between two tasks on a machine.

        Parameters
        ----------
        machine
            Machine on which the setup time occurs.
        task1
            First task.
        task2
            Second task.
        duration
            Duration of the setup time when switching from the first task
            to the second task on the machine.
        """
        machine_idx = self._id2machine[id(machine)]
        task_idx1 = self._id2task[id(task1)]
        task_idx2 = self._id2task[id(task2)]

        self._setup_times[machine_idx, task_idx1, task_idx2] = duration

    def set_horizon(self, horizon: int):
        """
        Sets the horizon of the model.

        Parameters
        ----------
        horizon
            The horizon.
        """
        self._horizon = horizon

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
        solver: str = "ortools",
        time_limit: float = float("inf"),
        log: bool = True,
        num_workers: Optional[int] = None,
    ) -> Result:
        """
        Solves the problem data instance created by the model.

        Parameters
        ----------
        solver
            The CP solver to use, one of ['ortools', 'cpoptimizer']. Default
            'ortools'.
        time_limit
            The time limit for the solver in seconds. Default ``float('inf')``.
        log
            Whether to log the solver output. Default ``True``.
        num_workers
            The number of workers to use for parallel solving. If not
            specified, the default value of the selected solver is used, which
            is typically the maximum number of available CPU cores.

        Returns
        -------
        Result
            A Result object containing the best found solution and additional
            information about the solver run.
        """
        return solve(self.data(), solver, time_limit, log, num_workers)
