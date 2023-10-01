from collections import defaultdict
from itertools import product

from ortools.sat.python.cp_model import CpModel

from fjsp.ProblemData import ProblemData

from .variables import AssignmentVar, OperationVar


def timing_precedence_constraints(
    m: CpModel,
    data: ProblemData,
    ops: list[OperationVar],
):
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

            m.Add(expr)


def assignment_precedence_constraints(
    m: CpModel, data: ProblemData, assign: dict[tuple[int, int], AssignmentVar]
):
    for machine, ops in enumerate(data.machine2ops):
        for op1, op2 in product(ops, repeat=2):
            if op1 == op2 or (op1, op2) not in data.precedences:
                continue

            var1 = assign[op1, machine]
            var2 = assign[op2, machine]

            for prec_type in data.precedences[op1, op2]:
                if prec_type == "previous":
                    raise NotImplementedError
                elif prec_type == "same_unit":
                    expr = var1.is_present == var2.is_present
                elif prec_type == "different_unit":
                    expr = var1.is_present != var2.is_present
                else:
                    continue

                m.Add(expr)


def alternative_constraints(
    m: CpModel,
    data: ProblemData,
    ops: list[OperationVar],
    assign: dict[tuple[int, int], AssignmentVar],
):
    """
    Creates the alternative constraints for the operations, ensuring that each
    operation is scheduled on exactly one machine.
    """
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
        m.AddExactlyOne(presences)


def no_overlap_constraints(
    m: CpModel, data: ProblemData, assign: dict[tuple[int, int], AssignmentVar]
):
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    sequences = defaultdict(list)
    for (_, machine), var in assign.items():
        sequences[machine].append(var)

    for machine in range(data.num_machines):
        m.AddNoOverlap([var.interval for var in sequences[machine]])

    # Sequence-dependent setup times.
    for machine in range(data.num_machines):
        arcs = []
        for idx1, intv1 in enumerate(sequences[machine]):
            arcs.append((0, idx1 + 1, m.NewBoolVar("Source")))
            arcs.append((idx1 + 1, 0, m.NewBoolVar("Sink")))

            for idx2, intv2 in enumerate(sequences[machine]):
                if idx1 == idx2:
                    continue

                lit = m.NewBoolVar(f"{idx1} setup {idx2} on {machine}")
                arcs.append((idx1 + 1, idx2 + 1, lit))

                is_present1 = intv1.is_present
                is_present2 = intv2.is_present

                # Link the literal: it is true iff both intervals are present
                # and idx => idx2 is true.
                follows = m.NewBoolVar(f"{idx1} => {idx2} on {machine}")
                literals = [follows, is_present1, is_present2]
                m.AddBoolAnd(literals).OnlyEnforceIf(lit)

                negated = [follows.Not(), is_present1.Not(), is_present2.Not()]
                m.AddBoolOr(negated).OnlyEnforceIf(lit.Not())

                op1 = int(intv1.interval.Name()[1:].split("_")[0])
                op2 = int(intv2.interval.Name()[1:].split("_")[0])
                setup = data.setup_times[op1, op2, machine]

                expr = intv1.start >= intv2.end + setup
                m.Add(expr).OnlyEnforceIf(lit)

        m.AddCircuit(arcs)


def machine_accessibility_constraints(
    m: CpModel, data: ProblemData, assign: dict[tuple[int, int], AssignmentVar]
):
    """
    Creates the machine accessibility constraints for the operations, ensuring
    that an operation can only be scheduled on a machine that is accessible
    from the machine on which the previous operation is scheduled.
    """
    for op1, op2 in data.precedences:
        machines1 = data.operations[op1].machines
        machines2 = data.operations[op2].machines

        for mach1, mach2 in product(machines1, machines2):
            if not data.access_matrix[mach1, mach2]:
                # If m1 cannot access m2, then we cannot schedule operation 1
                # on m1 and operation 2 on m2.
                var1 = assign[op1, mach1]
                var2 = assign[op2, mach2]
                m.Add(var1.is_present + var2.is_present <= 1)
