from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    job_data_constraints,
    job_operation_constraints,
    no_overlap_constraints,
    operation_constraints,
    operation_graph_constraints,
    processing_time_constraints,
    setup_times_constraints,
)
from .objectives import makespan
from .variables import assignment_variables, job_variables, operation_variables


def default_model(data: ProblemData) -> tuple[CpModel, list, dict]:
    model = CpModel()

    job_vars = job_variables(model, data)
    op_vars = operation_variables(model, data)
    assign = assignment_variables(model, data)

    if data.objective == "makespan":
        makespan(model, data, op_vars)
    else:
        msg = f"Objective '{data.objective}' not supported."
        raise NotImplementedError(msg)

    job_data_constraints(model, data, job_vars)
    job_operation_constraints(model, data, job_vars, op_vars)
    operation_constraints(model, data, op_vars)
    alternative_constraints(model, data, op_vars, assign)
    no_overlap_constraints(model, data, assign)
    processing_time_constraints(model, data, assign)
    setup_times_constraints(model, data, assign)
    operation_graph_constraints(model, data, op_vars, assign)

    return model, op_vars, assign
