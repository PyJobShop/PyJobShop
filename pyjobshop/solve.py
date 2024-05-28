from typing import Optional

import pyjobshop.ortools
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result

try:
    import pyjobshop.cpoptimizer

    CPOPTIMIZER_AVAILABLE = True
except ModuleNotFoundError:
    CPOPTIMIZER_AVAILABLE = False


def solve(
    data: ProblemData,
    solver: str,
    time_limit: float = float("inf"),
    log: bool = False,
    num_workers: Optional[int] = None,
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
    num_workers
        The number of workers to use for parallel solving. If not
        specified, the default value of the selected solver is used, which
        is typically the maximum number of available CPU cores.

    Returns
    -------
    Result
        A Result object containing the best found solution and additional
        information about the solver run.
    """
    if solver not in ["ortools", "cpoptimizer"]:
        raise ValueError(f"Unknown solver choice: {solver}.")

    args = data, time_limit, log, num_workers

    if solver == "cpoptimizer":
        if not CPOPTIMIZER_AVAILABLE:
            msg = (
                "Using CP Optimizer requires the relevant dependencies to be "
                "installed. You can install those using `pip install "
                "pyjobshop[cpoptimizer]`."
            )
            raise ModuleNotFoundError(msg)

        return pyjobshop.cpoptimizer.solve(*args)

    return pyjobshop.ortools.solve(*args)
