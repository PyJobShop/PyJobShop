from itertools import product

import numpy as np
from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .variables import AssignmentVar, JobVar, OperationVar, SequenceVar

JobVars = list[JobVar]
OperationVars = list[OperationVar]
AssignmentVars = dict[tuple[int, int], AssignmentVar]
SequenceVars = list[SequenceVar]


def job_data_constraints(m: CpModel, data: ProblemData, job_vars: JobVars):
    """
    Creates the constraints that ensure that the job variables are consistent
    with the job data.
    """
    for job_data, job_var in zip(data.jobs, job_vars):
        m.add(job_var.start >= job_data.release_date)

        if job_data.deadline is not None:
            m.add(job_var.end <= job_data.deadline)


def job_operation_constraints(
    m: CpModel, data: ProblemData, job_vars: JobVars, op_vars: OperationVars
):
    """
    Creates the constraints that ensure that the job variables govern the
    related operation variables.
    """
    for job in range(data.num_jobs):
        job_var = job_vars[job]
        related_vars = [op_vars[op] for op in data.job2ops[job]]

        m.add_min_equality(job_var.start, [var.start for var in related_vars])
        m.add_max_equality(job_var.end, [var.end for var in related_vars])

        for var in related_vars:
            m.add(var.start >= data.jobs[job].release_date)


def operation_constraints(
    m: CpModel, data: ProblemData, op_vars: OperationVars
):
    """
    Creates constraints on the operation variables.
    """
    for op_data, var in zip(data.operations, op_vars):
        if op_data.earliest_start is not None:
            m.add(var.start >= op_data.earliest_start)

        if op_data.latest_start is not None:
            m.add(var.start <= op_data.latest_start)

        if op_data.earliest_end is not None:
            m.add(var.end >= op_data.earliest_end)

        if op_data.latest_end is not None:
            m.add(var.end <= op_data.latest_end)


def operation_graph_constraints(
    m: CpModel,
    data: ProblemData,
    op_vars: OperationVars,
    assign: AssignmentVars,
    seq_vars: SequenceVars,
):
    """
    Creates constraints based on the operation graph, ensuring that the
    operations are scheduled according to the graph.
    """
    for (idx1, idx2), constraints in data.constraints.items():
        op_var1 = op_vars[idx1]
        op_var2 = op_vars[idx2]

        for prec_type in constraints:
            if prec_type == "start_at_start":
                expr = op_var1.start == op_var2.start
            elif prec_type == "start_at_end":
                expr = op_var1.start == op_var2.end
            elif prec_type == "start_before_start":
                expr = op_var1.start <= op_var2.start
            elif prec_type == "start_before_end":
                expr = op_var1.start <= op_var2.end
            elif prec_type == "end_at_start":
                expr = op_var1.end == op_var2.start
            elif prec_type == "end_at_end":
                expr = op_var1.end == op_var2.end
            elif prec_type == "end_before_start":
                expr = op_var1.end <= op_var2.start
            elif prec_type == "end_before_end":
                expr = op_var1.end <= op_var2.end
            else:
                continue

            m.add(expr)

    # Separately handle assignment related constraints for efficiency.
    for machine, ops in enumerate(data.machine2ops):
        for op1, op2 in product(ops, repeat=2):
            if op1 == op2 or (op1, op2) not in data.constraints:
                continue

            sequence = seq_vars[machine]
            var1 = assign[op1, machine]
            var2 = assign[op2, machine]

            for constraint in data.constraints[op1, op2]:
                if constraint == "previous":
                    sequence.activate()

                    rank1 = sequence.tasks.index(var1)
                    rank2 = sequence.tasks.index(var2)
                    arc_lit = sequence.arcs[rank1, rank2]

                    # Equivalent: arc_lit <=> var1.is_present & var2.is_present
                    m.add_bool_or(
                        [arc_lit, var1.is_present.Not(), var2.is_present.Not()]
                    )
                    m.add_implication(arc_lit, var1.is_present)
                    m.add_implication(arc_lit, var2.is_present)
                elif constraint == "same_unit":
                    expr = var1.is_present == var2.is_present
                    m.add(expr)
                elif constraint == "different_unit":
                    expr = var1.is_present != var2.is_present
                    m.add(expr)


