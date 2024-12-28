import numpy as np
from ortools.sat.python.cp_model import BoolVarT, CpModel, LinearExpr

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import Constraint, Machine, ProblemData

from .Variables import Variables


class Constraints:
    """
    Builds the core constraints of the OR-Tools model.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, variables: Variables
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
            task_starts = []
            task_ends = []

            for task in job.tasks:
                task_var = self._task_vars[task]

                if data.tasks[task].optional:
                    # When tasks are absent, they should not restrict the job's
                    # start and end times.
                    task_start = model.new_int_var(0, data.horizon, "")
                    task_end = model.new_int_var(0, data.horizon, "")

                    expr = task_start == task_var.start
                    model.add(expr).only_enforce_if(task_var.is_present)

                    expr = task_end == task_var.end
                    model.add(expr).only_enforce_if(task_var.is_present)
                else:
                    task_start = task_var.start
                    task_end = task_var.end

                task_starts.append(task_start)
                task_ends.append(task_end)

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
            task_var = self._task_vars[task]

            # Select exactly one optional interval variable for each task.
            presences = [
                self._mode_vars[mode].is_present for mode in task2modes[task]
            ]
            model.add(sum(presences) == task_var.is_present)

            for mode in task2modes[task]:
                mode_var = self._mode_vars[mode]
                both_present = [task_var.is_present, mode_var.is_present]

                # Sync each optional interval variable with the main variable.
                model.add(task_var.start == mode_var.start).only_enforce_if(
                    both_present
                )
                model.add(
                    task_var.duration == mode_var.duration
                ).only_enforce_if(both_present)
                model.add(task_var.end == mode_var.end).only_enforce_if(
                    both_present
                )

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
                mode_vars = [var.interval for var in seq_var.mode_vars]
                model.add_no_overlap(mode_vars)

    def _activate_setup_times(self):
        """
        Activates the sequence variables for resources that have setup times.
        The ``_circuit_constraints`` function will in turn add
        constraints to the CP-SAT model to enforce setup times.
        """
        model, data = self._model, self._data

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            if data.setup_times is not None and np.any(data.setup_times[idx]):
                seq_var = self._sequence_vars[idx]
                assert seq_var is not None
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
            if isinstance(idx2, tuple):
                continue  # HACK for if-then constraints

            task_var1 = self._task_vars[idx1]
            task_var2 = self._task_vars[idx2]
            both_present = [task_var1.is_present, task_var2.is_present]

            if Constraint.START_AT_START in constraints:
                expr = task_var1.start == task_var2.start
                model.add(expr).only_enforce_if(both_present)

            if Constraint.START_AT_END in constraints:
                expr = task_var1.start == task_var2.end
                model.add(expr).only_enforce_if(both_present)

            if Constraint.START_BEFORE_START in constraints:
                expr = task_var1.start <= task_var2.start
                model.add(expr).only_enforce_if(both_present)

            if Constraint.START_BEFORE_END in constraints:
                expr = task_var1.start <= task_var2.end
                model.add(expr).only_enforce_if(both_present)

            if Constraint.END_AT_START in constraints:
                expr = task_var1.end == task_var2.start
                model.add(expr).only_enforce_if(both_present)

            if Constraint.END_AT_END in constraints:
                expr = task_var1.end == task_var2.end
                model.add(expr).only_enforce_if(both_present)

            if Constraint.END_BEFORE_START in constraints:
                expr = task_var1.end <= task_var2.start
                model.add(expr).only_enforce_if(both_present)

            if Constraint.END_BEFORE_END in constraints:
                expr = task_var1.end <= task_var2.end
                model.add(expr).only_enforce_if(both_present)

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
                for resource in resources:
                    if not isinstance(data.resources[resource], Machine):
                        continue  # skip sequencing on non-machine resources

                    seq_var = self._sequence_vars[resource]
                    if seq_var is None:
                        msg = f"No sequence var found for resource {resource}."
                        raise ValueError(msg)

                    var1 = self._mode_vars[mode1]
                    var2 = self._mode_vars[mode2]

                    if Constraint.PREVIOUS in sequencing_constraints:
                        seq_var.activate(model)

                        idx1 = seq_var.mode_vars.index(var1)
                        idx2 = seq_var.mode_vars.index(var2)
                        arc = seq_var.arcs[idx1, idx2]
                        both_present = [var1.is_present, var2.is_present]

                        model.add(arc == 1).only_enforce_if(both_present)

                    if Constraint.BEFORE in sequencing_constraints:
                        seq_var.activate(model)

                        idx1 = seq_var.mode_vars.index(var1)
                        idx2 = seq_var.mode_vars.index(var2)
                        rank1 = seq_var.ranks[idx1]
                        rank2 = seq_var.ranks[idx2]
                        both_present = [var1.is_present, var2.is_present]

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
            both_present = [
                self._task_vars[task1].is_present,
                self._task_vars[task2].is_present,
            ]

            for mode1 in modes1:
                if Constraint.IDENTICAL_RESOURCES in assignment_constraints:
                    identical_modes2 = identical[mode1]
                    var1 = self._mode_vars[mode1].is_present
                    vars2 = [
                        self._mode_vars[mode2].is_present
                        for mode2 in identical_modes2
                    ]
                    model.add(sum(vars2) >= var1).only_enforce_if(both_present)

                if Constraint.DIFFERENT_RESOURCES in assignment_constraints:
                    disjoint_modes2 = disjoint[mode1]
                    var1 = self._mode_vars[mode1].is_present
                    vars2 = [
                        self._mode_vars[mode2].is_present
                        for mode2 in disjoint_modes2
                    ]
                    model.add(sum(vars2) >= var1).only_enforce_if(both_present)

    def _if_then_constraints(self):
        """
        Creates the if-then constraints.
        """
        model, data = self._model, self._data

        for (idx1, idcs2), constraints in data.constraints.items():
            if Constraint.IF_THEN not in constraints:
                continue

            task_var1 = self._task_vars[idx1]
            task_vars2 = [self._task_vars[idx2] for idx2 in idcs2]
            model.add(
                task_var1.is_present
                <= sum(var.is_present for var in task_vars2)
            )

    def _circuit_constraints(self):
        """
        Creates the circuit constraints for each machine, if activated by
        sequencing constraints (before, previous and setup times).
        """
        model, data = self._model, self._data

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            seq_var = self._sequence_vars[idx]
            assert seq_var is not None

            if not seq_var.is_active:
                # No sequencing constraints active. Skip the creation of
                # (expensive) circuit constraints.
                continue

            modes = seq_var.mode_vars
            starts = seq_var.starts
            ends = seq_var.ends
            ranks = seq_var.ranks
            arcs = seq_var.arcs

            # Add dummy node self-arc to allow empty circuits.
            empty = model.new_bool_var(f"empty_circuit_{idx}")
            graph: list[tuple[int, int, BoolVarT]] = [(-1, -1, empty)]

            for idx1, var1 in enumerate(modes):
                start = starts[idx1]  # "is start node" literal
                end = ends[idx1]  # "is end node" literal
                rank = ranks[idx1]

                # Arcs from the dummy node to/from a task.
                graph.append((-1, idx1, start))
                graph.append((idx1, -1, end))

                # Set rank for first task in the sequence.
                model.add(rank == 0).only_enforce_if(start)

                # Self arc if the task is not present.
                graph.append((idx1, idx1, ~var1.is_present))
                model.add(rank == -1).only_enforce_if(~var1.is_present)

                # If the circuit is empty then the var should not be present.
                model.add_implication(empty, ~var1.is_present)

                for idx2, var2 in enumerate(modes):
                    if idx1 == idx2:
                        continue

                    arc = arcs[idx1, idx2]
                    graph.append((idx1, idx2, arc))

                    model.add_implication(arc, var1.is_present)
                    model.add_implication(arc, var2.is_present)

                    # Maintain rank incrementally.
                    model.add(rank + 1 == ranks[idx2]).only_enforce_if(arc)

                    # Use the mode's task idx to get the correct setup times.
                    setup = (
                        data.setup_times[idx, var1.task_idx, var2.task_idx]
                        if data.setup_times is not None
                        else 0
                    )
                    expr = var1.end + setup <= var2.start
                    model.add(expr).only_enforce_if(arc)

            model.add_circuit(graph)

    def add_constraints(self):
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
        self._if_then_constraints()

        # From here onwards we know which sequence constraints are active.
        self._circuit_constraints()
