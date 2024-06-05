from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    job_data_constraints,
    job_task_constraints,
    no_overlap_and_setup_time_constraints,
    planning_horizon_constraints,
    processing_time_constraints,
    task_constraints,
    task_graph_constraints,
)
from .objectives import (
    makespan,
    tardy_jobs,
    total_completion_time,
    total_tardiness,
)
from .variables import (
    assignment_variables,
    job_variables,
    sequence_variables,
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
    assign_vars = assignment_variables(model, data)
    seq_vars = sequence_variables(model, data, assign_vars)

    if data.objective == "makespan":
        model.add(makespan(model, data, task_vars))
    elif data.objective == "tardy_jobs":
        model.add(tardy_jobs(model, data, job_vars))
    elif data.objective == "total_tardiness":
        model.add(total_tardiness(model, data, job_vars))
    elif data.objective == "total_completion_time":
        model.add(total_completion_time(model, data, job_vars))
    else:
        raise ValueError(f"Unknown objective: {data.objective}")

    model.add(job_data_constraints(model, data, job_vars))
    model.add(job_task_constraints(model, data, job_vars, task_vars))
    model.add(task_constraints(model, data, task_vars))
    model.add(alternative_constraints(model, data, task_vars, assign_vars))
    model.add(no_overlap_and_setup_time_constraints(model, data, seq_vars))
    model.add(
        planning_horizon_constraints(
            model, data, job_vars, assign_vars, task_vars
        )
    )
    model.add(processing_time_constraints(model, data, assign_vars))
    model.add(
        task_graph_constraints(model, data, task_vars, assign_vars, seq_vars)
    )

    return model
