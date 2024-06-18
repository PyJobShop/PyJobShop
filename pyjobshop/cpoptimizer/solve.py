from typing import Optional

from docplex.cp.solution import CpoSolveResult

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution, TaskData

from .create_model import create_model


def solve(
    data: ProblemData,
    time_limit: float,
    log: bool,
    num_workers: Optional[int] = None,
    initial_solution: Optional[Solution] = None,
    **kwargs,
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
    initial_solution
        An initial solution to start the solver from. Default is no solution.
    kwargs
        Additional parameters passed to the solver.

    Returns
    -------
    Result
        A Result object containing the best found solution and additional
        information about the solver run.
    """
    cp_model = create_model(data)

    params = {
        "TimeLimit": time_limit,
        "LogVerbosity": "Terse" if log else "Quiet",
        "Workers": num_workers if num_workers is not None else "Auto",
    }
    params.update(kwargs)  # this will override existing parameters!

    cp_result: CpoSolveResult = cp_model.solve(**params)  # type: ignore
    status = cp_result.get_solve_status()

    if status in ["Optimal", "Feasible"]:
        solution = _result2solution(data, cp_result)
        objective: float = cp_result.get_objective_value()  # type: ignore
    else:
        # No feasible solution found due to infeasible instance or time limit.
        solution = Solution([])
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


def _result2solution(data: ProblemData, result: CpoSolveResult) -> Solution:
    """
    Converts an CpoSolveResult object to a solution.
    """
    tasks = {}

    for var in result.get_all_var_solutions():  # type: ignore
        name = var.get_name()

        # Scheduled tasks are inferred from variables start with an "A"
        # (assignment) and that are present in the solution.
        if name.startswith("A") and var.is_present():
            task, machine = [int(num) for num in name[1:].split("_")]
            start = var.start
            duration = var.size
            end = var.end
            tasks[task] = TaskData(machine, start, duration, end)

    return Solution([tasks[idx] for idx in range(data.num_tasks)])
