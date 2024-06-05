from itertools import product

import numpy as np
from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData

from .variables import AssignmentVar, JobVar, SequenceVar, TaskVar

JobVars = list[JobVar]
TaskVars = list[TaskVar]
AssignmentVars = dict[tuple[int, int], AssignmentVar]
SequenceVars = list[SequenceVar]


def job_task_constraints(
    m: CpModel, data: ProblemData, job_vars: JobVars, task_vars: TaskVars
):
    """
    Creates the constraints that ensure that the job variables govern the
    related task variables.
    """
    for job in range(data.num_jobs):
        job_var = job_vars[job]
        related_vars = [task_vars[task] for task in data.job2tasks[job]]

        m.add_min_equality(job_var.start, [var.start for var in related_vars])
        m.add_max_equality(job_var.end, [var.end for var in related_vars])

        for var in related_vars:
            m.add(var.start >= data.jobs[job].release_date)


def task_graph(
    m: CpModel,
    data: ProblemData,
    task_vars: TaskVars,
    assign_vars: AssignmentVars,
    seq_vars: SequenceVars,
):
    """
    Creates constraints based on the task graph, ensuring that the
    tasks are scheduled according to the graph.
    """
    for (idx1, idx2), constraints in data.constraints.items():
        task_var1 = task_vars[idx1]
        task_var2 = task_vars[idx2]

        for prec_type in constraints:
            if prec_type == "start_at_start":
                expr = task_var1.start == task_var2.start
            elif prec_type == "start_at_end":
                expr = task_var1.start == task_var2.end
            elif prec_type == "start_before_start":
                expr = task_var1.start <= task_var2.start
            elif prec_type == "start_before_end":
                expr = task_var1.start <= task_var2.end
            elif prec_type == "end_at_start":
                expr = task_var1.end == task_var2.start
            elif prec_type == "end_at_end":
                expr = task_var1.end == task_var2.end
            elif prec_type == "end_before_start":
                expr = task_var1.end <= task_var2.start
            elif prec_type == "end_before_end":
                expr = task_var1.end <= task_var2.end
            else:
                continue

            m.add(expr)

    # Separately handle assignment related constraints for efficiency.
    for machine, tasks in enumerate(data.machine2tasks):
        for task1, task2 in product(tasks, repeat=2):
            if task1 == task2 or (task1, task2) not in data.constraints:
                continue

            sequence = seq_vars[machine]
            var1 = assign_vars[task1, machine]
            var2 = assign_vars[task2, machine]

            for constraint in data.constraints[task1, task2]:
                if constraint == "previous":
                    sequence.activate()

                    rank1 = sequence.tasks.index(var1)
                    rank2 = sequence.tasks.index(var2)
                    arc_lit = sequence.arcs[rank1, rank2]

                    # Equivalent: arc_lit <=> var1.is_present & var2.is_present
                    m.add_bool_or(
                        [arc_lit, ~var1.is_present, ~var2.is_present]
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
    task_vars: TaskVars,
    assign_vars: AssignmentVars,
):
    """
    Creates the alternative constraints for the tasks, ensuring that each
    task is scheduled on exactly one machine.
    """
    for task in range(data.num_tasks):
        presences = []

        for machine in data.task2machines[task]:
            main = task_vars[task]
            assign = assign_vars[task, machine]
            is_present = assign.is_present
            presences.append(is_present)

            # Link each optional interval variable with the main variable.
            m.add(main.start == assign.start).only_enforce_if(is_present)
            m.add(main.duration == assign.duration).only_enforce_if(is_present)
            m.add(main.end == assign.end).only_enforce_if(is_present)

        # Select exactly one machine for the task.
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
    m: CpModel, data: ProblemData, assign_vars: AssignmentVars
):
    """
    Creates the processing time constraints for the task variables, ensuring
    that the duration of the task on the machine is the processing time.
    If the task allows for variable duration, the duration could be longer
    than the processing time due to blocking.
    """
    for (task, machine), var in assign_vars.items():
        duration = data.processing_times[machine, task]

        if data.tasks[task].fixed_duration:
            m.add(var.duration == duration)
        else:
            m.add(var.duration >= duration)


def setup_time_constraints(
    m: CpModel, data: ProblemData, seq_vars: SequenceVars
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


def circuit_constraints(m: CpModel, data: ProblemData, seq_vars: SequenceVars):
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

        assign_vars = sequence.tasks
        starts = sequence.starts
        ends = sequence.ends
        arc_lits = sequence.arcs
        arcs = []

        for idx1, var1 in enumerate(assign_vars):
            # Set initial arcs from the dummy node (0) to/from a task.
            start_lit = starts[idx1]
            end_lit = ends[idx1]

            arcs.append([0, idx1 + 1, start_lit])
            arcs.append([idx1 + 1, 0, end_lit])

            # If this task is the first, set rank.
            m.add(var1.rank == 0).only_enforce_if(start_lit)

            # Self arc if the task is not present on this machine.
            arcs.append([idx1 + 1, idx1 + 1, ~var1.is_present])
            m.add(var1.rank == -1).only_enforce_if(~var1.is_present)

            for idx2, var2 in enumerate(assign_vars):
                if idx1 == idx2:
                    continue

                arc_lit = arc_lits[idx1, idx2]
                arcs.append([idx1 + 1, idx2 + 1, arc_lit])

                m.add_implication(arc_lit, var1.is_present)
                m.add_implication(arc_lit, var2.is_present)

                # Maintain rank incrementally.
                m.add(var1.rank + 1 == var2.rank).only_enforce_if(arc_lit)

                # TODO Validate that this cannot be combined with overlap.
                task1, task2 = var1.task_idx, var2.task_idx
                setup = data.setup_times[machine][task1, task2]
                m.add(var1.end + setup <= var2.start).only_enforce_if(arc_lit)

        if arcs:
            m.add_circuit(arcs)
