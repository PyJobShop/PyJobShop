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
    # TODO change
    obj_var = model.NewIntVar(0, 2**25, "makespan")
    completion_times = [ops[op].end for op in range(data.num_operations)]
    return model.AddMaxEquality(obj_var, completion_times)
