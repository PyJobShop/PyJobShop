from collections import defaultdict

from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

AssignVars = dict[tuple[int, int], CpoIntervalVar]


def job_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each job in the problem.
    """
    variables = []

    for job in data.jobs:
        var = m.interval_var(name=f"J{job}")

        var.set_start_min(job.release_date)
        var.set_end_max(min(job.deadline, data.planning_horizon))

        variables.append(var)

    return variables


def task_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each task in the problem.
    """
    variables = []

    # Improve duration bounds using processing times.
    min_durations: dict[int, int] = defaultdict(lambda: data.planning_horizon)
    max_durations: dict[int, int] = defaultdict(lambda: 0)

    for (_, task_idx), duration in data.processing_times.items():
        min_durations[task_idx] = min(min_durations[task_idx], duration)
        max_durations[task_idx] = max(max_durations[task_idx], duration)

    for idx, task in enumerate(data.tasks):
        var = m.interval_var(name=f"T{task}")

        var.set_start_min(task.earliest_start)
        var.set_start_max(task.latest_start)

        var.set_end_min(task.earliest_end)
        var.set_end_max(min(task.latest_end, data.planning_horizon))

        var.set_size_min(min_durations[idx])
        if task.fixed_duration:
            var.set_size_max(max_durations[idx])

        variables.append(var)

    return variables


def assignment_variables(m: CpoModel, data: ProblemData) -> AssignVars:
    """
    Creates an optional interval variable for each task and eligible
    machine pair, i.e., a task.
    """
    variables = {}

    for task_idx in range(data.num_tasks):
        for machine in data.task2machines[task_idx]:
            var = m.interval_var(optional=True, name=f"A{task_idx}_{machine}")
            task = data.tasks[task_idx]

            var.set_start_min(task.earliest_start)
            var.set_start_max(task.latest_start)

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, data.planning_horizon))

            duration = data.processing_times[machine, task_idx]
            if task.fixed_duration:
                var.set_size(duration)
            else:
                var.set_size_min(duration)  # at least duration

            variables[task_idx, machine] = var

    return variables


def sequence_variables(
    m: CpoModel, data: ProblemData, assign: AssignVars
) -> list[CpoSequenceVar]:
    """
    Creates a sequence variable for each machine, using the corresponding
    assignment variables.
    """
    variables = []

    for machine, tasks in enumerate(data.machine2tasks):
        intervals = [assign[task, machine] for task in tasks]
        variables.append(m.sequence_var(name=f"S{machine}", vars=intervals))

    return variables
