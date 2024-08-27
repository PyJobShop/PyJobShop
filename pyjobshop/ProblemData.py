from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Optional, TypeVar

import enum_tools.documentation
import numpy as np

from pyjobshop.constants import MAX_VALUE

_CONSTRAINTS_TYPE = dict[tuple[int, int], list["Constraint"]]
_T = TypeVar("_T")


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
        """
        The job importance weight, used as multiplicative factor in the
        objective function.
        """
        return self._weight

    @property
    def release_date(self) -> int:
        """
        The earliest time that the job may start.
        """
        return self._release_date

    @property
    def deadline(self) -> int:
        """
        The latest time by which the job must be completed.
        """
        return self._deadline

    @property
    def due_date(self) -> Optional[int]:
        """
        The latest time that the job should be completed before incurring
        penalties.
        """
        return self._due_date

    @property
    def tasks(self) -> list[int]:
        """
        List of task indices that belong to this job.
        """
        return self._tasks

    @property
    def name(self) -> str:
        """
        Name of the job.
        """
        return self._name

    def add_task(self, idx: int):
        """
        Adds a task index to the job.

        Parameters
        ----------
        idx
            Task index to add.
        """
        self._tasks.append(idx)


class Machine:
    """
    Simple dataclass for storing all machine-related data.

    Parameters
    ----------
    capacity
        Capacity of the machine. Default 0. If the capacity is nonzero, then
        the machine can process a number of tasks at the same time, which is
        determined by the task mode demands.
    name
        Name of the machine.
    """

    def __init__(self, capacity: int = 0, name: str = ""):
        self._capacity = capacity
        self._name = name

    @property
    def capacity(self) -> int:
        """
        Capacity of the machine.
        """
        return self._capacity

    @property
    def name(self) -> str:
        """
        Name of the machine.
        """
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
        """
        Earliest start time of the task.
        """
        return self._earliest_start

    @property
    def latest_start(self) -> int:
        """
        Latest start time of the task.
        """
        return self._latest_start

    @property
    def earliest_end(self) -> int:
        """
        Earliest end time of the task.
        """
        return self._earliest_end

    @property
    def latest_end(self) -> int:
        """
        Latest end time of the task.
        """
        return self._latest_end

    @property
    def fixed_duration(self) -> bool:
        """
        Whether the task has a fixed duration.
        """
        return self._fixed_duration

    @property
    def name(self) -> str:
        """
        Name of the task.
        """
        return self._name


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

    # TODO how do sequence and assignment constraints work in the context
    # of renewable resources and modes?
    #: Sequence :math:`i` right before :math:`j` (if assigned to same machine).
    PREVIOUS = "previous"

    #: Sequence :math:`i` before :math:`j` (if assigned to same machines).
    BEFORE = "before"

    #: Assign tasks :math:`i` and :math:`j` to the same machine.
    SAME_MACHINE = "same_machine"

    #: Assign tasks :math:`i` and :math:`j` to different machines.
    DIFFERENT_MACHINE = "different_machine"


@dataclass
class Objective:
    """
    Represents a weighted sum of the following objective functions:

    * Makespan
    * Number of tardy jobs
    * Total completion time
    * Total tardiness
    * Total earliness

    .. note::
        Use :attr:`Job.weight` to set a specific job's contribution to the
        objective function.
    """

    weight_makespan: int = 0
    weight_tardy_jobs: int = 0
    weight_total_completion_time: int = 0
    weight_total_tardiness: int = 0
    weight_total_earliness: int = 0

    @classmethod
    def makespan(cls):
        """
        Minimizes the makespan.
        """
        return cls(weight_makespan=1)

    @classmethod
    def total_completion_time(cls):
        """
        Minimizes the total completion time.
        """
        return cls(weight_total_completion_time=1)

    @classmethod
    def tardy_jobs(cls):
        """
        Minimizes the number of tardy jobs.
        """
        return cls(weight_tardy_jobs=1)

    @classmethod
    def total_tardiness(cls):
        """
        Minimizes the total tardiness.
        """
        return cls(weight_total_tardiness=1)

    @classmethod
    def total_earliness(cls):
        """
        Minimizes the total earliness.
        """
        return cls(weight_total_earliness=1)


