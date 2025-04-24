from itertools import product

import numpy as np
from ortools.sat.python.cp_model import CpModel, LinearExpr

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import (
    Machine,
    NonRenewable,
    ProblemData,
    Renewable,
)
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
        self._job_vars = variables.job_vars
        self._task_vars = variables.task_vars
        self._assign_vars = variables.assign_vars
        self._sequence_vars = variables.sequence_vars

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
        mode_vars = self._variables.new_mode_vars
        assign_vars = self._assign_vars

        for task_idx in range(data.num_tasks):
            task_var = self._task_vars[task_idx]
            task_mode_vars = mode_vars[task_idx]
            model.add_exactly_one(task_mode_vars.values())

            # If mode is selected, then set task_var to corresponding
            for mode_idx, mode_var in task_mode_vars.items():
                mode = data.modes[mode_idx]

                if data.tasks[task_idx].fixed_duration:
                    expr = task_var.duration == mode.duration
                else:
                    expr = task_var.duration >= mode.duration

                model.add(expr).only_enforce_if(mode_var)

            for mode_idx, mode_var in task_mode_vars.items():
                mode = data.modes[mode_idx]

                for res_idx in range(data.num_resources):
                    assign_var = assign_vars.get((task_idx, res_idx))
                    if assign_var is None:
                        continue

                    present = assign_var.present

                    if res_idx in mode.resources:
                        # TODO explain why this is necessary
                        model.add(present == 1).only_enforce_if(mode_var)
                    else:
                        model.add(present == 0).only_enforce_if(mode_var)

                for res_idx, demand in zip(mode.resources, mode.demands):
                    demand_var = assign_vars[task_idx, res_idx].demand
                    model.add(demand_var == demand).only_enforce_if(mode_var)

    def _machines_no_overlap(self):
        """
        Creates no-overlap constraints for machines.
        """
        model, data = self._model, self._data
        assign_vars = self._assign_vars

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            res_assign_vars = [
                var
                for (_, res_idx), var in assign_vars.items()
                if res_idx == idx
            ]
            intervals = [var.interval for var in res_assign_vars]
            model.add_no_overlap(intervals)

    def _renewable_capacity(self):
        """
        Creates capacity constraints for the renewable resources.
        """
        model, data = self._model, self._data
        assign_vars = self._assign_vars

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Renewable):
                continue

            res_assign_vars = [
                var
                for (_, res_idx), var in assign_vars.items()
                if res_idx == idx
            ]
            intervals = [var.interval for var in res_assign_vars]
            demands = [var.demand for var in res_assign_vars]
            model.add_cumulative(intervals, demands, resource.capacity)

    def _non_renewable_capacity(self):
        """
        Creates capacity constraints for the non-renewable resources.
        """
        model, data = self._model, self._data
        assign_vars = self._assign_vars

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, NonRenewable):
                continue

            res_assign_vars = [
                var
                for (_, res_idx), var in assign_vars.items()
                if res_idx == idx
            ]
            demands = [var.demand for var in res_assign_vars]
            usage = LinearExpr.sum(demands)
            model.add(usage <= resource.capacity)

    def _timing_constraints(self):
        """
        Creates constraints based on the timing relationship between tasks.
        """
        model, data = self._model, self._data

        for idx1, idx2, delay in data.constraints.start_before_start:
            expr1 = self._task_vars[idx1].start + delay
            expr2 = self._task_vars[idx2].start
            model.add(expr1 <= expr2)

        for idx1, idx2, delay in data.constraints.start_before_end:
            expr1 = self._task_vars[idx1].start + delay
            expr2 = self._task_vars[idx2].end
            model.add(expr1 <= expr2)

        for idx1, idx2, delay in data.constraints.end_before_start:
            expr1 = self._task_vars[idx1].end + delay
            expr2 = self._task_vars[idx2].start
            model.add(expr1 <= expr2)

        for idx1, idx2, delay in data.constraints.end_before_end:
            expr1 = self._task_vars[idx1].end + delay
            expr2 = self._task_vars[idx2].end
            model.add(expr1 <= expr2)

    def _identical_and_different_resource_constraints(self):
        """
        Creates constraints for identical and different resources constraints.
        """
        model, data = self._model, self._data
        assign_vars = self._assign_vars

        collect = []
        for idx1, idx2 in data.constraints.identical_resources:
            for res_idx in range(data.num_resources):
                assign1 = assign_vars.get((idx1, res_idx))
                assign2 = assign_vars.get((idx2, res_idx))
                presence1 = assign1.present if assign1 else 0
                presence2 = assign2.present if assign2 else 0

                # TODO why does this not work?
                expr = presence1 <= presence2
                collect.append(
                    [idx1, idx2, res_idx, presence1, presence2, expr]
                )
                model.add(presence1 == presence2)

        for idx1, idx2 in data.constraints.different_resources:
            for res_idx in range(data.num_resources):
                assign1 = assign_vars.get((idx1, res_idx))
                assign2 = assign_vars.get((idx2, res_idx))
                presence1 = assign1.present if assign1 else 0
                presence2 = assign2.present if assign2 else 0

                model.add(presence2 == 0).only_enforce_if(presence1)

    def _activate_setup_times(self):
        """
        Activates the sequence variables for resources that have setup times.
        The ``_circuit_constraints`` function will in turn add constraints to
        the CP-SAT model to enforce setup times.
        """
        model, data = self._model, self._data
        setup_times = utils.setup_times_matrix(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            if setup_times is not None and np.any(setup_times[idx]):
                self._sequence_vars[idx].activate(model, data)

    def _consecutive_constraints(self):
        """
        Creates the consecutive constraints.
        """
        model, data = self._model, self._data

        for idx1, idx2 in data.constraints.consecutive:
            for res_idx in range(data.num_resources):
                if not isinstance(data.resources[res_idx], Machine):
                    continue

                seq_var = self._sequence_vars[res_idx]
                seq_var.activate(model, data)
                var1 = self._assign_vars.get((idx1, res_idx))
                var2 = self._assign_vars.get((idx2, res_idx))

                if not (var1 and var2):
                    continue

                arc = seq_var.arcs[idx1, idx2]
                both_present = [var1.present, var2.present]

                model.add(arc == 1).only_enforce_if(both_present)

    def _circuit_constraints(self):
        """
        Creates the circuit constraints for each machine, if activated by
        sequencing constraints (consecutive and setup times).
        """
        model, data = self._model, self._data
        assign_vars = self._assign_vars
        setup_times = utils.setup_times_matrix(data)

        for res_idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            seq_var = self._sequence_vars[res_idx]
            if not seq_var.is_active:
                # No sequencing constraints active. Skip the creation of
                # expensive circuit constraints.
                continue

            arcs = seq_var.arcs
            graph = [(u, v, var) for (u, v), var in arcs.items()]
            model.add_circuit(graph)

            for idx1 in range(data.num_tasks):
                var1 = assign_vars.get((idx1, res_idx))
                if var1:
                    # If the (dummy) self arc is selected, then the var must
                    # not be present.
                    present1 = var1.present
                    model.add(arcs[idx1, idx1] <= ~present1)
                    model.add(arcs[seq_var.DUMMY, seq_var.DUMMY] <= ~present1)

            for idx1, idx2 in product(range(data.num_tasks), repeat=2):
                if idx1 == idx2:
                    continue

                var1 = assign_vars.get((idx1, res_idx))
                var2 = assign_vars.get((idx2, res_idx))
                if not (var1 and var2):
                    continue

                # If the arc is selected, then both tasks must be present.
                model.add(arcs[idx1, idx2] <= var1.present)
                model.add(arcs[idx1, idx2] <= var2.present)

                setup = (
                    setup_times[res_idx, idx1, idx2]
                    if setup_times is not None
                    else 0
                )
                expr = var1.end + setup <= var2.start
                model.add(expr).only_enforce_if(arcs[idx1, idx2])

    def add_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._select_one_mode()
        self._machines_no_overlap()
        self._renewable_capacity()
        self._non_renewable_capacity()
        self._timing_constraints()
        self._identical_and_different_resource_constraints()
        self._activate_setup_times()
        self._consecutive_constraints()

        # From here onwards we know which sequence constraints are active.
        self._circuit_constraints()
