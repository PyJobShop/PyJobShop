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
        self._job2tasks: dict[int, list[int]] = defaultdict(list)
        self._processing_times: dict[tuple[int, int], int] = {}
        self._constraints: dict[tuple[int, int], list[Constraint]] = (
            defaultdict(list)
        )

        self._setup_times: dict[tuple[int, int, int], int] = {}
        self._planning_horizon: int = MAX_VALUE
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
        num_jobs = len(self.jobs)
        num_tasks = len(self.tasks)
        num_machines = len(self.machines)

        job2tasks = [self._job2tasks[idx] for idx in range(num_jobs)]

        # Convert setup times into a 3D array with zero as default.
        setup_times = np.zeros((num_machines, num_tasks, num_tasks), dtype=int)
        for (machine, task1, task2), duration in self._setup_times.items():
            setup_times[machine, task1, task2] = duration

        return ProblemData(
            jobs=self.jobs,
            machines=self.machines,
            tasks=self.tasks,
            job2tasks=job2tasks,
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
            Whether it is allowed to schedule multiple tasks on the
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

    def add_task(
        self,
        job: Optional[Job] = None,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
        fixed_duration: bool = True,
        name: str = "",
    ) -> Task:
        """
        Adds a task to the model.

        Parameters
        ----------
        job
            The job that the task belongs to.
        earliest_start
            Earliest start time of the task.
        latest_start
            Latest start time of the task.
        earliest_end
            Earliest end time of the task.
        latest_end
            Latest end time of the task.
        fixed_duration
            Whether the duration of the task is fixed. Defaults to True.
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
            self._job2tasks[job_idx].append(task_idx)

        return task

    def add_processing_time(self, machine: Machine, task: Task, duration: int):
        """
        Adds a processing time for a machine and task combination.

        Parameters
        ----------
        machine
            The machine on which the task is processed.
        task
            The task.
        duration
            Processing time of the task on the machine.
        """
        if duration < 0:
            raise ValueError("Processing time must be non-negative.")

        machine_idx = self._id2machine[id(machine)]
        task_idx = self._id2task[id(task)]
        self._processing_times[machine_idx, task_idx] = duration

    def add_constraint(
        self, first: Task, second: Task, constraint: Constraint
    ):
        """
        Adds a precedence constraint between two tasks.

        Parameters
        ----------
        first
            First task.
        second
            Second task.
        constraint
            Constraint between the first and the second task.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(constraint)

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
