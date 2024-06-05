from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    circuit_constraints,
    job_spans_tasks,
    no_overlap_constraints,
    processing_time_constraints,
    setup_time_constraints,
    task_graph,
)
from .objectives import (
    makespan,
    tardy_jobs,
    total_completion_time,
    total_tardiness,
)
from .variables import (
    AssignmentVar,
    assignment_variables,
    job_variables,
    sequence_variables,
    task_variables,
)


def create_model(
    data: ProblemData,
) -> tuple[CpModel, dict[tuple[int, int], AssignmentVar]]:
    """
    Creates an OR-Tools model for the given problem.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    tuple[CpModel, dict[tuple[int, int], AssignmentVar]]
        The constraint programming model and the assignment variables.
    """
    model = CpModel()

    job_vars = job_variables(model, data)
    task_vars = task_variables(model, data)
    assign_vars = assignment_variables(model, data)
    seq_vars = sequence_variables(model, data, assign_vars)

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
    alternative_constraints(model, data, task_vars, assign_vars)
    no_overlap_constraints(model, data, seq_vars)
    processing_time_constraints(model, data, assign_vars)
    setup_time_constraints(model, data, seq_vars)
    task_graph(model, data, task_vars, assign_vars, seq_vars)

    # Must be called last to ensure that sequence constriants are enforced!
    circuit_constraints(model, data, seq_vars)

    return model, assign_vars
