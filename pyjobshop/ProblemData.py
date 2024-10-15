from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence, TypeVar, Union

import enum_tools.documentation
import numpy as np

from pyjobshop.constants import MAX_VALUE

_ConstraintsType = dict[tuple[int, int], list["Constraint"]]
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


class Resource:
    """
    Simple dataclass for storing all resource-related data.

    Parameters
    ----------
    capacity
        Capacity of the resource.
    renewable
        Whether the resource is renewable. A renewable resource replenishes
        its capacity after each task completion. Default ``True``.
    name
        Name of the resource.
    """

    def __init__(self, capacity: int, renewable: bool = True, name: str = ""):
        if capacity < 0:
            raise ValueError("Capacity must be non-negative.")

        self._capacity = capacity
        self._renewable = renewable
        self._name = name

    @property
    def capacity(self) -> int:
        """
        Capacity of the resource.
        """
        return self._capacity

    @property
    def renewable(self) -> bool:
        """
        Whether the resource is renewable.
        """
        return self._renewable

    @property
    def name(self) -> str:
        """
        Name of the resource.
        """
        return self._name


class Machine(Resource):
    """
    Simple dataclass for storing all machine-related data. A machine is a
    specialized resource type that allows for sequencing constraints.

    Parameters
    ----------
    name
        Name of the machine.
    """

    def __init__(self, name: str = ""):
        super().__init__(capacity=0, renewable=True, name=name)

    @property
    def name(self) -> str:
        """
        Name of the machine.
        """
        return self._name


ResourceType = Union["Resource", "Machine"]


