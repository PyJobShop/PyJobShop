from typing import Optional

from .Solution import Solution


class Result:
    """
    Solver result class.

    Parameters
    ----------
    solve_status: str
        The solve status.
    solution: Optional[Solution]
        The solution to the problem instance. None if no solution was found.
    objective_value: Optional[float]
        The objective value of the solution. None if no solution was found.
    """

    def __init__(
        self,
        solve_status: str,
        solution: Optional[Solution],
        objective_value: Optional[float],
    ):
        self._solution = solution
        self._status = solve_status
        self._objective_value = objective_value

    @property
    def solution(self) -> Optional[Solution]:
        return self._solution

    @property
    def solve_status(self) -> str:
        return self._status

    @property
    def objective_value(self) -> Optional[float]:
        return self._objective_value
