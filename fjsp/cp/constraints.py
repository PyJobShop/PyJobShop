from itertools import product

import numpy as np
from docplex.cp.expression import CpoExpr, CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from fjsp.ProblemData import ProblemData

JobVars = list[CpoIntervalVar]
OpVars = list[CpoIntervalVar]
AssignVars = dict[tuple[int, int], CpoIntervalVar]
SeqVars = list[CpoSequenceVar]


def job_operation_constraints(
    m: CpoModel, data: ProblemData, job_vars: JobVars, ops: OpVars
) -> list[CpoExpr]:
    """
    Creates the constraints that ensure that the job variables govern the
    related operation variables.
    """
    constraints = []

    for job in range(data.num_jobs):
        job_var = job_vars[job]
        related_op_vars = [ops[op] for op in data.job2ops[job]]

        constraints.append(m.span(job_var, related_op_vars))

        for op_var in related_op_vars:
            # Operation may not start before the job's release date if present.
            constraints.append(
                m.start_of(op_var)
                >= data.jobs[job].release_date * m.presence_of(op_var)
            )

    return constraints


def timing_precedence_constraints(
    m: CpoModel, data: ProblemData, ops: OpVars
) -> list[CpoExpr]:
    constraints = []

    for (idx1, idx2), precedence_types in data.precedences.items():
        op1 = ops[idx1]
        op2 = ops[idx2]

        for prec_type in precedence_types:
            if prec_type == "start_at_start":
                expr = m.start_at_start(op1, op2)
            elif prec_type == "start_at_end":
                expr = m.start_at_end(op1, op2)
            elif prec_type == "start_before_start":
                expr = m.start_before_start(op1, op2)
            elif prec_type == "start_before_end":
                expr = m.start_before_end(op1, op2)
            elif prec_type == "end_at_start":
                expr = m.end_at_start(op1, op2)
            elif prec_type == "end_at_end":
                expr = m.end_at_end(op1, op2)
            elif prec_type == "end_before_start":
                expr = m.end_before_start(op1, op2)
            elif prec_type == "end_before_end":
                expr = m.end_before_end(op1, op2)
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
            if op1 == op2 or (op1, op2) not in data.precedences:
                continue

            var1 = assign[op1, machine]
            var2 = assign[op2, machine]

            for prec_type in data.precedences[op1, op2]:
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
    m: CpoModel, data: ProblemData, ops: OpVars, assign: AssignVars
) -> list[CpoExpr]:
    """
    Creates the alternative constraints for the operations, ensuring that each
    operation is scheduled on exactly one machine.
    """
    constraints = []

    for op in range(data.num_operations):
        optional = [assign[op, machine] for machine in data.op2machines[op]]
        constraints.append(m.alternative(ops[op], optional))

    return constraints


def no_overlap_constraints(
    m: CpoModel, data: ProblemData, sequences: SeqVars
) -> list[CpoExpr]:
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    constraints = []
    for machine in range(data.num_machines):
        # Assumption is that the interval variables in the sequence variable
        # are ordered in the same way as the operations in machine2ops.
        if not (ops := data.machine2ops[machine]):
            continue  # There no operations for this machine.

        distance_matrix = data.setup_times[:, :, machine][np.ix_(ops, ops)]
        constraints.append(m.no_overlap(sequences[machine], distance_matrix))

    return constraints


def machine_accessibility_constraints(
    m: CpoModel, data: ProblemData, assign: AssignVars
) -> list[CpoExpr]:
    """
    Creates the machine accessibility constraints for the operations, ensuring
    that an operation can only be scheduled on a machine that is accessible
    from the machine on which the previous operation is scheduled.
    """
    constraints = []

    for op1, op2 in data.precedences:
        machines1 = data.op2machines[op1]
        machines2 = data.op2machines[op2]

        for mach1, mach2 in product(machines1, machines2):
            if not data.access_matrix[mach1, mach2]:
                # If m1 cannot access m2, then we cannot schedule operation 1
                # on m1 and operation 2 on m2.
                frm = assign[op1, mach1]
                to = assign[op2, mach2]
                constraints.append(m.presence_of(frm) + m.presence_of(to) <= 1)

    return constraints
