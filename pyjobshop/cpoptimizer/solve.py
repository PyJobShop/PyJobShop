from typing import Optional

from docplex.cp.solution import CpoSolveResult

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result

from .default_model import default_model
from .result2solution import result2solution


def solve(data: ProblemData, time_limit: Optional[float], log: bool):
    """
    TODO
    """
    cp_model = default_model(data)

    log_verbosity = "Terse" if log else "Quiet"
    kwargs = {"TimeLimit": time_limit, "LogVerbosity": log_verbosity}
    cp_result: CpoSolveResult = cp_model.solve(**kwargs)  # type: ignore

    solve_status = cp_result.get_solve_status()
    runtime = cp_result.get_solve_time()

    if solve_status == "Infeasible":
        solution = None
        objective_value = None
    else:
        solution = result2solution(data, cp_result)
        objective_value = cp_result.get_objective_value()

    return Result(solve_status, runtime, solution, objective_value)
