import docplex.cp.modeler as cpo
import numpy as np
from docplex.cp.function import CpoStepFunction
from docplex.cp.model import CpoModel

import pyjobshop.solvers.utils as utils
from pyjobshop.constants import MAX_VALUE
from pyjobshop.ProblemData import ProblemData

from .Variables import Variables


class Constraints:
    """
    Builds the core constraints of the CP Optimizer model.
    """

    def __init__(
        self, model: CpoModel, data: ProblemData, variables: Variables
    ):
        self._model = model
        self._data = data
        self._job_vars = variables.job_vars
        self._task_vars = variables.task_vars
        self._mode_vars = variables.mode_vars
        self._sequence_vars = variables.sequence_vars

    def _job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        model, data = self._model, self._data

        for idx, job in enumerate(data.jobs):
            job_var = self._job_vars[idx]
            task_vars = [self._task_vars[task] for task in job.tasks]
            model.add(cpo.span(job_var, task_vars))

    def _select_one_mode(self):
        """
        Selects one mode for each task, ensuring that each task performs
        exactly one mode.
        """
        model, data = self._model, self._data

        for task_idx in range(data.num_tasks):
            mode_idcs = data.task2modes(task_idx)
            mode_vars = [self._mode_vars[idx] for idx in mode_idcs]
            model.add(cpo.alternative(self._task_vars[task_idx], mode_vars))

    def _machines_no_overlap_and_setup_times(self):
        """
        Creates the no-overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping. If setup times are
        available, the setup times are enforced as well.
        """
        model, data = self._model, self._data

        for idx in data.machine_idcs:
            if not data.resource2modes(idx):
                continue  # skip because cpo warns if there are no modes

            seq_var = self._sequence_vars[idx]
            setup_times = utils.setup_times_matrix(data)

            if setup_times is not None:
                # The indexing of setup times is correctly handled by the
                # interval variable's task index "type".
                matrix = setup_times[idx, :, :]
                matrix = matrix if np.any(matrix > 0) else None
            else:
                matrix = None

            model.add(cpo.no_overlap(seq_var, matrix))

    def _get_demand(self, mode_idx: int, res_idx: int) -> int:
        """
        Returns the demand of the mode for a specific resource.
        """
        mode = self._data.modes[mode_idx]
        return mode.demands[mode.resources.index(res_idx)]

    def _renewable_capacity(self):
        """
        Creates capacity constraints for the renewable resources.
        """
        model, data = self._model, self._data

        for res_idx in data.renewable_idcs:
            modes = data.resource2modes(res_idx)
            pulses = sum(
                cpo.pulse(self._mode_vars[mode_idx], demand)
                for mode_idx in modes
                # non-positive demand triggers cpo warnings
                if (demand := self._get_demand(mode_idx, res_idx)) > 0
            )
            capacity = data.resources[res_idx].capacity
            model.add(pulses <= capacity)

    def _non_renewable_capacity(self):
        """
        Creates capacity constraints for the non-renewable resources.
        """
        model, data = self._model, self._data

        for res_idx in data.non_renewable_idcs:
            modes = data.resource2modes(res_idx)
            usage = sum(
                cpo.presence_of(self._mode_vars[mode_idx])
                * self._get_demand(mode_idx, res_idx)
                for mode_idx in modes
            )
            capacity = data.resources[res_idx].capacity
            model.add(usage <= capacity)

    def _resource_breaks_constraints(self):
        """
        Creates constraints for renewable resources that have breaks.
        """
        model, data = self._model, self._data

        for res_idx in data.renewable_idcs + data.machine_idcs:
            for start, end in data.resources[res_idx].breaks:
                for mode_idx in data.resource2modes(res_idx):
                    step = CpoStepFunction()
                    step.set_value(0, MAX_VALUE, 1)
                    step.set_value(start, end, 0)

                    expr = cpo.forbid_extent(self._mode_vars[mode_idx], step)
                    model.add(expr)

    def _timing_constraints(self):
        """
        Creates constraints based on the task graph for task variables.
        """
        model, data = self._model, self._data

        for idx1, idx2, delay in data.constraints.start_before_start:
            task_var1 = self._task_vars[idx1]
            task_var2 = self._task_vars[idx2]
            model.add(cpo.start_before_start(task_var1, task_var2, delay))

        for idx1, idx2, delay in data.constraints.start_before_end:
            task_var1 = self._task_vars[idx1]
            task_var2 = self._task_vars[idx2]
            model.add(cpo.start_before_end(task_var1, task_var2, delay))

        for idx1, idx2, delay in data.constraints.end_before_start:
            task_var1 = self._task_vars[idx1]
            task_var2 = self._task_vars[idx2]
            model.add(cpo.end_before_start(task_var1, task_var2, delay))

        for idx1, idx2, delay in data.constraints.end_before_end:
            task_var1 = self._task_vars[idx1]
            task_var2 = self._task_vars[idx2]
            model.add(cpo.end_before_end(task_var1, task_var2, delay))

    def _identical_and_different_resource_constraints(self):
        """
        Creates constraints for identical and different resources constraints.
        """
        model, data = self._model, self._data

        for idx1, idx2 in data.constraints.identical_resources:
            for mode1, modes2 in utils.identical_modes(data, idx1, idx2):
                expr1 = cpo.presence_of(self._mode_vars[mode1])
                expr2 = sum(
                    cpo.presence_of(self._mode_vars[mode2]) for mode2 in modes2
                )
                model.add(expr1 <= expr2)

        for idx1, idx2 in data.constraints.different_resources:
            for mode1, modes2 in utils.different_modes(data, idx1, idx2):
                expr1 = cpo.presence_of(self._mode_vars[mode1])
                expr2 = sum(
                    cpo.presence_of(self._mode_vars[mode2]) for mode2 in modes2
                )
                model.add(expr1 <= expr2)

    def _consecutive_constraints(self):
        """
        Creates the consecutive constraints.
        """
        model, data = self._model, self._data

        for idx1, idx2 in data.constraints.consecutive:
            intersecting = utils.intersecting_modes(data, idx1, idx2)

            for mode1, mode2, resources in intersecting:
                res_idcs = set(resources) & set(data.machine_idcs)

                for res_idx in res_idcs:
                    seq_var = self._sequence_vars[res_idx]
                    var1 = self._mode_vars[mode1]
                    var2 = self._mode_vars[mode2]

                    model.add(cpo.previous(seq_var, var1, var2))

    def _mode_dependencies(self):
        """
        Implements the mode dependency constraints.
        """
        model, data = self._model, self._data

        for idx1, idcs2 in data.constraints.mode_dependencies:
            mode_var1 = self._mode_vars[idx1]
            modes_vars2 = [self._mode_vars[idx] for idx in idcs2]
            expr1 = cpo.presence_of(mode_var1)
            expr2 = sum(cpo.presence_of(mode2) for mode2 in modes_vars2)

            model.add(expr1 <= expr2)

    def add_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._machines_no_overlap_and_setup_times()
        self._renewable_capacity()
        self._non_renewable_capacity()
        self._resource_breaks_constraints()
        self._timing_constraints()
        self._identical_and_different_resource_constraints()
        self._consecutive_constraints()
        self._mode_dependencies()
