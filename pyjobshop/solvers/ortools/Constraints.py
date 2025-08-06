from collections import defaultdict
from itertools import product

import numpy as np
from ortools.sat.python.cp_model import CpModel, LinearExpr

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import ProblemData
from pyjobshop.solvers.ortools.Variables import Variables


class Constraints:
    """
    Builds the core constraints of the OR-Tools model.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, variables: Variables
    ):
        self._model = model
        self._data = data
        self._variables = variables

    def _job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx, job in enumerate(data.jobs):
            job_var = variables.job_vars[idx]
            starts = [variables.task_vars[task].start for task in job.tasks]
            ends = [variables.task_vars[task].end for task in job.tasks]

            model.add_min_equality(job_var.start, starts)
            model.add_max_equality(job_var.end, ends)

    def _select_one_mode(self):
        """
        Selects one mode for each task, ensuring that each task obtains the
        correct duration, is assigned to a set of resources, and demands are
        correctly set.
        """
        model, data, variables = self._model, self._data, self._variables

        for task_idx in range(data.num_tasks):
            task_var = variables.task_vars[task_idx]
            mode_idcs = data.task2modes(task_idx)
            mode_vars = [variables.mode_vars[idx] for idx in mode_idcs]
            model.add_exactly_one(mode_vars)

            for mode_idx, mode_var in zip(mode_idcs, mode_vars):
                mode = data.modes[mode_idx]

                # Set task duration to the selected mode's duration.
                fixed = data.tasks[task_idx].fixed_duration
                expr = (
                    task_var.duration == mode.duration
                    if fixed
                    else task_var.duration >= mode.duration
                )
                model.add(expr).only_enforce_if(mode_var)

                for res_idx in range(data.num_resources):
                    if (task_idx, res_idx) not in variables.assign_vars:
                        continue

                    # Select assignments based on selected mode's resources.
                    # Because of cross interactions with assignment constraints
                    # we also explicitly set absence of assignment variables.
                    presence = variables.assign_vars[task_idx, res_idx].present
                    required = res_idx in mode.resources
                    model.add(presence == required).only_enforce_if(mode_var)

                for res_idx, demand in zip(mode.resources, mode.demands):
                    # Set demands based on selected mode's demands.
                    dem_var = variables.assign_vars[task_idx, res_idx].demand
                    model.add(dem_var == demand).only_enforce_if(mode_var)

    def _machines_no_overlap(self):
        """
        Creates no-overlap constraints for machines.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx in data.machine_idcs:
            intervals = [var.interval for var in variables.res2assign(idx)]
            intervals += [
                model.new_fixed_size_interval_var(start, end - start, "")
                for start, end in data.resources[idx].breaks
            ]
            model.add_no_overlap(intervals)

    def _renewable_capacity(self):
        """
        Creates capacity constraints for the renewable resources.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx in data.renewable_idcs:
            intervals = [var.interval for var in variables.res2assign(idx)]
            demands = [var.demand for var in variables.res2assign(idx)]
            capacity = data.resources[idx].capacity
            model.add_cumulative(intervals, demands, capacity)

    def _non_renewable_capacity(self):
        """
        Creates capacity constraints for the non-renewable resources.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx in data.non_renewable_idcs:
            demands = [var.demand for var in variables.res2assign(idx)]
            total = LinearExpr.sum(demands)
            capacity = data.resources[idx].capacity
            model.add(total <= capacity)

    def _renewable_resource_breaks_constraints(self):
        """
        Creates constraints for renewable resources that have breaks.
        """
        model, data, variables = self._model, self._data, self._variables

        res2vars = defaultdict(list)
        for (_, res_idx), var in variables.assign_vars.items():
            res2vars[res_idx].append(var)

        for res_idx in data.renewable_idcs:
            intervals = [
                model.new_fixed_size_interval_var(start, end - start, "")
                for start, end in data.resources[res_idx].breaks
            ]
            for var in res2vars[res_idx]:
                model.add_no_overlap([var.interval, *intervals])

    def _timing_constraints(self):
        """
        Creates constraints based on the timing relationship between tasks.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx1, idx2, delay in data.constraints.start_before_start:
            expr1 = variables.task_vars[idx1].start + delay
            expr2 = variables.task_vars[idx2].start
            model.add(expr1 <= expr2)

        for idx1, idx2, delay in data.constraints.start_before_end:
            expr1 = variables.task_vars[idx1].start + delay
            expr2 = variables.task_vars[idx2].end
            model.add(expr1 <= expr2)

        for idx1, idx2, delay in data.constraints.end_before_start:
            expr1 = variables.task_vars[idx1].end + delay
            expr2 = variables.task_vars[idx2].start
            model.add(expr1 <= expr2)

        for idx1, idx2, delay in data.constraints.end_before_end:
            expr1 = variables.task_vars[idx1].end + delay
            expr2 = variables.task_vars[idx2].end
            model.add(expr1 <= expr2)

    def _identical_and_different_resource_constraints(self):
        """
        Creates constraints for identical and different resources constraints.
        """
        model, data, variables = self._model, self._data, self._variables

        for task_idx1, task_idx2 in data.constraints.identical_resources:
            for res_idx in range(data.num_resources):
                assign1 = variables.assign_vars.get((task_idx1, res_idx))
                assign2 = variables.assign_vars.get((task_idx2, res_idx))
                presence1 = assign1.present if assign1 else 0
                presence2 = assign2.present if assign2 else 0

                model.add(presence1 == presence2)

        for task_idx1, task_idx2 in data.constraints.different_resources:
            for res_idx in range(data.num_resources):
                assign1 = variables.assign_vars.get((task_idx1, res_idx))
                assign2 = variables.assign_vars.get((task_idx2, res_idx))
                presence1 = assign1.present if assign1 else 0
                presence2 = assign2.present if assign2 else 0

                model.add(presence2 == 0).only_enforce_if(presence1)

    def _consecutive_constraints(self):
        """
        Creates the consecutive constraints.
        """
        model, data, variables = self._model, self._data, self._variables

        for task_idx1, task_idx2 in data.constraints.consecutive:
            for res_idx in data.machine_idcs:
                seq_var = variables.sequence_vars[res_idx]
                seq_var.activate(model)
                var1 = variables.assign_vars.get((task_idx1, res_idx))
                var2 = variables.assign_vars.get((task_idx2, res_idx))

                if not (var1 and var2):
                    continue

                arc = seq_var.arcs[task_idx1, task_idx2]
                both_present = [var1.present, var2.present]

                model.add(arc == 1).only_enforce_if(both_present)

    def _same_sequence_constraints(self):
        """
        Creates the same sequence constraints.
        """
        model, data, variables = self._model, self._data, self._variables

        for idcs in data.constraints.same_sequence:
            res_idx1, res_idx2, task_idcs1, task_idcs2 = idcs

            seq_var1 = variables.sequence_vars[res_idx1]
            seq_var2 = variables.sequence_vars[res_idx2]
            seq_var1.activate(model)
            seq_var2.activate(model)

            if task_idcs1 is None:
                mode_idcs1 = data.resource2modes(res_idx1)
                task_idcs1 = sorted(data.modes[idx].task for idx in mode_idcs1)

            if task_idcs2 is None:
                mode_idcs2 = data.resource2modes(res_idx2)
                task_idcs2 = sorted(data.modes[idx].task for idx in mode_idcs2)

            pairs1 = product(task_idcs1, repeat=2)
            pairs2 = product(task_idcs2, repeat=2)

            for (i, j), (u, v) in zip(pairs1, pairs2):
                # This ensures that task i -> j on machine 1 if and only if
                # u -> v on machine 2.
                arc1 = seq_var1.arcs[i, j]
                arc2 = seq_var2.arcs[u, v]
                model.add(arc1 == arc2)

    def _circuit_constraints(self):
        """
        Creates the circuit constraints for each machine, if activated by
        sequencing constraints.
        """
        model, data, variables = self._model, self._data, self._variables
        setup_times = utils.setup_times_matrix(data)

        for res_idx in data.machine_idcs:
            machine = data.resources[res_idx]
            seq_var = variables.sequence_vars[res_idx]

            if setup_times is not None and np.any(setup_times[res_idx]):
                seq_var.activate(model)

            if machine.no_idle:
                seq_var.activate(model)

            if not seq_var.is_active:
                # No sequencing constraints active. Skip the creation of
                # expensive circuit constraints.
                continue

            arcs = seq_var.arcs
            graph = [(u, v, var) for (u, v), var in arcs.items()]
            model.add_circuit(graph)

            res_modes = data.resource2modes(res_idx)
            res_tasks = {data.modes[m].task for m in res_modes}

            for task_idx1 in res_tasks:
                var1 = variables.assign_vars[task_idx1, res_idx]

                # Absent intervals require selecting loops (self-arcs).
                loop = arcs[task_idx1, task_idx1]
                model.add(loop == ~var1.present)

                # This handles the case where a machine does not process any
                # task. Selecting the dummy loop makes all intervals absent,
                # and satisfies the circuit constraint.
                dummy_loop = arcs[seq_var.DUMMY, seq_var.DUMMY]
                model.add(dummy_loop <= ~var1.present)

                for task_idx2 in res_tasks:
                    if task_idx1 == task_idx2:
                        continue

                    var2 = variables.assign_vars[task_idx2, res_idx]
                    arc = arcs[task_idx1, task_idx2]
                    model.add(arc <= var1.present)
                    model.add(arc <= var2.present)

                    setup = (
                        setup_times[res_idx, task_idx1, task_idx2]
                        if setup_times is not None
                        else 0
                    )

                    if machine.no_idle:
                        expr = var1.end + setup == var2.start
                    else:
                        expr = var1.end + setup <= var2.start

                    model.add(expr).only_enforce_if(arc)

    def _mode_dependencies(self):
        """
        Implements the mode dependency constraints.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx1, idcs2 in data.constraints.mode_dependencies:
            expr1 = variables.mode_vars[idx1]
            expr2 = sum(variables.mode_vars[idx] for idx in idcs2)
            model.add(expr1 <= expr2)

    def add_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._machines_no_overlap()
        self._renewable_capacity()
        self._non_renewable_capacity()
        self._renewable_resource_breaks_constraints()
        self._timing_constraints()
        self._identical_and_different_resource_constraints()
        self._consecutive_constraints()
        self._same_sequence_constraints()
        self._mode_dependencies()

        # From here onwards we know which sequence constraints are active.
        self._circuit_constraints()
