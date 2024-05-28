from collections import defaultdict
from itertools import product

import numpy as np
from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .variables import AssignmentVar, JobVar, OperationVar

JobVars = list[JobVar]
OperationVars = list[OperationVar]
AssignmentVars = dict[tuple[int, int], AssignmentVar]


def job_data_constraints(m: CpModel, data: ProblemData, job_vars: JobVars):
    """
    Creates the constraints that ensure that the job variables are consistent
    with the job data.
    """
    for job_data, job_var in zip(data.jobs, job_vars):
        m.Add(job_var.start >= job_data.release_date)

        if job_data.deadline is not None:
            m.Add(job_var.end <= job_data.deadline)


def job_operation_constraints(
    m: CpModel, data: ProblemData, job_vars: JobVars, op_vars: OperationVars
):
    """
    Creates the constraints that ensure that the job variables govern the
    related operation variables.
    """
    for job in range(data.num_jobs):
        job_var = job_vars[job]
        related_op_vars = [op_vars[op] for op in data.job2ops[job]]

        m.AddMinEquality(job_var.start, [var.start for var in related_op_vars])
        m.AddMaxEquality(job_var.end, [var.end for var in related_op_vars])

        for var in related_op_vars:
            m.Add(var.start >= data.jobs[job].release_date)


def operation_constraints(
    m: CpModel, data: ProblemData, op_vars: OperationVars
):
    """
    Creates constraints on the operation variables.
    """
    for op_data, var in zip(data.operations, op_vars):
        if op_data.earliest_start is not None:
            m.Add(var.start >= op_data.earliest_start)

        if op_data.latest_start is not None:
            m.Add(var.start <= op_data.latest_start)

        if op_data.earliest_end is not None:
            m.Add(var.end >= op_data.earliest_end)

        if op_data.latest_end is not None:
            m.Add(var.end <= op_data.latest_end)


def operation_graph_constraints(
    m: CpModel,
    data: ProblemData,
    op_vars: OperationVars,
    assign: AssignmentVars,
):
    for (idx1, idx2), op_constraints in data.constraints.items():
        op_var1 = op_vars[idx1]
        op_var2 = op_vars[idx2]

        for prec_type in op_constraints:
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

            m.Add(expr)

    # Separately handle assignment related constraints for efficiency.
    for machine, ops in enumerate(data.machine2ops):
        for op1, op2 in product(ops, repeat=2):
            if op1 == op2 or (op1, op2) not in data.constraints:
                continue

            var1 = assign[op1, machine]
            var2 = assign[op2, machine]

            for constraint in data.constraints[op1, op2]:
                if constraint == "previous":
                    raise NotImplementedError
                elif constraint == "same_unit":
                    expr = var1.is_present == var2.is_present
                elif constraint == "different_unit":
                    expr = var1.is_present != var2.is_present

                m.Add(expr)


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
            m.Add(main.start == assign.start).OnlyEnforceIf(is_present)
            m.Add(main.duration == assign.duration).OnlyEnforceIf(is_present)
            m.Add(main.end == assign.end).OnlyEnforceIf(is_present)

        # Select exactly one machine for the operation.
        m.AddExactlyOne(presences)


def no_overlap_constraints(
    m: CpModel, data: ProblemData, assign: AssignmentVars
):
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    sequences = defaultdict(list)
    for (_, machine), var in assign.items():
        sequences[machine].append(var)

    for machine in range(data.num_machines):
        if not data.machines[machine].allow_overlap:
            m.AddNoOverlap([var.interval for var in sequences[machine]])


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
            m.Add(var.duration == duration)
        else:
            m.Add(var.duration >= duration)


def setup_times_constraints(
    m: CpModel, data: ProblemData, assign: AssignmentVars
):
    """
    Creates the setup time constraints for each machine, ensuring that the
    setup times are respected.

    The implementation is based on the following example:
    https://github.com/google/or-tools/blob/d4f9b8/examples/contrib/scheduling_with_transitions_sat.py
    """
    sequences = defaultdict(list)
    op_idcs = defaultdict(list)
    for (op, machine), var in assign.items():
        sequences[machine].append(var)
        op_idcs[machine].append(op)

    for machine in range(data.num_machines):
        arcs = []
        sequence = sequences[machine]
        setup_times = data.setup_times[machine]

        if np.all(setup_times == 0):
            continue

        for idx1, var1 in enumerate(sequence):
            # Set initial arcs from the dummy node (0) to/from a task.
            start_lit = m.NewBoolVar("")
            end_lit = m.NewBoolVar("")

            arcs.append([0, idx1 + 1, start_lit])
            arcs.append([idx1 + 1, 0, end_lit])

            # If this task is the first, set rank.
            m.Add(var1.rank == 0).OnlyEnforceIf(start_lit)

            # If this task is the first, set start.
            # TODO Do we want to set this? Not when the earliest start is
            # defined or the release date.
            # m.Add(var1.start == 0).OnlyEnforceIf(start_lit)

            # Self arc if the task is not present on this machine.
            arcs.append([idx1 + 1, idx1 + 1, var1.is_present.Not()])
            m.Add(var1.rank == -1).OnlyEnforceIf(var1.is_present.Not())

            for idx2, var2 in enumerate(sequence):
                if idx1 == idx2:
                    continue

                lit = m.NewBoolVar(f"{idx1} -> {idx2}")
                arcs.append([idx1 + 1, idx2 + 1, lit])

                m.AddImplication(lit, var1.is_present)
                m.AddImplication(lit, var2.is_present)

                # Maintain rank incrementally.
                m.Add(var1.rank + 1 == var2.rank).OnlyEnforceIf(lit)

                # TODO This automatically enforces classic start -> end
                # precedence constraints and also does not allow for overlap.
                # We need to validate this to catch it.
                op1 = op_idcs[machine][idx1]
                op2 = op_idcs[machine][idx2]
                setup = setup_times[op1, op2]
                m.Add(var1.end + setup <= var2.start).OnlyEnforceIf(lit)

        if arcs:
            m.AddCircuit(arcs)
