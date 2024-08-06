from functools import cached_property

from ortools.sat.python.cp_model import (
    BoolVarT,
    CpModel,
    IntVar,
    LinearExpr,
    LinearExprT,
)

from pyjobshop.ProblemData import Objective, ProblemData

from .VariablesManager import VariablesManager


class ObjectiveManager:
    """
    Helper class to manage the objective of the model.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, vars_manager: VariablesManager
    ):
        self._m = model
        self._data = data
        self._task_vars = vars_manager.task_vars
        self._job_vars = vars_manager.job_vars

    @cached_property
    def makespan_var(self) -> IntVar:
        """
        Returns the makespan variable of the model.
        """
        var = self._m.new_int_var(0, self._data.horizon, "makespan")
        completion_times = [var.end for var in self._task_vars]
        self._m.add_max_equality(var, completion_times)
        return var

    @cached_property
    def is_tardy_vars(self) -> list[BoolVarT]:
        """
        Returns a list of booleans representing whether a job is tardy.
        """
        variables = []

        for job, job_var in zip(self._data.jobs, self._job_vars):
            assert job.due_date is not None
            is_tardy = self._m.new_bool_var(f"is_tardy_{job}")
            self._m.add(job_var.end > job.due_date).only_enforce_if(is_tardy)
            self._m.add(job_var.end <= job.due_date).only_enforce_if(~is_tardy)
            variables.append(is_tardy)

        return variables

    @cached_property
    def tardiness_vars(self) -> list[IntVar]:
        """
        Returns a list of integer variables representing the job tardiness.
        """
        variables = []

        for job, var in zip(self._data.jobs, self._job_vars):
            tardiness = self._m.new_int_var(
                0, self._data.horizon, f"tardiness_{job}"
            )
            self._m.add_max_equality(tardiness, [0, var.end - job.due_date])
            variables.append(tardiness)

        return variables

    def _makespan_expr(self) -> LinearExprT:
        """
        Returns an expression representing the makespan of the model.
        """
        return self.makespan_var

    def _tardy_jobs_expr(self) -> LinearExprT:
        """
        Returns an expression representing the number of tardy jobs.
        """
        return LinearExpr.sum(self.is_tardy_vars)

    def _total_completion_time_expr(self) -> LinearExprT:
        """
        Returns an expression representing the total completion time of jobs.
        """
        exprs = [var.end for var in self._job_vars]
        weights = [job.weight for job in self._data.jobs]
        return LinearExpr.weighted_sum(exprs, weights)

    def _total_tardiness_expr(self) -> LinearExprT:
        """
        Returns an expression representing the total tardiness of jobs.
        """
        weights = [job.weight for job in self._data.jobs]
        return LinearExpr.weighted_sum(self.tardiness_vars, weights)

    def _objective2expr(self, objective: Objective):
        """
        Returns the expression corresponding to the given objective.
        """
        if objective == "makespan":
            return self._makespan_expr()
        elif objective == "tardy_jobs":
            return self._tardy_jobs_expr()
        elif objective == "total_completion_time":
            return self._total_completion_time_expr()
        elif objective == "total_tardiness":
            return self._total_tardiness_expr()
        else:
            raise ValueError(f"Objective {objective} not supported")

    def set_objective(self, objective: Objective):
        """
        Sets the objective of the the model.
        """
        self._m.clear_objective()
        self._m.minimize(self._objective2expr(objective))

    def add_objective_as_constraint(self, objective: Objective, value: int):
        """
        Adds the objective function as constraint to the model.
        """
        self._m.add(self._objective2expr(objective) <= value)
