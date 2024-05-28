from typing import Optional

from ortools.sat.python.cp_model import CpSolver
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result

from .default_model import default_model
from .result2solution import result2solution


def solve(data: ProblemData, time_limit: Optional[int], log: bool):
    """
    TODO
    """
    ort_model, op_vars, assign_vars = default_model(data)

    cp_solver = CpSolver()

    if time_limit is not None:
        cp_solver.parameters.max_time_in_seconds = time_limit

    status_code = cp_solver.Solve(ort_model)
    status = cp_solver.StatusName(status_code)
    objective = cp_solver.ObjectiveValue()

    print(f"Solve status: {status}")
    print(f"Optimal objective value: {objective}")

    if status != "INFEASIBLE":
        solution = result2solution(data, cp_solver, assign_vars)
    else:
        solution = None

    return Result(
        status.capitalize(),
        cp_solver.WallTime(),
        solution,
        objective,
    )
