from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    circuit_constraints,
    job_data_constraints,
    job_operation_constraints,
    no_overlap_constraints,
    operation_constraints,
    operation_graph_constraints,
    processing_time_constraints,
    setup_time_constraints,
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
    operation_variables,
    sequence_variables,
)


def default_model(data: ProblemData) -> tuple[CpModel, list, dict]:
    model = CpModel()

    job_vars = job_variables(model, data)
    op_vars = operation_variables(model, data)
    assign = assignment_variables(model, data)
    seq_vars = sequence_variables(model, data, assign)

    if data.objective == "makespan":
        makespan(model, data, op_vars)
    elif data.objective == "tardy_jobs":
        tardy_jobs(model, data, job_vars)
    elif data.objective == "total_tardiness":
        total_tardiness(model, data, job_vars)
    elif data.objective == "total_completion_time":
        total_completion_time(model, data, job_vars)
    else:
        raise ValueError(f"Unknown objective: {data.objective}")

    job_data_constraints(model, data, job_vars)
    job_operation_constraints(model, data, job_vars, op_vars)
    operation_constraints(model, data, op_vars)
    alternative_constraints(model, data, op_vars, assign)
    no_overlap_constraints(model, data, seq_vars)
    processing_time_constraints(model, data, assign)
    setup_time_constraints(model, data, seq_vars)
    operation_graph_constraints(model, data, op_vars, assign, seq_vars)

    # Must be called last to ensure that sequence constriants are enforced!
    circuit_constraints(model, data, seq_vars)

    return model, op_vars, assign
