from ortools.sat.python.cp_model import CpModel

from fjsp.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    assignment_precedence_constraints,
    machine_accessibility_constraints,
    no_overlap_constraints,
    setup_times_constraints,
    timing_precedence_constraints,
)
from .objectives import makespan
from .variables import assignment_variables, operation_variables


def default_model(data: ProblemData) -> CpModel:
    model = CpModel()

    ops = operation_variables(model, data)
    assign = assignment_variables(model, data)

    makespan(model, data, ops)

    timing_precedence_constraints(model, data, ops)
    assignment_precedence_constraints(model, data, assign)
    alternative_constraints(model, data, ops, assign)
    no_overlap_constraints(model, data, assign)
    setup_times_constraints(model, data, assign)
    machine_accessibility_constraints(model, data, assign)

    return model, ops, assign
