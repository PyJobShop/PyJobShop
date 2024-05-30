from collections import defaultdict
from dataclasses import dataclass

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntervalVar, IntVar

from pyjobshop.ProblemData import ProblemData


@dataclass
class JobVar:
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class OperationVar:
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class AssignmentVar:
    task_idx: int
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar
    is_present: IntVar
    rank: IntVar  # the rank of the task on machine


@dataclass
class SequenceVar:
    """
    Represents a sequence of tasks assigned to a machine.

    Parameters
    ----------
    tasks
        The task variables in the sequence.
    starts
        The start literals for each task.
    ends
        The end literals for each task.
    arcs
        The arc literals between each pair of tasks. Keys are tuples of
        indices.
    """

    tasks: list[AssignmentVar]
    starts: list[BoolVarT]
    ends: list[BoolVarT]
    arcs: dict[tuple[int, int], BoolVarT]


def job_variables(m: CpModel, data: ProblemData) -> list[JobVar]:
    """
    Creates an interval variable for each job.
    """
    jobs = []

    for job in data.jobs:
        name = f"J{job}"
        start_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        duration_var = m.NewIntVar(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.NewIntVar(0, data.planning_horizon, f"{name}_end")
        interval_var = m.NewIntervalVar(
            start_var, duration_var, end_var, f"interval_{job}"
        )
        jobs.append(JobVar(interval_var, start_var, duration_var, end_var))

    return jobs


def operation_variables(m: CpModel, data: ProblemData) -> list[OperationVar]:
    """
    Creates an interval variable for each operation.
    """
    tasks = []

    for op in data.operations:
        name = f"O{op}"
        start_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        duration_var = m.NewIntVar(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.NewIntVar(0, data.planning_horizon, f"{name}_end")
        interval_var = m.NewIntervalVar(
            start_var, duration_var, end_var, f"interval_{op}"
        )
        op_var = OperationVar(interval_var, start_var, duration_var, end_var)
        tasks.append(op_var)

    return tasks


def assignment_variables(
    m: CpModel, data: ProblemData
) -> dict[tuple[int, int], AssignmentVar]:
    """
    Creates an interval variable for each operation and eligible machine pair.
    """
    variables = {}

    for (machine, op), duration in data.processing_times.items():
        name = f"A{op}_{machine}"
        start_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        duration_var = m.NewIntVar(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        is_present_var = m.NewBoolVar(f"{name}_is_present")
        interval_var = m.NewOptionalIntervalVar(
            start_var,
            duration_var,
            end_var,
            is_present_var,
            f"{name}_interval",
        )
        rank_var = m.NewIntVar(-1, data.num_jobs, f"{name}_rank")
        variables[op, machine] = AssignmentVar(
            task_idx=op,
            interval=interval_var,
            start=start_var,
            duration=duration_var,
            end=end_var,
            is_present=is_present_var,
            rank=rank_var,
        )

        m.Add(duration_var >= duration)

    return variables


def sequence_variables(m: CpModel, data: ProblemData, assign):
    variables = []

    tasks_by_machine = defaultdict(list)
    for (_, machine), var in assign.items():
        tasks_by_machine[machine].append(var)

    for machine in range(data.num_machines):
        sequence = tasks_by_machine[machine]
        starts = []
        ends = []
        arcs = {}

        for idx1 in range(len(sequence)):
            start_lit = m.NewBoolVar(f"sequence {machine} pos {idx1} start")
            end_lit = m.NewBoolVar(f"sequence {machine} pos {idx1} end")
            starts.append(start_lit)
            ends.append(end_lit)

            for idx2 in range(len(sequence)):
                lit = m.NewBoolVar(f"sequence {machine} arc {idx1} -> {idx2}")
                arcs[idx1, idx2] = lit

        variables.append(
            SequenceVar(tasks=sequence, starts=starts, ends=ends, arcs=arcs)
        )

    return variables
