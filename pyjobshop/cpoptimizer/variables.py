from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData
from pyjobshop.utils import compute_min_max_durations


def job_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each job in the problem.
    """
    variables = []

    for job in data.jobs:
        var = m.interval_var(name=f"J{job}")

        var.set_start_min(job.release_date)
        var.set_end_max(min(job.deadline, data.horizon))

        variables.append(var)

    return variables


def task_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each task in the problem.
    """
    variables = []
    min_durations, max_durations = compute_min_max_durations(data)

    for idx, task in enumerate(data.tasks):
        var = m.interval_var(name=f"T{task}")

        var.set_start_min(task.earliest_start)
        var.set_start_max(min(task.latest_start, data.horizon))

        var.set_end_min(task.earliest_end)
        var.set_end_max(min(task.latest_end, data.horizon))

        var.set_size_min(min_durations[idx])
        var.set_size_max(
            max_durations[idx] if task.fixed_duration else data.horizon
        )

        variables.append(var)

    return variables


def task_alternatives_variables(
    m: CpoModel, data: ProblemData
) -> dict[tuple[int, int], CpoIntervalVar]:
    """
    Creates an optional interval variable for each eligible task and machine
    pair.

    Returns
    -------
    dict[tuple[int, int], CpoIntervalVar]
        A dictionary that maps each task index and machine index pair to its
        corresponding interval variable.
    """
    variables = {}

    for (task_idx, machine), duration in data.processing_times.items():
        var = m.interval_var(optional=True, name=f"A{task_idx}_{machine}")
        task = data.tasks[task_idx]

        var.set_start_min(task.earliest_start)
        var.set_start_max(min(task.latest_start, data.horizon))

        var.set_end_min(task.earliest_end)
        var.set_end_max(min(task.latest_end, data.horizon))

        if task.fixed_duration:
            var.set_size(duration)
        else:
            var.set_size_min(duration)
            var.set_size_max(data.horizon)

        variables[task_idx, machine] = var

    return variables


def sequence_variables(
    m: CpoModel,
    data: ProblemData,
    task_alt_vars: dict[tuple[int, int], CpoIntervalVar],
) -> list[CpoSequenceVar]:
    """
    Creates a sequence variable for each machine, using the corresponding
    assignment variables.
    """
    variables = []

    for machine, tasks in enumerate(data.machine2tasks):
        intervals = [task_alt_vars[task, machine] for task in tasks]
        variables.append(m.sequence_var(name=f"S{machine}", vars=intervals))

    return variables
