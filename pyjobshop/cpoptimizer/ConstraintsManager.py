from collections import defaultdict

import docplex.cp.modeler as cpo
import numpy as np
from docplex.cp.model import CpoModel

import pyjobshop.utils as utils
from pyjobshop.ProblemData import Constraint, ProblemData

from .VariablesManager import VariablesManager


class ConstraintsManager:
    """
    Handles the core constraints of the CP Optimizer model.
    """

    def __init__(
        self,
        model: CpoModel,
        data: ProblemData,
        vars_manager: VariablesManager,
    ):
        self._model = model
        self._data = data
        self._job_vars = vars_manager.job_vars
        self._task_vars = vars_manager.task_vars
        self._mode_vars = vars_manager.mode_vars
        self._sequence_vars = vars_manager.sequence_vars

    def _job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        model, data = self._model, self._data

        for idx, job in enumerate(data.jobs):
            job_var = self._job_vars[idx]
            job_task_vars = [self._task_vars[task] for task in job.tasks]

            model.add(cpo.span(job_var, job_task_vars))

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

    def _no_overlap_and_setup_times(self):
        """
        Creates the no-overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping. If setup times are
        available, the setup times are enforced as well.
        """
        model, data = self._model, self._data
        machine2modes = utils.machine2modes(data)

        for machine in range(data.num_machines):
            if not (modes := machine2modes[machine]):
                continue  # skip if no modes for this machine

            if data.machines[machine].capacity > 0:
                continue  # skip since machine is resource

            tasks = [data.modes[mode].task for mode in modes]
            setups = data.setup_times[machine, :, :][np.ix_(tasks, tasks)]
            seq_var = self._sequence_vars[machine]

            if np.all(setups == 0):  # no setup times
                model.add(cpo.no_overlap(seq_var))
            else:
                model.add(cpo.no_overlap(seq_var, setups))

    def _resource_capacity(self):
        """
        Creates constraints for the resource capacity.
        """
        model, data = self._model, self._data
        machine2modes = utils.machine2modes(data)

        for idx, resource in enumerate(data.machines):
            if resource.capacity == 0:
                continue

            modes = machine2modes[idx]
            demands = [
                data.modes[mode].demands[data.modes[mode].resources.index(idx)]
                for mode in modes
            ]
            pulses = []
            for mode, demand in zip(modes, demands):
                if demand > 0:
                    pulses.append(cpo.pulse(self._mode_vars[mode], demand))

            model.add(model.sum(pulses) <= resource.capacity)

    def _timing_constraints(self):
        """
        Creates constraints based on the task graph for task variables.
        """
        model, data = self._model, self._data

        for (idx1, idx2), constraints in data.constraints.items():
            task1 = self._task_vars[idx1]
            task2 = self._task_vars[idx2]

            for constraint in constraints:
                if constraint == Constraint.START_AT_START:
                    expr = cpo.start_at_start(task1, task2)
                elif constraint == Constraint.START_AT_END:
                    expr = cpo.start_at_end(task1, task2)
                elif constraint == Constraint.START_BEFORE_START:
                    expr = cpo.start_before_start(task1, task2)
                elif constraint == Constraint.START_BEFORE_END:
                    expr = cpo.start_before_end(task1, task2)
                elif constraint == Constraint.END_AT_START:
                    expr = cpo.end_at_start(task1, task2)
                elif constraint == Constraint.END_AT_END:
                    expr = cpo.end_at_end(task1, task2)
                elif constraint == Constraint.END_BEFORE_START:
                    expr = cpo.end_before_start(task1, task2)
                elif constraint == Constraint.END_BEFORE_END:
                    expr = cpo.end_before_end(task1, task2)
                else:
                    continue

                model.add(expr)

    def _previous_before_constraints(self):
        """
        Creates constraints based on the task graph which involve task
        alternative variables.
        """
        model, data = self._model, self._data
        task2modes = utils.task2modes(data)
        relevant_constraints = {
            Constraint.PREVIOUS,
            Constraint.BEFORE,
        }

        for (task1, task2), constraints in data.constraints.items():
            task_alt_constraints = set(constraints) & relevant_constraints
            if not task_alt_constraints:
                continue

            # Find the common modes for both tasks, because the constraints
            # apply to the mode variables on the same machine.
            # TODO this is super complex but I don't have a good idea yet
            # how to deal with modes and assignment constraints.
            modes1 = task2modes[task1]
            modes2 = task2modes[task2]
            machines1 = [
                machine
                for mode in modes1
                for machine in data.modes[mode].resources
            ]
            machines2 = [
                machine
                for mode in modes2
                for machine in data.modes[mode].resources
            ]
            machines = set(machines1) & set(machines2)

            for machine in machines:
                seq_var = self._sequence_vars[machine]
                mode1 = modes1[machines1.index(machine)]
                mode2 = modes2[machines2.index(machine)]
                var1 = self._mode_vars[mode1]
                var2 = self._mode_vars[mode2]

                for constraint in task_alt_constraints:
                    if constraint == Constraint.PREVIOUS:
                        expr = cpo.previous(seq_var, var1, var2)
                    elif constraint == Constraint.BEFORE:
                        expr = cpo.before(seq_var, var1, var2)

                    model.add(expr)

    def _same_and_different_machine_constraints(self):
        """
        Creates the constraints for the same and different machine constraints.
        """
        model, data = self._model, self._data
        task2modes = utils.task2modes(data)
        relevant = {Constraint.SAME_MACHINE, Constraint.DIFFERENT_MACHINE}

        for (task1, task2), constraints in data.constraints.items():
            task_alt_constraints = set(constraints) & relevant
            if not task_alt_constraints:
                continue

            modes1 = task2modes[task1]
            modes2 = task2modes[task2]

            # Find the modes of task 2 that use the same machines or disjoint
            # machines with the modes of task 1.
            same = defaultdict(list)
            disjoint = defaultdict(list)
            for idx1 in modes1:
                resources1 = set(data.modes[idx1].resources)
                for idx2 in modes2:
                    resources2 = set(data.modes[idx2].resources)
                    if resources1 == resources2:
                        same[idx1].append(idx2)
                    if resources1.isdisjoint(resources2):
                        disjoint[idx1].append(idx2)

            for constraint in task_alt_constraints:
                if constraint == Constraint.SAME_MACHINE:
                    for mode1 in modes1:
                        same_modes2 = same[mode1]
                        var1 = cpo.presence_of(self._mode_vars[mode1])
                        vars2 = [
                            cpo.presence_of(self._mode_vars[mode2])
                            for mode2 in same_modes2
                        ]
                        model.add(sum(vars2) >= var1)
                elif constraint == Constraint.DIFFERENT_MACHINE:
                    for mode1 in modes1:
                        disjoint_modes2 = disjoint[mode1]
                        var1 = cpo.presence_of(self._mode_vars[mode1])
                        vars2 = [
                            cpo.presence_of(self._mode_vars[mode2])
                            for mode2 in disjoint_modes2
                        ]
                        model.add(sum(vars2) >= var1)

    def add_all_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._no_overlap_and_setup_times()
        self._resource_capacity()
        self._timing_constraints()
        self._previous_before_constraints()
        self._same_and_different_machine_constraints()
