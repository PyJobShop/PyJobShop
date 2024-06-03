from ortools.sat.python.cp_model import (
    Constraint,
    CpModel,
)

from pyjobshop.ProblemData import ProblemData

from .variables import OperationVar


def makespan(
    model: CpModel, data: ProblemData, ops: list[OperationVar]
) -> Constraint:
    """
    Minimizes the makespan of the schedule.
    """
    makespan = model.new_int_var(0, data.planning_horizon, "makespan")
    completion_times = [ops[op].end for op in range(data.num_operations)]

    model.add_max_equality(makespan, completion_times)
    model.minimize(makespan)
