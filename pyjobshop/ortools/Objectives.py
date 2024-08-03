from ortools.sat.python.cp_model import CpModel, LinearExpr

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

        self.task_vars = variables.task_vars
        self.job_vars = variables.job_vars

        self.makespan_var = self._m.new_int_var(0, data.horizon, "makespan")
        completion_times = [var.end for var in self.task_vars]
        self._m.add_max_equality(self.makespan_var, completion_times)

        self.is_tardy_vars = [
            self._m.new_bool_var(f"is_tardy_{job}") for job in data.jobs
        ]
        self.tardiness_vars = [
            self._m.new_int_var(0, data.horizon, f"tardiness_{job}")
            for job in data.jobs
        ]

    def _makespan(self):
        """
        Minimizes the makespan.
        """
        completion_times = [var.end for var in self.task_vars]
        self._m.add_max_equality(self.makespan_var, completion_times)
        self._m.minimize(self.makespan_var)

    def _tardy_jobs(self):
        """
        Minimize the number of tardy jobs.
        """
        for job, var, is_tardy in zip(
            self._data.jobs, self.job_vars, self.is_tardy_vars
        ):
            self._m.add(var.end > job.due_date).only_enforce_if(is_tardy)
            self._m.add(var.end <= job.due_date).only_enforce_if(~is_tardy)

        self._m.minimize(LinearExpr.sum(self.is_tardy_vars))

    def _total_completion_time(self):
        """
        Minimizes the weighted sum of the completion times of each job.
        """
        exprs = [var.end for var in self.job_vars]
        weights = [job.weight for job in self._data.jobs]

        self._m.minimize(LinearExpr.weighted_sum(exprs, weights))

    def _total_tardiness(self):
        """
        Minimizes the weighted sum of the tardiness of each job.
        """
        for job, var, tardiness in zip(
            self._data.jobs, self.job_vars, self.tardiness_vars
        ):
            self._m.add_max_equality(tardiness, [0, var.end - job.due_date])

        weights = [job.weight for job in self._data.jobs]
        self._m.minimize(LinearExpr.weighted_sum(self.tardiness_vars, weights))

    def set_objective(self, objective: Objective):
        """
        Sets the objective of the the model.
        """
        self._m.clear_objective()

        if objective == "makespan":
            self._makespan()
        elif objective == "tardy_jobs":
            self._tardy_jobs()
        elif objective == "total_completion_time":
            self._total_completion_time()
        elif objective == "total_tardiness":
            self._total_tardiness()
        else:
            raise ValueError(f"Objective {objective} not supported.")

    def add_objective_constraint(self, objective: Objective, bound: int):
        """
        Adds constraints to the model based on the objective.
        """
        if objective == "makespan":
            expr = self.makespan_var <= bound
        elif objective == "tardy_jobs":
            expr = LinearExpr.sum(self.is_tardy_vars) <= bound
        elif objective == "total_completion_time":
            expr = (
                LinearExpr.weighted_sum(
                    [var.end for var in self.job_vars],
                    [job.weight for job in self._data.jobs],
                )
                <= bound
            )
        elif objective == "total_tardiness":
            expr = (
                LinearExpr.weighted_sum(
                    self.tardiness_vars,
                    [job.weight for job in self._data.jobs],
                )
                <= bound
            )
        else:
            raise ValueError(f"Objective {objective} not supported.")

        self._m.add(expr)
