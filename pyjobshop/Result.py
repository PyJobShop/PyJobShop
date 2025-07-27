from dataclasses import dataclass
from enum import Enum

from .Solution import Solution


class SolveStatus(Enum):
    """
    Enum representing the termination status of the solver run.
    """

    OPTIMAL = "Optimal"  #: Solution is proven optimal.
    FEASIBLE = "Feasible"  #: A feasible solution was found.
    INFEASIBLE = "Infeasible"  #: Problem is proven infeasible.
    TIME_LIMIT = "Time-limit"  #: Solver terminated due to time limit.
    UNKNOWN = "Unknown"  #: Solver terminated with unknown status.


@dataclass
class Result:
    """
    Result class that stores information about the solver run.

    Parameters
    ----------
    objective
        The objective value of the solution. If no solution was found, this
        should be set to ``float('inf')``.
    lower_bound
        The lower bound of the objective function.
    status
        The termination status of the solver run.
    runtime
        The runtime of the solver.
    best
        The best found solution. If no solution was found, this should be a
        dummy solution.
    """

    objective: float
    lower_bound: float
    status: SolveStatus
    runtime: float
    best: Solution

    def __str__(self):
        content = [
            "Solution results",
            "================",
            f"  objective: {self.objective:.2f}",
            f"lower bound: {self.lower_bound:.2f}",
            f"     status: {self.status.value}",
            f"    runtime: {self.runtime:.2f} seconds",
        ]
        return "\n".join(content)
