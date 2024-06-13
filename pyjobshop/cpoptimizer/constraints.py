from itertools import product

import numpy as np
from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

JobVars = list[CpoIntervalVar]
TaskVars = list[CpoIntervalVar]
AssignmentVars = dict[tuple[int, int], CpoIntervalVar]
SeqVars = list[CpoSequenceVar]


def job_spans_tasks(
    m: CpoModel, data: ProblemData, job_vars: JobVars, task_vars: TaskVars
):
    """
    Ensures that the job variables span the related task variables.
    """
    for idx, job in enumerate(data.jobs):
        job_var = job_vars[idx]
        related_task_vars = [task_vars[task_idx] for task_idx in job.tasks]

        m.add(m.span(job_var, related_task_vars))


def no_overlap_and_setup_times(
    m: CpoModel, data: ProblemData, seq_vars: SeqVars
):
    """
    Creates the no-overlap constraints for machines, ensuring that no two
    intervals in a sequence variable are overlapping. If setup times are
    available, the setup times are enforced as well.
    """
    # Assumption: the interval variables in the sequence variable
    # are ordered in the same way as the tasks in machine2tasks.
    for machine in range(data.num_machines):
        if data.machines[machine].allow_overlap:
            continue  # Overlap is allowed for this machine.

        if not (tasks := data.machine2tasks[machine]):
            continue  # There no tasks for this machine.

        setups = data.setup_times[machine, :, :][np.ix_(tasks, tasks)]

        if np.all(setups == 0):  # No setup times for this machine.
            m.add(m.no_overlap(seq_vars[machine]))
        else:
            m.add(m.no_overlap(seq_vars[machine], setups))


def select_one_task_alternative(
    m: CpoModel,
    data: ProblemData,
    task_vars: TaskVars,
    assign_vars: AssignmentVars,
):
    """
    Selects one optional (assignment) interval for each task, ensuring that
    each task is scheduled on exactly one machine.
    """
    for task in range(data.num_tasks):
        machines = data.task2machines[task]
        optional = [assign_vars[task, machine] for machine in machines]
        m.add(m.alternative(task_vars[task], optional))


def task_graph(
    m: CpoModel,
    data: ProblemData,
    task_vars: TaskVars,
    assign_vars: AssignmentVars,
    seq_vars: SeqVars,
):
    """
    Creates constraints based on the task graph, ensuring that the
    tasks are scheduled according to the graph.
    """
    for (idx1, idx2), constraints in data.constraints.items():
        task1 = task_vars[idx1]
        task2 = task_vars[idx2]

        for constraint in constraints:
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

            m.add(expr)

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
                elif constraint == "same_machine":
                    expr = m.presence_of(var1) == m.presence_of(var2)
                elif constraint == "different_machine":
                    expr = m.presence_of(var1) != m.presence_of(var2)

                m.add(expr)
