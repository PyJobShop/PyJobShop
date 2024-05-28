from typing import Optional

import pyjobshop.cpoptimizer as cpoptimizer
import pyjobshop.ortools as ortools
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result


def solve(
    data: ProblemData,
    solver: str,
    time_limit: Optional[float] = None,
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
        The time limit for the solver in seconds. If not set, the solver will
        run until an optimal solution is found.
    log
        Whether to log the solver output. Default ``False``.

    Returns
    -------
    Result
        The result of the solver run, including the status, runtime, solution,
        and objective value.
    """
    if solver not in ["ortools", "cpoptimizer"]:
        raise ValueError(f"Unknown solver: {solver}.")

    solve_funcs = {"ortools": ortools.solve, "cpoptimizer": cpoptimizer.solve}
    return solve_funcs[solver](data, time_limit, log)
