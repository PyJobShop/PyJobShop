from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    job_spans_tasks,
    no_overlap_and_setup_times,
    select_one_task_alternative,
    task_graph,
)
from .objectives import (
    makespan,
    tardy_jobs,
    total_completion_time,
    total_tardiness,
)
from .variables import (
    job_variables,
    sequence_variables,
    task_alternatives_variables,
    task_variables,
)


def create_model(data: ProblemData) -> CpoModel:
    """
    Creates a CP Optimizer model for the given problem data.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    CpoModel
        The constraint programming model for the given problem data.
    """
    model = CpoModel()

    job_vars = job_variables(model, data)
    task_vars = task_variables(model, data)
    task_alt_vars = task_alternatives_variables(model, data)
    seq_vars = sequence_variables(model, data, task_alt_vars)

    if data.objective == "makespan":
        makespan(model, data, task_vars)
    elif data.objective == "tardy_jobs":
        tardy_jobs(model, data, job_vars)
    elif data.objective == "total_tardiness":
        total_tardiness(model, data, job_vars)
    elif data.objective == "total_completion_time":
        total_completion_time(model, data, job_vars)
    else:
        raise ValueError(f"Unknown objective: {data.objective}")

    job_spans_tasks(model, data, job_vars, task_vars)
    no_overlap_and_setup_times(model, data, seq_vars)
    select_one_task_alternative(model, data, task_vars, task_alt_vars)
    task_graph(model, data, task_vars, task_alt_vars, seq_vars)

    return model
