from dataclasses import dataclass, field

from ortools.sat.python.cp_model import (
    BoolVarT,
    CpModel,
    IntervalVar,
    IntVar,
)

from pyjobshop.ProblemData import ProblemData
from pyjobshop.utils import compute_min_max_durations


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
class TaskAltVar:
    """
    Variables that represent an assignment of a task to a machine.

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
    task_alts
        The task alternative variables in the sequence.
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

    task_alts: list[TaskAltVar]
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
        num_tasks = len(self.task_alts)

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
    Helper class that manages the core variables for OR-Tools.
    """

    def __init__(self, m: CpModel, data: ProblemData):
        self._model = m
        self._data = data

        self.job_vars = self._make_job_variables()
        self.task_vars = self._make_task_variables()
        self.task_alt_vars = self._make_task_alternative_variables()
        self.sequence_vars = self._make_sequence_variables()

    def _make_job_variables(self) -> list[JobVar]:
        """
        Creates an interval variable for each job.
        """
        m, data = self._model, self._data
        variables = []

        for job in data.jobs:
            name = f"J{job}"
            start = m.new_int_var(
                lb=job.release_date,
                ub=data.horizon,
                name=f"{name}_start",
            )
            duration = m.new_int_var(
                lb=0,
                ub=min(job.deadline - job.release_date, data.horizon),
                name=f"{name}_duration",
            )
            end = m.new_int_var(
                lb=0,
                ub=min(job.deadline, data.horizon),
                name=f"{name}_end",
            )
            interval = m.NewIntervalVar(
                start, duration, end, f"{name}_interval"
            )
            variables.append(JobVar(interval, start, duration, end))

        return variables

    def _make_task_variables(self) -> list[TaskVar]:
        """
        Creates an interval variable for each task.
        """
        m, data = self._model, self._data
        variables = []
        min_durations, max_durations = compute_min_max_durations(data)

        for idx, task in enumerate(data.tasks):
            name = f"T{task}"
            start = m.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, data.horizon),
                name=f"{name}_start",
            )
            duration = m.new_int_var(
                lb=min_durations[idx],
                ub=max_durations[idx] if task.fixed_duration else data.horizon,
                name=f"{name}_duration",
            )
            end = m.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, data.horizon),
                name=f"{name}_end",
            )
            interval = m.NewIntervalVar(
                start, duration, end, f"interval_{task}"
            )
            variables.append(TaskVar(interval, start, duration, end))

        return variables

    def _make_task_alternative_variables(
        self,
    ) -> dict[tuple[int, int], TaskAltVar]:
        """
        Creates an optional interval variable for each eligible task and
        machine pair.

        Returns
        -------
        dict[tuple[int, int], TaskAltVar]
            A dictionary that maps each task index and machine index pair to
            its corresponding task alternative variable.
        """
        m, data = self._model, self._data
        variables = {}

        for (
            task_idx,
            machine_idx,
        ), proc_time in data.processing_times.items():
            task = data.tasks[task_idx]
            machine = data.machines[machine_idx]
            name = f"A{task}_{machine}"
            start = m.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, data.horizon),
                name=f"{name}_start",
            )
            duration = m.new_int_var(
                lb=proc_time,
                ub=proc_time if task.fixed_duration else data.horizon,
                name=f"{name}_duration",
            )
            end = m.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, data.horizon),
                name=f"{name}_start",
            )
            is_present = m.new_bool_var(f"{name}_is_present")
            interval = m.new_optional_interval_var(
                start, duration, end, is_present, f"{name}_interval"
            )
            variables[task_idx, machine_idx] = TaskAltVar(
                task_idx=task_idx,
                interval=interval,
                start=start,
                duration=duration,
                end=end,
                is_present=is_present,
            )

        return variables

    def _make_sequence_variables(self) -> list[SequenceVar]:
        """
        Creates a sequence variable for each machine. Sequence variables are
        used to model the ordering of intervals on a given machine. This is
        used for modeling machine setups and sequencing task constraints, such
        as previous, before, first, last and permutations.
        """
        data = self._data
        variables = []

        for machine in range(data.num_machines):
            tasks = data.machine2tasks[machine]
            alt_vars = [self.task_alt_vars[task, machine] for task in tasks]
            variables.append(SequenceVar(alt_vars))

        return variables
