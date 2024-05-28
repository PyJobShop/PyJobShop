from dataclasses import dataclass

from ortools.sat.python.cp_model import CpModel, IntervalVar, IntVar

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
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar
    is_present: IntVar
    rank: IntVar  # the rank of the task on machine


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
            interval=interval_var,
            start=start_var,
            duration=duration_var,
            end=end_var,
            is_present=is_present_var,
            rank=rank_var,
        )

        m.Add(duration_var >= duration)

    return variables
