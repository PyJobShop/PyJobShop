from ortools.sat.python.cp_model import (
    Constraint,
    CpModel,
)

from fjsp.ProblemData import ProblemData

from .variables import OperationVar


def makespan(
    model: CpModel, data: ProblemData, ops: list[OperationVar]
) -> Constraint:
    """
    Minimizes the makespan of the schedule.
    """
    makespan = model.NewIntVar(0, 2**25, "makespan")
    completion_times = [ops[op].end for op in range(data.num_operations)]

    model.AddMaxEquality(makespan, completion_times)
    model.Minimize(makespan)
