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

    for machine, ops in enumerate(data.machine2ops):
        seq_var = sequence[machine]

        for op1, op2 in product(ops, repeat=2):
            if op1 == op2 or (op1, op2) not in data.operations_graph.edges:
                continue

            var1 = assign[op1][machine]
            var2 = assign[op2][machine]
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

    for op in range(data.num_operations):
        optional = [assign[op][mach] for mach in data.operations[op].machines]
        constraints.append(m.alternative(ops[op], optional))

    return constraints


def no_overlap_constraints(
    m: CpoModel, data: ProblemData, sequences: SeqVars
) -> list[CpoExpr]:
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    return [m.no_overlap(sequences[mach]) for mach in range(data.num_machines)]


def machine_accessibility_constraints(
    m: CpoModel, data: ProblemData, assign: AssignVars
) -> list[CpoExpr]:
    """
    Creates the machine accessibility constraints for the operations, ensuring
    that an operation can only be scheduled on a machine that is accessible
    from the machine on which the previous operation is scheduled.
    """
    constraints = []

    for op1, op2 in data.operations_graph.edges:
        machines1 = data.operations[op1].machines
        machines2 = data.operations[op2].machines

        for mach1, mach2 in product(machines1, machines2):
            if (mach1, mach2) not in data.machine_graph.edges:
                # If (m1 -> m2) is not an edge in the machine graph, then
                # we cannot schedule operation 1 on m1 and operation 2 on m2.
                frm = assign[op1][mach1]
                to = assign[op2][mach2]
                constraints.append(m.presence_of(frm) + m.presence_of(to) <= 1)

    return constraints
