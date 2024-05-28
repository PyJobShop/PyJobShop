from typing import Optional

from ortools.sat.python.cp_model import CpSolver

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
) -> Result:
    """
    Solves the given problem data instance with Google OR-Tools.

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
    cp_model, _, assign_vars = default_model(data)

    cp_solver = CpSolver()
    cp_solver.parameters.max_time_in_seconds = time_limit
    cp_solver.parameters.log_search_progress = log

    if num_workers is not None:
        cp_solver.parameters.num_workers = num_workers

    status_code = cp_solver.Solve(cp_model)
    status = cp_solver.StatusName(status_code)
    objective = cp_solver.ObjectiveValue()

    if status in ["OPTIMAL", "FEASIBLE"]:
        solution = result2solution(data, cp_solver, assign_vars)
    else:
        # No feasible solution found due to infeasible instance or time limit.
        solution = Solution(data, [])
        objective = float("inf")

    return Result(
        _get_solve_status(status),
        cp_solver.WallTime(),
        solution,
        objective,
    )


def _get_solve_status(status):
    if status == "OPTIMAL":
        return SolveStatus.OPTIMAL
    elif status == "FEASIBLE":
        return SolveStatus.FEASIBLE
    elif status == "INFEASIBLE":
        return SolveStatus.INFEASIBLE
    else:
        return SolveStatus.TIME_LIMIT
