import numpy as np
from ortools.sat.python.cp_model import (
    CpModel,
)

from pyjobshop.ProblemData import ProblemData

from .VariablesManager import VariablesManager


class ConstraintsManager:
    """
    Handles the core constraints of the OR-Tools CP model.

    Parameters
    ----------
    data
        The problem data instance.
    """

    def __init__(
        self, model: CpModel, data: ProblemData, vars_manager: VariablesManager
    ):
        self._m = model
        self._data = data

        self.job_vars = vars_manager.job_vars
        self.task_vars = vars_manager.task_vars
        self.task_alt_vars = vars_manager.task_alt_vars
        self.sequence_vars = vars_manager.sequence_vars

    def job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        for idx, job in enumerate(self._data.jobs):
            job_var = self.job_vars[idx]
            task_start_vars = [
                self.task_vars[task].start for task in job.tasks
            ]
            task_end_vars = [self.task_vars[task].end for task in job.tasks]

            self._m.add_min_equality(job_var.start, task_start_vars)
            self._m.add_max_equality(job_var.end, task_end_vars)

    def select_one_task_alternative(self):
        """
        Selects one optional interval for each task alternative, ensuring that
        each task is scheduled on exactly one machine.
        """
        m, data = self._m, self._data
        task_vars, task_alt_vars = self.task_vars, self.task_alt_vars

        for task in range(data.num_tasks):
            presences = []

            for machine in data.task2machines[task]:
                main = task_vars[task]
                alt = task_alt_vars[task, machine]
                is_present = alt.is_present
                presences.append(is_present)

                # Sync each optional interval variable with the main variable.
                m.add(main.start == alt.start).only_enforce_if(is_present)
                m.add(main.duration == alt.duration).only_enforce_if(
                    is_present
                )
                m.add(main.end == alt.end).only_enforce_if(is_present)

            # Select exactly one optional interval variable for each task.
            m.add_exactly_one(presences)

    def no_overlap_machines(self):
        """
        Creates the no overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping.
        """
        m, data = self._m, self._data
        seq_vars = self.sequence_vars

        for machine in range(data.num_machines):
            m.add_no_overlap(
                [var.interval for var in seq_vars[machine].task_alts]
            )

    def activate_setup_times(self):
        """
        Activates the sequence variables for machines that have setup times.
        The ``circuit_constraints`` function will in turn add constraints to
        the CP-SAT model to enforce setup times.
        """
        m, data = self._m, self._data
        seq_vars = self.sequence_vars

        for machine in range(data.num_machines):
            if np.any(data.setup_times[machine]):
                seq_vars[machine].activate(m)

    def task_graph(self):
        """
        Creates constraints based on the task graph for task variables.
        """
        m, data = self._m, self._data
        task_vars = self.task_vars

        for (idx1, idx2), constraints in data.constraints.items():
            task_var1 = task_vars[idx1]
            task_var2 = task_vars[idx2]

            for prec_type in constraints:
                if prec_type == "start_at_start":
                    expr = task_var1.start == task_var2.start
                elif prec_type == "start_at_end":
                    expr = task_var1.start == task_var2.end
                elif prec_type == "start_before_start":
                    expr = task_var1.start <= task_var2.start
                elif prec_type == "start_before_end":
                    expr = task_var1.start <= task_var2.end
                elif prec_type == "end_at_start":
                    expr = task_var1.end == task_var2.start
                elif prec_type == "end_at_end":
                    expr = task_var1.end == task_var2.end
                elif prec_type == "end_before_start":
                    expr = task_var1.end <= task_var2.start
                elif prec_type == "end_before_end":
                    expr = task_var1.end <= task_var2.end
                else:
                    continue

                m.add(expr)

    def task_alt_graph(self):
        """
        Creates constraints based on the task graph which involve task
        alternative variables.
        """
        m, data = self._m, self._data
        relevant_constraints = {
            "previous",
            "before",
            "same_machine",
            "different_machine",
        }

        for (task1, task2), constraints in data.constraints.items():
            task_alt_constraints = set(constraints) & relevant_constraints
            if not task_alt_constraints:
                continue

            # Find the common machines for both tasks, because the constraints
            # apply to the task alternative variables on the same machine.
            machines1 = data.task2machines[task1]
            machines2 = data.task2machines[task2]
            machines = set(machines1) & set(machines2)

            for machine in machines:
                sequence = self.sequence_vars[machine]
                var1 = self.task_alt_vars[task1, machine]
                var2 = self.task_alt_vars[task2, machine]

                for constraint in task_alt_constraints:
                    if constraint == "previous":
                        sequence.activate(m)

                        idx1 = sequence.task_alts.index(var1)
                        idx2 = sequence.task_alts.index(var2)
                        arc = sequence.arcs[idx1, idx2]

                        # arc <=> var1.is_present & var2.is_present
                        m.add_bool_or(
                            [arc, ~var1.is_present, ~var2.is_present]
                        )
                        m.add_implication(arc, var1.is_present)
                        m.add_implication(arc, var2.is_present)
                    if constraint == "before":
                        sequence.activate(m)
                        both_present = m.new_bool_var("")

                        # both_present <=> var1.is_present & var2.is_present
                        m.add_bool_or(
                            [both_present, ~var1.is_present, ~var2.is_present]
                        )
                        m.add_implication(both_present, var1.is_present)
                        m.add_implication(both_present, var2.is_present)

                        # Schedule var1 before var2 when both are present.
                        idx1 = sequence.task_alts.index(var1)
                        idx2 = sequence.task_alts.index(var2)
                        rank1 = sequence.ranks[idx1]
                        rank2 = sequence.ranks[idx2]

                        m.add(rank1 <= rank2).only_enforce_if(both_present)
                    elif constraint == "same_machine":
                        expr = var1.is_present == var2.is_present
                        m.add(expr)
                    elif constraint == "different_machine":
                        expr = var1.is_present != var2.is_present
                        m.add(expr)

    def enforce_circuit(self):
        """
        Enforce the circuit constraints for each machine, ensuring that the
        sequencing constraints are respected.
        """
        data, m = self._data, self._m
        seq_vars = self.sequence_vars

        for machine in range(data.num_machines):
            sequence = seq_vars[machine]

            if not sequence.is_active:
                # No sequencing constraints found. Skip the creation of
                # (expensive) circuit constraints.
                continue

            task_alt_vars = sequence.task_alts
            starts = sequence.starts
            ends = sequence.ends
            ranks = sequence.ranks
            arcs = sequence.arcs

            # Add dummy node self-arc to allow empty circuits.
            empty = m.new_bool_var(f"empty_circuit_{machine}")
            circuit = [(-1, -1, empty)]

            for idx1, var1 in enumerate(task_alt_vars):
                start = starts[idx1]  # "is start node" literal
                end = ends[idx1]  # "is end node" literal
                rank = ranks[idx1]

                # Arcs from the dummy node to/from a task.
                circuit.append([-1, idx1, start])
                circuit.append([idx1, -1, end])

                # Set rank for first task in the sequence.
                m.add(rank == 0).only_enforce_if(start)

                # Self arc if the task is not present on this machine.
                circuit.append([idx1, idx1, ~var1.is_present])
                m.add(rank == -1).only_enforce_if(~var1.is_present)

                # If the circuit is empty then the var should not be present.
                m.add_implication(empty, ~var1.is_present)

                for idx2, var2 in enumerate(task_alt_vars):
                    if idx1 == idx2:
                        continue

                    arc = arcs[idx1, idx2]
                    circuit.append([idx1, idx2, arc])

                    m.add_implication(arc, var1.is_present)
                    m.add_implication(arc, var2.is_present)

                    # Maintain rank incrementally.
                    m.add(rank + 1 == ranks[idx2]).only_enforce_if(arc)

                    # TODO Validate that this cannot be combined with overlap.
                    task1, task2 = var1.task_idx, var2.task_idx
                    setup = data.setup_times[machine, task1, task2]
                    m.add(var1.end + setup <= var2.start).only_enforce_if(arc)

            m.add_circuit(circuit)

    def add_all_constraints(self):
        """
        Adds the constraints for the CP Model.
        """
        self.job_spans_tasks()
        self.select_one_task_alternative()
        self.no_overlap_machines()
        self.activate_setup_times()
        self.task_graph()
        self.task_alt_graph()

        # From here onwards we know which sequence constraints are active.
        self.enforce_circuit()
