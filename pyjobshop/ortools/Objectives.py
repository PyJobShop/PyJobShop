import functools

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntVar, LinearExpr

from pyjobshop.ProblemData import Objective, ProblemData

from .Variables import Variables


class Objectives:
    """
    Helper class to set the objective of the model.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, variables: Variables
    ):
        self._m = model
        self._data = data
        self._task_vars = variables.task_vars
        self._job_vars = variables.job_vars

    @functools.cached_property
    def makespan_var(self) -> IntVar:
        var = self._m.new_int_var(0, self._data.horizon, "makespan")
        completion_times = [var.end for var in self._task_vars]
        self._m.add_max_equality(var, completion_times)
        return var

    @functools.cached_property
    def is_tardy_vars(self) -> list[BoolVarT]:
        tardy_vars = []
        for job, var in zip(self._data.jobs, self._job_vars):
            is_tardy = self._m.new_bool_var(f"is_tardy_{job}")
            tardy_vars.append(is_tardy)
            self._m.add(var.end > job.due_date).only_enforce_if(is_tardy)
            self._m.add(var.end <= job.due_date).only_enforce_if(~is_tardy)
        return tardy_vars

    @functools.cached_property
    def tardiness_vars(self) -> list[IntVar]:
        tardiness_vars = []
        for job, var in zip(self._data.jobs, self._job_vars):
            tardiness = self._m.new_int_var(
                0, self._data.horizon, f"tardiness_{job}"
            )
            self._m.add_max_equality(tardiness, [0, var.end - job.due_date])
            tardiness_vars.append(tardiness)
        return tardiness_vars

    def _makespan_expr(self):
        return self.makespan_var

    def _tardy_jobs_expr(self):
        return LinearExpr.sum(self.is_tardy_vars)

    def _total_completion_time_expr(self):
        exprs = [var.end for var in self._job_vars]
        weights = [job.weight for job in self._data.jobs]
        return LinearExpr.weighted_sum(exprs, weights)

    def _total_tardiness_expr(self):
        weights = [job.weight for job in self._data.jobs]
        return LinearExpr.weighted_sum(self.tardiness_vars, weights)

    def set_objective(self, objective: Objective):
        """
        Sets the objective of the the model.
        """
        self._m.clear_objective()

        if objective == "makespan":
            self._m.minimize(self._makespan_expr())
        elif objective == "tardy_jobs":
            self._m.minimize(self._tardy_jobs_expr())
        elif objective == "total_completion_time":
            self._m.minimize(self._total_completion_time_expr())
        elif objective == "total_tardiness":
            self._m.minimize(self._total_tardiness_expr())
        else:
            raise ValueError(f"Objective {objective} not supported.")

    def add_objective_constraint(self, objective: Objective, bound: int):
        """
        Adds constraints to the model based on the objective.
        """
        if objective == "makespan":
            self._m.add(self._makespan_expr() <= bound)
        elif objective == "tardy_jobs":
            self._m.add(self._tardy_jobs_expr() <= bound)
        elif objective == "total_completion_time":
            self._m.add(self._total_completion_time_expr() <= bound)
        elif objective == "total_tardiness":
            self._m.add(self._total_tardiness_expr() <= bound)
        else:
            raise ValueError(f"Objective {objective} not supported.")
