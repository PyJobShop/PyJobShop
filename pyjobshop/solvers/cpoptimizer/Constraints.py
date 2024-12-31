import docplex.cp.modeler as cpo
import numpy as np
from docplex.cp.model import CpoModel

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import (
    Constraint,
    Machine,
    NonRenewable,
    ProblemData,
    Renewable,
)

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
        task2modes = utils.task2modes(data)

        for task in range(data.num_tasks):
            mode_vars = [self._mode_vars[mode] for mode in task2modes[task]]
            model.add(cpo.alternative(self._task_vars[task], mode_vars))

    def _machines_no_overlap_and_setup_times(self):
        """
        Creates the no-overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping. If setup times are
        available, the setup times are enforced as well.
        """
        model, data = self._model, self._data
        resource2modes = utils.resource2modes(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            if not (modes := resource2modes[idx]):
                continue  # skip because cpo warns if there are no modes

            seq_var = self._sequence_vars[idx]

            if (setups := data.setup_times) is not None:
                # Use the mode's task indices to get the correct setup times.
                tasks = [data.modes[mode].task for mode in modes]
                matrix = setups[idx, :, :][np.ix_(tasks, tasks)]
                matrix = matrix if np.any(matrix > 0) else None
            else:
                matrix = None

            model.add(cpo.no_overlap(seq_var, matrix))

    def _renewable_capacity(self):
        """
        Creates capacity constraints for the renewable resources.
        """
        model, data = self._model, self._data
        res2modes, res2demands = utils.resource2modes_demands(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Renewable):
                continue

            pulses = [
                cpo.pulse(self._mode_vars[mode], demand)
                for (mode, demand) in zip(res2modes[idx], res2demands[idx])
            ]
            model.add(model.sum(pulses) <= resource.capacity)

    def _non_renewable_capacity(self):
        """
        Creates capacity constraints for the non-renewable resources.
        """
        model, data = self._model, self._data
        res2modes, res2demands = utils.resource2modes_demands(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, NonRenewable):
                continue

            usage = [
                cpo.presence_of(self._mode_vars[mode]) * demand
                for (mode, demand) in zip(res2modes[idx], res2demands[idx])
            ]
            model.add(model.sum(usage) <= resource.capacity)

    def _timing_constraints(self):
        """
        Creates constraints based on the task graph for task variables.
        """
        model, data = self._model, self._data

        for (idx1, idx2), constraints in data.constraints.items():
            task1 = self._task_vars[idx1]
            task2 = self._task_vars[idx2]

            if Constraint.START_AT_START in constraints:
                model.add(cpo.start_at_start(task1, task2))

            if Constraint.START_AT_END in constraints:
                model.add(cpo.start_at_end(task1, task2))

            if Constraint.START_BEFORE_START in constraints:
                model.add(cpo.start_before_start(task1, task2))

            if Constraint.START_BEFORE_END in constraints:
                model.add(cpo.start_before_end(task1, task2))

            if Constraint.END_AT_START in constraints:
                model.add(cpo.end_at_start(task1, task2))

            if Constraint.END_AT_END in constraints:
                model.add(cpo.end_at_end(task1, task2))

            if Constraint.END_BEFORE_START in constraints:
                model.add(cpo.end_before_start(task1, task2))

            if Constraint.END_BEFORE_END in constraints:
                model.add(cpo.end_before_end(task1, task2))

    def _identical_and_different_resource_constraints(self):
        """
        Creates constraints for the same and different resource constraints.
        """
        model, data = self._model, self._data
        task2modes = utils.task2modes(data)
        relevant = {
            Constraint.IDENTICAL_RESOURCES,
            Constraint.DIFFERENT_RESOURCES,
        }

        for (task1, task2), constraints in data.constraints.items():
            assignment_constraints = set(constraints) & relevant
            if not assignment_constraints:
                continue

            identical = utils.find_modes_with_identical_resources(
                data, task1, task2
            )
            disjoint = utils.find_modes_with_disjoint_resources(
                data, task1, task2
            )

            modes1 = task2modes[task1]
            for mode1 in modes1:
                if Constraint.IDENTICAL_RESOURCES in assignment_constraints:
                    identical_modes2 = identical[mode1]
                    var1 = cpo.presence_of(self._mode_vars[mode1])
                    vars2 = [
                        cpo.presence_of(self._mode_vars[mode2])
                        for mode2 in identical_modes2
                    ]
                    model.add(sum(vars2) >= var1)

                if Constraint.DIFFERENT_RESOURCES in assignment_constraints:
                    disjoint_modes2 = disjoint[mode1]
                    var1 = cpo.presence_of(self._mode_vars[mode1])
                    vars2 = [
                        cpo.presence_of(self._mode_vars[mode2])
                        for mode2 in disjoint_modes2
                    ]
                    model.add(sum(vars2) >= var1)

    def _consecutive_constraints(self):
        """
        Creates the consecutive constraints.
        """
        model, data = self._model, self._data

        for (task1, task2), constraints in data.constraints.items():
            if Constraint.CONSECUTIVE not in constraints:
                continue

            # Find the modes of the task that have intersecting resources,
            # because we need to enforce consecutive constraints on them.
            intersecting = utils.find_modes_with_intersecting_resources(
                data, task1, task2
            )
            for mode1, mode2, resources in intersecting:
                for resource in resources:
                    if not isinstance(data.resources[resource], Machine):
                        continue  # skip sequencing on non-machine resources

                    seq_var = self._sequence_vars[resource]
                    var1 = self._mode_vars[mode1]
                    var2 = self._mode_vars[mode2]

                    model.add(cpo.previous(seq_var, var1, var2))

    def add_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._machines_no_overlap_and_setup_times()
        self._renewable_capacity()
        self._non_renewable_capacity()
        self._timing_constraints()
        self._identical_and_different_resource_constraints()
        self._consecutive_constraints()
