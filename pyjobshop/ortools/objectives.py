from ortools.sat.python.cp_model import CpModel, LinearExpr

from pyjobshop.ProblemData import ProblemData

from .variables import JobVar, TaskVar


def makespan(m: CpModel, data: ProblemData, task_vars: list[TaskVar]):
    """
    Minimizes the makespan.
    """
    makespan = m.new_int_var(0, data.horizon, "makespan")
    completion_times = [var.end for var in task_vars]

    m.add_max_equality(makespan, completion_times)
    m.minimize(makespan)


def tardy_jobs(m: CpModel, data: ProblemData, job_vars: list[JobVar]):
    """
    Minimize the number of tardy jobs.
    """
    exprs = []

    for job, var in zip(data.jobs, job_vars):
        is_tardy = m.new_bool_var(f"is_tardy_{job}")
        exprs.append(is_tardy)

        m.add(var.end > job.due_date).only_enforce_if(is_tardy)
        m.add(var.end <= job.due_date).only_enforce_if(~is_tardy)

    m.minimize(LinearExpr.sum(exprs))


def total_completion_time(
    m: CpModel, data: ProblemData, job_vars: list[JobVar]
):
    """
    Minimizes the weighted sum of the completion times of each job.
    """
    exprs = [var.end for var in job_vars]
    weights = [job.weight for job in data.jobs]

    m.minimize(LinearExpr.weighted_sum(exprs, weights))


def total_tardiness(m: CpModel, data: ProblemData, job_vars: list[JobVar]):
    """
    Minimizes the weighted sum of the tardiness of each job.
    """
    exprs = []

    for job, var in zip(data.jobs, job_vars):
        tardiness = m.new_int_var(0, data.horizon, f"tardiness_{job}")
        exprs.append(tardiness)

        m.add_max_equality(tardiness, [0, var.end - job.due_date])

    weights = [job.weight for job in data.jobs]
    m.minimize(LinearExpr.weighted_sum(exprs, weights))
