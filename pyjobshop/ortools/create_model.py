from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    activate_setup_times,
    enforce_circuit,
    job_spans_tasks,
    no_overlap_machines,
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
    TaskAltVar,
    job_variables,
    sequence_variables,
    task_alternative_variables,
    task_variables,
)


def create_model(
    data: ProblemData,
) -> tuple[CpModel, dict[tuple[int, int], TaskAltVar]]:
    """
    Creates an OR-Tools model for the given problem.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    tuple[CpModel, dict[tuple[int, int], TaskAltVar]]
        The constraint programming model and the task alternative variables.
    """
    model = CpModel()

    job_vars = job_variables(model, data)
    task_vars = task_variables(model, data)
    task_alt_vars = task_alternative_variables(model, data)
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
    select_one_task_alternative(model, data, task_vars, task_alt_vars)
    no_overlap_machines(model, data, seq_vars)
    activate_setup_times(model, data, seq_vars)
    task_graph(model, data, task_vars, task_alt_vars, seq_vars)

    # Must be called last to ensure that sequence constriants are enforced!
    enforce_circuit(model, data, seq_vars)

    return model, task_alt_vars
