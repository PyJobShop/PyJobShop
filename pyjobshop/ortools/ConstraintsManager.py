import numpy as np
from ortools.sat.python.cp_model import BoolVarT, CpModel

import pyjobshop.utils as utils
from pyjobshop.ProblemData import Constraint, ProblemData

from .VariablesManager import VariablesManager


class ConstraintsManager:
    """
    Handles the core constraints of the OR-Tools model.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, vars_manager: VariablesManager
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
            task_starts = [self._task_vars[task].start for task in job.tasks]
            task_ends = [self._task_vars[task].end for task in job.tasks]

            model.add_min_equality(job_var.start, task_starts)
            model.add_max_equality(job_var.end, task_ends)

    def _select_one_mode(self):
        """
        Selects one mode for each task, ensuring that each task performs
        exactly one mode.
        """
        model, data = self._model, self._data
        task2modes = utils.task2modes(data)

        for task in range(data.num_tasks):
            presences = []

            for mode in task2modes[task]:
                main = self._task_vars[task]
                opt = self._mode_vars[mode]
                is_present = opt.is_present
                presences.append(is_present)

                # Sync each optional interval variable with the main variable.
                model.add(main.start == opt.start).only_enforce_if(is_present)
                model.add(main.duration == opt.duration).only_enforce_if(
                    is_present
                )
                model.add(main.end == opt.end).only_enforce_if(is_present)

            # Select exactly one optional interval variable for each task.
            model.add_exactly_one(presences)

    def _no_overlap_machines(self):
        """
        Creates the no overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping.
        """
        model, data = self._model, self._data

        for idx in range(data.num_machines):
            if (seq_var := self._sequence_vars[idx]) is not None:
                model.add_no_overlap([var.interval for var in seq_var.modes])

    def _activate_setup_times(self):
        """
        Activates the sequence variables for machines that have setup times.
        The ``circuit_constraints`` function will in turn add constraints to
        the CP-SAT model to enforce setup times.
        """
        model, data = self._model, self._data

        for idx in range(data.num_machines):
            seq_var = self._sequence_vars[idx]
            has_setup_times = np.any(data.setup_times[idx])

            if seq_var is not None and has_setup_times:
                seq_var.activate(model)

    def _resource_capacity(self):
        """
        Creates constraints for the resource capacity.
        """
        model, data = self._model, self._data
        machine2modes = utils.machine2modes(data)

        for idx, machine in enumerate(data.machines):
            if machine.capacity == 0:
                continue

            modes = machine2modes[idx]
            intervals = [self._mode_vars[mode].interval for mode in modes]

            # TODO simplify
            demands = []
            for mode in modes:
                mode_data = data.modes[mode]
                resource_index = mode_data.resources.index(idx)
                demand = mode_data.demands[resource_index]
                demands.append(demand)

            model.add_cumulative(intervals, demands, machine.capacity)

    def _timing_constraints(self):
        """
        Creates constraints based on the timing relationship between tasks.
        """
        model, data = self._model, self._data

        for (idx1, idx2), constraints in data.constraints.items():
            task_var1 = self._task_vars[idx1]
            task_var2 = self._task_vars[idx2]

            if Constraint.START_AT_START in constraints:
                model.add(task_var1.start == task_var2.start)

            if Constraint.START_AT_END in constraints:
                model.add(task_var1.start == task_var2.end)

            if Constraint.START_BEFORE_START in constraints:
                model.add(task_var1.start <= task_var2.start)

            if Constraint.START_BEFORE_END in constraints:
                model.add(task_var1.start <= task_var2.end)

            if Constraint.END_AT_START in constraints:
                model.add(task_var1.end == task_var2.start)

            if Constraint.END_AT_END in constraints:
                model.add(task_var1.end == task_var2.end)

            if Constraint.END_BEFORE_START in constraints:
                model.add(task_var1.end <= task_var2.start)

            if Constraint.END_BEFORE_END in constraints:
                model.add(task_var1.end <= task_var2.end)

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
                        sequence.activate(model)

                        idx1 = sequence.modes.index(var1)
                        idx2 = sequence.modes.index(var2)
                        arc = sequence.arcs[idx1, idx2]

                        # arc <=> var1.is_present & var2.is_present
                        model.add_bool_or(
                            [arc, ~var1.is_present, ~var2.is_present]
                        )
                        model.add_implication(arc, var1.is_present)
                        model.add_implication(arc, var2.is_present)

                    if Constraint.BEFORE in sequencing_constraints:
                        sequence.activate(model)
                        both_present = model.new_bool_var("")

                        # both_present <=> var1.is_present & var2.is_present
                        model.add_bool_or(
                            [both_present, ~var1.is_present, ~var2.is_present]
                        )
                        model.add_implication(both_present, var1.is_present)
                        model.add_implication(both_present, var2.is_present)

                        # Schedule var1 before var2 when both are present.
                        idx1 = sequence.modes.index(var1)
                        idx2 = sequence.modes.index(var2)
                        rank1 = sequence.ranks[idx1]
                        rank2 = sequence.ranks[idx2]

                        model.add(rank1 <= rank2).only_enforce_if(both_present)

    def _same_and_different_machine_constraints(self):
        """
        Creates the constraints for the same and different machine constraints.
        """
        model, data = self._model, self._data
        task2modes = utils.task2modes(data)
        relevant = {Constraint.SAME_MACHINE, Constraint.DIFFERENT_MACHINE}

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
                if Constraint.SAME_MACHINE in assignment_constraints:
                    identical_modes2 = identical[mode1]
                    var1 = self._mode_vars[mode1].is_present
                    vars2 = [
                        self._mode_vars[mode2].is_present
                        for mode2 in identical_modes2
                    ]
                    model.add(sum(vars2) >= var1)

                if Constraint.DIFFERENT_MACHINE in assignment_constraints:
                    disjoint_modes2 = disjoint[mode1]
                    var1 = self._mode_vars[mode1].is_present
                    vars2 = [
                        self._mode_vars[mode2].is_present
                        for mode2 in disjoint_modes2
                    ]
                    model.add(sum(vars2) >= var1)

    def _enforce_circuit(self):
        """
        Enforce the circuit constraints for each machine, ensuring that the
        sequencing constraints are respected.
        """
        model, data = self._model, self._data

        for machine in range(data.num_machines):
            sequence = self._sequence_vars[machine]

            if sequence is None or not sequence.is_active:
                # No sequencing constraints found. Skip the creation of
                # (expensive) circuit constraints.
                continue

            modes = sequence.modes
            starts = sequence.starts
            ends = sequence.ends
            ranks = sequence.ranks
            arcs = sequence.arcs

            # Add dummy node self-arc to allow empty circuits.
            empty = model.new_bool_var(f"empty_circuit_{machine}")
            circuit: list[tuple[int, int, BoolVarT]] = [(-1, -1, empty)]

            for idx1, var1 in enumerate(modes):
                start = starts[idx1]  # "is start node" literal
                end = ends[idx1]  # "is end node" literal
                rank = ranks[idx1]

                # Arcs from the dummy node to/from a task.
                circuit.append((-1, idx1, start))
                circuit.append((idx1, -1, end))

                # Set rank for first task in the sequence.
                model.add(rank == 0).only_enforce_if(start)

                # Self arc if the task is not present on this machine.
                circuit.append((idx1, idx1, ~var1.is_present))
                model.add(rank == -1).only_enforce_if(~var1.is_present)

                # If the circuit is empty then the var should not be present.
                model.add_implication(empty, ~var1.is_present)

                for idx2, var2 in enumerate(modes):
                    if idx1 == idx2:
                        continue

                    arc = arcs[idx1, idx2]
                    circuit.append((idx1, idx2, arc))

                    model.add_implication(arc, var1.is_present)
                    model.add_implication(arc, var2.is_present)

                    # Maintain rank incrementally.
                    model.add(rank + 1 == ranks[idx2]).only_enforce_if(arc)

                    # TODO Validate that this cannot be combined with overlap.
                    task1, task2 = var1.task_idx, var2.task_idx
                    setup = data.setup_times[machine, task1, task2]
                    model.add(var1.end + setup <= var2.start).only_enforce_if(
                        arc
                    )

            model.add_circuit(circuit)

    def add_all_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._no_overlap_machines()
        self._resource_capacity()
        self._activate_setup_times()
        self._timing_constraints()
        self._previous_before_constraints()
        self._same_and_different_machine_constraints()

        # From here onwards we know which sequence constraints are active.
        self._enforce_circuit()
