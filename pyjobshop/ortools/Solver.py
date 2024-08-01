from typing import Optional

from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
)

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution, TaskData

from .Constraints import Constraints
from .Objectives import Objectives
from .Variables import Variables


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

        self._m = CpModel()
        self._variables = Variables(self._m, data)
        self._constraints = Constraints(self._m, data, self._variables)
        self._objectives = Objectives(self._m, data, self._variables)

    def add_hints(self, solution: Solution):
        """
        Adds hints to variables based on the given solution.
        """
        m, data = self._m, self._data
        job_vars, task_vars, task_alt_vars = (
            self._variables.job_vars,
            self._variables.task_vars,
            self._variables.task_alt_vars,
        )

        for idx in range(data.num_jobs):
            job = data.jobs[idx]
            job_var = job_vars[idx]
            sol_tasks = [solution.tasks[task] for task in job.tasks]

            job_start = min(task.start for task in sol_tasks)
            job_end = max(task.end for task in sol_tasks)

            m.add_hint(job_var.start, job_start)
            m.add_hint(job_var.duration, job_end - job_start)
            m.add_hint(job_var.end, job_end)

        for idx in range(data.num_tasks):
            task_var = task_vars[idx]
            sol_task = solution.tasks[idx]

            m.add_hint(task_var.start, sol_task.start)
            m.add_hint(task_var.duration, sol_task.duration)
            m.add_hint(task_var.end, sol_task.end)

        for (task_idx, machine_idx), var in task_alt_vars.items():
            sol_task = solution.tasks[task_idx]

            m.add_hint(var.start, sol_task.start)
            m.add_hint(var.duration, sol_task.duration)
            m.add_hint(var.end, sol_task.end)
            m.add_hint(var.is_present, machine_idx == sol_task.machine)

    def _get_solve_status(self, status: str):
        if status == "OPTIMAL":
            return SolveStatus.OPTIMAL
        elif status == "FEASIBLE":
            return SolveStatus.FEASIBLE
        elif status == "INFEASIBLE":
            return SolveStatus.INFEASIBLE
        else:
            return SolveStatus.TIME_LIMIT

    def _convert_to_solution(self, cp_solver: CpSolver) -> Solution:
        """
        Converts a result from the OR-Tools CP solver to a Solution object.

        Parameters
        ----------
        cp_solver
            The CP solver.

        Returns
        -------
        Solution
            The solution.
        """
        tasks = {}

        for (task, machine), var in self._variables.task_alt_vars.items():
            if cp_solver.value(var.is_present):
                start = cp_solver.value(var.start)
                duration = cp_solver.value(var.duration)
                end = cp_solver.value(var.end)
                tasks[task] = TaskData(machine, start, duration, end)

        return Solution([tasks[idx] for idx in range(self._data.num_tasks)])

    def solve(
        self,
        time_limit: float,
        log: bool,
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
        log
            Whether to log the solver output.
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
            self.add_hints(initial_solution)

        self._constraints.add_all_constraints()
        self._objectives.set_objective(self._data.objective)

        params = {
            "max_time_in_seconds": time_limit,
            "log_search_progress": log,
            # 0 means using all available CPU cores.
            "num_workers": num_workers if num_workers is not None else 0,
        }
        params.update(kwargs)  # this will override existing parameters!

        cp_solver = CpSolver()
        for key, value in params.items():
            setattr(cp_solver.parameters, key, value)

        status_code = cp_solver.solve(self._m)
        status = cp_solver.status_name(status_code)
        objective = cp_solver.objective_value

        if status in ["OPTIMAL", "FEASIBLE"]:
            solution = self._convert_to_solution(cp_solver)
        else:
            # No feasible solution found due to infeasibility or time limit.
            solution = Solution([])
            objective = float("inf")

        return Result(
            self._get_solve_status(status),
            cp_solver.wall_time,
            solution,
            objective,
        )
