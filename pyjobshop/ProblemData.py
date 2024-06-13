import bisect
from enum import Enum
from typing import Optional

import enum_tools.documentation
import numpy as np

from pyjobshop.constants import MAX_VALUE

_CONSTRAINTS_TYPE = dict[tuple[int, int], list["Constraint"]]


class Job:
    """
    Simple dataclass for storing all job-related data.

    Parameters
    ----------
    weight
        The job importance weight, used as multiplicative factor in the
        objective function. Default 1.
    release_date
        The earliest time that the job may start. Default 0.
    deadline
        The latest time by which the job must be completed. Note that a
        deadline is different from a due date; the latter does not restrict
        the latest completion time. Default ``MAX_VALUE``.
    due_date
        The latest time that the job should be completed before incurring
        penalties. Default is None, meaning that there is no due date.
    tasks
        List of task indices that belong to this job. Default is None,
        which initializes an empty list.
    name
        Name of the job.
    """

    def __init__(
        self,
        weight: int = 1,
        release_date: int = 0,
        deadline: int = MAX_VALUE,
        due_date: Optional[int] = None,
        tasks: Optional[list[int]] = None,
        name: str = "",
    ):
        if weight < 0:
            raise ValueError("Weight must be non-negative.")

        if release_date < 0:
            raise ValueError("Release date must be non-negative.")

        if deadline < 0:
            raise ValueError("Deadline must be non-negative.")

        if release_date > deadline:
            raise ValueError("Must have release_date <= deadline.")

        if due_date is not None and due_date < 0:
            raise ValueError("Due date must be non-negative.")

        self._weight = weight
        self._release_date = release_date
        self._deadline = deadline
        self._due_date = due_date
        self._tasks = [] if tasks is None else tasks
        self._name = name

    @property
    def weight(self) -> int:
        return self._weight

    @property
    def release_date(self) -> int:
        return self._release_date

    @property
    def deadline(self) -> int:
        return self._deadline

    @property
    def due_date(self) -> Optional[int]:
        return self._due_date

    @property
    def tasks(self) -> list[int]:
        return self._tasks

    @property
    def name(self) -> str:
        return self._name

    def add_task(self, idx: int):
        self._tasks.append(idx)


class Machine:
    """
    Simple dataclass for storing all machine-related data.

    Parameters
    ----------
    allow_overlap
        Whether it is allowed to schedule multiple tasks on the machine
        at the same time. Default is False.
    name
        Name of the machine.
    """

    def __init__(self, allow_overlap: bool = False, name: str = ""):
        self._allow_overlap = allow_overlap
        self._name = name

    @property
    def allow_overlap(self) -> bool:
        return self._allow_overlap

    @property
    def name(self) -> str:
        return self._name


class Task:
    """
    Simple dataclass for storing all task related data.

    Parameters
    ----------
    earliest_start
        Earliest start time of the task. Default 0.
    latest_start
        Latest start time of the task. Default ``MAX_VALUE``.
    earliest_end
        Earliest end time of the task. Default 0.
    latest_end
        Latest end time of the task. Default ``MAX_VALUE``.
    fixed_duration
        Whether the task has a fixed duration. A fixed duration means that
        the task duration is precisely the processing time (on a given
        machine). If the duration is not fixed, then the task duration
        can take longer than the processing time, e.g., due to blocking.
        Default ``True``.
    name
        Name of the task.
    """

    def __init__(
        self,
        earliest_start: int = 0,
        latest_start: int = MAX_VALUE,
        earliest_end: int = 0,
        latest_end: int = MAX_VALUE,
        fixed_duration: bool = True,
        name: str = "",
    ):
        if earliest_start > latest_start:
            raise ValueError("earliest_start must be <= latest_start.")

        if earliest_end > latest_end:
            raise ValueError("earliest_end must be <= latest_end.")

        self._earliest_start = earliest_start
        self._latest_start = latest_start
        self._earliest_end = earliest_end
        self._latest_end = latest_end
        self._fixed_duration = fixed_duration
        self._name = name

    @property
    def earliest_start(self) -> int:
        return self._earliest_start

    @property
    def latest_start(self) -> int:
        return self._latest_start

    @property
    def earliest_end(self) -> int:
        return self._earliest_end

    @property
    def latest_end(self) -> int:
        return self._latest_end

    @property
    def fixed_duration(self) -> bool:
        return self._fixed_duration

    @property
    def name(self) -> str:
        return self._name


