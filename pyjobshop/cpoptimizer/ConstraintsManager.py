import numpy as np
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

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
        self._task_alt_vars = vars_manager.task_alt_vars
        self._sequence_vars = vars_manager.sequence_vars

    def _job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        model, data = self._model, self._data

        for idx, job in enumerate(data.jobs):
            job_var = self._job_vars[idx]
            job_task_vars = [self._task_vars[task] for task in job.tasks]

            model.add(model.span(job_var, job_task_vars))

    def _select_one_task_alternative(self):
        """
        Selects one task alternative for each main task, ensuring that each
        task is assigned to exactly one machine.
        """
        model, data = self._model, self._data

        for task in range(data.num_tasks):
            machines = data.task2machines[task]
            alts = [self._task_alt_vars[task, machine] for machine in machines]
            model.add(model.alternative(self._task_vars[task], alts))

    def _no_overlap_and_setup_times(self):
        """
        Creates the no-overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping. If setup times are
        available, the setup times are enforced as well.
        """
        model, data = self._model, self._data

        for machine in range(data.num_machines):
            if not (tasks := data.machine2tasks[machine]):
                continue  # skip if no tasks on this machine

            setups = data.setup_times[machine, :, :][np.ix_(tasks, tasks)]
            seq_var = self._sequence_vars[machine]

            if np.all(setups == 0):  # no setup times
                model.add(model.no_overlap(seq_var))
            else:
                model.add(model.no_overlap(seq_var, setups))

    def _task_graph(self):
        """
        Creates constraints based on the task graph for task variables.
        """
        model, data = self._model, self._data

        for (idx1, idx2), constraints in data.constraints.items():
            task1 = self._task_vars[idx1]
            task2 = self._task_vars[idx2]

            for constraint in constraints:
                if constraint == "start_at_start":
                    expr = model.start_at_start(task1, task2)
                elif constraint == "start_at_end":
                    expr = model.start_at_end(task1, task2)
                elif constraint == "start_before_start":
                    expr = model.start_before_start(task1, task2)
                elif constraint == "start_before_end":
                    expr = model.start_before_end(task1, task2)
                elif constraint == "end_at_start":
                    expr = model.end_at_start(task1, task2)
                elif constraint == "end_at_end":
                    expr = model.end_at_end(task1, task2)
                elif constraint == "end_before_start":
                    expr = model.end_before_start(task1, task2)
                elif constraint == "end_before_end":
                    expr = model.end_before_end(task1, task2)
                else:
                    continue

                model.add(expr)

    def _task_alt_graph(self):
        """
        Creates constraints based on the task graph which involve task
        alternative variables.
        """
        model, data = self._model, self._data
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
                seq_var = self._sequence_vars[machine]
                var1 = self._task_alt_vars[task1, machine]
                var2 = self._task_alt_vars[task2, machine]

                for constraint in task_alt_constraints:
                    if constraint == "previous":
                        expr = model.previous(seq_var, var1, var2)
                    elif constraint == "before":
                        expr = model.before(seq_var, var1, var2)
                    elif constraint == "same_machine":
                        presence1 = model.presence_of(var1)
                        presence2 = model.presence_of(var2)
                        expr = presence1 == presence2
                    elif constraint == "different_machine":
                        presence1 = model.presence_of(var1)
                        presence2 = model.presence_of(var2)
                        expr = presence1 != presence2

                    model.add(expr)

    def add_all_constraints(self):
        """
        Adds all the constraints to the CP model.
        """
        self._job_spans_tasks()
        self._no_overlap_and_setup_times()
        self._select_one_task_alternative()
        self._task_graph()
        self._task_alt_graph()
