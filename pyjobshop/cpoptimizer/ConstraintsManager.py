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
                continue

            tasks = [data.modes[mode].task for mode in modes]
            setups = data.setup_times[machine, :, :][np.ix_(tasks, tasks)]
            seq_var = self._sequence_vars[machine]

            if np.all(setups == 0):  # no setup times
                model.add(cpo.no_overlap(seq_var))
            else:
                model.add(cpo.no_overlap(seq_var, setups))

    def _machine_capacity(self):
        """
        Creates constraints for the machine capacity.
        """
        model, data = self._model, self._data

        # Map machines to the relevant modes and their demands.
        mapper = [[] for _ in range(data.num_machines)]
        for idx, mode in enumerate(data.modes):
            for machine, demand in zip(mode.machines, mode.demands):
                if demand > 0:
                    mapper[machine].append((idx, demand))

        for idx, machine in enumerate(data.machines):
            if machine.capacity == 0:
                continue

            pulses = [
                cpo.pulse(self._mode_vars[mode], demand)
                for (mode, demand) in mapper[idx]
                if demand > 0
            ]
            model.add(model.sum(pulses) <= machine.capacity)

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

    def _previous_before_constraints(self):
        """
        Creates the constraints for the previous and before constraints.
        """
        model, data = self._model, self._data
        relevant = {Constraint.PREVIOUS, Constraint.BEFORE}

        for (task1, task2), constraints in data.constraints.items():
            sequencing_constraints = set(constraints) & relevant
            if not sequencing_constraints:
                continue

            # Find the modes of the task that have intersecting machines,
            # because we need to enforce sequencing constraints on them.
            intersecting = utils.find_modes_with_intersecting_machines(
                data, task1, task2
            )
            for mode1, mode2, machines in intersecting:
                for machine in machines:
                    sequence = self._sequence_vars[machine]
                    if sequence is None:
                        msg = f"No sequence var found for machine {machine}."
                        raise ValueError(msg)

                    var1 = self._mode_vars[mode1]
                    var2 = self._mode_vars[mode2]

                    if Constraint.PREVIOUS in sequencing_constraints:
                        model.add(cpo.previous(sequence, var1, var2))

                    if Constraint.BEFORE in sequencing_constraints:
                        model.add(cpo.before(sequence, var1, var2))

    def _identical_and_different_machine_constraints(self):
        """
        Creates the constraints for the same and different machine constraints.
        """
        model, data = self._model, self._data
        task2modes = utils.task2modes(data)
        relevant = {
            Constraint.IDENTICAL_MACHINES,
            Constraint.DIFFERENT_MACHINES,
        }

        for (task1, task2), constraints in data.constraints.items():
            assignment_constraints = set(constraints) & relevant
            if not assignment_constraints:
                continue

            identical = utils.find_modes_with_identical_machines(
                data, task1, task2
            )
            disjoint = utils.find_modes_with_disjoint_machines(
                data, task1, task2
            )

            modes1 = task2modes[task1]
            for mode1 in modes1:
                if Constraint.IDENTICAL_MACHINES in assignment_constraints:
                    identical_modes2 = identical[mode1]
                    var1 = cpo.presence_of(self._mode_vars[mode1])
                    vars2 = [
                        cpo.presence_of(self._mode_vars[mode2])
                        for mode2 in identical_modes2
                    ]
                    model.add(sum(vars2) >= var1)

                if Constraint.DIFFERENT_MACHINES in assignment_constraints:
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
        self._machine_capacity()
        self._timing_constraints()
        self._previous_before_constraints()
        self._identical_and_different_machine_constraints()
