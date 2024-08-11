from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution
from pyjobshop.utils import compute_min_max_durations


class VariablesManager:
    """
    Manages the core variables of the CP Optimizer model.
    """

    def __init__(self, model: CpoModel, data: ProblemData):
        self._model = model
        self._data = data

        self._job_vars = self._make_job_variables()
        self._task_vars = self._make_task_variables()
        self._task_alt_vars = self._make_task_alternative_variables()
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
    def task_alt_vars(self) -> dict[tuple[int, int], CpoIntervalVar]:
        """
        Returns the task alternative variables.
        """
        return self._task_alt_vars

    @property
    def sequence_vars(self) -> list[CpoSequenceVar]:
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
            var = self._model.interval_var(name=f"J{job}")

            var.set_start_min(job.release_date)
            var.set_end_max(min(job.deadline, self._data.horizon))

            variables.append(var)

        return variables

    def _make_task_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an interval variable for each task.
        """
        m, data = self._model, self._data
        variables = []
        min_durations, max_durations = compute_min_max_durations(self._data)

        for idx, task in enumerate(data.tasks):
            var = m.interval_var(name=f"T{task}")

            var.set_start_min(task.earliest_start)
            var.set_start_max(min(task.latest_start, data.horizon))

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, data.horizon))

            var.set_size_min(min_durations[idx])
            var.set_size_max(
                max_durations[idx] if task.fixed_duration else data.horizon
            )

            variables.append(var)

        return variables

    def _make_task_alternative_variables(
        self,
    ) -> dict[tuple[int, int], CpoIntervalVar]:
        """
        Creates an optional interval variable for each eligible task and
        machine pair.

        Returns
        -------
        dict[tuple[int, int], TaskAltVar]
            A dictionary that maps each task index and machine index pair to
            its corresponding task alternative variable.
        """
        m, data = self._model, self._data
        variables = {}

        for (task_idx, machine), duration in data.processing_times.items():
            var = m.interval_var(optional=True, name=f"A{task_idx}_{machine}")
            task = data.tasks[task_idx]

            var.set_start_min(task.earliest_start)
            var.set_start_max(min(task.latest_start, data.horizon))

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, data.horizon))

            if task.fixed_duration:
                var.set_size(duration)
            else:
                var.set_size_min(duration)
                var.set_size_max(data.horizon)

            variables[task_idx, machine] = var

        return variables

    def _make_sequence_variables(self) -> list[CpoSequenceVar]:
        """
        Creates a sequence variable for each machine. Sequence variables are
        used to model the ordering of intervals on a given machine. This is
        used for modeling machine setups and sequencing task constraints, such
        as previous, before, first, last and permutations.
        """
        m, data = self._model, self._data
        variables = []

        for machine, tasks in enumerate(data.machine2tasks):
            intervals = [self.task_alt_vars[task, machine] for task in tasks]
            variables.append(
                m.sequence_var(name=f"S{machine}", vars=intervals)
            )

        return variables

    def warmstart(self, solution: Solution):
        """
        Warm-starts the variables based on the given solution.
        """
        m, data = self._model, self._data
        stp = m.create_empty_solution()

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
                size=sol_task.duration,
            )

        for (task_idx, machine_idx), var in self.task_alt_vars.items():
            sol_task = solution.tasks[task_idx]

            stp.add_interval_var_solution(
                var,
                presence=machine_idx == sol_task.machine,
                start=sol_task.start,
                end=sol_task.end,
                size=sol_task.duration,
            )

        m.set_starting_point(stp)
