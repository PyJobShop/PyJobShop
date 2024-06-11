from docplex.cp.expression import CpoIntervalVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData


def makespan(m: CpoModel, data: ProblemData, op_vars: list[CpoIntervalVar]):
    """
    Minimizes the makespan of the schedule.
    """
    m.add(m.minimize(m.max(m.end_of(var) for var in op_vars)))


def tardy_jobs(m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]):
    """
    Minimize the number of tardy jobs.
    """
    total = []

    for job, var in zip(data.jobs, job_vars):
        is_tardy = m.greater(m.end_of(var) - job.due_date, 0)
        total.append(is_tardy)

    m.add(m.minimize(m.sum(total)))


def total_completion_time(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
):
    """
    Minimizes the weighted sum of the completion times of each job.
    """
    total = []

    for job, var in zip(data.jobs, job_vars):
        completion_time = job.weight * m.end_of(var)
        total.append(completion_time)

    m.add(m.minimize(m.sum(total)))


def total_tardiness(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
):
    """
    Minimizes the weighted sum of the tardiness of each job.
    """
    total = []

    for job, var in zip(data.jobs, job_vars):
        tardiness = m.max(0, job.weight * (m.end_of(var) - job.due_date))
        total.append(tardiness)

    m.add(m.minimize(m.sum(total)))
