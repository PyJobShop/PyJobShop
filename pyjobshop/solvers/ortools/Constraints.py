import numpy as np
from ortools.sat.python.cp_model import BoolVarT, CpModel, LinearExpr

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
            main = self._task_vars[task]

            for mode in task2modes[task]:
                opt = self._mode_vars[mode]
                present = opt.present
                presences.append(present)

                # Sync each optional interval variable with the main variable.
                model.add(main.start == opt.start).only_enforce_if(present)
                model.add(main.duration == opt.duration).only_enforce_if(
                    present
                )
                model.add(main.end == opt.end).only_enforce_if(present)

            # Select exactly one optional interval variable for each task.
            model.add_exactly_one(presences)

    def _machines_no_overlap(self):
        """
        Creates no-overlap constraints for machines.
        """
        model, data = self._model, self._data

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            seq_var = self._sequence_vars[idx]
            mode_vars = [var.interval for var in seq_var.mode_vars]
            model.add_no_overlap(mode_vars)

    def _renewable_capacity(self):
        """
        Creates capacity constraints for the renewable resources.
        """
        model, data = self._model, self._data
        mode_vars = self._mode_vars
        res2modes, res2demands = utils.resource2modes_demands(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Renewable):
                continue

            intervals = [mode_vars[mode].interval for mode in res2modes[idx]]
            demands = res2demands[idx]
            model.add_cumulative(intervals, demands, resource.capacity)

    def _non_renewable_capacity(self):
        """
        Creates capacity constraints for the non-renewable resources.
        """
        model, data = self._model, self._data
        mode_vars = self._mode_vars
        res2modes, res2demands = utils.resource2modes_demands(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, NonRenewable):
                continue

            precenses = [mode_vars[mode].present for mode in res2modes[idx]]
            demands = res2demands[idx]
            usage = LinearExpr.weighted_sum(precenses, demands)
            model.add(usage <= resource.capacity)

    def _timing_constraints(self):
        """
        Creates constraints based on the timing relationship between tasks.
        """
        model, data = self._model, self._data

        for idx1, idx2 in data.constraints.start_at_start:
            expr1 = self._task_vars[idx1].start
            expr2 = self._task_vars[idx2].start
            model.add(expr1 == expr2)

        for idx1, idx2 in data.constraints.start_at_end:
            expr1 = self._task_vars[idx1].start
            expr2 = self._task_vars[idx2].end
            model.add(expr1 == expr2)

        for idx1, idx2 in data.constraints.start_before_start:
            expr1 = self._task_vars[idx1].start
            expr2 = self._task_vars[idx2].start
            model.add(expr1 <= expr2)

        for idx1, idx2 in data.constraints.start_before_end:
            expr1 = self._task_vars[idx1].start
            expr2 = self._task_vars[idx2].end
            model.add(expr1 <= expr2)

        for idx1, idx2 in data.constraints.end_at_start:
            expr1 = self._task_vars[idx1].end
            expr2 = self._task_vars[idx2].start
            model.add(expr1 == expr2)

        for idx1, idx2 in data.constraints.end_at_end:
            expr1 = self._task_vars[idx1].end
            expr2 = self._task_vars[idx2].end
            model.add(expr1 == expr2)

        for idx1, idx2 in data.constraints.end_before_start:
            expr1 = self._task_vars[idx1].end
            expr2 = self._task_vars[idx2].start
            model.add(expr1 <= expr2)

        for idx1, idx2 in data.constraints.end_before_end:
            expr1 = self._task_vars[idx1].end
            expr2 = self._task_vars[idx2].end
            model.add(expr1 <= expr2)

    def _identical_and_different_resource_constraints(self):
        """
        Creates constraints for identical and different resources constraints.
        """
        model, data = self._model, self._data

        for idx1, idx2 in data.constraints.identical_resources:
            for mode1, modes2 in utils.identical_modes(data, idx1, idx2):
                expr1 = self._mode_vars[mode1].present
                expr2 = sum(self._mode_vars[mode2].present for mode2 in modes2)
                model.add(expr1 <= expr2)

        for idx1, idx2 in data.constraints.different_resources:
            for mode1, modes2 in utils.different_modes(data, idx1, idx2):
                expr1 = self._mode_vars[mode1].present
                expr2 = sum(self._mode_vars[mode2].present for mode2 in modes2)
                model.add(expr1 <= expr2)

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
                self._sequence_vars[idx].activate(model)

    def _consecutive_constraints(self):
        """
        Creates the consecutive constraints.
        """
        model, data = self._model, self._data

        for idx1, idx2 in data.constraints.consecutive:
            intersecting = utils.intersecting_modes(data, idx1, idx2)
            for mode1, mode2, resources in intersecting:
                for resource in resources:
                    if not isinstance(data.resources[resource], Machine):
                        continue

                    seq_var = self._sequence_vars[resource]
                    seq_var.activate(model)
                    var1 = self._mode_vars[mode1]
                    var2 = self._mode_vars[mode2]

                    idx1 = seq_var.mode_vars.index(var1)
                    idx2 = seq_var.mode_vars.index(var2)
                    arc = seq_var.arcs[idx1, idx2]
                    both_present = [var1.present, var2.present]

                    model.add(arc == 1).only_enforce_if(both_present)

    def _circuit_constraints(self):
        """
        Creates the circuit constraints for each machine, if activated by
        sequencing constraints (consecutive and setup times).
        """
        model, data = self._model, self._data
        setup_times = utils.setup_times_matrix(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            seq_var = self._sequence_vars[idx]
            if not seq_var.is_active:
                # No sequencing constraints active. Skip the creation of
                # (expensive) circuit constraints.
                continue

            modes = seq_var.mode_vars
            arcs = seq_var.arcs

            # Add dummy node self-arc to allow empty circuits.
            empty = model.new_bool_var("")
            graph: list[tuple[int, int, BoolVarT]] = [(-1, -1, empty)]

            for idx1, var1 in enumerate(modes):
                # Arcs from and to the dummy node.
                graph.append((-1, idx1, model.new_bool_var("")))
                graph.append((idx1, -1, model.new_bool_var("")))

                # Self arc if the task is not present
                graph.append((idx1, idx1, ~var1.present))

                # If the circuit is empty then the present not be present.
                model.add_implication(empty, ~var1.present)

                for idx2, var2 in enumerate(modes):
                    if idx1 == idx2:
                        continue

                    arc = arcs[idx1, idx2]
                    graph.append((idx1, idx2, arc))

                    model.add_implication(arc, var1.present)
                    model.add_implication(arc, var2.present)

                    setup = (
                        setup_times[idx, var1.task_idx, var2.task_idx]
                        if setup_times is not None
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
        self._machines_no_overlap()
        self._renewable_capacity()
        self._non_renewable_capacity()
        self._timing_constraints()
        self._identical_and_different_resource_constraints()
        self._activate_setup_times()
        self._consecutive_constraints()

        # From here onwards we know which sequence constraints are active.
        self._circuit_constraints()
