from fjsp.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    assignment_precedence_constraints,
    machine_accessibility_constraints,
    no_overlap_constraints,
    timing_precedence_constraints,
)
from .CpModel import CpModel
from .objectives import makespan
from .variables import (
    assignment_variables,
    operation_variables,
    sequence_variables,
)


def default_model(data: ProblemData) -> CpModel:
    """
    Creates a CP model for the given problem data.
    """
    m = CpModel()

    operation_variables(m, data)
    assignment_variables(m, data)
    sequence_variables(m, data)

    m.add(makespan(m, data))

    timing_precedence_constraints(m, data)
    assignment_precedence_constraints(m, data)
    alternative_constraints(m, data)
    no_overlap_constraints(m, data)
    machine_accessibility_constraints(m, data)

    return m
