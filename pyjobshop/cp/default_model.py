from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    assignment_precedence_constraints,
    job_data_constraints,
    job_operation_constraints,
    machine_data_constraints,
    no_overlap_and_setup_time_constraints,
    operation_constraints,
    optional_operation_selection_constraints,
    planning_horizon_constraints,
    processing_time_constraints,
    timing_precedence_constraints,
)
from .objectives import (
    makespan,
    tardy_jobs,
    total_completion_time,
    total_tardiness,
)
from .variables import (
    job_variables,
    operation_variables,
    sequence_variables,
    task_variables,
)


def default_model(data: ProblemData) -> CpoModel:
    """
    Creates a CP model for the given problem data.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    CpoModel
        The CP model for the given problem data.
    """
    model = CpoModel()

    job_vars = job_variables(model, data)
    op_vars = operation_variables(model, data)
    task_vars = task_variables(model, data)
    seq_vars = sequence_variables(model, data, task_vars)

    if data.objective == "makespan":
        model.add(makespan(model, data, op_vars))
    elif data.objective == "tardy_jobs":
        model.add(tardy_jobs(model, data, job_vars))
    elif data.objective == "total_tardiness":
        model.add(total_tardiness(model, data, job_vars))
    elif data.objective == "total_completion_time":
        model.add(total_completion_time(model, data, job_vars))
    else:
        raise ValueError(f"Unknown objective: {data.objective}")

    model.add(job_data_constraints(model, data, job_vars))
    model.add(machine_data_constraints(model, data, task_vars))
    model.add(job_operation_constraints(model, data, job_vars, op_vars))
    model.add(operation_constraints(model, data, op_vars))
    model.add(
        assignment_precedence_constraints(model, data, task_vars, seq_vars)
    )
    model.add(alternative_constraints(model, data, op_vars, task_vars))
    model.add(no_overlap_and_setup_time_constraints(model, data, seq_vars))
    model.add(optional_operation_selection_constraints(model, data, op_vars))
    model.add(
        planning_horizon_constraints(model, data, job_vars, task_vars, op_vars)
    )
    model.add(processing_time_constraints(model, data, task_vars))
    model.add(timing_precedence_constraints(model, data, op_vars))

    return model