@enum_tools.documentation.document_enum
class Objective(str, Enum):
    """
    Choices for objective functions (to be minimized).
    """

    #: Minimize the maximum completion time of all jobs.
    MAKESPAN = "makespan"

    #: Minimizes the number of jobs whose completion times exceed the due date.
    TARDY_JOBS = "tardy_jobs"

    #: Minimize the sum of job completion times.
    TOTAL_COMPLETION_TIME = "total_completion_time"

    #: Minimize the sum of job tardiness.
    TOTAL_TARDINESS = "total_tardiness"


@enum_tools.documentation.document_enum
class Constraint(str, Enum):
    """
    Task constraints between two tasks :math:`i` and :math:`j`.
    """

    #: Task :math:`i` must start when task :math:`j` starts.
    START_AT_START = "start_at_start"

    #: Task :math:`i` must at start when task :math:`j` ends.
    START_AT_END = "start_at_end"

    #: Task :math:`i` must start before task :math:`j` starts.
    START_BEFORE_START = "start_before_start"

    #: Task :math:`i` must start before task :math:`j` ends.
    START_BEFORE_END = "start_before_end"

    #: Task :math:`i` must end when task :math:`j` starts.
    END_AT_START = "end_at_start"

    #: Task :math:`i` must end when task :math:`j` ends.
    END_AT_END = "end_at_end"

    #: Task :math:`i` must end before task :math:`j` starts.
    END_BEFORE_START = "end_before_start"

    #: Task :math:`i` must end before task :math:`j` ends.
    END_BEFORE_END = "end_before_end"

    #: Sequence :math:`i` right before :math:`j` (if assigned to same machine).
    PREVIOUS = "previous"

    #: Assign tasks :math:`i` and :math:`j` to the same machine.
    SAME_UNIT = "same_unit"

    #: Assign tasks :math:`i` and :math:`j` to different machine.
    DIFFERENT_UNIT = "different_unit"


