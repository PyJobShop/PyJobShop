from collections import defaultdict
from typing import Optional

import numpy as np

from pyjobshop.constants import MAX_VALUE
from pyjobshop.ProblemData import (
    Constraint,
    Job,
    Machine,
    Mode,
    Objective,
    ProblemData,
    Task,
)
from pyjobshop.Result import Result
from pyjobshop.Solution import Solution
from pyjobshop.solve import solve


class Model:
    """
    Model class to build a problem instance step-by-step.
    """

    def __init__(self):
        self._jobs: list[Job] = []
        self._machines: list[Machine] = []
        self._tasks: list[Task] = []
        self._modes: list[Mode] = []
        self._constraints: dict[tuple[int, int], list[Constraint]] = (
            defaultdict(list)
        )

        self._setup_times: dict[tuple[int, int, int], int] = {}
        self._horizon: int = MAX_VALUE
        self._objective: Objective = Objective.makespan()

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
        Returns the objective function in this model.
        """
        return self._objective

    @classmethod
    def from_data(cls, data: ProblemData):
        """
        Creates a Model instance from a ProblemData instance.
        """
        model = cls()

        for job in data.jobs:
            model.add_job(
                weight=job.weight,
                release_date=job.release_date,
                due_date=job.due_date,
                deadline=job.deadline,
                name=job.name,
            )

        for machine in data.machines:
            model.add_machine(capacity=machine.capacity, name=machine.name)

        task2job = {}
        for job_idx, job in enumerate(data.jobs):
            for task_idx in job.tasks:
                task2job[task_idx] = job_idx

        for task in data.tasks:
            model.add_task(
                job=model.jobs[job_idx],
                earliest_start=task.earliest_start,
                latest_start=task.latest_start,
                earliest_end=task.earliest_end,
                latest_end=task.latest_end,
                fixed_duration=task.fixed_duration,
                name=task.name,
            )

        for mode in data.modes:
            model.add_processing_time(
                task=model.tasks[mode.task],
                machine=model.machines[mode.machine],
                duration=mode.duration,
            )

        for (idx1, idx2), constraints in data.constraints.items():
            task1, task2 = model.tasks[idx1], model.tasks[idx2]

            for constraint in constraints:
                if constraint == Constraint.START_AT_START:
                    model.add_start_at_start(task1, task2)
                elif constraint == Constraint.START_AT_END:
                    model.add_start_at_end(task1, task2)
                elif constraint == Constraint.START_BEFORE_START:
                    model.add_start_before_start(task1, task2)
                elif constraint == Constraint.START_BEFORE_END:
                    model.add_start_before_end(task1, task2)
                elif constraint == Constraint.END_AT_START:
                    model.add_end_at_start(task1, task2)
                elif constraint == Constraint.END_AT_END:
                    model.add_end_at_end(task1, task2)
                elif constraint == Constraint.END_BEFORE_START:
                    model.add_end_before_start(task1, task2)
                elif constraint == Constraint.END_BEFORE_END:
                    model.add_end_before_end(task1, task2)
                elif constraint == Constraint.PREVIOUS:
                    model.add_previous(task1, task2)
                elif constraint == Constraint.BEFORE:
                    model.add_before(task1, task2)
                elif constraint == Constraint.SAME_MACHINE:
                    model.add_same_machine(task1, task2)
                elif constraint == Constraint.DIFFERENT_MACHINE:
                    model.add_different_machine(task1, task2)

        for (mach, idx1, idx2), duration in np.ndenumerate(data.setup_times):
            if duration != 0:
                model.add_setup_time(
                    machine=model.machines[mach],
                    task1=model.tasks[idx1],
                    task2=model.tasks[idx2],
                    duration=duration,
                )

        model.set_horizon(data.horizon)
        model.set_objective(
            weight_makespan=data.objective.weight_makespan,
            weight_tardy_jobs=data.objective.weight_tardy_jobs,
            weight_total_tardiness=data.objective.weight_total_tardiness,
            weight_total_completion_time=data.objective.weight_total_completion_time,
        )

        return model

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
            modes=self._modes,
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

    def add_machine(self, capacity: int = 0, name: str = "") -> Machine:
        """
        Adds a machine to the model.

        Parameters
        ----------
        capacity
            The capacity of the machine.
        name
            Name of the machine.

        Returns
        -------
        Machine
            The created machine.
        """
        machine = Machine(capacity=capacity, name=name)

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

    def add_processing_time(
        self, task: Task, machine: Machine, duration: int, demand: int = 0
    ):
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
        demand
            Resource demand of the task on the machine. Default 0.
        """

        task_idx = self._id2task[id(task)]
        machine_idx = self._id2machine[id(machine)]

        self._modes.append(Mode(task_idx, duration, [machine_idx], [demand]))

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
        the second task, meaning that no task is allowed to schedule between,
        if they are scheduled on the same machine.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.PREVIOUS)

    def add_before(self, first: Task, second: Task):
        """
        Adds a constraint that the first task must be scheduled before the
        second task, if they are scheduled on the same machine.
        """
        task1 = self._id2task[id(first)]
        task2 = self._id2task[id(second)]
        self._constraints[task1, task2].append(Constraint.BEFORE)

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

    def set_objective(
        self,
        weight_makespan: int = 0,
        weight_tardy_jobs: int = 0,
        weight_total_tardiness: int = 0,
        weight_total_completion_time: int = 0,
        weight_total_earliness: int = 0,
    ):
        """
        Sets the objective function in this model.

        Parameters
        ----------
        weight_makespan
            Weight of the makespan objective. Default 0.
        weight_tardy_jobs
            Weight of the tardy jobs objective. Default 0.
        weight_total_tardiness
            Weight of the total tardiness objective. Default 0.
        weight_total_completion_time
            Weight of the total completion time objective. Default 0.
        weight_total_earliness
            Weight of the total earliness objective. Default 0.
        """
        self._objective = Objective(
            weight_makespan=weight_makespan,
            weight_tardy_jobs=weight_tardy_jobs,
            weight_total_tardiness=weight_total_tardiness,
            weight_total_completion_time=weight_total_completion_time,
            weight_total_earliness=weight_total_earliness,
        )

    def solve(
        self,
        solver: str = "ortools",
        time_limit: float = float("inf"),
        display: bool = True,
        num_workers: Optional[int] = None,
        initial_solution: Optional[Solution] = None,
        **kwargs,
    ) -> Result:
        """
        Solves the problem data instance created by the model.

        Parameters
        ----------
        solver
            The solver to use. Either ``'ortools'`` (default) or
            ``'cpoptimizer'``.
        time_limit
            The time limit for the solver in seconds. Default ``float('inf')``.
        display
            Whether to display the solver output. Default ``True``.
        num_workers
            The number of workers to use for parallel solving. If not
            specified, the default of the selected solver is used, which is
            typically the number of available CPU cores.
        initial_solution
            An initial solution to start the solver from. Default is no
            solution.
        kwargs
            Additional parameters passed to the solver.

        Returns
        -------
        Result
            A Result object containing the best found solution and additional
            information about the solver run.
        """
        return solve(
            self.data(),
            solver,
            time_limit,
            display,
            num_workers,
            initial_solution,
            **kwargs,
        )
