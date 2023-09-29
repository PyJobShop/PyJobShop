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
    m = CpoModel()

    ops = operation_variables(m, data)
    assign = assignment_variables(m, data)
    sequences = sequence_variables(m, data, assign)

    m.add(makespan(m, data, ops))

    m.add(timing_precedence_constraints(m, data, ops))
    m.add(assignment_precedence_constraints(m, data, assign, sequences))
    m.add(alternative_constraints(m, data, ops, assign))
    m.add(no_overlap_constraints(m, data, sequences))
    m.add(machine_accessibility_constraints(m, data, assign))

    return m