class ProblemData:
    """
    Creates a problem data instance. This instance contains all information
    need to solve the scheduling problem.

    Parameters
    ----------
    jobs
        List of jobs.
    machines
        List of machines.
    tasks
        List of tasks.
    processing_times
        Processing times of tasks on machines. First index is the machine
        index, second index is the task index.
    constraints
        Dict indexed by task pairs with a list of constraints as values.
    setup_times
        Sequence-dependent setup times between tasks on a given machine.
        The first dimension of the array is indexed by the machine index. The
        last two dimensions of the array are indexed by task indices.
    horizon
        The horizon value. Default ``MAX_VALUE``.
    objective
        The objective function to be minimized. Default is the makespan.
    """

    def __init__(
        self,
        jobs: list[Job],
        machines: list[Machine],
        tasks: list[Task],
        processing_times: dict[tuple[int, int], int],
        constraints: _CONSTRAINTS_TYPE,
        setup_times: Optional[np.ndarray] = None,
        horizon: int = MAX_VALUE,
        objective: Objective = Objective.MAKESPAN,
    ):
        self._jobs = jobs
        self._machines = machines
        self._tasks = tasks
        self._processing_times = processing_times
        self._constraints = constraints

        num_mach = self.num_machines
        num_tasks = self.num_tasks

        self._setup_times = (
            setup_times
            if setup_times is not None
            else np.zeros((num_mach, num_tasks, num_tasks), dtype=int)
        )
        self._horizon = horizon
        self._objective = objective

        self._machine2tasks: list[list[int]] = [[] for _ in range(num_mach)]
        self._task2machines: list[list[int]] = [[] for _ in range(num_tasks)]

        for machine, task in self.processing_times.keys():
            bisect.insort(self._machine2tasks[machine], task)
            bisect.insort(self._task2machines[task], machine)

        self._validate_parameters()

    def _validate_parameters(self):
        """
        Validates the problem data parameters.
        """
        num_mach = self.num_machines
        num_tasks = self.num_tasks

        for job in self.jobs:
            if any(task >= num_tasks for task in job.tasks):
                raise ValueError("Job references to unknown task.")

        if any(duration < 0 for duration in self.processing_times.values()):
            raise ValueError("Processing times must be non-negative.")

        tasks_with_processing = {t for _, t in self.processing_times.keys()}
        if set(range(num_tasks)) != tasks_with_processing:
            raise ValueError("Processing times missing for some tasks.")

        if np.any(self.setup_times < 0):
            raise ValueError("Setup times must be non-negative.")

        if self.setup_times.shape != (num_mach, num_tasks, num_tasks):
            msg = "Setup times shape not (num_machines, num_tasks, num_tasks)."
            raise ValueError(msg)

        if self.horizon < 0:
            raise ValueError("Horizon must be non-negative.")

        if self.objective in [Objective.TARDY_JOBS, Objective.TOTAL_TARDINESS]:
            if any(job.due_date is None for job in self.jobs):
                msg = "Job due dates required for tardiness-based objectives."
                raise ValueError(msg)

    @property
    def jobs(self) -> list[Job]:
        """
        Returns the job data of this problem instance.
        """
        return self._jobs

    @property
    def machines(self) -> list[Machine]:
        """
        Returns the machine data of this problem instance.
        """
        return self._machines

    @property
    def tasks(self) -> list[Task]:
        """
        Returns the task data of this problem instance.
        """
        return self._tasks

    @property
    def processing_times(self) -> dict[tuple[int, int], int]:
        """
        Processing times of tasks on machines.

        Returns
        -------
        dict[tuple[int, int], int]
            Processing times of tasks on machines. First index is
            the machine index, second index is the task index.
        """
        return self._processing_times

    @property
    def constraints(self) -> _CONSTRAINTS_TYPE:
        """
        Constraints between tasks.

        Returns
        -------
        dict[tuple[int, int], list[Constraint]]
            The dictionary is indexed by task pairs with a list of
            constraints.
        """
        return self._constraints

    @property
    def setup_times(self) -> np.ndarray:
        """
        Sequence-dependent setup times between tasks on a given machine.

        Returns
        -------
        np.ndarray
            Sequence-dependent setup times between tasks on a given
            machine. The first dimension of the array is indexed by the machine
            index. The last two dimensions of the array are indexed by
            task indices.
        """
        return self._setup_times

    @property
    def horizon(self) -> int:
        """
        The time horizon of this instance. This is an upper bound on the
        completion time of all tasks.

        Returns
        -------
        int
            The horizon value.
        """
        return self._horizon

    @property
    def objective(self) -> Objective:
        """
        The objective function to be minimized.

        Returns
        -------
        Objective
            The objective function to be minimized.
        """
        return self._objective

    @property
    def machine2tasks(self) -> list[list[int]]:
        """
        List of task indices for each machine. These are inferred from
        the (machine, task) pairs in the processing times dict.

        Returns
        -------
        list[list[int]]
            List of task indices for each machine.
        """
        return self._machine2tasks

    @property
    def task2machines(self) -> list[list[int]]:
        """
        List of eligible machine indices for each task. These are inferred
        from the (machine, task) pairs in the processing times dict.

        Returns
        -------
        list[list[int]]
            List of eligible machine indices for each task.
        """
        return self._task2machines

    @property
    def num_jobs(self) -> int:
        """
        Returns the number of jobs in this instance.
        """
        return len(self._jobs)

    @property
    def num_machines(self) -> int:
        """
        Returns the number of machines in this instance.
        """
        return len(self._machines)

    @property
    def num_tasks(self) -> int:
        """
        Returns the number of tasks in this instance.
        """
        return len(self._tasks)
