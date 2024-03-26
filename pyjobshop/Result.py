from typing import Optional

from .Solution import Solution


class Result:
    """
    Solver result class.

    Parameters
    ----------
    solve_status
        The solve status.
    runtime
        The runtime of the solver.
    best
        The best found solution. None if no solution was found.
    objective_value
        The objective value of the solution. None if no solution was found.
    """

    def __init__(
        self,
        solve_status: str,
        runtime: float,
        best: Optional[Solution],
        objective_value: Optional[float],
    ):
        self._solve_status = solve_status
        self._runtime = runtime
        self._best = best
        self._objective_value = objective_value

    @property
    def solve_status(self) -> str:
        return self._solve_status

    @property
    def runtime(self) -> float:
        return self._runtime

    @property
    def best(self) -> Optional[Solution]:
        return self._best

    @property
    def objective_value(self) -> Optional[float]:
        return self._objective_value
