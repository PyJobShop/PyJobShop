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
        data, variables, objective = (
            self._data,
            self._variables,
            self._data.objective,
        )
        job_weights = [job.weight for job in data.jobs]
        expr = 0

        def weighted_sum(variables, weights):
            return LinearExpr.weighted_sum(variables, weights)

        if (obj_weight := objective.weight_makespan) > 0:
            expr += obj_weight * variables.makespan_var

        if (obj_weight := objective.weight_tardy_jobs) > 0:
            is_tardy_vars = variables.is_tardy_vars
            expr += obj_weight * weighted_sum(is_tardy_vars, job_weights)

        if (obj_weight := objective.weight_total_flow_time) > 0:
            flow_time_vars = variables.flow_time_vars
            expr += obj_weight * weighted_sum(flow_time_vars, job_weights)

        if (obj_weight := objective.weight_total_tardiness) > 0:
            tardiness_vars = variables.tardiness_vars
            expr += obj_weight * weighted_sum(tardiness_vars, job_weights)

        if (obj_weight := objective.weight_total_earliness) > 0:
            earliness_vars = variables.earliness_vars
            expr += obj_weight * weighted_sum(earliness_vars, job_weights)

        if (obj_weight := objective.weight_max_tardiness) > 0:
            expr += obj_weight * variables.max_tardiness_var

        if (obj_weight := objective.weight_total_setup_time) > 0:
            data = self._data
            setup_times = utils.setup_times_matrix(data)
            setup_time_vars = []

            for res_idx in data.machine_idcs:
                seq_var = variables.sequence_vars[res_idx]
                if not seq_var.is_active:
                    continue

                for (idx1, idx2), arc in seq_var.arcs.items():
                    if idx1 == seq_var.DUMMY or idx2 == seq_var.DUMMY:
                        continue

                    setup = (
                        setup_times[res_idx, idx1, idx2]
                        if setup_times is not None
                        else 0
                    )
                    setup_time_vars.append(arc * setup)

            expr += obj_weight * LinearExpr.sum(setup_time_vars)

        self._model.minimize(expr)
