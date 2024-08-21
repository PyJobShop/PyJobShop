from dataclasses import dataclass, field

from ortools.sat.python.cp_model import (
    BoolVarT,
    CpModel,
    Domain,
    IntervalVar,
    IntVar,
)

import pyjobshop.utils as utils
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution
from pyjobshop.utils import compute_task_durations


@dataclass
class JobVar:
    """
    Variables that represent a job in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the job.
    start
        The start time variable of the interval.
    duration
        The duration variable of the interval.
    end
        The end time variable of the interval.
    """

    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class TaskVar:
    """
    Variables that represent a task in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the task.
    start
        The start time variable of the interval.
    duration
        The duration variable of the interval.
    end
        The end time variable of the interval.
    """

    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class ModeVar:
    """
    Variables that represent a possible processing mode of a task.

    Parameters
    ----------
    task_idx
        The index of the task.
    interval
        The optional interval variable representing the assignment of the task.
    start
        The start time variable of the interval.
    duration
        The duration variable of the interval.
    end
        The end time variable of the interval.
    is_present
        The boolean variable indicating whether the interval is present.
    """

    task_idx: int
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar
    is_present: IntVar


@dataclass
class SequenceVar:
    """
    Represents a sequence of interval variables of task alternatives. Relevant
    sequence variables are lazily generated when activated by constraints that
    call the ``activate`` method.

    Parameters
    ----------
    modes
        The mode variables of each task belonging to this sequence.
    starts
        The start literals for each task.
    ends
        The end literals for each task.
    ranks
        The rank variables of each interval on the machine. Used to define the
        ordering of the intervals in the machine sequence.
    arcs
        The arc literals between each pair of intervals in the sequence.
        Keys are tuples of indices.
    is_active
        A boolean that indicates whether the sequence is active, meaning that a
        circuit constraint must be added for this machine. Default ``False``.
    """

    modes: list[ModeVar]
    starts: list[BoolVarT] = field(default_factory=list)
    ends: list[BoolVarT] = field(default_factory=list)
    ranks: list[IntVar] = field(default_factory=list)
    arcs: dict[tuple[int, int], BoolVarT] = field(default_factory=dict)
    is_active: bool = False

    def activate(self, m: CpModel):
        """
        Activates the sequence variable by creating all relevant literals.
        """
        if self.is_active:
            return

        self.is_active = True
        num_tasks = len(self.modes)

        # Start and end literals define whether the corresponding interval
        # is first or last in the sequence, respectively.
        self.starts = [m.new_bool_var("") for _ in range(num_tasks)]
        self.ends = [m.new_bool_var("") for _ in range(num_tasks)]

        # Rank variables define the position of the task in the sequence.
        self.ranks = [
            m.new_int_var(-1, num_tasks, "") for _ in range(num_tasks)
        ]

        # Arcs indicate if two intervals are scheduled consecutively.
        self.arcs = {
            (i, j): m.new_bool_var(f"{i}->{j}")
            for i in range(num_tasks)
            for j in range(num_tasks)
        }


