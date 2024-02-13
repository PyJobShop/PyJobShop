import sys
from itertools import product

import numpy as np
from docplex.cp.expression import CpoExpr, CpoIntervalVar, CpoSequenceVar
from docplex.cp.function import CpoStepFunction
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

JobVars = list[CpoIntervalVar]
OpVars = list[CpoIntervalVar]
TaskVars = dict[tuple[int, int], CpoIntervalVar]
SeqVars = list[CpoSequenceVar]

_INT_MAX = sys.maxsize


def alternative_constraints(
    m: CpoModel, data: ProblemData, op_vars: OpVars, task_vars: TaskVars
) -> list[CpoExpr]:
    """
    Creates the alternative constraints for the operations, ensuring that each
    operation is scheduled on exactly one machine.
    """
    constraints = []

    for op in range(data.num_operations):
        machines = data.op2machines[op]
        optional = [task_vars[op, machine] for machine in machines]
        constraints.append(m.alternative(op_vars[op], optional))

    return constraints


def assignment_precedence_constraints(
    m: CpoModel, data: ProblemData, task_vars: TaskVars, seq_vars: SeqVars
) -> list[CpoExpr]:
    constraints = []

    for machine, ops in enumerate(data.machine2ops):
        seq_var = seq_vars[machine]

        for op1, op2 in product(ops, repeat=2):
            if op1 == op2 or (op1, op2) not in data.assignment_precedences:
                continue

            var1 = task_vars[op1, machine]
            var2 = task_vars[op2, machine]

            for prec_type in data.assignment_precedences[op1, op2]:
                if prec_type == "previous":
                    expr = m.previous(seq_var, var1, var2)
                elif prec_type == "same_unit":
                    expr = m.presence_of(var1) == m.presence_of(var2)
                elif prec_type == "different_unit":
                    expr = m.presence_of(var1) != m.presence_of(var2)
                else:
                    raise ValueError(f"Unknown precedence type: {prec_type}")

                constraints.append(expr)

    return constraints


def job_data_constraints(
    m: CpoModel, data: ProblemData, job_vars: JobVars
) -> list[CpoExpr]:
    """
    Creates constraints related to the job data.
    """
    constraints = []

    for job_data, job_var in zip(data.jobs, job_vars):
        constraints.append(m.start_of(job_var) >= job_data.release_date)

        if job_data.deadline is not None:
            constraints.append(m.end_of(job_var) <= job_data.deadline)

    return constraints


def job_operation_constraints(
    m: CpoModel, data: ProblemData, job_vars: JobVars, op_vars: OpVars
) -> list[CpoExpr]:
    """
    Creates the constraints that ensure that the job variables govern the
    related operation variables.
    """
    constraints = []

    for job in range(data.num_jobs):
        job_var = job_vars[job]
        related_op_vars = [op_vars[op] for op in data.job2ops[job]]

        constraints.append(m.span(job_var, related_op_vars))

        for op_var in related_op_vars:
            constraints.append(
                m.start_of(op_var) >= data.jobs[job].release_date
            )

    return constraints


def machine_data_constraints(
    m: CpoModel, data: ProblemData, task_vars: TaskVars
) -> list[CpoExpr]:
    """
    Creates constraints related to the machine data.
    """
    constraints = []

    for (_, machine), var in task_vars.items():
        machine_data = data.machines[machine]

        for start, end in machine_data.downtimes:
            step = CpoStepFunction()
            step.set_value(0, _INT_MAX, 1)
            step.set_value(start, end, 0)

            constraints.append(m.forbid_extent(var, step))

    return constraints


