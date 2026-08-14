import numpy as np
from docplex.cp.expression import (
    CpoIntervalVar,
    CpoSequenceVar,
    interval_var,
    sequence_var,
)
from docplex.cp.model import CpoModel

import pyjobshop.solvers.utils as utils
from pyjobshop.constants import MAX_VALUE
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution


class Variables:
    """
    Manages the core variables of the CP Optimizer model.
    """

    def __init__(
        self,
        model: CpoModel,
        data: ProblemData,
        global_setup_matrix: bool = False,
    ):
        self._model = model
        self._data = data
        self._global_setup_matrix = global_setup_matrix
        self._sequence_task_types: dict[int, dict[int, int]] = {}

        self._job_vars = self._make_job_variables()
        self._task_vars = self._make_task_variables()
        self._mode_vars = self._make_mode_variables()
        self._sequence_vars = self._make_sequence_variables()
        self._setup_matrices = self._make_setup_matrices()

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
    def sequence_vars(self) -> dict[int, CpoSequenceVar]:
        """
        Returns the sequence variables.
        """
        return self._sequence_vars

    @property
    def sequence_task_types(self) -> dict[int, dict[int, int]]:
        """
        Maps task indices to sequence types for each machine.
        """
        return self._sequence_task_types

    @property
    def setup_matrices(self) -> dict[int, np.ndarray]:
        """
        Returns setup matrices indexed by machine.
        """
        return self._setup_matrices

    def _make_job_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an interval variable for each job.
        """
        data = self._data
        variables = []

        for idx, job in enumerate(data.jobs):
            # Job variable has to be optional if all tasks are optional.
            optional = all(data.tasks[idx].optional for idx in job.tasks)
            var = interval_var(optional=optional, name=f"J{idx}")

            var.set_start_min(job.release_date)
            var.set_end_max(min(job.deadline, MAX_VALUE))

            variables.append(var)
            self._model.add(var)

        return variables

    def _make_task_variables(self) -> list[CpoIntervalVar]:
        """
        Creates an interval variable for each task.
        """
        data = self._data
        variables = []

        for idx, task in enumerate(data.tasks):
            var = interval_var(optional=task.optional, name=f"T{idx}")

            var.set_start_min(task.earliest_start)
            var.set_start_max(min(task.latest_start, MAX_VALUE))

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, MAX_VALUE))

            modes = [data.modes[mode_idx] for mode_idx in data.task2modes(idx)]
            mode_durations = [mode.duration for mode in modes]
            var.set_size_min(min(mode_durations))

            if not (task.allow_idle or task.allow_breaks):
                var.set_size_max(max(mode_durations))

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
            var.set_start_max(min(task.latest_start, MAX_VALUE))

            var.set_end_min(task.earliest_end)
            var.set_end_max(min(task.latest_end, MAX_VALUE))

            var.set_size_min(mode.duration)
            if not task.allow_idle:
                var.set_size(mode.duration)

            variables.append(var)
            self._model.add(var)

        return variables

    def _make_sequence_variables(self) -> dict[int, CpoSequenceVar]:
        """
        Creates a sequence variable for each machine.
        """
        data = self._data
        variables: dict[int, CpoSequenceVar] = {}

        for res_idx in data.machine_idcs:
            if not (modes := data.resource2modes(res_idx)):
                # Skip machines without modes to avoid CPO warning
                # about unused sequence variables.
                continue

            task_idcs = sorted({data.modes[idx].task for idx in modes})
            if self._global_setup_matrix:
                task_types = {task_idx: task_idx for task_idx in task_idcs}
            else:
                task_types = {
                    task_idx: type_idx
                    for type_idx, task_idx in enumerate(task_idcs)
                }

            intervals = [self.mode_vars[idx] for idx in modes]
            types = [task_types[data.modes[idx].task] for idx in modes]
            seq_var = sequence_var(
                name=f"S{res_idx}",
                types=types,
                vars=intervals,
            )
            self._model.add(seq_var)
            self._sequence_task_types[res_idx] = task_types
            variables[res_idx] = seq_var

        return variables

    def _make_setup_matrices(self) -> dict[int, np.ndarray]:
        """
        Builds the setup matrix used by each machine sequence.
        """
        data = self._data

        if self._global_setup_matrix:
            setup_times = utils.setup_times_matrix(data)
            if setup_times is None:
                return {}

            return {
                res_idx: setup_times[res_idx]
                for res_idx in self._sequence_task_types
            }

        matrices: dict[int, np.ndarray] = {}
        for res_idx, task1, task2, duration in data.constraints.setup_times:
            task_types = self._sequence_task_types.get(res_idx)
            if task_types is None:
                continue

            type1 = task_types.get(task1)
            type2 = task_types.get(task2)
            if type1 is None or type2 is None:
                continue

            if res_idx not in matrices:
                size = len(task_types)
                matrices[res_idx] = np.zeros((size, size), dtype=int)

            matrices[res_idx][type1, type2] = duration

        return {
            res_idx: matrix
            for res_idx, matrix in matrices.items()
            if matrix.any()
        }

    def warmstart(self, solution: Solution):
        """
        Warmstarts the variables based on the given solution.
        """
        data = self._data
        init = self._model.create_empty_solution()

        for idx in range(data.num_jobs):
            job_var = self.job_vars[idx]
            sol_job = solution.jobs[idx]

            init.add_interval_var_solution(
                job_var,
                presence=sol_job.present,
                start=sol_job.start,
                end=sol_job.end,
            )

        # Only presence, start, and end are set: for a present interval
        # they determine length, and without an intensity function CP
        # Optimizer requires size == length, so passing the processing
        # time as size triggers "inconsistent with its initial domain"
        # warnings for tasks that allow idle time. Absent intervals get
        # presence only, since another mode's timing values need not
        # fit their domain.
        for idx in range(data.num_tasks):
            task_var = self.task_vars[idx]
            sol_task = solution.tasks[idx]

            init.add_interval_var_solution(
                task_var,
                presence=sol_task.present,
                start=sol_task.start,
                end=sol_task.end,
            )

        for idx, mode in enumerate(data.modes):
            sol_task = solution.tasks[mode.task]
            var = self.mode_vars[idx]

            if idx != sol_task.mode:
                init.add_interval_var_solution(var, presence=False)
                continue

            init.add_interval_var_solution(
                var,
                presence=True,
                start=sol_task.start,
                end=sol_task.end,
            )

        self._model.set_starting_point(init)