class VariablesManager:
    """
    Manages the core variables of the OR-Tools model.
    """

    def __init__(self, model: CpModel, data: ProblemData):
        self._model = model
        self._data = data

        self._job_vars = self._make_job_variables()
        self._task_vars = self._make_task_variables()
        self._mode_vars = self._make_mode_variables()
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
    def mode_vars(self) -> list[ModeVar]:
        """
        Returns the mode variables.
        """
        return self._mode_vars

    @property
    def sequence_vars(self) -> list[SequenceVar]:
        """
        Returns the sequence variables.
        """
        return self._sequence_vars

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
                ub=data.horizon,
                name=f"{name}_start",
            )
            duration = model.new_int_var(
                lb=0,
                ub=min(job.deadline - job.release_date, data.horizon),
                name=f"{name}_duration",
            )
            end = model.new_int_var(
                lb=0,
                ub=min(job.deadline, data.horizon),
                name=f"{name}_end",
            )
            interval = model.NewIntervalVar(
                start, duration, end, f"{name}_interval"
            )
            variables.append(JobVar(interval, start, duration, end))

        return variables

    def _make_task_variables(self) -> list[TaskVar]:
        """
        Creates an interval variable for each task.
        """
        model, data = self._model, self._data
        variables = []
        task_durations = compute_task_durations(data)

        for idx, task in enumerate(data.tasks):
            name = f"T{idx}"
            start = model.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, data.horizon),
                name=f"{name}_start",
            )
            if task.fixed_duration:
                duration = model.new_int_var_from_domain(
                    Domain.from_values(task_durations[idx]), f"{name}_duration"
                )
            else:
                duration = model.new_int_var(
                    lb=min(task_durations[idx]),
                    ub=data.horizon,
                    name=f"{name}_duration",
                )
            end = model.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, data.horizon),
                name=f"{name}_end",
            )
            interval = model.NewIntervalVar(
                start, duration, end, f"interval_{task}"
            )
            variables.append(TaskVar(interval, start, duration, end))

        return variables

    def _make_mode_variables(
        self,
    ) -> list[ModeVar]:
        """
        Creates an optional interval variable for mode.
        """
        model, data = self._model, self._data
        variables = []

        for mode in data.modes:
            task = data.tasks[mode.task]
            name = f"M{mode.task}_{mode.machine}"
            start = model.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, data.horizon),
                name=f"{name}_start",
            )
            duration = model.new_int_var(
                lb=mode.duration,
                ub=mode.duration if task.fixed_duration else data.horizon,
                name=f"{name}_duration",
            )
            end = model.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, data.horizon),
                name=f"{name}_start",
            )
            is_present = model.new_bool_var(f"{name}_is_present")
            interval = model.new_optional_interval_var(
                start, duration, end, is_present, f"{name}_interval"
            )
            var = ModeVar(
                task_idx=mode.task,
                interval=interval,
                start=start,
                duration=duration,
                end=end,
                is_present=is_present,
            )
            variables.append(var)

        return variables

    def _make_sequence_variables(self) -> list[SequenceVar]:
        """
        Creates a sequence variable for each machine. Sequence variables are
        used to model the ordering of intervals on a given machine. This is
        used for modeling machine setups and sequencing task constraints, such
        as previous, before, first, last and permutations.
        """
        variables = []

        for modes in utils.machine2modes(self._data):
            intervals = [self.mode_vars[mode] for mode in modes]
            variables.append(SequenceVar(intervals))

        return variables

    def warmstart(self, solution: Solution):
        """
        Warmstarts the variables based on the given solution.
        """
        model, data = self._model, self._data
        job_vars, task_vars, mode_vars = (
            self.job_vars,
            self.task_vars,
            self.mode_vars,
        )

        model.clear_hints()

        for idx in range(data.num_jobs):
            job = data.jobs[idx]
            job_var = job_vars[idx]
            sol_tasks = [solution.tasks[task] for task in job.tasks]

            job_start = min(task.start for task in sol_tasks)
            job_end = max(task.end for task in sol_tasks)

            model.add_hint(job_var.start, job_start)
            model.add_hint(job_var.duration, job_end - job_start)
            model.add_hint(job_var.end, job_end)

        for idx in range(data.num_tasks):
            task_var = task_vars[idx]
            sol_task = solution.tasks[idx]

            model.add_hint(task_var.start, sol_task.start)
            model.add_hint(task_var.duration, sol_task.duration)
            model.add_hint(task_var.end, sol_task.end)

        for idx in range(len(data.modes)):
            var = mode_vars[idx]
            mode = data.modes[idx]
            sol_task = solution.tasks[mode.task]

            model.add_hint(var.start, sol_task.start)
            model.add_hint(var.duration, sol_task.duration)
            model.add_hint(var.end, sol_task.end)
            model.add_hint(var.is_present, mode.machine == sol_task.machine)
