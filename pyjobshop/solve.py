import pyjobshop.cpoptimizer
import pyjobshop.ortools
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result


def solve(
    data: ProblemData,
    solver: str,
    time_limit: float = float("inf"),
    log: bool = False,
) -> Result:
    """
    Solves the given problem data instance.

    Parameters
    ----------
    data
        The problem data instance.
    solver
        The solver to use. Either "ortools" or "cpoptimizer".
    time_limit
        The time limit for the solver in seconds. Default ``float('inf')``.
    log
        Whether to log the solver output. Default ``False``.

    Returns
    -------
    Result
        The result of the solver run, including the status, runtime, solution,
        and objective value.
    """
    solve_funcs = {
        "ortools": pyjobshop.ortools.solve,
        "cpoptimizer": pyjobshop.cpoptimizer.solve,
    }

    if solver not in solve_funcs:
        raise ValueError(f"Unknown solver choice: {solver}.")

    return solve_funcs[solver](data, time_limit, log)
