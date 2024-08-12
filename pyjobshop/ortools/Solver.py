from typing import Optional

from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
)

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution, TaskData

from .ConstraintsManager import ConstraintsManager
from .ObjectiveManager import ObjectiveManager
from .VariablesManager import VariablesManager


class Solver:
    """
    Wrapper around the OR-Tools CP model.

    Parameters
    ----------
    data
        The problem data instance.
    """

    def __init__(self, data: ProblemData):
        self._data = data

        self._model = CpModel()
        self._vars = VariablesManager(self._model, data)
        self._constraints = ConstraintsManager(self._model, data, self._vars)
        self._objective = ObjectiveManager(self._model, data, self._vars)

    def _get_solve_status(self, status: str):
        if status == "OPTIMAL":
            return SolveStatus.OPTIMAL
        elif status == "FEASIBLE":
            return SolveStatus.FEASIBLE
        elif status == "INFEASIBLE":
            return SolveStatus.INFEASIBLE
        elif status == "MODEL_INVALID":
            return SolveStatus.UNKNOWN
        else:
            return SolveStatus.TIME_LIMIT

    def _convert_to_solution(self, cp_solver: CpSolver) -> Solution:
        """
        Converts a result from the OR-Tools CP solver to a Solution object.
        """
        tasks = {}

        for idx, var in enumerate(self._vars.mode_vars):
            if cp_solver.value(var.is_present):
                start = cp_solver.value(var.start)
                duration = cp_solver.value(var.duration)
                end = cp_solver.value(var.end)
                mode = self._data.modes[idx]
                tasks[mode.task] = TaskData(mode.machine, start, duration, end)

        return Solution([tasks[idx] for idx in range(self._data.num_tasks)])

    def solve(
        self,
        time_limit: float = float("inf"),
        display: bool = False,
        num_workers: Optional[int] = None,
        initial_solution: Optional[Solution] = None,
        **kwargs,
    ) -> Result:
        """
        Solves the given problem data instance with Google OR-Tools.

        Parameters
        ----------
        time_limit
            The time limit for the solver in seconds.
        display
            Whether to display the solver output. Default ``False``.
        num_workers
            The number of workers to use for parallel solving. If not set, all
            available CPU cores are used.
        initial_solution
            Initial solution to start the solver from. Default is no solution.
        kwargs
            Additional parameters passed to the solver.

        Returns
        -------
        Result
            A Result object containing the best found solution and additional
            information about the solver run.
        """
        if initial_solution is not None:
            self._vars.warmstart(initial_solution)

        self._constraints.add_all_constraints()
        self._objective.set_objective(self._data.objective)

        params = {
            "max_time_in_seconds": time_limit,
            "log_search_progress": display,
            # 0 means using all available CPU cores.
            "num_workers": num_workers if num_workers is not None else 0,
        }
        params.update(kwargs)  # this will override existing parameters!

        cp_solver = CpSolver()
        for key, value in params.items():
            setattr(cp_solver.parameters, key, value)

        status_code = cp_solver.solve(self._model)
        status = cp_solver.status_name(status_code)
        objective_value = cp_solver.objective_value

        if status in ["OPTIMAL", "FEASIBLE"]:
            solution = self._convert_to_solution(cp_solver)
        else:
            # No feasible solution found due to infeasibility or time limit.
            solution = Solution([])
            objective_value = float("inf")

        return Result(
            self._get_solve_status(status),
            cp_solver.wall_time,
            solution,
            objective_value,
        )