def no_overlap_and_setup_time_constraints(
    m: CpoModel, data: ProblemData, seq_vars: SeqVars
) -> list[CpoExpr]:
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping.
    """
    constraints = []

    # Assumption: the interval variables in the sequence variable
    # are ordered in the same way as the operations in machine2ops.
    for machine in range(data.num_machines):
        if data.machines[machine].allow_overlap:
            continue  # Overlap is allowed for this machine.

        if not (ops := data.machine2ops[machine]):
            continue  # There no operations for this machine.

        setups = data.setup_times[machine, :, :][np.ix_(ops, ops)]

        if np.all(setups == 0):  # No setup times for this machine.
            constraints.append(m.no_overlap(seq_vars[machine]))
        else:
            constraints.append(m.no_overlap(seq_vars[machine], setups))

    return constraints


def operation_constraints(
    m: CpoModel, data: ProblemData, op_vars: OpVars
) -> list[CpoExpr]:
    """
    Creates constraints on the operation variables.
    """
    for op_data, var in zip(data.operations, op_vars):
        if op_data.earliest_start is not None:
            var.set_start_min(op_data.earliest_start)

        if op_data.latest_start is not None:
            var.set_start_max(op_data.latest_start)

        if op_data.earliest_end is not None:
            var.set_end_min(op_data.earliest_end)

        if op_data.latest_end is not None:
            var.set_end_max(op_data.latest_end)

    return []  # no constraints because we use setters


def optional_operation_selection_constraints(
    m: CpoModel, data: ProblemData, op_vars: OpVars
) -> list[CpoExpr]:
    """
    Creates the process plan selection constraints. These constraints
    ensure that for process plan, exactly one operation list is selected
    and all operations in that list are set to present.
    """
    constraints = []

    for plan in data.process_plans:
        presence_by_plan = []

        for operations in plan:
            presence = [m.presence_of(op_vars[idx]) for idx in operations]
            presence_by_plan.append(m.logical_and(presence))

            # Presence of operation intervals is the same for all operations
            # within one process plan option.
            for idx in range(len(operations) - 1):
                constraints.append(presence[idx] == presence[idx + 1])

        # Select exactly one group per process plan.
        constraints.append(m.sum(presence_by_plan) == 1)

    return constraints


def planning_horizon_constraints(
    m: CpoModel,
    data: ProblemData,
    job_vars: JobVars,
    task_vars: TaskVars,
    op_vars: OpVars,
) -> list[CpoExpr]:
    """
    Creates the planning horizon constraints for the interval variables,
    ensuring that the end of each interval is within the planning horizon.
    """
    if data.planning_horizon is None:
        return []  # unbounded planning horizon

    constraints = []

    for vars in [job_vars, task_vars.values(), op_vars]:
        constraints += [m.end_of(var) <= data.planning_horizon for var in vars]

    return constraints


def processing_time_constraints(
    m: CpoModel, data: ProblemData, task_vars: TaskVars
) -> list[CpoExpr]:
    """
    Creates the processing time constraints for the task variables, ensuring
    that the duration of the operation on the machine is the processing time.
    If the operation allows for variable duration, the duration could be longer
    than the processing time due to blocking.
    """
    for (op, machine), var in task_vars.items():
        duration = data.processing_times[machine, op]

        if data.operations[op].fixed_duration:
            var.set_size(duration)
        else:
            var.set_size_min(duration)  # at least duration

    return []  # no constraints because we use setters


def timing_precedence_constraints(
    m: CpoModel, data: ProblemData, op_vars: OpVars
) -> list[CpoExpr]:
    constraints = []

    for (idx1, idx2), precedences in data.timing_precedences.items():
        op1 = op_vars[idx1]
        op2 = op_vars[idx2]

        for prec_type, delay in precedences:
            if prec_type == "start_at_start":
                expr = m.start_at_start(op1, op2, delay)
            elif prec_type == "start_at_end":
                expr = m.start_at_end(op1, op2, delay)
            elif prec_type == "start_before_start":
                expr = m.start_before_start(op1, op2, delay)
            elif prec_type == "start_before_end":
                expr = m.start_before_end(op1, op2, delay)
            elif prec_type == "end_at_start":
                expr = m.end_at_start(op1, op2, delay)
            elif prec_type == "end_at_end":
                expr = m.end_at_end(op1, op2, delay)
            elif prec_type == "end_before_start":
                expr = m.end_before_start(op1, op2, delay)
            elif prec_type == "end_before_end":
                expr = m.end_before_end(op1, op2, delay)
            else:
                raise ValueError(f"Unknown precedence type: {prec_type}")

            constraints.append(expr)

    return constraints
