from typing import Optional

from pyjobshop.ortools.Solver import Solver as ORToolsSolver
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result
from pyjobshop.Solution import Solution


def solve(
    data: ProblemData,
    solver: str = "ortools",
    time_limit: float = float("inf"),
    display: bool = False,
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
    display
        Whether to display the solver output. Default ``False``.
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
        ortools = ORToolsSolver(data)
        return ortools.solve(
            time_limit,
            display,
            num_workers,
            initial_solution,
            **kwargs,
        )
    elif solver == "cpoptimizer":
        from pyjobshop.cpoptimizer.Solver import Solver as CPOptimizerSolver

        cpoptimizer = CPOptimizerSolver(data)
        return cpoptimizer.solve(
            time_limit,
            display,
            num_workers,
            initial_solution,
            **kwargs,
        )
    else:
        raise ValueError(f"Unknown solver choice: {solver}.")
