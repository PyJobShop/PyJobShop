from ortools.sat.python.cp_model import CpModel
from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    assignment_precedence_constraints,
    job_data_constraints,
    job_operation_constraints,
    no_overlap_constraints,
    operation_constraints,
    timing_precedence_constraints,
)
from .objectives import makespan
from .variables import assignment_variables, job_variables, operation_variables


def default_model(data: ProblemData) -> CpModel:
    model = CpModel()

    job_vars = job_variables(model, data)
    op_vars = operation_variables(model, data)
    assign = assignment_variables(model, data)

    if data.objective == "makespan":
        makespan(model, data, op_vars)
    else:
        pass  # TODO

    job_data_constraints(model, data, job_vars)
    # machine_data_constraints(model, data, task_vars)
    job_operation_constraints(model, data, job_vars, op_vars)
    operation_constraints(model, data, op_vars)
    assignment_precedence_constraints(model, data, assign)
    alternative_constraints(model, data, op_vars, assign)
    no_overlap_constraints(model, data, assign)
    # model.add(optional_operation_selection_constraints(model, data, op_vars))
    # model.add(planning_horizon_constraints(model, data, job_vars, task_vars, op_vars))
    # model.add(processing_time_constraints(model, data, task_vars))
    timing_precedence_constraints(model, data, op_vars)
    # setup_times_constraints(model, data, assign)

    return model, op_vars, assign
