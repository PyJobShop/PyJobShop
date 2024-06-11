from dataclasses import dataclass

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntervalVar, IntVar

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
class AssignmentVar:
    """
    Variables that represent an assignment of a task to a machine.

    Parameters
    ----------
    task_idx
        The index of the task.
    interval
        The interval variable representing the assignment of the task.
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
    Represents a sequence of tasks assigned to a machine.

    Parameters
    ----------
    tasks
        The task variables in the sequence.
    starts
        The start literals for each task.
    ends
        The end literals for each task.
    ranks
        The rank variables of each interval on the machine. Used to define the
        ordering of the intervals in the machine sequence.
    arcs
        The arc literals between each pair of tasks. Keys are tuples of
        indices.
    is_active
        A boolean that indicates whether the sequence is active, meaning that a
        circuit constraint must be added for this machine. Default ``False``.
    """

    tasks: list[AssignmentVar]
    starts: list[BoolVarT]
    ends: list[BoolVarT]
    ranks: list[IntVar]
    arcs: dict[tuple[int, int], BoolVarT]
    is_active: bool = False

    def activate(self):
        """
        Activates the sequence variable, meaning that a circuit constraint
        must be added for this machine.
        """
        self.is_active = True


def job_variables(m: CpModel, data: ProblemData) -> list[JobVar]:
    """
    Creates an interval variable for each job.
    """
    variables = []

    for job in data.jobs:
        name = f"J{job}"
        start = m.new_int_var(
            lb=job.release_date,
            ub=data.planning_horizon,
            name=f"{name}_start",
        )
        duration = m.new_int_var(
            lb=0,
            ub=min(job.deadline - job.release_date, data.planning_horizon),
            name=f"{name}_duration",
        )
        end = m.new_int_var(
            lb=0,
            ub=min(job.deadline, data.planning_horizon),
            name=f"{name}_end",
        )
        interval = m.NewIntervalVar(start, duration, end, f"{name}_interval")
        variables.append(JobVar(interval, start, duration, end))

    return variables


def task_variables(m: CpModel, data: ProblemData) -> list[TaskVar]:
    """
    Creates an interval variable for each task.
    """
    variables = []
    min_durations, max_durations = compute_min_max_durations(data)

    for idx, task in enumerate(data.tasks):
        name = f"T{task}"
        start = m.new_int_var(
            lb=task.earliest_start,
            ub=min(task.latest_start, data.planning_horizon),
            name=f"{name}_start",
        )
        duration = m.new_int_var(
            lb=min_durations[idx],
            ub=max_durations[idx]
            if task.fixed_duration
            else data.planning_horizon,  # unbounded if variable duration
            name=f"{name}_duration",
        )
        end = m.new_int_var(
            lb=task.earliest_end,
            ub=min(task.latest_end, data.planning_horizon),
            name=f"{name}_end",
        )
        interval = m.NewIntervalVar(start, duration, end, f"interval_{task}")
        variables.append(TaskVar(interval, start, duration, end))

    return variables


def assignment_variables(
    m: CpModel, data: ProblemData
) -> dict[tuple[int, int], AssignmentVar]:
    """
    Creates an interval variable for each task and eligible machine pair.
    """
    variables = {}

    for (machine_idx, task_idx), proc_time in data.processing_times.items():
        task = data.tasks[task_idx]
        machine = data.machines[machine_idx]
        name = f"A{task}_{machine}"
        start = m.new_int_var(
            lb=task.earliest_start,
            ub=min(task.latest_start, data.planning_horizon),
            name=f"{name}_start",
        )
        duration = m.new_int_var(
            lb=proc_time,
            ub=proc_time if task.fixed_duration else data.planning_horizon,
            name=f"{name}_duration",
        )
        end = m.new_int_var(
            lb=task.earliest_end,
            ub=min(task.latest_end, data.planning_horizon),
            name=f"{name}_start",
        )
        is_present = m.new_bool_var(f"{name}_is_present")
        interval = m.new_optional_interval_var(
            start, duration, end, is_present, f"{name}_interval"
        )
        variables[task_idx, machine_idx] = AssignmentVar(
            task_idx=task_idx,
            interval=interval,
            start=start,
            duration=duration,
            end=end,
            is_present=is_present,
        )

    return variables


def sequence_variables(
    m: CpModel, data: ProblemData, assign: dict[tuple[int, int], AssignmentVar]
) -> list[SequenceVar]:
    """
    Creates a sequence variable for each machine. Sequence variables are used
    to model the ordering of intervals on a given machine. This is used for
    modeling machine setups and sequencing task constraints, such as previous,
    before, first, last and permutations.
    """
    variables = []

    for machine in range(data.num_machines):
        tasks = data.machine2tasks[machine]
        assign_vars = [assign[task, machine] for task in tasks]
        num_tasks = len(assign_vars)

        # Start and end literals define whether the corresponding interval
        # is first or last in the sequence, respectively.
        starts = [m.new_bool_var("") for _ in range(num_tasks)]
        ends = [m.new_bool_var("") for _ in range(num_tasks)]

        # Rank variables define the position of the task in the sequence.
        ranks = [m.new_int_var(-1, num_tasks, "") for _ in range(num_tasks)]

        # Arc literals indicate if two intervals are scheduled consecutively.
        arcs = {
            (i, j): m.new_bool_var(f"{i}->{j}")
            for i in range(num_tasks)
            for j in range(num_tasks)
        }

        variables.append(SequenceVar(assign_vars, starts, ends, ranks, arcs))

    return variables