@dataclass
class Mode:
    """
    Simple dataclass for storing processing mode data.

    Parameters
    ----------
    task
        Task index that this mode belongs to.
    duration
        Processing duration of this mode.
    resources
        List of resources that are required for this mode.
    demands
        List of resource demands for this mode.
    """

    task: int
    duration: int
    resources: list[int]
    demands: Optional[list[int]] = None

    def __post_init__(self):
        if self.demands is None:
            self.demands = [0] * len(self.resources)

        if self.duration < 0:
            raise ValueError("Processing mode duration must be non-negative.")

        if self.demand < 0:
            raise ValueError("Demand must be non-negative.")

    @property
    def machine(self):
        return self.resources[0]

    @property
    def demand(self):
        return self.demands[0] if len(self.demands) > 0 else 0


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
    modes
        List of processing modes of tasks.
    constraints
        Dict indexed by task pairs with a list of constraints as values.
        Default is None, which initializes an empty dict.
    setup_times
        Sequence-dependent setup times between tasks on a given machine. The
        first dimension of the array is indexed by the machine index. The last
        two dimensions of the array are indexed by task indices.
    horizon
        The horizon value. Default ``MAX_VALUE``.
    objective
        The objective function. Default is minimizing the makespan.
    """

    def __init__(
        self,
        jobs: list[Job],
        machines: list[Machine],
        tasks: list[Task],
        modes: list[Mode],
        constraints: Optional[_CONSTRAINTS_TYPE] = None,
        setup_times: Optional[np.ndarray] = None,
        horizon: int = MAX_VALUE,
        objective: Optional[Objective] = None,
    ):
        self._jobs = jobs
        self._machines = machines
        self._tasks = tasks
        self._modes = modes
        self._constraints = constraints if constraints is not None else {}

        num_mach = self.num_machines
        num_tasks = self.num_tasks

        self._setup_times = (
            setup_times
            if setup_times is not None
            else np.zeros((num_mach, num_tasks, num_tasks), dtype=int)
        )
        self._horizon = horizon
        self._objective = (
            objective if objective is not None else Objective.makespan()
        )

        self._validate_parameters()

    def _validate_parameters(self):
        """
        Validates the problem data parameters.
        """
        num_mach = self.num_machines
        num_tasks = self.num_tasks

        for job in self.jobs:
            if any(task < 0 or task >= num_tasks for task in job.tasks):
                raise ValueError("Job references to unknown task index.")

        for mode in self.modes:
            if mode.task < 0 or mode.task >= num_tasks:
                raise ValueError("Mode references to unknown task index.")

            if mode.machine < 0 or mode.machine >= num_mach:
                raise ValueError("Mode references to unknown machine index.")

        without = set(range(num_tasks)) - {mode.task for mode in self.modes}
        names = [self.tasks[idx].name or idx for idx in sorted(without)]
        if names:  # task indices if names are not available
            raise ValueError(f"Processing modes missing for tasks {without}.")

        if np.any(self.setup_times < 0):
            raise ValueError("Setup times must be non-negative.")

        if self.setup_times.shape != (num_mach, num_tasks, num_tasks):
            msg = "Setup times shape not (num_machines, num_tasks, num_tasks)."
            raise ValueError(msg)

        if self.horizon < 0:
            raise ValueError("Horizon must be non-negative.")

        if (
            self.objective.weight_tardy_jobs > 0
            or self.objective.weight_total_tardiness > 0
            or self.objective.weight_total_earliness > 0
        ):
            if any(job.due_date is None for job in self.jobs):
                msg = "Job due dates required for due date-based objectives."
                raise ValueError(msg)

    def replace(
        self,
        jobs: Optional[list[Job]] = None,
        machines: Optional[list[Machine]] = None,
        tasks: Optional[list[Task]] = None,
        modes: Optional[list[Mode]] = None,
        constraints: Optional[_CONSTRAINTS_TYPE] = None,
        setup_times: Optional[np.ndarray] = None,
        horizon: Optional[int] = None,
        objective: Optional[Objective] = None,
    ) -> "ProblemData":
        """
        Returns a new ProblemData instance with possibly replaced data. If a
        parameter is not provided, the original data is deepcopied instead.

        Parameters
        ----------
        jobs
            Optional list of jobs.
        machines
            Optional list of machines.
        tasks
            Optional list of tasks.
        modes
            Optional processing modes of tasks.
        constraints
            Optional constraints between tasks.
        setup_times
            Optional sequence-dependent setup times.
        horizon
            Optional horizon value.
        objective
            Optional objective function.

        Returns
        -------
        ProblemData
            A new ProblemData instance with possibly replaced data.
        """

        def _deepcopy_if_none(value: Optional[_T], default: _T) -> _T:
            return value if value is not None else deepcopy(default)

        jobs = _deepcopy_if_none(jobs, self.jobs)
        machines = _deepcopy_if_none(machines, self.machines)
        tasks = _deepcopy_if_none(tasks, self.tasks)
        modes = _deepcopy_if_none(modes, self.modes)
        constraints = _deepcopy_if_none(constraints, self.constraints)
        setup_times = _deepcopy_if_none(setup_times, self.setup_times)
        horizon = _deepcopy_if_none(horizon, self.horizon)
        objective = _deepcopy_if_none(objective, self.objective)

        return ProblemData(
            jobs=jobs,
            machines=machines,
            tasks=tasks,
            modes=modes,
            constraints=constraints,
            setup_times=setup_times,
            horizon=horizon,
            objective=objective,
        )

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
    def modes(self) -> list[Mode]:
        """
        Returns the processing modes of this problem instance.
        """
        return self._modes

    @property
    def constraints(self) -> _CONSTRAINTS_TYPE:
        """
        Dict indexed by task pairs with a list of constraints as values.
        Indexed by task pairs.
        """
        return self._constraints

    @property
    def setup_times(self) -> np.ndarray:
        """
        Sequence-dependent setup times between tasks on a given machine. The
        first dimension of the array is indexed by the machine index. The last
        two dimensions of the array are indexed by task indices.
        """
        return self._setup_times

    @property
    def horizon(self) -> int:
        """
        The time horizon of this instance. This is an upper bound on the
        completion time of all tasks.
        """
        return self._horizon

    @property
    def objective(self) -> Objective:
        """
        The objective function.
        """
        return self._objective

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
