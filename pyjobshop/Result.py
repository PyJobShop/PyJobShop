from dataclasses import dataclass
from enum import Enum

from .Solution import Solution


class SolveStatus(str, Enum):
    OPTIMAL = "Optimal"
    FEASIBLE = "Feasible"
    INFEASIBLE = "Infeasible"
    TIME_LIMIT = "Time-limit"


@dataclass
class Result:
    """
    Result class that stores information about the solver run.

    Parameters
    ----------
    status
        The status of the solver run.
    runtime
        The runtime of the solver.
    best
        The best-found solution. If no solution was found, this is an dummy
        solution.
    objective
        The objective value of the solution. If no solution was found, this is
        set to ``float('inf')``.
    """

    status: SolveStatus
    runtime: float
    best: Solution
    objective: float
