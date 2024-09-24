from ortools.sat.python.cp_model import (
    CpModel,
    LinearExpr,
    LinearExprT,
)

from pyjobshop.ProblemData import Objective as DataObjective
from pyjobshop.ProblemData import ProblemData

from .Variables import Variables


class Objective:
    """
    Builds the objective expressions of the OR-Tools model.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, variables: Variables
    ):
        self._model = model
        self._data = data
        self._task_vars = variables.task_vars
        self._job_vars = variables.job_vars

    def _makespan_expr(self) -> LinearExprT:
        """
        Returns an expression representing the makespan of the model.
        """
        makespan = self._model.new_int_var(0, self._data.horizon, "makespan")
        completion_times = [var.end for var in self._task_vars]
        self._model.add_max_equality(makespan, completion_times)
        return makespan

    def _tardy_jobs_expr(self) -> LinearExprT:
        """
        Returns an expression representing the number of tardy jobs.
        """
        model, data = self._model, self._data
        is_tardy_vars = []

        for job, job_var in zip(data.jobs, self._job_vars):
            assert job.due_date is not None
            is_tardy = model.new_bool_var(f"is_tardy_{job}")
            model.add(job_var.end > job.due_date).only_enforce_if(is_tardy)
            model.add(job_var.end <= job.due_date).only_enforce_if(~is_tardy)
            is_tardy_vars.append(is_tardy)

        weights = [job.weight for job in data.jobs]
        return LinearExpr.weighted_sum(is_tardy_vars, weights)

    def _total_flow_time_expr(self) -> LinearExprT:
        """
        Returns an expression representing the total flow time of jobs.
        """
        model, data = self._model, self._data
        flow_time_vars = []

        for job, var in zip(data.jobs, self._job_vars):
            flow_time = model.new_int_var(0, data.horizon, f"flow_time_{job}")
            model.add_max_equality(flow_time, [0, var.end - job.release_date])
            flow_time_vars.append(flow_time)

        weights = [job.weight for job in data.jobs]
        return LinearExpr.weighted_sum(flow_time_vars, weights)

    def _total_tardiness_expr(self) -> LinearExprT:
        """
        Returns an expression representing the total tardiness of jobs.
        """
        model, data = self._model, self._data
        tardiness_vars = []

        for job, var in zip(data.jobs, self._job_vars):
            assert job.due_date is not None
            tardiness = model.new_int_var(0, data.horizon, f"tardiness_{job}")
            model.add_max_equality(tardiness, [0, var.end - job.due_date])
            tardiness_vars.append(tardiness)

        weights = [job.weight for job in data.jobs]
        return LinearExpr.weighted_sum(tardiness_vars, weights)

    def _total_earliness_expr(self) -> LinearExprT:
        """
        Returns an expression representing the total earliness of jobs.
        """
        model, data = self._model, self._data
        earliness_vars = []

        for job, var in zip(data.jobs, self._job_vars):
            assert job.due_date is not None
            earliness = model.new_int_var(0, data.horizon, f"earliness_{job}")
            model.add_max_equality(earliness, [0, job.due_date - var.end])
            earliness_vars.append(earliness)

        weights = [job.weight for job in data.jobs]
        return LinearExpr.weighted_sum(earliness_vars, weights)

    def _objective_expr(self, objective: DataObjective) -> LinearExprT:
        """
        Returns the expression corresponding to the given objective.
        """
        expr = 0

        if objective.weight_makespan > 0:
            expr += objective.weight_makespan * self._makespan_expr()

        if objective.weight_tardy_jobs > 0:
            expr += objective.weight_tardy_jobs * self._tardy_jobs_expr()

        if objective.weight_total_tardiness > 0:
            expr += (
                objective.weight_total_tardiness * self._total_tardiness_expr()
            )

        if objective.weight_total_flow_time > 0:
            expr += (
                objective.weight_total_flow_time * self._total_flow_time_expr()
            )

        if objective.weight_total_earliness > 0:
            expr += (
                objective.weight_total_earliness * self._total_earliness_expr()
            )

        return expr

    def set_objective(self, objective: DataObjective):
        """
        Sets the objective of the the model.
        """
        self._model.clear_objective()
        self._model.minimize(self._objective_expr(objective))
