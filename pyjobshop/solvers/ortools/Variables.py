from dataclasses import dataclass, field
from typing import TypeAlias

from ortools.sat.python.cp_model import (
    BoolVarT,
    CpModel,
    Domain,
    IntervalVar,
    IntVar,
    LinearExprT,
)

import pyjobshop.solvers.utils as utils
from pyjobshop.constants import MAX_VALUE
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution

TaskIdx = int
ResourceIdx = int
ModeVar: TypeAlias = IntVar  # actually BoolVarT


@dataclass
class JobVar:
    """
    Variables that represent a job in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the job.
    """

    interval: IntervalVar

    @property
    def start(self) -> LinearExprT:
        return self.interval.start_expr()

    @property
    def duration(self) -> LinearExprT:
        return self.interval.size_expr()

    @property
    def end(self) -> LinearExprT:
        return self.interval.end_expr()


@dataclass
class TaskVar:
    """
    Variables that represent a task in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the task.
    """

    interval: IntervalVar

    @property
    def start(self) -> LinearExprT:
        return self.interval.start_expr()

    @property
    def duration(self) -> LinearExprT:
        return self.interval.size_expr()

    @property
    def end(self) -> LinearExprT:
        return self.interval.end_expr()


@dataclass
class AssignVar:
    """
    Variables that represent a task-resource assignment in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the task-resource assignment.
    present
        The Boolean variable indicating whether the interval is present.
    demand
        The demand consumed by the task-resource pair.
    """

    interval: IntervalVar
    present: BoolVarT
    demand: LinearExprT

    @property
    def start(self) -> LinearExprT:
        return self.interval.start_expr()

    @property
    def duration(self) -> LinearExprT:
        return self.interval.size_expr()

    @property
    def end(self) -> LinearExprT:
        return self.interval.end_expr()


@dataclass
class SequenceVar:
    """
    Represents the sequence of interval variables for all tasks that may
    be assigned to this machine.

    Parameters
    ----------
    arcs
        The arc literals between each pair of intervals indicating whether
        intervals are scheduled directly behind each other. Includes arcs
        to and from a dummy node for each interval.
    is_active
        A Boolean that indicates whether the sequence is active, meaning that a
        circuit constraint must be added for this machine. Default ``False``.

    Notes
    -----
    Sequence variables are lazily generated when activated by constraints that
    call the ``activate`` method. This avoids creating unnecessary variables
    when the sequence variable is not used in the model.

    """

    DUMMY = -1

    arcs: dict[tuple[TaskIdx, TaskIdx], BoolVarT] = field(default_factory=dict)
    is_active: bool = False

    def activate(self, m: CpModel, data: ProblemData, res_idx: int):
        """
        Activates the sequence variable by creating all relevant arc literals
        for this particular resource.
        """
        if self.is_active:
            return

        # We only need to create nodes for tasks that can be assigned to this
        # resource, because any other task is not going to be used.
        tasks = {data.modes[m].task for m in data.resource2modes(res_idx)}
        nodes = sorted(tasks) + [self.DUMMY]

        self.is_active = True
        self.arcs = {
            (i, j): m.new_bool_var(f"{i}->{j}") for i in nodes for j in nodes
        }