def alternative_constraints(
    m: CpModel,
    data: ProblemData,
    ops: OperationVars,
    assign_vars: AssignmentVars,
):
    """
    Creates the alternative constraints for the operations, ensuring that each
    operation is scheduled on exactly one machine.
    """
    for op in range(data.num_operations):
        presences = []

        for machine in data.op2machines[op]:
            main = ops[op]
            assign = assign_vars[op, machine]
            is_present = assign.is_present
            presences.append(is_present)

            # Link each optional interval variable with the main variable.
            m.add(main.start == assign.start).OnlyEnforceIf(is_present)
            m.add(main.duration == assign.duration).OnlyEnforceIf(is_present)
            m.add(main.end == assign.end).OnlyEnforceIf(is_present)

        # Select exactly one machine for the operation.
        m.add_exactly_one(presences)


def no_overlap_constraints(
    m: CpModel, data: ProblemData, seq_vars: SequenceVars
):
    """
    Creates the no overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    for machine in range(data.num_machines):
        if not data.machines[machine].allow_overlap:
            m.add_no_overlap([var.interval for var in seq_vars[machine].tasks])


def processing_time_constraints(
    m: CpModel, data: ProblemData, assign: AssignmentVars
):
    """
    Creates the processing time constraints for the task variables, ensuring
    that the duration of the operation on the machine is the processing time.
    If the operation allows for variable duration, the duration could be longer
    than the processing time due to blocking.
    """
    for (op, machine), var in assign.items():
        duration = data.processing_times[machine, op]

        if data.operations[op].fixed_duration:
            m.add(var.duration == duration)
        else:
            m.add(var.duration >= duration)


def setup_time_constraints(
    m: CpModel,
    data: ProblemData,
    seq_vars: SequenceVars,
):
    """
    Actives the sequence variables for machines that have setup times. The
    ``circuit_constraints`` function will in turn add the constraints to the
    CP-SAT model to enforce setup times.
    """
    for machine in range(data.num_machines):
        setup_times = data.setup_times[machine]

        if np.any(setup_times != 0):
            seq_vars[machine].activate()


def circuit_constraints(
    m: CpModel,
    data: ProblemData,
    seq_vars: SequenceVars,
):
    """
    Creates the circuit constraints for each machine, ensuring that the
    sequencing constraints are respected.
    """
    for machine in range(data.num_machines):
        sequence = seq_vars[machine]

        if not sequence.is_active:
            # No sequencing constraints found. Skip the creation of (expensive)
            # circuit constraints.
            continue

        assigns = sequence.tasks
        starts = sequence.starts
        ends = sequence.ends
        arc_lits = sequence.arcs
        arcs = []

        for idx1, var1 in enumerate(assigns):
            # Set initial arcs from the dummy node (0) to/from a task.
            start_lit = starts[idx1]
            end_lit = ends[idx1]

            arcs.append([0, idx1 + 1, start_lit])
            arcs.append([idx1 + 1, 0, end_lit])

            # If this task is the first, set rank.
            m.add(var1.rank == 0).OnlyEnforceIf(start_lit)

            # Self arc if the task is not present on this machine.
            arcs.append([idx1 + 1, idx1 + 1, var1.is_present.Not()])
            m.add(var1.rank == -1).OnlyEnforceIf(var1.is_present.Not())

            for idx2, var2 in enumerate(assigns):
                if idx1 == idx2:
                    continue

                arc_lit = arc_lits[idx1, idx2]
                arcs.append([idx1 + 1, idx2 + 1, arc_lit])

                m.add_implication(arc_lit, var1.is_present)
                m.add_implication(arc_lit, var2.is_present)

                # Maintain rank incrementally.
                m.add(var1.rank + 1 == var2.rank).OnlyEnforceIf(arc_lit)

                # TODO Validate that this cannot be combined with overlap.
                op1, op2 = var1.task_idx, var2.task_idx
                setup = data.setup_times[machine][op1, op2]
                m.add(var1.end + setup <= var2.start).OnlyEnforceIf(arc_lit)

        if arcs:
            m.add_circuit(arcs)
