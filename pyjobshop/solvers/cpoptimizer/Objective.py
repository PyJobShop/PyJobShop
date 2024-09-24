import docplex.cp.modeler as cpo
from docplex.cp.model import CpoExpr, CpoModel

from pyjobshop.ProblemData import Objective as DataObjective
from pyjobshop.ProblemData import ProblemData

from .Variables import Variables


class Objective:
    """
    Builds the objective expressions of the CP Optimizer model.
    """

    def __init__(
        self, model: CpoModel, data: ProblemData, variables: Variables
    ):
        self._model = model
        self._data = data
        self._task_vars = variables.task_vars
        self._job_vars = variables.job_vars

        self._current_objective_expr = None

    def _makespan_expr(self) -> CpoExpr:
        """
        Returns an expression representing the makespan of the model.
        """
        return cpo.max(cpo.end_of(var) for var in self._task_vars)

    def _tardy_jobs_expr(self) -> CpoExpr:
        """
        Returns an expression representing the number of tardy jobs.
        """
        data = self._data
        exprs = []

        for job, var in zip(data.jobs, self._job_vars):
            is_tardy = cpo.greater(cpo.end_of(var) - job.due_date, 0)
            exprs.append(job.weight * is_tardy)

        return cpo.sum(exprs)  # type: ignore

    def _total_flow_time_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total flow time of jobs.
        """
        data = self._data
        total = []

        for job, var in zip(data.jobs, self._job_vars):
            flow_time = cpo.max(0, cpo.end_of(var) - job.release_date)
            total.append(job.weight * flow_time)

        return cpo.sum(total)  # type: ignore

    def _total_tardiness_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total tardiness of jobs.
        """
        data = self._data
        total = []

        for job, var in zip(data.jobs, self._job_vars):
            tardiness = cpo.max(0, cpo.end_of(var) - job.due_date)
            total.append(job.weight * tardiness)

        return cpo.sum(total)  # type: ignore

    def _total_earliness_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total earliness of jobs.
        """
        data = self._data
        total = []

        for job, var in zip(data.jobs, self._job_vars):
            earliness = cpo.max(0, job.due_date - cpo.end_of(var))
            total.append(job.weight * earliness)

        return cpo.sum(total)  # type: ignore

    def _objective_expr(self, objective: DataObjective) -> CpoExpr:
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

        return self._model.minimize(expr)

    def build(self, objective: DataObjective):
        """
        Builds the objective of the model.
        """
        if self._current_objective_expr is not None:
            self._model.remove(self._current_objective_expr)

        obj_expr = self._objective_expr(objective)
        self._model.add(obj_expr)
        self._current_objective_expr = obj_expr
