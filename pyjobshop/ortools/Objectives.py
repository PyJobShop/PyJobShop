from ortools.sat.python.cp_model import CpModel, LinearExpr

from pyjobshop.ProblemData import Objective, ProblemData

from .Variables import Variables


class Objectives:
    def __init__(
        self, model: CpModel, data: ProblemData, variables: Variables
    ):
        self._m = model
        self._data = data

        self.task_vars = variables.task_vars
        self.job_vars = variables.job_vars

    def _makespan(self):
        """
        Minimizes the makespan.
        """
        makespan = self._m.new_int_var(0, self._data.horizon, "makespan")
        completion_times = [var.end for var in self.task_vars]

        self._m.add_max_equality(makespan, completion_times)
        self._m.minimize(makespan)

    def _tardy_jobs(self):
        """
        Minimize the number of tardy jobs.
        """
        exprs = []

        for job, var in zip(self._data.jobs, self.job_vars):
            is_tardy = self._m.new_bool_var(f"is_tardy_{job}")
            exprs.append(is_tardy)

            self._m.add(var.end > job.due_date).only_enforce_if(is_tardy)
            self._m.add(var.end <= job.due_date).only_enforce_if(~is_tardy)

        self._m.minimize(LinearExpr.sum(exprs))

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
        exprs = []

        for job, var in zip(self._data.jobs, self.job_vars):
            tardiness = self._m.new_int_var(
                0, self._data.horizon, f"tardiness_{job}"
            )
            exprs.append(tardiness)

            self._m.add_max_equality(tardiness, [0, var.end - job.due_date])

        weights = [job.weight for job in self._data.jobs]
        self._m.minimize(LinearExpr.weighted_sum(exprs, weights))

    def set_objective(self, objective: Objective):
        """
        Sets the objective of the the model.
        """
        if objective == "makespan":
            self._makespan()
        elif objective == "tardy_jobs":
            self._tardy_jobs()
        elif objective == "total_completion_time":
            self._total_completion_time()
        elif objective == "total_tardiness":
            self._total_tardiness()
