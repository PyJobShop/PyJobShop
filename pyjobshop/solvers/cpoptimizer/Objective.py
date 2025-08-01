import docplex.cp.modeler as cpo
from docplex.cp.model import CpoExpr, CpoModel

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import Objective as ObjectiveData
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
        self._sequence_vars = variables.sequence_vars

    def _makespan_expr(self) -> CpoExpr:
        """
        Returns an expression representing the makespan of the model.
        """
        if not self._task_vars:
            return 0  # type: ignore

        return cpo.max(cpo.end_of(var) for var in self._task_vars)  # type: ignore

    def _tardy_jobs_expr(self) -> CpoExpr:
        """
        Returns an expression representing the number of tardy jobs.
        """
        exprs = []
        for job, var in zip(self._data.jobs, self._job_vars):
            is_tardy = cpo.greater(cpo.end_of(var) - job.due_date, 0)
            exprs.append(job.weight * is_tardy)

        return cpo.sum(exprs)  # type: ignore

    def _total_flow_time_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total flow time of jobs.
        """
        total = []
        for job, var in zip(self._data.jobs, self._job_vars):
            flow_time = cpo.max(0, cpo.end_of(var) - job.release_date)
            total.append(job.weight * flow_time)

        return cpo.sum(total)  # type: ignore

    def _total_tardiness_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total tardiness of jobs.
        """
        total = []
        for job, var in zip(self._data.jobs, self._job_vars):
            tardiness = cpo.max(0, cpo.end_of(var) - job.due_date)
            total.append(job.weight * tardiness)

        return cpo.sum(total)  # type: ignore

    def _total_earliness_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total earliness of jobs.
        """
        total = []
        for job, var in zip(self._data.jobs, self._job_vars):
            earliness = cpo.max(0, job.due_date - cpo.end_of(var))
            total.append(job.weight * earliness)

        return cpo.sum(total)  # type: ignore

    def _max_tardiness_expr(self) -> CpoExpr:
        """
        Returns an expression representing the maximum tardiness of jobs.
        """
        tardiness = [
            job.weight * cpo.max(0, cpo.end_of(var) - job.due_date)
            for job, var in zip(self._data.jobs, self._job_vars)
        ]
        return cpo.max(tardiness)  # type: ignore

    def _total_setup_time_expr(self) -> CpoExpr:
        """
        Returns an expression representing the total setup times.
        """
        data = self._data
        total = []

        for res_idx in data.machine_idcs:
            if (setup_times := utils.setup_times_matrix(data)) is None:
                continue

            seq_var = self._sequence_vars[res_idx]
            intervals = seq_var.get_interval_variables()
            resource_modes = data.resource2modes(res_idx)
            task_idcs = [data.modes[m].task for m in resource_modes]

            for idx, interval in enumerate(intervals):
                # The setup time for the current interval is a variable that
                # depends on the next interval's task in the sequence. If the
                # interval is last or absent, we set the setup time to 0.
                task_idx = task_idcs[idx]
                setup_array = setup_times[res_idx, task_idx, :].tolist()
                setup_array.append(0)  # padding for last or absent
                next_idx = cpo.type_of_next(
                    seq_var,
                    interval,
                    lastValue=data.num_tasks,
                    absentValue=data.num_tasks,
                )
                setup_time = cpo.element(setup_array, next_idx)
                total.append(setup_time)

        return cpo.sum(total)  # type: ignore

    def _objective_expr(self, objective: ObjectiveData) -> CpoExpr:
        """
        Returns the expression corresponding to the given objective.
        """
        items = [
            (objective.weight_makespan, self._makespan_expr),
            (objective.weight_tardy_jobs, self._tardy_jobs_expr),
            (objective.weight_total_tardiness, self._total_tardiness_expr),
            (objective.weight_total_flow_time, self._total_flow_time_expr),
            (objective.weight_total_earliness, self._total_earliness_expr),
            (objective.weight_max_tardiness, self._max_tardiness_expr),
            (objective.weight_total_setup_time, self._total_setup_time_expr),
        ]
        exprs = [weight * expr() for weight, expr in items if weight > 0]
        return cpo.minimize(cpo.sum(exprs))

    def add_objective(self):
        """
        Adds the objective expression to the CP model.
        """
        obj_expr = self._objective_expr(self._data.objective)
        self._model.add(obj_expr)
