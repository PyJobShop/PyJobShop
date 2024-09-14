from itertools import product

import numpy as np
from ortools.sat.python.cp_model import CpModel, LinearExpr

import pyjobshop.utils as utils
from pyjobshop.ProblemData import Constraint, Machine, ProblemData

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

    def _no_overlap_resources(self):
        """
        Creates the no overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping.
        """
        model, data = self._model, self._data

        for idx, resource in enumerate(data.resources):
            if isinstance(resource, Machine):
                seq_var = self._sequence_vars[idx]
                assert seq_var is not None
                model.add_no_overlap([var.interval for var in seq_var.modes])

    def _activate_setup_times(self):
        """
        Activates the sequence variables for resources that have setup times.
        The ``circuit_constraints`` function will in turn add constraints to
        the CP-SAT model to enforce setup times.
        """
        model, data = self._model, self._data

        for idx, resource in enumerate(data.resources):
            if isinstance(resource, Machine):
                seq_var = self._sequence_vars[idx]
                has_setup_times = np.any(data.setup_times[idx])

                if seq_var is not None and has_setup_times:
                    seq_var.activate(model)

    def _resource_capacity(self):
        """
        Creates constraints for the resource capacity.
        """
        model, data = self._model, self._data
        mode_vars = self._mode_vars

        # Map resources to the relevant modes and their demands.
        mapper = [[] for _ in range(data.num_resources)]
        for idx, mode in enumerate(data.modes):
            for resource, demand in zip(mode.resources, mode.demands):
                if demand > 0:
                    mapper[resource].append((idx, demand))

        for idx, resource in enumerate(data.resources):
            if isinstance(resource, Machine):
                continue  # handled by no-overlap constraints

            demands = [demand for _, demand in mapper[idx]]
            if resource.renewable:
                intvs = [mode_vars[mode].interval for mode, _ in mapper[idx]]
                model.add_cumulative(intvs, demands, resource.capacity)
            else:
                precenses = [
                    mode_vars[mode].is_present for mode, _ in mapper[idx]
                ]
                usage = LinearExpr.weighted_sum(precenses, demands)
                model.add(usage <= resource.capacity)

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

            # Find the modes of the task that have intersecting resources,
            # because we need to enforce sequencing constraints on them.
            intersecting = utils.find_modes_with_intersecting_resources(
                data, task1, task2
            )
            for mode1, mode2, resources in intersecting:
                if any(
                    not isinstance(data.resources[res], Machine)
                    for res in resources
                ):
                    raise ValueError(
                        "Resource must be machine for sequencing constraints."
                    )

                for resource in resources:
                    seq_var = self._sequence_vars[resource]
                    if seq_var is None:
                        msg = f"No sequence var found for resource {resource}."
                        raise ValueError(msg)

                    var1 = self._mode_vars[mode1]
                    var2 = self._mode_vars[mode2]

                    if Constraint.PREVIOUS in sequencing_constraints:
                        seq_var.activate(model)

                        idx1 = seq_var.modes.index(var1)
                        idx2 = seq_var.modes.index(var2)
                        arc = seq_var.arcs[idx1, idx2]

                        # arc <=> var1.is_present & var2.is_present
                        model.add_bool_or(
                            [arc, ~var1.is_present, ~var2.is_present]
                        )
                        model.add_implication(arc, var1.is_present)
                        model.add_implication(arc, var2.is_present)

                    if Constraint.BEFORE in sequencing_constraints:
                        seq_var.activate(model)
                        both_present = model.new_bool_var("")

                        # both_present <=> var1.is_present & var2.is_present
                        model.add_bool_or(
                            [both_present, ~var1.is_present, ~var2.is_present]
                        )
                        model.add_implication(both_present, var1.is_present)
                        model.add_implication(both_present, var2.is_present)

                        # Schedule var1 before var2 when both are present.
                        idx1 = seq_var.modes.index(var1)
                        idx2 = seq_var.modes.index(var2)
                        rank1 = seq_var.ranks[idx1]
                        rank2 = seq_var.ranks[idx2]

                        model.add(rank1 <= rank2).only_enforce_if(both_present)

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
                    var1 = self._mode_vars[mode1].is_present
                    vars2 = [
                        self._mode_vars[mode2].is_present
                        for mode2 in identical_modes2
                    ]
                    model.add(sum(vars2) >= var1)

                if Constraint.DIFFERENT_RESOURCES in assignment_constraints:
                    disjoint_modes2 = disjoint[mode1]
                    var1 = self._mode_vars[mode1].is_present
                    vars2 = [
                        self._mode_vars[mode2].is_present
                        for mode2 in disjoint_modes2
                    ]
                    model.add(sum(vars2) >= var1)

    def _enforce_circuit(self):
        """
        Enforce the circuit constraints for each resource, ensuring that the
        sequencing constraints are respected.

        IMPORTANT: This is specifically implemented for the experiments in the
        paper and it is not meant to be used outside the scope of those
        experiments because it may not be compatible with all other features.
        """
        model, data = self._model, self._data

        if not data.permutation:
            return  # not a permutation problem, skip

        # Create arcs for circuit constraints.
        arcs = []
        for idx1 in range(data.num_jobs):
            arcs.append((0, idx1 + 1, model.new_bool_var("start")))
            arcs.append((idx1 + 1, 0, model.new_bool_var("end")))

        lits = {}
        for idx1, idx2 in product(range(data.num_jobs), repeat=2):
            if idx1 != idx2:
                lit = model.new_bool_var(f"{idx1} -> {idx2}")
                lits[idx1, idx2] = lit
                arcs.append((idx1 + 1, idx2 + 1, lit))

        model.add_circuit(arcs)

        for res_idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                raise ValueError("Machines only in permutation problems.")

            seq_var = self._sequence_vars[res_idx]
            assert seq_var is not None

            for idx1, idx2 in product(range(data.num_jobs), repeat=2):
                if idx1 == idx2:
                    continue

                var1 = seq_var.modes[idx1]
                var2 = seq_var.modes[idx2]

                lit = lits[idx1, idx2]
                setup = data.setup_times[res_idx, var1.task_idx, var2.task_idx]
                expr = var1.end + setup <= var2.start
                model.add(expr).only_enforce_if(lit)

    def add_all_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._no_overlap_resources()
        self._resource_capacity()
        self._activate_setup_times()
        self._timing_constraints()
        self._previous_before_constraints()
        self._identical_and_different_resource_constraints()

        # From here onwards we know which sequence constraints are active.
        self._enforce_circuit()
