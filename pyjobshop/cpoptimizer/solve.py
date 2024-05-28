from typing import Optional

from docplex.cp.solution import CpoSolveResult

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution

from .default_model import default_model
from .result2solution import result2solution


def solve(
    data: ProblemData,
    time_limit: float,
    log: bool,
    num_workers: Optional[int] = None,
):
    """
    Solves the given problem data instance with IBM ILOG CP Optimizer.

    Parameters
    ----------
    data
        The problem data instance.
    time_limit
        The time limit for the solver in seconds.
    log
        Whether to log the solver output.
    num_workers
        The number of workers to use for parallel solving. If not set, the
        maximum number of available CPU cores is used.

    Returns
    -------
    Result
        A Result object containing the best found solution and additional
        information about the solver run.
    """
    cp_model = default_model(data)

    log_verbosity = "Terse" if log else "Quiet"
    params = {
        "TimeLimit": time_limit,
        "LogVerbosity": log_verbosity,
        "Workers": num_workers if num_workers is not None else "Auto",
    }
    cp_result: CpoSolveResult = cp_model.solve(**params)  # type: ignore
    status = cp_result.get_solve_status()

    if status in ["Optimal", "Feasible"]:
        solution = result2solution(data, cp_result)
        objective: float = cp_result.get_objective_value()  # type: ignore
    else:
        # No feasible solution found due to infeasible instance or time limit.
        solution = Solution(data, [])
        objective = float("inf")

    return Result(
        _get_solve_status(status),
        cp_result.get_solve_time(),
        solution,
        objective,
    )


def _get_solve_status(status):
    if status == "Optimal":
        return SolveStatus.OPTIMAL
    elif status == "Feasible":
        return SolveStatus.FEASIBLE
    elif status == "Infeasible":
        return SolveStatus.INFEASIBLE
    else:
        return SolveStatus.TIME_LIMIT
