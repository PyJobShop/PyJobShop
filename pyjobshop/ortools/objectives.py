from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .variables import JobVar, OperationVar


def makespan(model: CpModel, data: ProblemData, ops: list[OperationVar]):
    """
    Minimizes the makespan of the schedule.
    """
    makespan = model.new_int_var(0, data.planning_horizon, "makespan")
    completion_times = [ops[op].end for op in range(data.num_operations)]

    model.add_max_equality(makespan, completion_times)
    model.minimize(makespan)


def tardy_jobs(m: CpModel, data: ProblemData, job_vars: list[JobVar]):
    """
    Minimize the number of tardy jobs.
    """
    # total = []

    # for job_data, job_var in zip(data.jobs, job_vars):
    #     is_tardy = m.greater(m.end_of(job_var) - job_data.due_date, 0)
    #     total.append(is_tardy)

    # return m.minimize(m.sum(total))


def total_completion_time(
    m: CpModel, data: ProblemData, job_vars: list[JobVar]
):
    """
    Minimizes the sum of the completion times of each job.
    """
    # total = []

    # for job_data, job_var in zip(data.jobs, job_vars):
    #     completion_time = job_data.weight * m.end_of(job_var)
    #     total.append(completion_time)

    # return m.minimize(m.sum(total))


def total_tardiness(m: CpModel, data: ProblemData, job_vars: list[JobVar]):
    """
    Minimizes the sum of the tardiness of each job. A job's tardiness is
    defined as the maximum of 0 and its completion time minus the job's
    due date.
    """
    # total = []

    # for job_data, job_var in zip(data.jobs, job_vars):
    #     tardiness = m.max(
    #         0, job_data.weight * (m.end_of(job_var) - job_data.due_date)
    #     )
    #     total.append(tardiness)

    # return m.minimize(m.sum(total))
