from typing import Optional

from docplex.cp.expression import (
    CpoIntervalVar,
    CpoSequenceVar,
    interval_var,
    sequence_var,
)
from docplex.cp.model import CpoModel

import pyjobshop.solvers.utils as utils
from pyjobshop.ProblemData import Machine, ProblemData
from pyjobshop.Solution import Solution


class Variables:
    """
    Manages the core variables of the CP Optimizer model.
    """

    def __init__(self, model: CpoModel, data: ProblemData):
        self._model = model
        self._data = data

        self._job_vars = self._make_job_variables()
        self._task_vars = self._make_task_variables()
        self._mode_vars = self._make_mode_variables()
        self._sequence_vars = self._make_sequence_variables()

    @property
    def job_vars(self) -> list[CpoIntervalVar]:
        """
        Returns the job variables.
        """
        return self._job_vars

    @property
    def task_vars(self) -> list[CpoIntervalVar]:
        """
        Returns the task variables.
        """
        return self._task_vars

    @property
    def mode_vars(self) -> list[CpoIntervalVar]:
        """
        Returns the mode variables.
        """
        return self._mode_vars

    @property
    def sequence_vars(self) -> list[Optional[CpoSequenceVar]]:
        """
        Returns the sequence variables.
        """
        return self._sequence_vars

    def _make_job_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an interval variable for each job.
        """
        variables = []

        for job in self._data.jobs:
            var = interval_var(name=f"J{job}")

            var.set_start_min(job.release_date)
            var.set_end_max(min(job.deadline, self._data.horizon))

            variables.append(var)
            self._model.add(var)

        return variables

    def _make_task_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an interval variable for each task.
        """
        data = self._data
        variables = []
        task_durations = utils.compute_task_durations(self._data)

        for idx, task in enumerate(data.tasks):
            var = interval_var(name=f"T{task}")

            var.set_start_min(task.earliest_start)
            var.set_start_max(min(task.latest_start, data.horizon))

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, data.horizon))

            var.set_size_min(min(task_durations[idx]))
            var.set_size_max(
                max(task_durations[idx])
                if task.fixed_duration
                else data.horizon
            )

            variables.append(var)
            self._model.add(var)

        return variables

    def _make_mode_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an optional interval variable for each mode variable.
        """
        data = self._data
        variables = []

        for idx, mode in enumerate(data.modes):
            var = interval_var(optional=True, name=f"M{idx}_{mode.task}")
            task = data.tasks[mode.task]

            var.set_start_min(task.earliest_start)
            var.set_start_max(min(task.latest_start, data.horizon))

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, data.horizon))

            if task.fixed_duration:
                var.set_size(mode.duration)
            else:
                var.set_size_min(mode.duration)
                var.set_size_max(data.horizon)

            variables.append(var)
            self._model.add(var)

        return variables

    def _make_sequence_variables(self) -> list[Optional[CpoSequenceVar]]:
        """
        Creates a sequence variable for each machine, and no variable for
        general resources.
        """
        data = self._data
        resource2modes = utils.resource2modes(data)
        variables: list[Optional[CpoSequenceVar]] = []

        for resource, modes in enumerate(resource2modes):
            if not isinstance(data.resources[resource], Machine):
                variables.append(None)
            else:
                intervals = [self.mode_vars[mode] for mode in modes]
                seq_var = sequence_var(name=f"S{resource}", vars=intervals)
                self._model.add(seq_var)
                variables.append(seq_var)

        return variables

    def warmstart(self, solution: Solution):
        """
        Warmstarts the variables based on the given solution.
        """
        data = self._data
        stp = self._model.create_empty_solution()

        for idx in range(data.num_jobs):
            job = data.jobs[idx]
            job_var = self.job_vars[idx]
            sol_tasks = [solution.tasks[task] for task in job.tasks]

            job_start = min(task.start for task in sol_tasks)
            job_end = max(task.end for task in sol_tasks)

            stp.add_interval_var_solution(
                job_var, start=job_start, end=job_end
            )

        for idx in range(data.num_tasks):
            task_var = self.task_vars[idx]
            sol_task = solution.tasks[idx]

            stp.add_interval_var_solution(
                task_var,
                start=sol_task.start,
                end=sol_task.end,
                size=sol_task.end - sol_task.start,
            )

        for idx, mode in enumerate(data.modes):
            sol_task = solution.tasks[mode.task]
            var = self.mode_vars[idx]

            stp.add_interval_var_solution(
                var,
                presence=idx == sol_task.mode,
                start=sol_task.start,
                end=sol_task.end,
                size=sol_task.end - sol_task.start,
            )

        self._model.set_starting_point(stp)
