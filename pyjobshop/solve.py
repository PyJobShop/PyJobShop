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
    if solver not in ["ortools", "cpoptimizer"]:
        raise ValueError(f"Unknown solver choice: {solver}.")

    if solver == "cpoptimizer":
        if not CPOPTIMIZER_AVAILABLE:
            msg = (
                "Using CP Optimizer requires the relevant dependencies to be "
                "installed. You can install those using `pip install "
                "pyjobshop[cpoptimizer]`."
            )
            raise ModuleNotFoundError(msg)

        return pyjobshop.cpoptimizer.solve(data, time_limit, log)

    return pyjobshop.ortools.solve(data, time_limit, log)
