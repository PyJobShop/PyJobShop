from typing import Optional

from ortools.sat.python.cp_model import CpSolver

from pyjobshop.ortools.variables import TaskAltVar
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
        The number of workers to use for parallel solving. If not set, all
        available CPU cores are used.
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
    cp_model, task_alt_vars = create_model(data, initial_solution)
    cp_solver = CpSolver()

    params = {
        "max_time_in_seconds": time_limit,
        "log_search_progress": log,
        # 0 means using all available CPU cores.
        "num_workers": num_workers if num_workers is not None else 0,
    }
    params.update(kwargs)  # this will override existing parameters!

    for key, value in params.items():
        setattr(cp_solver.parameters, key, value)

    cp_solver.log_callback = print  # TODO how to enable this only in tests?

    status_code = cp_solver.solve(cp_model)
    status = cp_solver.status_name(status_code)
    objective = cp_solver.objective_value

    if status in ["OPTIMAL", "FEASIBLE"]:
        solution = _result2solution(data, cp_solver, task_alt_vars)
    else:
        # No feasible solution found due to infeasible instance or time limit.
        solution = Solution([])
        objective = float("inf")

    return Result(
        _get_solve_status(status),
        cp_solver.wall_time,
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


def _result2solution(
    data: ProblemData,
    cp_solver: CpSolver,
    task_alt_vars: dict[tuple[int, int], TaskAltVar],
) -> Solution:
    """
    Converts a result from the OR-Tools CP solver to a Solution object.

    Parameters
    ----------
    data
        The problem data instance.
    cp_solver
        The CP solver.
    task_alt_vars
        The task alternatives variables.

    Returns
    -------
    Solution
        The solution.
    """
    tasks = {}

    for (task, machine), var in task_alt_vars.items():
        if cp_solver.value(var.is_present):
            start = cp_solver.value(var.start)
            duration = cp_solver.value(var.duration)
            end = cp_solver.value(var.end)
            tasks[task] = TaskData(machine, start, duration, end)

    return Solution([tasks[idx] for idx in range(data.num_tasks)])
