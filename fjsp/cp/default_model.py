from docplex.cp.model import CpoModel

from fjsp.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    assignment_precedence_constraints,
    machine_accessibility_constraints,
    no_overlap_constraints,
    timing_precedence_constraints,
)
from .objectives import makespan
from .variables import (
    assignment_variables,
    operation_variables,
    sequence_variables,
)


def default_model(data: ProblemData) -> CpoModel:
    """
    Creates a CP model for the given problem data.
    """
    model = CpoModel()

    ops = operation_variables(model, data)
    assign = assignment_variables(model, data)
    sequences = sequence_variables(model, data, assign)

    model.add(makespan(model, data, ops))

    model.add(timing_precedence_constraints(model, data, ops))
    model.add(
        assignment_precedence_constraints(model, data, assign, sequences)
    )
    model.add(alternative_constraints(model, data, ops, assign))
    model.add(no_overlap_constraints(model, data, sequences))
    model.add(machine_accessibility_constraints(model, data, assign))

    return model
