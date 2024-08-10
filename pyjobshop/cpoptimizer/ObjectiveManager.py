from docplex.cp.model import CpoExpr, CpoModel

from pyjobshop.ProblemData import Objective, ProblemData

from .VariablesManager import VariablesManager


class ObjectiveManager:
    """
    Manages the objective expressions of the CP Optimizer model.
    """

    def __init__(
        self,
        model: CpoModel,
        data: ProblemData,
        vars_manager: VariablesManager,
    ):
        self._model = model
        self._data = data
        self._task_vars = vars_manager.task_vars
        self._job_vars = vars_manager.job_vars

    def _makespan_expr(self) -> CpoExpr:
        """
        Returns an expression representing the makespan of the model.
        """
        return self._model.max(
            self._model.end_of(var) for var in self._task_vars
        )

    def _tardy_jobs_expr(self) -> CpoExpr:
        """
        Returns an expression representing the number of tardy jobs.
        """
        m, data = self._model, self._data
        exprs = []

        for job, var in zip(data.jobs, self._job_vars):
            is_tardy = m.greater(m.end_of(var) - job.due_date, 0)
            exprs.append(job.weight * is_tardy)

        return m.sum(exprs)

    def _total_completion_time_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total completion time of jobs.
        """
        m, data = self._model, self._data
        total = []

        for job, var in zip(data.jobs, self._job_vars):
            completion_time = m.end_of(var)
            total.append(job.weight * completion_time)

        return m.sum(total)

    def _total_tardiness_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total tardiness of jobs.
        """
        m, data = self._model, self._data
        total = []

        for job, var in zip(data.jobs, self._job_vars):
            tardiness = m.max(0, m.end_of(var) - job.due_date)
            total.append(job.weight * tardiness)

        return m.sum(total)

    def _objective_expr(self, objective: Objective) -> CpoExpr:
        """
        Returns the expression corresponding to the given objective.
        """
        expr = 0
        objective = self._data.objective

        if objective.weight_makespan > 0:
            expr += objective.weight_makespan * self._makespan_expr()

        if objective.weight_tardy_jobs > 0:
            expr += objective.weight_tardy_jobs * self._tardy_jobs_expr()

        if objective.weight_total_tardiness > 0:
            expr += (
                objective.weight_total_tardiness * self._total_tardiness_expr()
            )

        if objective.weight_total_completion_time > 0:
            expr += (
                objective.weight_total_completion_time
                * self._total_completion_time_expr()
            )

        return expr

    def set_objective(self, objective: Objective):
        """
        Sets the objective of the the model.
        """
        # self._model.clear_objective() # TODO is this necessary?
        self._model.minimize(self._objective_expr(objective))

    def add_objective_as_constraint(self, objective: Objective, value: int):
        """
        Adds the objective function as constraint to the model.
        """
        self._model.add(self._objective_expr(objective) <= value)
