from itertools import product

import numpy as np
from docplex.cp.expression import CpoExpr, CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

JobVars = list[CpoIntervalVar]
TaskVars = list[CpoIntervalVar]
AssignmentVars = dict[tuple[int, int], CpoIntervalVar]
SeqVars = list[CpoSequenceVar]


def alternative_constraints(
    m: CpoModel,
    data: ProblemData,
    task_vars: TaskVars,
    assign_vars: AssignmentVars,
) -> list[CpoExpr]:
    """
    Creates the alternative constraints for the tasks, ensuring that each
    task is scheduled on exactly one machine.
    """
    constraints = []

    for task in range(data.num_tasks):
        machines = data.task2machines[task]
        optional = [assign_vars[task, machine] for machine in machines]
        constraints.append(m.alternative(task_vars[task], optional))

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


def job_task_constraints(
    m: CpoModel, data: ProblemData, job_vars: JobVars, task_vars: TaskVars
) -> list[CpoExpr]:
    """
    Creates the constraints that ensure that the job variables govern the
    related task variables.
    """
    constraints = []

    for job in range(data.num_jobs):
        job_var = job_vars[job]
        related_task_vars = [task_vars[task] for task in data.job2tasks[job]]

        constraints.append(m.span(job_var, related_task_vars))

        for task_var in related_task_vars:
            constraints.append(
                m.start_of(task_var) >= data.jobs[job].release_date
            )

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
    # are ordered in the same way as the tasks in machine2tasks.
    for machine in range(data.num_machines):
        if data.machines[machine].allow_overlap:
            continue  # Overlap is allowed for this machine.

        if not (tasks := data.machine2tasks[machine]):
            continue  # There no tasks for this machine.

        setups = data.setup_times[machine, :, :][np.ix_(tasks, tasks)]

        if np.all(setups == 0):  # No setup times for this machine.
            constraints.append(m.no_overlap(seq_vars[machine]))
        else:
            constraints.append(m.no_overlap(seq_vars[machine], setups))

    return constraints


def task_constraints(
    m: CpoModel, data: ProblemData, task_vars: TaskVars
) -> list[CpoExpr]:
    """
    Creates constraints on the task variables.
    """
    for task_data, var in zip(data.tasks, task_vars):
        if task_data.earliest_start is not None:
            var.set_start_min(task_data.earliest_start)

        if task_data.latest_start is not None:
            var.set_start_max(task_data.latest_start)

        if task_data.earliest_end is not None:
            var.set_end_min(task_data.earliest_end)

        if task_data.latest_end is not None:
            var.set_end_max(task_data.latest_end)

    return []  # no constraints because we use setters


def planning_horizon_constraints(
    m: CpoModel,
    data: ProblemData,
    job_vars: JobVars,
    assign_vars: AssignmentVars,
    task_vars: TaskVars,
) -> list[CpoExpr]:
    """
    Creates the planning horizon constraints for the interval variables,
    ensuring that the end of each interval is within the planning horizon.
    """
    if data.planning_horizon is None:
        return []  # unbounded planning horizon

    constraints = []

    for vars in [job_vars, assign_vars.values(), task_vars]:
        constraints += [m.end_of(var) <= data.planning_horizon for var in vars]

    return constraints


def processing_time_constraints(
    m: CpoModel, data: ProblemData, assign_vars: AssignmentVars
) -> list[CpoExpr]:
    """
    Creates the processing time constraints for the task variables, ensuring
    that the duration of the task on the machine is the processing time.
    If the task allows for variable duration, the duration could be longer
    than the processing time due to blocking.
    """
    for (task, machine), var in assign_vars.items():
        duration = data.processing_times[machine, task]

        if data.tasks[task].fixed_duration:
            var.set_size(duration)
        else:
            var.set_size_min(duration)  # at least duration

    return []  # no constraints because we use setters


def task_graph_constraints(
    m: CpoModel,
    data: ProblemData,
    task_vars: TaskVars,
    assign_vars: AssignmentVars,
    seq_vars: SeqVars,
) -> list[CpoExpr]:
    constraints = []

    for (idx1, idx2), constraints_ in data.constraints.items():
        task1 = task_vars[idx1]
        task2 = task_vars[idx2]

        for constraint in constraints_:
            if constraint == "start_at_start":
                expr = m.start_at_start(task1, task2)
            elif constraint == "start_at_end":
                expr = m.start_at_end(task1, task2)
            elif constraint == "start_before_start":
                expr = m.start_before_start(task1, task2)
            elif constraint == "start_before_end":
                expr = m.start_before_end(task1, task2)
            elif constraint == "end_at_start":
                expr = m.end_at_start(task1, task2)
            elif constraint == "end_at_end":
                expr = m.end_at_end(task1, task2)
            elif constraint == "end_before_start":
                expr = m.end_before_start(task1, task2)
            elif constraint == "end_before_end":
                expr = m.end_before_end(task1, task2)
            else:
                continue

            constraints.append(expr)

    # Separately handle assignment related constraints for efficiency.
    for machine, tasks in enumerate(data.machine2tasks):
        seq_var = seq_vars[machine]

        for task1, task2 in product(tasks, repeat=2):
            if task1 == task2 or (task1, task2) not in data.constraints:
                continue

            var1 = assign_vars[task1, machine]
            var2 = assign_vars[task2, machine]

            for constraint in data.constraints[task1, task2]:
                if constraint == "previous":
                    expr = m.previous(seq_var, var1, var2)
                elif constraint == "same_unit":
                    expr = m.presence_of(var1) == m.presence_of(var2)
                elif constraint == "different_unit":
                    expr = m.presence_of(var1) != m.presence_of(var2)

                constraints.append(expr)

    return constraints
