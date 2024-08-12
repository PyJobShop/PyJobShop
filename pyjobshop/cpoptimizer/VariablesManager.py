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
        model, data = self._model, self._data
        variables = []
        min_durations, max_durations = compute_min_max_durations(self._data)

        for idx, task in enumerate(data.tasks):
            var = model.interval_var(name=f"T{task}")

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

    def _make_mode_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an optional interval variable for each mode variable.
        """
        model, data = self._model, self._data
        variables = []

        for mode in self._data.modes:
            task_idx, machine_idx = mode.task, mode.machine
            var = model.interval_var(
                optional=True, name=f"A{task_idx}_{machine_idx}"
            )
            task = data.tasks[task_idx]

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

        return variables

    def _make_sequence_variables(self) -> list[CpoSequenceVar]:
        """
        Creates a sequence variable for each machine. Sequence variables are
        used to model the ordering of intervals on a given machine. This is
        used for modeling machine setups and sequencing task constraints, such
        as previous, before, first, last and permutations.
        """
        model, data = self._model, self._data
        variables = []

        for machine, modes in enumerate(data._machine2modes):
            intervals = [self.mode_vars[mode] for mode in modes]
            seq_var = model.sequence_var(name=f"S{machine}", vars=intervals)
            variables.append(seq_var)

        return variables

    def warmstart(self, solution: Solution):
        """
        Warmstarts the variables based on the given solution.
        """
        model, data = self._model, self._data
        stp = model.create_empty_solution()

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

        for idx, mode in enumerate(data.modes):
            sol_task = solution.tasks[mode.task]
            var = self.mode_vars[idx]

            stp.add_interval_var_solution(
                var,
                presence=mode.machine == sol_task.machine,
                start=sol_task.start,
                end=sol_task.end,
                size=sol_task.duration,
            )

        model.set_starting_point(stp)