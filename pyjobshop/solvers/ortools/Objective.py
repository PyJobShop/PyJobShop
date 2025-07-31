from ortools.sat.python.cp_model import (
    CpModel,
    LinearExpr,
    LinearExprT,
)

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import Objective as ObjectiveData
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

    def _objective_expr(self, objective: ObjectiveData) -> LinearExprT:
        """
        Returns the expression corresponding to the given objective.
        """
        variables = self._variables
        job_weights = [job.weight for job in self._data.jobs]
        exprs = []

        if objective.weight_makespan > 0:
            exprs += [objective.weight_makespan * variables.makespan_var]

        if objective.weight_tardy_jobs > 0:
            exprs += [
                objective.weight_tardy_jobs
                * LinearExpr.weighted_sum(variables.is_tardy_vars, job_weights)
            ]

        if objective.weight_total_flow_time > 0:
            exprs += [
                objective.weight_total_flow_time
                * LinearExpr.weighted_sum(
                    variables.flow_time_vars, job_weights
                )
            ]

        if objective.weight_total_tardiness > 0:
            exprs += [
                objective.weight_total_tardiness
                * LinearExpr.weighted_sum(
                    variables.tardiness_vars, job_weights
                )
            ]

        if objective.weight_total_earliness > 0:
            exprs += [
                objective.weight_total_earliness
                * LinearExpr.weighted_sum(
                    variables.earliness_vars, job_weights
                )
            ]

        if objective.weight_max_tardiness > 0:
            exprs += [
                objective.weight_max_tardiness * variables.max_tardiness_var
            ]

        if objective.weight_max_lateness > 0:
            exprs += [
                objective.weight_max_lateness * variables.max_lateness_var
            ]

        if objective.weight_total_setup_time > 0:
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

            exprs += [
                objective.weight_total_setup_time
                * LinearExpr.sum(setup_time_vars)
            ]

        return LinearExpr.sum(exprs)

    def add_objective(self):
        """
        Adds the objective expression to the CP model.
        """
        obj_expr = self._objective_expr(self._data.objective)
        self._model.minimize(obj_expr)