class Variables:
    """
    Manages the core variables of the OR-Tools model.
    """

    def __init__(self, model: CpModel, data: ProblemData):
        self._model = model
        self._data = data

        self._job_vars = self._make_job_variables()
        self._task_vars = self._make_task_variables()
        self._mode_vars = [model.new_bool_var("") for _ in self._data.modes]
        self._assign_vars = self._make_assign_variables(self._task_vars)
        self._sequence_vars = self._make_sequence_variables()

    @property
    def job_vars(self) -> list[JobVar]:
        """
        Returns the job variables.
        """
        return self._job_vars

    @property
    def task_vars(self) -> list[TaskVar]:
        """
        Returns the task variables.
        """
        return self._task_vars

    @property
    def assign_vars(self) -> dict[tuple[TaskIdx, ResourceIdx], AssignVar]:
        """
        Retruns the assignment variables.
        """
        return self._assign_vars

    @property
    def mode_vars(self) -> list[ModeVar]:
        """
        Returns the mode variables.
        """
        return self._mode_vars

    @property
    def sequence_vars(self) -> dict[int, SequenceVar]:
        """
        Returns the sequence variables.
        """
        return self._sequence_vars

    def res2assign(self, idx: int) -> list[AssignVar]:
        """
        Returns all assignment variables for the given resource.
        """
        items = self.assign_vars.items()
        return [var for (_, res_idx), var in items if res_idx == idx]

    def _make_job_variables(self) -> list[JobVar]:
        """
        Creates an interval variable for each job.
        """
        model, data = self._model, self._data
        variables = []

        for idx, job in enumerate(data.jobs):
            name = f"J{idx}"
            start = model.new_int_var(
                lb=job.release_date,
                ub=MAX_VALUE,
                name=f"{name}_start",
            )
            duration = model.new_int_var(
                lb=0,
                ub=min(job.deadline - job.release_date, MAX_VALUE),
                name=f"{name}_duration",
            )
            end = model.new_int_var(
                lb=0,
                ub=min(job.deadline, MAX_VALUE),
                name=f"{name}_end",
            )
            interval = model.new_interval_var(
                start, duration, end, f"{name}_interval"
            )
            variables.append(JobVar(interval))

        return variables

    def _make_task_variables(self) -> list[TaskVar]:
        """
        Creates an interval variable for each task.
        """
        model, data = self._model, self._data
        variables = []
        task_durations = utils.compute_task_durations(data)

        for idx, task in enumerate(data.tasks):
            name = f"T{idx}"
            start = model.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, MAX_VALUE),
                name=f"{name}_start",
            )
            if task.fixed_duration:
                duration = model.new_int_var_from_domain(
                    Domain.from_values(task_durations[idx]), f"{name}_duration"
                )
            else:
                duration = model.new_int_var(
                    lb=min(task_durations[idx]),
                    ub=MAX_VALUE,
                    name=f"{name}_duration",
                )
            end = model.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, MAX_VALUE),
                name=f"{name}_end",
            )
            interval = model.new_interval_var(
                start, duration, end, f"interval_{task}"
            )
            variables.append(TaskVar(interval))

        return variables

    def _make_assign_variables(
        self, task_vars: list[TaskVar]
    ) -> dict[tuple[TaskIdx, ResourceIdx], AssignVar]:
        """
        Creates an optional interval variable for each task-resource pair.
        """
        model, data = self._model, self._data
        variables = {}

        for task_idx in range(data.num_tasks):
            # Only create assignment variables for (task, resource) pairs
            # that are actually used in the problem.
            resources = {
                res
                for mode in data.task2modes(task_idx)
                for res in data.modes[mode].resources
            }

            for res_idx in resources:
                name = f"A_{task_idx}_{res_idx}"
                task_var = task_vars[task_idx]
                present = model.new_bool_var(f"{name}_present")
                interval = model.new_optional_interval_var(
                    task_var.start,
                    task_var.duration,
                    task_var.end,
                    present,
                    f"{name}_interval",
                )
                demand = model.new_int_var(0, MAX_VALUE, f"{name}_demand")
                var = AssignVar(interval, present, demand)
                variables[task_idx, res_idx] = var

        return variables

    def _make_sequence_variables(self) -> dict[ResourceIdx, SequenceVar]:
        """
        Creates a sequence variable for each machine.
        """
        data = self._data
        variables: dict[ResourceIdx, SequenceVar] = {}

        for idx in data.machine_idcs:
            variables[idx] = SequenceVar()

        return variables

    def warmstart(self, solution: Solution):
        """
        Warmstarts the variables based on the given solution.
        """
        model, data = self._model, self._data
        job_vars, task_vars, assign_vars = (
            self.job_vars,
            self.task_vars,
            self.assign_vars,
        )

        model.clear_hints()

        for idx in range(data.num_jobs):
            job = data.jobs[idx]
            job_var = job_vars[idx]
            sol_tasks = [solution.tasks[task] for task in job.tasks]

            job_start = min(task.start for task in sol_tasks)
            job_end = max(task.end for task in sol_tasks)
            job_duration = job_end - job_start

            model.add_hint(job_var.start, job_start)  # type: ignore
            model.add_hint(job_var.duration, job_duration)  # type: ignore
            model.add_hint(job_var.end, job_end)  # type: ignore

        for idx in range(data.num_tasks):
            task_var = task_vars[idx]
            sol_task = solution.tasks[idx]
            task_duration = sol_task.end - sol_task.start

            model.add_hint(task_var.start, sol_task.start)  # type: ignore
            model.add_hint(task_var.duration, task_duration)  # type: ignore
            model.add_hint(task_var.end, sol_task.end)  # type: ignore

        for task_idx in range(data.num_tasks):
            sol_task = solution.tasks[task_idx]

            for res_idx in sol_task.resources:
                if (task_idx, res_idx) in assign_vars:
                    var = assign_vars[task_idx, res_idx]
                    model.add_hint(var.present, True)
