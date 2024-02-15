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
    solution
        The solution to the problem instance. None if no solution was found.
    objective_value
        The objective value of the solution. None if no solution was found.
    """

    def __init__(
        self,
        solve_status: str,
        runtime: float,
        solution: Optional[Solution],
        objective_value: Optional[float],
    ):
        self._solve_status = solve_status
        self._runtime = runtime
        self._solution = solution
        self._objective_value = objective_value

    @property
    def solve_status(self) -> str:
        return self._solve_status

    @property
    def runtime(self) -> float:
        return self._runtime

    @property
    def solution(self) -> Optional[Solution]:
        return self._solution

    @property
    def objective_value(self) -> Optional[float]:
        return self._objective_value
