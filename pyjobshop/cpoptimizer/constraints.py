import numpy as np
from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

JobVars = list[CpoIntervalVar]
TaskVars = list[CpoIntervalVar]
TaskAltVars = dict[tuple[int, int], CpoIntervalVar]
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
    task_alt_vars: TaskAltVars,
):
    """
    Selects one optional interval for each task alternative, ensuring that
    each task is scheduled on exactly one machine.
    """
    for task in range(data.num_tasks):
        machines = data.task2machines[task]
        optional = [task_alt_vars[task, machine] for machine in machines]
        m.add(m.alternative(task_vars[task], optional))


def task_graph(
    m: CpoModel,
    data: ProblemData,
    task_vars: TaskVars,
):
    """
    Creates constraints based on the task graph for task variables.
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


def task_alt_graph(
    m: CpoModel,
    data: ProblemData,
    task_alt_vars: TaskAltVars,
    seq_vars: SeqVars,
):
    """
    Creates constraints based on the task graph which involve task
    alternative variables.
    """
    relevant_constraints = {
        "previous",
        "before",
        "same_machine",
        "different_machine",
    }
    for (task1, task2), constraints in data.constraints.items():
        task_alt_constraints = set(constraints) & relevant_constraints
        if not task_alt_constraints:
            continue

        # Find the common machines for both tasks, because the constraints
        # apply to the task alternative variables on the same machine.
        machines1 = data.task2machines[task1]
        machines2 = data.task2machines[task2]
        machines = set(machines1) & set(machines2)

        for machine in machines:
            seq_var = seq_vars[machine]
            var1 = task_alt_vars[task1, machine]
            var2 = task_alt_vars[task2, machine]

            for constraint in task_alt_constraints:
                if constraint == "previous":
                    expr = m.previous(seq_var, var1, var2)
                elif constraint == "before":
                    expr = m.before(seq_var, var1, var2)
                elif constraint == "same_machine":
                    expr = m.presence_of(var1) == m.presence_of(var2)
                elif constraint == "different_machine":
                    expr = m.presence_of(var1) != m.presence_of(var2)

                m.add(expr)
