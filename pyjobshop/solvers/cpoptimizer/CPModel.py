from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoSolveResult

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution, TaskData

from .Constraints import Constraints
from .Objective import Objective
from .Variables import Variables


class CPModel:
    """
    Wrapper around the CP Optimizer CP model.

    Parameters
    ----------
    data
        The problem data instance.
    model
        CpoModel instance to use. If None (default), a new one is created.
    """

    def __init__(self, data: ProblemData, model: CpoModel | None = None):
        self._data = data

        self._model = model if model is not None else CpoModel()
        self._variables = Variables(self._model, data)
        self._constraints = Constraints(self._model, data, self._variables)
        self._objective = Objective(self._model, data, self._variables)

        self._constraints.add_constraints()
        self._objective.add_objective()

    @property
    def model(self) -> CpoModel:
        """
        Returns the underlying CpoModel.
        """
        return self._model

    @property
    def variables(self) -> Variables:
        """
        Returns the Variables object containing all model variables.
        """
        return self._variables

    def _get_solve_status(self, status: str) -> SolveStatus:
        if status == "Optimal":
            return SolveStatus.OPTIMAL

        if status == "Feasible":
            return SolveStatus.FEASIBLE

        if status == "Infeasible":
            return SolveStatus.INFEASIBLE

        return SolveStatus.TIME_LIMIT

    def _convert_to_solution(self, result: CpoSolveResult) -> Solution:
        """
        Converts an CpoSolveResult object to a solution.
        """
        data = self._data
        tasks = {}

        for var in result.get_all_var_solutions():  # type: ignore
            name = var.get_name()

            # Scheduled tasks are inferred from present mode variables.
            if name.startswith("M") and var.is_present():
                mode_idx, task = map(int, name[1:].split("_"))
                overlap = var.get_length() - var.size
                processing = data.modes[mode_idx].duration
                idle = var.get_length() - processing - overlap
                tasks[task] = TaskData(
                    mode_idx,
                    data.modes[mode_idx].resources,
                    var.start,
                    var.end,
                    idle,
                    overlap,
                    present=True,
                )

        for idx in range(data.num_tasks):
            if idx not in tasks:
                tasks[idx] = TaskData(
                    data.num_modes, [], 0, 0, 0, 0, present=False
                )

        return Solution([tasks[idx] for idx in range(self._data.num_tasks)])

    def solve(
        self,
        time_limit: float = float("inf"),
        display: bool = False,
        num_workers: int | None = None,
        initial_solution: Solution | None = None,
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
            self._variables.warmstart(initial_solution)

        params = {
            "TimeLimit": time_limit,
            "LogVerbosity": "Terse" if display else "Quiet",
            "Workers": num_workers if num_workers is not None else "Auto",
        }
        params.update(kwargs)  # this will override existing parameters!

        cp_result: CpoSolveResult = self._model.solve(**params)  # type: ignore
        status = cp_result.get_solve_status()

        if status in ["Optimal", "Feasible"]:
            solution = self._convert_to_solution(cp_result)
            objective: float = cp_result.get_objective_value()  # type: ignore
            lower_bound: float = cp_result.get_objective_bound()  # type: ignore
        else:
            # No feasible solution due to infeasible instance or time limit.
            solution = Solution([])
            objective = float("inf")
            lower_bound = float("-inf")

        return Result(
            objective=objective,
            lower_bound=lower_bound,
            status=self._get_solve_status(status),
            runtime=cp_result.get_solve_time(),
            best=solution,
        )
