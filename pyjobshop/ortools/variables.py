from dataclasses import dataclass, field

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntervalVar, IntVar

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution
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
    Represents a sequence of tasks assigned to a machine. Relevant sequence
    variables are lazily generated when activated by constraints that call
    the ``activate`` method.

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
        The arc literals between each pair of intervals in the sequence.
        Keys are tuples of indices.
    is_active
        A boolean that indicates whether the sequence is active, meaning that a
        circuit constraint must be added for this machine. Default ``False``.
    """

    tasks: list[AssignmentVar]
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
        num_tasks = len(self.tasks)

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


def job_variables(m: CpModel, data: ProblemData) -> list[JobVar]:
    """
    Creates an interval variable for each job.
    """
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

    for (task_idx, machine_idx), proc_time in data.processing_times.items():
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
        variables.append(SequenceVar(assign_vars))

    return variables


def add_hint_to_vars(
    m: CpModel,
    data: ProblemData,
    init: Solution,
    job_vars: list[JobVar],
    task_vars: list[TaskVar],
    assign_vars: dict[tuple[int, int], AssignmentVar],
    seq_vars: list[SequenceVar],
):
    """
    Adds hints to variables based on the given initial solution.
    """
    for idx in range(data.num_jobs):
        job = data.jobs[idx]
        job_var = job_vars[idx]
        sol_tasks = [init.tasks[task] for task in job.tasks]

        job_start = min(task.start for task in sol_tasks)
        job_end = max(task.end for task in sol_tasks)

        m.add_hint(job_var.start, job_start)
        m.add_hint(job_var.duration, job_end - job_start)
        m.add_hint(job_var.end, job_end)

    for idx in range(data.num_tasks):
        task_var = task_vars[idx]
        sol_task = init.tasks[idx]

        m.add_hint(task_var.start, sol_task.start)
        m.add_hint(task_var.duration, sol_task.duration)
        m.add_hint(task_var.end, sol_task.end)

    for (task, machine), var in assign_vars.items():
        sol_task = init.tasks[task]

        m.add_hint(var.start, sol_task.start)
        m.add_hint(var.duration, sol_task.duration)
        m.add_hint(var.end, sol_task.end)
        m.add_hint(var.is_present, machine == sol_task.machine)

    # Compute solution sequences.
    sequences_: list[list[tuple]] = [[] for _ in range(data.num_machines)]
    for idx, task_ in enumerate(init.tasks):
        sequences_[task_.machine].append((task_.start, idx))

    sequences = [[idx for _, idx in seq] for seq in sequences_]

    for idx in range(data.num_machines):
        seq_var = seq_vars[idx]  # sequence variable for the machine
        seq_tasks = seq_var.tasks  # assignment variables in the sequence
        seq = sequences[idx]  # sequence of _scheduled_ task indices

        if not seq_var.is_active:
            continue

        for idx in range(len(seq_tasks)):
            task_idx = seq_tasks[idx].task_idx
            rank = seq.index(task_idx) if task_idx in seq else -1

            m.add_hint(seq_var.ranks[idx], rank)
            m.add_hint(seq_var.starts[idx], rank == 0)
            m.add_hint(seq_var.ends[idx], rank == len(seq) - 1)

        arcs = [(seq[idx], seq[idx + 1]) for idx in range(len(seq) - 1)]

        for (i, j), var in seq_var.arcs.items():
            task1, task2 = seq_tasks[i].task_idx, seq_tasks[j].task_idx
            m.add_hint(var, (task1, task2) in arcs)