class Task:
    """
    Simple dataclass for storing all task related data.

    Parameters
    ----------
    earliest_start
        Earliest start time of the task. Default ``0``.
    latest_start
        Latest start time of the task. Default ``MAX_VALUE``.
    earliest_end
        Earliest end time of the task. Default ``0``.
    latest_end
        Latest end time of the task. Default ``MAX_VALUE``.
    fixed_duration
        Whether the task has a fixed duration. A fixed duration means that
        the task duration is precisely the processing time (on a given
        resource). If the duration is not fixed, then the task duration
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


class Mode:
    """
    Simpel dataclass for storing processing mode data.

    Parameters
    ----------
    task
        Task index that this mode belongs to.
    resources
        List of resources that are required for this mode.
    duration
        Processing duration of this mode.
    demands
        Optional list of demands for each resource for this mode. If ``None``
        is given, then the demands are initialized as list of zeros with the
        same length as the resources.
    """

    def __init__(
        self,
        task: int,
        resources: list[int],
        duration: int,
        demands: Optional[list[int]] = None,
    ):
        if len(set(resources)) != len(resources):
            raise ValueError("Mode resources must be unique.")

        if duration < 0:
            raise ValueError("Mode duration must be non-negative.")

        demands = demands if demands is not None else [0] * len(resources)
        if any(demand < 0 for demand in demands):
            raise ValueError("Mode demands must be non-negative.")

        if len(resources) != len(demands):
            raise ValueError("resources and demands must have same length.")

        self._task = task
        self._resources = resources
        self._duration = duration
        self._demands = demands

    @property
    def task(self) -> int:
        return self._task

    @property
    def resources(self) -> list[int]:
        return self._resources

    @property
    def duration(self) -> int:
        return self._duration

    @property
    def demands(self) -> list[int]:
        return self._demands

    def __eq__(self, other) -> bool:
        return (
            self.task == other.task
            and self.resources == other.resources
            and self.duration == other.duration
            and self.demands == other.demands
        )


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

    #: Assign tasks :math:`i` and :math:`j` to modes with the same set of resources. # noqa
    IDENTICAL_RESOURCES = "identical_resources"

    #: Assign tasks :math:`i` and :math:`j` to modes with disjoint sets of resources. # noqa
    DIFFERENT_RESOURCES = "different_resources"

    #: Sequence :math:`i` right before :math:`j` (if assigned to same resource). # noqa
    PREVIOUS = "previous"

    #: Sequence :math:`i` before :math:`j` (if assigned to same resources).
    BEFORE = "before"


@dataclass
class Objective:
    """
    Represents a weighted sum of the following objective functions:

    * Makespan
    * Number of tardy jobs
    * Total flow time
    * Total tardiness
    * Total earliness

    .. note::
        Use :attr:`Job.weight` to set a specific job's contribution to the
        objective function.
    """

    weight_makespan: int = 0
    weight_tardy_jobs: int = 0
    weight_total_flow_time: int = 0
    weight_total_tardiness: int = 0
    weight_total_earliness: int = 0

    @classmethod
    def makespan(cls):
        """
        Minimizes the makespan.
        """
        return cls(weight_makespan=1)

    @classmethod
    def total_flow_time(cls):
        """
        Minimizes the total flow time.
        """
        return cls(weight_total_flow_time=1)

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


class ProblemData:
    """
    Creates a problem data instance. This instance contains all information
    need to solve the scheduling problem.

    Parameters
    ----------
    jobs
        List of jobs.
    resources
        List of resources.
    tasks
        List of tasks.
    modes
        List of processing modes of tasks.
    constraints
        Dict indexed by task pairs with a list of constraints as values.
        Default is None, which initializes an empty dict.
    setup_times
        Sequence-dependent setup times between tasks on a given resource. The
        first dimension of the array is indexed by the resource index. The last
        two dimensions of the array are indexed by task indices.
    horizon
        The horizon value. Default ``MAX_VALUE``.
    objective
        The objective function. Default is minimizing the makespan.
    """

    def __init__(
        self,
        jobs: list[Job],
        resources: Sequence[ResourceType],
        tasks: list[Task],
        modes: list[Mode],
        constraints: Optional[_ConstraintsType] = None,
        setup_times: Optional[np.ndarray] = None,
        horizon: int = MAX_VALUE,
        objective: Optional[Objective] = None,
    ):
        self._jobs = jobs
        self._resources = resources
        self._tasks = tasks
        self._modes = modes
        self._constraints = constraints if constraints is not None else {}
        self._setup_times = setup_times
        self._horizon = horizon
        self._objective = (
            objective if objective is not None else Objective.makespan()
        )

        self._validate_parameters()

    def _validate_parameters(self):
        """
        Validates the problem data parameters.
        """
        num_res = self.num_resources
        num_tasks = self.num_tasks

        for job in self.jobs:
            if any(task < 0 or task >= num_tasks for task in job.tasks):
                raise ValueError("Job references to unknown task index.")

        for idx, mode in enumerate(self.modes):
            if mode.task < 0 or mode.task >= num_tasks:
                raise ValueError(f"Mode {idx} references unknown task index.")

            for resource in mode.resources:
                if resource < 0 or resource >= num_res:
                    msg = f"Mode {idx} references unknown resource index."
                    raise ValueError(msg)

        without = set(range(num_tasks)) - {mode.task for mode in self.modes}
        names = [self.tasks[idx].name or idx for idx in sorted(without)]
        if names:  # task indices if names are not available
            raise ValueError(f"Processing modes missing for tasks {without}.")

        infeasible_modes = Counter()
        num_modes = Counter()

        for mode in self.modes:
            num_modes[mode.task] += 1
            infeasible_modes[mode.task] += any(
                demand > self.resources[resource].capacity
                for demand, resource in zip(mode.demands, mode.resources)
            )

        for task, count in num_modes.items():
            if infeasible_modes[task] == count:
                msg = f"All modes for task {task} have infeasible demands."
                raise ValueError(msg)

        if self.setup_times is not None:
            if np.any(self.setup_times < 0):
                raise ValueError("Setup times must be non-negative.")

            if self.setup_times.shape != (num_res, num_tasks, num_tasks):
                shape = "(num_resources, num_tasks, num_tasks)"
                raise ValueError(f"Setup times shape must be {shape}.")

            for idx, resource in enumerate(self.resources):
                is_machine = isinstance(resource, Machine)
                has_setup_times = np.any(self.setup_times[idx] > 0)

                if not is_machine and has_setup_times:
                    msg = "Setup times only allowed for machines."
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
        resources: Optional[Sequence[ResourceType]] = None,
        tasks: Optional[list[Task]] = None,
        modes: Optional[list[Mode]] = None,
        constraints: Optional[_ConstraintsType] = None,
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
        resources
            Optional list of resources.
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
        resources = _deepcopy_if_none(resources, self.resources)
        tasks = _deepcopy_if_none(tasks, self.tasks)
        modes = _deepcopy_if_none(modes, self.modes)
        constraints = _deepcopy_if_none(constraints, self.constraints)
        setup_times = _deepcopy_if_none(setup_times, self.setup_times)
        horizon = _deepcopy_if_none(horizon, self.horizon)
        objective = _deepcopy_if_none(objective, self.objective)

        return ProblemData(
            jobs=jobs,
            resources=resources,
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
    def resources(self) -> Sequence[ResourceType]:
        """
        Returns the resource data of this problem instance.
        """
        return self._resources

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
    def constraints(self) -> _ConstraintsType:
        """
        Dict indexed by task pairs with a list of constraints as values.
        Indexed by task pairs.
        """
        return self._constraints

    @property
    def setup_times(self) -> Optional[np.ndarray]:
        """
        Optional sequence-dependent setup times between tasks on a given
        machine. The first index is the resource index and the last two
        indices are the task indices.
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
    def num_resources(self) -> int:
        """
        Returns the number of resources in this instance.
        """
        return len(self._resources)

    @property
    def num_tasks(self) -> int:
        """
        Returns the number of tasks in this instance.
        """
        return len(self._tasks)

    @property
    def num_modes(self) -> int:
        """
        Returns the number of modes in this instance.
        """
        return len(self._modes)
