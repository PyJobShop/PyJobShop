from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

from .constraints import (
    alternative_constraints,
    assignment_precedence_constraints,
    job_operation_constraints,
    machine_accessibility_constraints,
    no_overlap_constraints,
    operation_constraints,
    optional_operation_selection_constraints,
    timing_precedence_constraints,
)
from .objectives import makespan
from .variables import (
    assignment_variables,
    job_variables,
    operation_variables,
    sequence_variables,
)


def default_model(data: ProblemData) -> CpoModel:
    """
    Creates a CP model for the given problem data.
    """
    model = CpoModel()

    job_vars = job_variables(model, data)
    op_vars = operation_variables(model, data)
    assign_vars = assignment_variables(model, data)
    seq_vars = sequence_variables(model, data, assign_vars)

    if data.objective == "makespan":
        model.add(makespan(model, data, op_vars))
    else:
        raise ValueError(f"Unknown objective: {data.objective}")

    model.add(job_operation_constraints(model, data, job_vars, op_vars))
    model.add(operation_constraints(model, data, op_vars))
    model.add(timing_precedence_constraints(model, data, op_vars))
    model.add(
        assignment_precedence_constraints(model, data, assign_vars, seq_vars)
    )
    model.add(alternative_constraints(model, data, op_vars, assign_vars))
    model.add(no_overlap_constraints(model, data, seq_vars))
    model.add(machine_accessibility_constraints(model, data, assign_vars))
    model.add(optional_operation_selection_constraints(model, data, op_vars))

    return model
