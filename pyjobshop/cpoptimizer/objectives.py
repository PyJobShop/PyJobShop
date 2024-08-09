from docplex.cp.expression import CpoIntervalVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData


def add_objective(
    m: CpoModel,
    data: ProblemData,
    job_vars: list[CpoIntervalVar],
    task_vars: list[CpoIntervalVar],
):
    """
    Adds the objective to the model.
    """
    expr = 0
    objective = data.objective

    if objective.weight_makespan > 0:
        expr += objective.weight_makespan * _makespan(m, task_vars)

    if objective.weight_tardy_jobs > 0:
        expr += objective.weight_tardy_jobs * _tardy_jobs(m, data, job_vars)

    if objective.weight_total_tardiness > 0:
        expr += objective.weight_total_tardiness * _total_tardiness(
            m, data, job_vars
        )

    if objective.weight_total_completion_time > 0:
        expr += (
            objective.weight_total_completion_time
            * _total_completion_time(m, data, job_vars)
        )

    return m.minimize(expr)


def _makespan(m: CpoModel, task_vars: list[CpoIntervalVar]):
    """
    Minimizes the makespan of the schedule.
    """
    return m.max(m.end_of(var) for var in task_vars)


def _tardy_jobs(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
):
    """
    Minimize the number of tardy jobs.
    """
    total = []

    for job, var in zip(data.jobs, job_vars, strict=True):
        is_tardy = m.greater(m.end_of(var) - job.due_date, 0)
        total.append(is_tardy)

    return m.sum(total)


def _total_completion_time(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
):
    """
    Minimizes the weighted sum of the completion times of each job.
    """
    total = []

    for job, var in zip(data.jobs, job_vars, strict=True):
        completion_time = job.weight * m.end_of(var)
        total.append(completion_time)

    return m.sum(total)


def _total_tardiness(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
):
    """
    Minimizes the weighted sum of the tardiness of each job.
    """
    total = []

    for job, var in zip(data.jobs, job_vars, strict=True):
        tardiness = m.max(0, job.weight * (m.end_of(var) - job.due_date))
        total.append(tardiness)

    return m.sum(total)
