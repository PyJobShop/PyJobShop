from docplex.cp.expression import CpoExpr, CpoIntervalVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData


def makespan(
    m: CpoModel, data: ProblemData, op_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the makespan of the schedule.
    """
    return m.minimize(m.max(m.end_of(var) for var in op_vars))


def tardy_jobs(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimize the number of tardy jobs.
    """
    total = []

    for job_data, job_var in zip(data.jobs, job_vars):
        is_tardy = m.greater(m.end_of(job_var) - job_data.due_date, 0)
        total.append(is_tardy)

    return m.minimize(m.sum(total))


def total_completion_time(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the sum of the completion times of each job.
    """
    total = []

    for job_data, job_var in zip(data.jobs, job_vars):
        completion_time = job_data.weight * m.end_of(job_var)
        total.append(completion_time)

    return m.minimize(m.sum(total))


def total_tardiness(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the sum of the tardiness of each job. A job's tardiness is
    defined as the maximum of 0 and its completion time minus the job's
    due date.
    """
    total = []

    for job_data, job_var in zip(data.jobs, job_vars):
        tardiness = m.max(
            0, job_data.weight * (m.end_of(job_var) - job_data.due_date)
        )
        total.append(tardiness)

    return m.minimize(m.sum(total))
