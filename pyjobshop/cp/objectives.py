from docplex.cp.expression import CpoExpr, CpoIntervalVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData


def makespan(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the makespan of the schedule.
    """
    return m.minimize(m.max(m.end_of(var) for var in job_vars))


def total_completion_time(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the sum of the completion times of each job.
    """
    return m.minimize(m.sum(m.end_of(var) for var in job_vars))


def total_tardiness(
    m: CpoModel, data: ProblemData, job_vars: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the sum of the tardiness of each job. A job's tardiness is
    defined as the maximum of 0 and its completion time minus the job's
    deadline.
    """
    expr = m.sum(
        m.max(0, m.end_of(var) - job_data.deadline)
        for job_data, var in zip(data.jobs, job_vars)
    )
    return m.minimize(expr)
