import numpy as np
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

from .VariablesManager import VariablesManager


class ConstraintsManager:
    """
    Handles the core constraints of the OR-Tools model.
    """

    def __init__(
        self,
        model: CpoModel,
        data: ProblemData,
        vars_manager: VariablesManager,
    ):
        self._m = model
        self._data = data

        # TODO make private
        self.job_vars = vars_manager.job_vars
        self.task_vars = vars_manager.task_vars
        self.task_alt_vars = vars_manager.task_alt_vars
        self.sequence_vars = vars_manager.sequence_vars

    def job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        m, data = self._m, self._data
        for idx, job in enumerate(data.jobs):
            job_var = self.job_vars[idx]
            related_task_vars = [
                self.task_vars[task_idx] for task_idx in job.tasks
            ]

            m.add(m.span(job_var, related_task_vars))

    def select_one_task_alternative(self):
        """
        Selects one optional interval for each task alternative, ensuring that
        each task is scheduled on exactly one machine.
        """
        m, data = self._m, self._data
        for task in range(data.num_tasks):
            machines = data.task2machines[task]
            optional = [
                self.task_alt_vars[task, machine] for machine in machines
            ]
            m.add(m.alternative(self.task_vars[task], optional))

    def no_overlap_and_setup_times(self):
        """
        Creates the no-overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping. If setup times are
        available, the setup times are enforced as well.
        """
        m, data = self._m, self._data
        for machine in range(data.num_machines):
            if not (tasks := data.machine2tasks[machine]):
                continue  # There no tasks for this machine.

            setups = data.setup_times[machine, :, :][np.ix_(tasks, tasks)]
            seq_var = self.sequence_vars[machine]

            if np.all(setups == 0):  # No setup times for this machine.
                m.add(m.no_overlap(seq_var))
            else:
                m.add(m.no_overlap(seq_var, setups))

    def task_graph(self):
        """
        Creates constraints based on the task graph for task variables.
        """
        m, data = self._m, self._data
        for (idx1, idx2), constraints in data.constraints.items():
            task1 = self.task_vars[idx1]
            task2 = self.task_vars[idx2]

            for constraint in constraints:
                if constraint == "start_at_start":
                    expr = m.start_at_start(task1, task2)
                elif constraint == "start_at_end":
                    expr = m.start_at_end(task1, task2)
                elif constraint == "start_before_start":
                    expr = m.start_before_start(task1, task2)
                elif constraint == "start_before_end":
                    expr = m.start_before_end(task1, task2)
                elif constraint == "end_at_start":
                    expr = m.end_at_start(task1, task2)
                elif constraint == "end_at_end":
                    expr = m.end_at_end(task1, task2)
                elif constraint == "end_before_start":
                    expr = m.end_before_start(task1, task2)
                elif constraint == "end_before_end":
                    expr = m.end_before_end(task1, task2)
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
                seq_var = self.sequence_vars[machine]
                var1 = self.task_alt_vars[task1, machine]
                var2 = self.task_alt_vars[task2, machine]

                for constraint in task_alt_constraints:
                    if constraint == "previous":
                        expr = m.previous(seq_var, var1, var2)
                    elif constraint == "before":
                        expr = m.before(seq_var, var1, var2)
                    elif constraint == "same_machine":
                        expr = m.presence_of(var1) == m.presence_of(var2)
                    elif constraint == "different_machine":
                        expr = m.presence_of(var1) != m.presence_of(var2)

                    m.add(expr)

    def add_all_constraints(self):
        """
        Adds the constraints for the CP Model.
        """
        self.job_spans_tasks()
        self.no_overlap_and_setup_times()
        self.select_one_task_alternative()
        self.task_graph()
        self.task_alt_graph()
