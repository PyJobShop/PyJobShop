from typing import Optional

import pyjobshop.ortools
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result
from pyjobshop.Solution import Solution

try:
    import pyjobshop.cpoptimizer

    CPOPTIMIZER_AVAILABLE = True
except ModuleNotFoundError:
    CPOPTIMIZER_AVAILABLE = False


def solve(
    data: ProblemData,
    solver: str = "ortools",
    time_limit: float = float("inf"),
    log: bool = False,
    num_workers: Optional[int] = None,
    initial_solution: Optional[Solution] = None,
    **kwargs,
) -> Result:
    """
    Solves the given problem data instance.

    Parameters
    ----------
    data
        The problem data instance.
    solver
        The solver to use. Either ``'ortools'`` (default) or ``'cpoptimizer'``.
    time_limit
        The time limit for the solver in seconds. Default ``float('inf')``.
    log
        Whether to log the solver output. Default ``False``.
    num_workers
        The number of workers to use for parallel solving. If not specified,
        the default of the selected solver is used, which is typically the
        number of available CPU cores.
    initial_solution
        An initial solution to start the solver from. Default is no solution.
    kwargs
        Additional parameters passed to the solver.

    Returns
    -------
    Result
        A Result object containing the best found solution and additional
        information about the solver run.

    Raises
    ------
    ModuleNotFoundError
        If CP Optimizer is chosen but its dependencies are not installed.
    """
    if solver == "ortools":
        return pyjobshop.ortools.solve(
            data, time_limit, log, num_workers, initial_solution, **kwargs
        )
    elif solver == "cpoptimizer" and CPOPTIMIZER_AVAILABLE:
        return pyjobshop.cpoptimizer.solve(
            data, time_limit, log, num_workers, initial_solution, **kwargs
        )
    elif solver == "cpoptimizer" and not CPOPTIMIZER_AVAILABLE:
        msg = (
            "Using CP Optimizer requires the relevant dependencies to be "
            "installed. You can install those using `pip install "
            "pyjobshop[cpoptimizer]`."
        )
        raise ModuleNotFoundError(msg)
    else:
        raise ValueError(f"Unknown solver choice: {solver}.")
