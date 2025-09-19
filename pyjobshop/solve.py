import textwrap
from importlib.metadata import version
from typing import Any

from ortools.sat.python.cp_model import CpSolverSolutionCallback

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result
from pyjobshop.Solution import Solution
from pyjobshop.solvers.ortools import CPModel as ORToolsModel


def solve(
    data: ProblemData,
    solver: str = "ortools",
    time_limit: float = float("inf"),
    display: bool = False,
    num_workers: int | None = None,
    initial_solution: Solution | None = None,
    callback: object | None = None,
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
    callback
        A suitable callback to use during solving with solver.
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
    if solver not in ["ortools", "cpoptimizer"]:
        raise ValueError(f"Unknown solver choice: {solver}.")

    if display:
        print(f"PyJobShop v{version('pyjobshop')}\n")
        print("Solving an instance with:")
        print(textwrap.indent(str(data), "    ") + "\n")
        print(" START SOLVER LOG ".center(79, "="))

    if solver == "ortools":
        cp_model = ORToolsModel(data)
    else:
        from pyjobshop.solvers.cpoptimizer import (
            CPModel as CPOptimizerModel,
        )

        cp_model = CPOptimizerModel(data)  # type: ignore

    result = cp_model.solve(
        time_limit,
        display,
        num_workers,
        initial_solution,
        callback,
        **kwargs,
    )

    if display:
        print(" END SOLVER LOG ".center(79, "="))

    return result


def solve_model_with_callback(
    cp_model: Any,
    callback: Any,
    time_limit: float = float("inf"),
    display: bool = False,
    num_workers: int | None = None,
    initial_solution: Solution | None = None,
    **kwargs,
) -> Result:
    """
    Solves the given model with a corresponding callback.

    Parameters
    ----------
    cp_model
        The CP model to solve for a corresponding solver.
    callback
        A callback to use during solving with corresponding solver.
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
        If CP Optimizer model is given but its dependencies are not installed.
    """
    if isinstance(cp_model, ORToolsModel):
        if not isinstance(callback, CpSolverSolutionCallback):
            raise ValueError("Use CpSolverSolutionCallback for OR-Tools.")
    else:
        from docplex.cp.solver.cpo_callback import CpoCallback

        from pyjobshop.solvers.cpoptimizer import CPModel as CPOptimizerModel

        if not isinstance(cp_model, CPOptimizerModel):
            raise ValueError(
                "cp_model must be ORToolsModel or CPOptimizerModel."
            )
        if not isinstance(callback, CpoCallback):
            raise ValueError("Use CpoCallback for CP Optimizer.")

    if display:
        print(f"PyJobShop v{version('pyjobshop')}\n")
        print("Solving an instance with:")
        print(textwrap.indent(str(cp_model.data), "    ") + "\n")
        print(" START SOLVER LOG ".center(79, "="))

    result = cp_model.solve(
        time_limit,
        display,
        num_workers,
        initial_solution,
        callback=callback,
        **kwargs,
    )

    if display:
        print(" END SOLVER LOG ".center(79, "="))

    return result
