from docplex.cp.expression import CpoExpr, CpoIntervalVar
from docplex.cp.model import CpoModel

from fjsp.ProblemData import ProblemData


def makespan(
    m: CpoModel, data: ProblemData, ops: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the makespan of the schedule.
    """
    completion_times = [m.end_of(ops[op]) for op in range(data.num_operations)]
    return m.minimize(m.max(completion_times))


def total_completion_time(
    m: CpoModel, data: ProblemData, ops: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the sum of the completion times of each job. A job's completion
    time is defined as the completion time of its last completed operation.
    """
    completion_times = []

    for _, operations in data.job2ops.items():
        expr = m.max([ops[op] for op in operations])
        completion_times.append(expr)

    return m.minimize(m.sum(completion_times))


def total_tardiness(
    m: CpoModel, data: ProblemData, ops: list[CpoIntervalVar]
) -> CpoExpr:
    """
    Minimizes the sum of the tardiness of each job. A job's tardiness is
    defined as the maximum of 0 and the completion time of its last completed
    operation minus the job's deadline.
    """
    total = []

    for job, operations in data.job2ops.items():
        expr = m.max([m.end_of(ops[op]) for op in operations])
        tardiness = m.max(0, expr - data.jobs[job.idx].deadline)
        total.append(tardiness)

    return m.minimize(m.sum(total))
