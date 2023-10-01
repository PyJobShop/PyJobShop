from dataclasses import dataclass

from ortools.sat.python.cp_model import CpModel, IntervalVar, IntVar

from fjsp.ProblemData import ProblemData

_INT_MAX = 2_147_483_647


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


def operation_variables(m: CpModel, data: ProblemData) -> list[OperationVar]:
    """
    Creates an interval variable for each operation.
    """
    tasks = []

    for op in data.operations:
        name = f"O{op}"
        start_var = m.NewIntVar(0, _INT_MAX, f"{name}_start")
        duration_var = m.NewIntVar(0, _INT_MAX, f"{name}_duration")
        end_var = m.NewIntVar(0, _INT_MAX, f"{name}_end")
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
    Creates an interval variable for each operation.
    """
    variables = {}
    for op, op_data in enumerate(data.operations):
        for machine in op_data.machines:
            name = f"A{op}_{machine}"
            start_var = m.NewIntVar(0, _INT_MAX, f"{name}_start")
            duration_var = m.NewIntVar(0, _INT_MAX, f"{name}_duration")
            end_var = m.NewIntVar(0, _INT_MAX, f"{name}_start")
            is_present_var = m.NewBoolVar(f"{name}_is_present")
            interval_var = m.NewOptionalIntervalVar(
                start_var,
                duration_var,
                end_var,
                is_present_var,
                f"{name}_interval",
            )
            variables[op, machine] = AssignmentVar(
                interval_var, start_var, duration_var, end_var, is_present_var
            )

            m.Add(duration_var >= data.processing_times[op, machine])

    return variables
