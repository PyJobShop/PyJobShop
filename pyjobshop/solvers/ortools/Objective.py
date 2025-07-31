from ortools.sat.python.cp_model import CpModel, LinearExpr

import pyjobshop.solvers.utils as utils
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
        self._variables = variables

    def add_objective(self):
        """
        Adds the objective expression to the CP model.
        """
        variables = self._variables
        obj = self._data.objective
        job_weights = [job.weight for job in self._data.jobs]
        expr = 0

        def weighted_sum(variables, weights):
            return LinearExpr.weighted_sum(variables, weights)

        if (obj_weight := obj.weight_makespan) > 0:
            expr += obj_weight * variables.makespan_var

        if (obj_weight := obj.weight_tardy_jobs) > 0:
            is_tardy_vars = variables.is_tardy_vars
            expr += obj_weight * weighted_sum(is_tardy_vars, job_weights)

        if (obj_weight := obj.weight_total_flow_time) > 0:
            flow_time_vars = variables.flow_time_vars
            expr += obj_weight * weighted_sum(flow_time_vars, job_weights)

        if (obj_weight := obj.weight_total_tardiness) > 0:
            tardiness_vars = variables.tardiness_vars
            expr += obj_weight * weighted_sum(tardiness_vars, job_weights)

        if (obj_weight := obj.weight_total_earliness) > 0:
            earliness_vars = variables.earliness_vars
            expr += obj_weight * weighted_sum(earliness_vars, job_weights)

        if (obj_weight := obj.weight_max_tardiness) > 0:
            expr += obj_weight * variables.max_tardiness_var

        if (obj_weight := obj.weight_total_setup_time) > 0:
            data = self._data
            setup_times = utils.setup_times_matrix(data)
            setup_time_vars = []
            for res_idx in data.machine_idcs:
                seq_var = variables.sequence_vars[res_idx]
                if not seq_var.is_active:
                    continue

                for task_idx1 in range(data.num_tasks):
                    for task_idx2 in range(data.num_tasks):
                        var1 = variables.assign_vars.get((task_idx1, res_idx))
                        var2 = variables.assign_vars.get((task_idx2, res_idx))
                        if not (var1 and var2):
                            continue

                        setup = (
                            setup_times[res_idx, task_idx1, task_idx2]
                            if setup_times is not None
                            else 0
                        )
                        arc_selected = seq_var.arcs[task_idx1, task_idx2]
                        setup_time_vars.append(arc_selected * setup)

            expr += obj_weight * LinearExpr.sum(setup_time_vars)

        self._model.minimize(expr)
