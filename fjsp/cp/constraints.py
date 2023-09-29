from itertools import product

from docplex.cp.expression import CpoExpr, CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from fjsp.ProblemData import ProblemData

OpsVars = list[CpoIntervalVar]
AssignVars = dict[int, dict[int, CpoIntervalVar]]
SeqVars = list[CpoSequenceVar]


def timing_precedence_constraints(
    m: CpoModel, data: ProblemData, ops: OpsVars
) -> list[CpoExpr]:
    constraints = []

    for frm_idx, to_idx, attr in data.operations_graph.edges(data=True):
        frm = ops[frm_idx]
        to = ops[to_idx]

        for prec_type in attr["precedence_types"]:
            if prec_type == "start_at_start":
                expr = m.start_at_start(frm, to)
            elif prec_type == "start_at_end":
                expr = m.start_at_end(frm, to)
            elif prec_type == "start_before_start":
                expr = m.start_before_start(frm, to)
            elif prec_type == "start_before_end":
                expr = m.start_before_end(frm, to)
            elif prec_type == "end_at_start":
                expr = m.end_at_start(frm, to)
            elif prec_type == "end_at_end":
                expr = m.end_at_end(frm, to)
            elif prec_type == "end_before_start":
                expr = m.end_before_start(frm, to)
            elif prec_type == "end_before_end":
                expr = m.end_before_end(frm, to)
            else:
                continue

            constraints.append(expr)

    return constraints


def assignment_precedence_constraints(
    m: CpoModel, data: ProblemData, assign: AssignVars, sequence: SeqVars
) -> list[CpoExpr]:
    constraints = []

    for machine, ops in data.machine2ops.items():
        seq_var = sequence[machine.idx]

        for op1, op2 in product(ops, repeat=2):
            if op1 == op2 or (op1, op2) not in data.operations_graph.edges:
                continue

            var1 = assign[op1][machine.idx]
            var2 = assign[op2][machine.idx]
            edge = data.operations_graph.edges[op1, op2]

            for prec_type in edge["precedence_types"]:
                if prec_type == "previous":
                    expr = m.previous(seq_var, var1, var2)
                elif prec_type == "same_unit":
                    expr = m.presence_of(var1) == m.presence_of(var2)
                elif prec_type == "different_unit":
                    expr = m.presence_of(var1) != m.presence_of(var2)
                else:
                    continue

                constraints.append(expr)

    return constraints


def alternative_constraints(
    m: CpoModel, data: ProblemData, ops: OpsVars, assign: AssignVars
) -> list[CpoExpr]:
    """
    Creates the alternative constraints for the operations, ensuring that each
    operation is scheduled on exactly one machine.
    """
    constraints = []

    for op in data.operations:
        op_var = ops[op.idx]
        optional = [assign[op.idx][mach.idx] for mach in op.machines]
        constraints.append(m.alternative(op_var, optional))

    return constraints


def no_overlap_constraints(
    m: CpoModel, data: ProblemData, sequences: SeqVars
) -> list[CpoExpr]:
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    return [m.no_overlap(sequences[machine.idx]) for machine in data.machines]


def machine_accessibility_constraints(
    m: CpoModel, data: ProblemData, assign: AssignVars
) -> list[CpoExpr]:
    """
    Creates the machine accessibility constraints for the operations, ensuring
    that an operation can only be scheduled on a machine that is accessible
    from the machine on which the previous operation is scheduled.
    """
    constraints = []

    for i, j in data.operations_graph.edges:
        op1, op2 = data.operations[i], data.operations[j]

        for m1, m2 in product(op1.machines, op2.machines):
            if (m1.idx, m2.idx) not in data.machine_graph.edges:
                # If (m1 -> m2) is not an edge in the machine graph, then
                # we cannot schedule operation 1 on m1 and operation 2 on m2.
                frm = assign[op1.idx][m1.idx]
                to = assign[op2.idx][m2.idx]
                constraints.append(m.presence_of(frm) + m.presence_of(to) <= 1)

    return constraints
