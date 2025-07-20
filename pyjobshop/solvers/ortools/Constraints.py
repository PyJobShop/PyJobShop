import numpy as np
from ortools.sat.python.cp_model import CpModel, LinearExpr

import pyjobshop.solvers.utils as utils
from pyjobshop.constants import MAX_VALUE
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

    def _job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx, job in enumerate(data.jobs):
            job_var = variables.job_vars[idx]
            starts = []
            ends = []

            for task in job.tasks:
                task_var = variables.task_vars[task]

                # Introduce intermediate task start and end variables. When
                # tasks are absent, they should not affect the job's start and
                # end times.
                task_start = model.new_int_var(0, MAX_VALUE, "")
                task_end = model.new_int_var(0, MAX_VALUE, "")

                expr = task_start == task_var.start
                model.add(expr).only_enforce_if(task_var.present)

                expr = task_end == task_var.end
                model.add(expr).only_enforce_if(task_var.present)

                starts.append(task_start)
                ends.append(task_end)

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
            # Select exactly one mode iff the task is present.
            task_var = variables.task_vars[task_idx]
            task_mode_vars = variables.mode_vars[task_idx]
            model.add(sum(task_mode_vars.values()) == task_var.present)

            for mode_idx, mode_var in task_mode_vars.items():
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

        for task_idx in range(data.num_tasks):
            for res_idx in range(data.num_resources):
                if (task_idx, res_idx) not in variables.assign_vars:
                    continue

                task_var = variables.task_vars[task_idx]
                assign_var = variables.assign_vars[task_idx, res_idx]

                # Assignment variable can only be present if task is present.
                model.add(assign_var.present <= task_var.present)

    def _machines_no_overlap(self):
        """
        Creates no-overlap constraints for machines.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            intervals = [var.interval for var in variables.res2assign(idx)]
            model.add_no_overlap(intervals)

    def _renewable_capacity(self):
        """
        Creates capacity constraints for the renewable resources.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Renewable):
                continue

            intervals = [var.interval for var in variables.res2assign(idx)]
            demands = [var.demand for var in variables.res2assign(idx)]
            model.add_cumulative(intervals, demands, resource.capacity)

    def _non_renewable_capacity(self):
        """
        Creates capacity constraints for the non-renewable resources.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, NonRenewable):
                continue

            demands = [var.demand for var in variables.res2assign(idx)]
            total = LinearExpr.sum(demands)
            model.add(total <= resource.capacity)

    def _timing_constraints(self):
        """
        Creates constraints based on the timing relationship between tasks.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx1, idx2, delay in data.constraints.start_before_start:
            var1 = variables.task_vars[idx1]
            var2 = variables.task_vars[idx2]
            both_present = [var1.present, var2.present]
            expr = var1.start + delay <= var2.start
            model.add(expr).only_enforce_if(both_present)

        for idx1, idx2, delay in data.constraints.start_before_end:
            var1 = variables.task_vars[idx1]
            var2 = variables.task_vars[idx2]
            both_present = [var1.present, var2.present]
            expr = var1.start + delay <= var2.end
            model.add(expr).only_enforce_if(both_present)

        for idx1, idx2, delay in data.constraints.end_before_start:
            var1 = variables.task_vars[idx1]
            var2 = variables.task_vars[idx2]
            both_present = [var1.present, var2.present]
            expr = var1.end + delay <= var2.start
            model.add(expr).only_enforce_if(both_present)

        for idx1, idx2, delay in data.constraints.end_before_end:
            var1 = variables.task_vars[idx1]
            var2 = variables.task_vars[idx2]
            both_present = [var1.present, var2.present]
            expr = var1.end + delay <= var2.end
            model.add(expr).only_enforce_if(both_present)

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

    def _task_selection_constraints(self):
        """
        Creates the selection constraints.
        """
        model, data, variables = self._model, self._data, self._variables

        for idx1, idcs2 in data.constraints.select_at_least_one:
            pred = variables.task_vars[idx1].present
            succs = sum(variables.task_vars[idx2].present for idx2 in idcs2)
            model.add(succs >= 1).only_enforce_if(pred)

    def _activate_setup_times(self):
        """
        Activates the sequence variables for resources that have setup times.
        The ``_circuit_constraints`` function will in turn add constraints to
        the CP-SAT model to enforce setup times.
        """
        model, data, variables = self._model, self._data, self._variables
        setup_times = utils.setup_times_matrix(data)

        for idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            if setup_times is not None and np.any(setup_times[idx]):
                variables.sequence_vars[idx].activate(model, data)

    def _consecutive_constraints(self):
        """
        Creates the consecutive constraints.
        """
        model, data, variables = self._model, self._data, self._variables

        for task_idx1, task_idx2 in data.constraints.consecutive:
            for res_idx in range(data.num_resources):
                if not isinstance(data.resources[res_idx], Machine):
                    continue

                seq_var = variables.sequence_vars[res_idx]
                seq_var.activate(model, data)

                var1 = variables.assign_vars.get((task_idx1, res_idx))
                var2 = variables.assign_vars.get((task_idx2, res_idx))

                if not (var1 and var2):
                    continue

                arc = seq_var.arcs[task_idx1, task_idx2]
                both_present = [var1.present, var2.present]

                model.add(arc == 1).only_enforce_if(both_present)

    def _circuit_constraints(self):
        """
        Creates the circuit constraints for each machine, if activated by
        sequencing constraints (consecutive and setup times).
        """
        model, data, variables = self._model, self._data, self._variables
        setup_times = utils.setup_times_matrix(data)

        for res_idx, resource in enumerate(data.resources):
            if not isinstance(resource, Machine):
                continue

            seq_var = variables.sequence_vars[res_idx]
            if not seq_var.is_active:
                # No sequencing constraints active. Skip the creation of
                # expensive circuit constraints.
                continue

            arcs = seq_var.arcs
            graph = [(u, v, var) for (u, v), var in arcs.items()]
            model.add_circuit(graph)

            for task_idx in range(data.num_tasks):
                if (task_idx, res_idx) in variables.assign_vars:
                    # Absent intervals require selecting loops (self-arcs).
                    present = variables.assign_vars[task_idx, res_idx].present
                    loop = arcs[task_idx, task_idx]
                    model.add(loop == ~present)

                    # This handles the case where a machine does not process
                    # any task. Selecting the dummy loop makes all intervals
                    # absent, and satisfies the circuit constraint.
                    dummy_loop = arcs[seq_var.DUMMY, seq_var.DUMMY]
                    model.add(dummy_loop <= ~present)

            for task_idx1 in range(data.num_tasks):
                for task_idx2 in range(data.num_tasks):
                    if task_idx1 == task_idx2:
                        continue

                    var1 = variables.assign_vars.get((task_idx1, res_idx))
                    var2 = variables.assign_vars.get((task_idx2, res_idx))
                    if not (var1 and var2):
                        # Deactivate arc if tasks are not on this machine.
                        model.add(arcs[task_idx1, task_idx2] == 0)
                        continue

                    arc_selected = arcs[task_idx1, task_idx2]
                    model.add(arc_selected <= var1.present)
                    model.add(arc_selected <= var2.present)

                    setup = (
                        setup_times[res_idx, task_idx1, task_idx2]
                        if setup_times is not None
                        else 0
                    )
                    expr = var1.end + setup <= var2.start
                    model.add(expr).only_enforce_if(arc_selected)

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
        self._task_selection_constraints()
        self._activate_setup_times()
        self._consecutive_constraints()

        # From here onwards we know which sequence constraints are active.
        self._circuit_constraints()
