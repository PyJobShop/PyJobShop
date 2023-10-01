from collections import defaultdict

from ortools.sat.python.cp_model import Constraint, CpModel

from fjsp.ProblemData import ProblemData

from .variables import AssignmentVar, OperationVar


def timing_precedence_constraints(
    m: CpModel,
    data: ProblemData,
    ops: list[OperationVar],
) -> list[Constraint]:
    constraints = []

    for (idx1, idx2), precedence_types in data.precedences.items():
        op1 = ops[idx1]
        op2 = ops[idx2]

        for prec_type in precedence_types:
            if prec_type == "start_at_start":
                expr = op1.start == op2.start
            elif prec_type == "start_at_end":
                expr = op1.start == op2.end
            elif prec_type == "start_before_start":
                expr = op1.start <= op2.start
            elif prec_type == "start_before_end":
                expr = op1.start <= op2.end
            elif prec_type == "end_at_start":
                expr = op1.end == op2.start
            elif prec_type == "end_at_end":
                expr = op1.end == op2.end
            elif prec_type == "end_before_start":
                expr = op1.end <= op2.start
            elif prec_type == "end_before_end":
                expr = op1.end <= op2.end
            else:
                continue

            constraints.append(m.Add(expr))

    return constraints

    pass


def alternative_constraints(
    m: CpModel,
    data: ProblemData,
    ops: list[OperationVar],
    assign: dict[tuple[int, int], AssignmentVar],
) -> list[Constraint]:
    """
    Creates the alternative constraints for the operations, ensuring that each
    operation is scheduled on exactly one machine.
    """
    constraints = []

    for op in range(data.num_operations):
        presences = []

        for machine in data.operations[op].machines:
            main = ops[op]
            optional = assign[op, machine]
            is_present = optional.is_present
            presences.append(is_present)

            # Link each optional interval variable with the global variable.
            m.Add(main.start == optional.start).OnlyEnforceIf()
            m.Add(main.duration == optional.duration).OnlyEnforceIf()
            m.Add(main.end == optional.end).OnlyEnforceIf()

        # Select exactly one machine for the operation.
        constraints.append(m.AddExactlyOne(presences))

    return constraints


def no_overlap_constraints(
    m: CpModel, data: ProblemData, assign: dict[tuple[int, int], AssignmentVar]
) -> list[Constraint]:
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    sequences = defaultdict(list)
    for (_, machine), var in assign.items():
        sequences[machine].append(var.interval)

    constraints = []
    for machine in range(data.num_machines):
        constraints.append(m.AddNoOverlap(sequences[machine]))

    return constraints
