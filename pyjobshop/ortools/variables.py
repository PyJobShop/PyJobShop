from collections import defaultdict
from dataclasses import dataclass

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntervalVar, IntVar

from pyjobshop.ProblemData import ProblemData


@dataclass
class JobVar:
    """
    Variables that represent a job in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the job.
    start
        The start variable time of the interval.
    duration
        The duration variable of the interval.
    end
        The end variable time of the interval.
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
        The start variable time of the interval.
    duration
        The duration variable of the interval.
    end
        The end variable time of the interval.
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
        The start variable time of the interval.
    duration
        The duration variable of the interval.
    end
        The end variable time of the interval.
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
    jobs = []

    for job in data.jobs:
        name = f"J{job}"
        start_var = m.new_int_var(0, data.planning_horizon, f"{name}_start")
        duration_var = m.new_int_var(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.new_int_var(0, data.planning_horizon, f"{name}_end")
        interval_var = m.NewIntervalVar(
            start_var, duration_var, end_var, f"interval_{job}"
        )
        job_var = JobVar(interval_var, start_var, duration_var, end_var)
        jobs.append(job_var)

        # Impose job data constraints.
        m.add(job_var.start >= job.release_date)

        if job.deadline is not None:
            m.add(job_var.end <= job.deadline)

    return jobs


def task_variables(m: CpModel, data: ProblemData) -> list[TaskVar]:
    """
    Creates an interval variable for each task.
    """
    tasks = []

    for task in data.tasks:
        name = f"T{task}"
        start_var = m.new_int_var(0, data.planning_horizon, f"{name}_start")
        duration_var = m.new_int_var(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.new_int_var(0, data.planning_horizon, f"{name}_end")
        interval_var = m.NewIntervalVar(
            start_var, duration_var, end_var, f"interval_{task}"
        )
        task_var = TaskVar(interval_var, start_var, duration_var, end_var)
        tasks.append(task_var)

        # Impose task data constraints.
        m.add(task_var.start >= task.earliest_start)

        m.add(task_var.start <= task.latest_start)

        m.add(task_var.end >= task.earliest_end)

        m.add(task_var.end <= task.latest_end)

    return tasks


def assignment_variables(
    m: CpModel, data: ProblemData
) -> dict[tuple[int, int], AssignmentVar]:
    """
    Creates an interval variable for each task and eligible machine pair.
    """
    variables = {}

    for (machine, task), duration in data.processing_times.items():
        name = f"A{task}_{machine}"
        start_var = m.new_int_var(0, data.planning_horizon, f"{name}_start")

        duration = data.processing_times[machine, task]
        lb = duration
        ub = lb if data.tasks[task].fixed_duration else data.planning_horizon
        duration_var = m.new_int_var(lb, ub, f"{name}_duration")

        end_var = m.new_int_var(0, data.planning_horizon, f"{name}_start")
        is_present_var = m.new_bool_var(f"{name}_is_present")
        interval_var = m.new_optional_interval_var(
            start_var,
            duration_var,
            end_var,
            is_present_var,
            f"{name}_interval",
        )
        variables[task, machine] = AssignmentVar(
            task_idx=task,
            interval=interval_var,
            start=start_var,
            duration=duration_var,
            end=end_var,
            is_present=is_present_var,
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

    # Group the assignment variables by machine.
    machine2tasks = defaultdict(list)
    for (_, machine), var in assign.items():
        machine2tasks[machine].append(var)

    for machine in range(data.num_machines):
        tasks = machine2tasks[machine]
        num_tasks = len(tasks)

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

        variables.append(SequenceVar(tasks, starts, ends, ranks, arcs))

    return variables
