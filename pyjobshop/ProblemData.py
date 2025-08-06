from collections import Counter, defaultdict
from copy import deepcopy
from dataclasses import dataclass, field, fields
from itertools import pairwise
from typing import Sequence, TypeVar

from pyjobshop.constants import MAX_VALUE

_T = TypeVar("_T")


class Job:
    """
    Simple dataclass for storing job related data.

    Parameters
    ----------
    weight
        The weight of the job, used as multiplicative factor in the
        objective function. Default ``1``.
    release_date
        The earliest time that the job may start. Default ``0``.
    deadline
        The latest time by which the job must be completed. Note that a
        deadline is different from a due date; the latter does not restrict
        the latest completion time.
        Default :const:`~pyjobshop.constants.MAX_VALUE`.
    due_date
        The latest time that the job should be completed before incurring
        penalties. Default ``None``, meaning that there is no due date.
    tasks
        List of task indices that belong to this job. Default ``None``,
        which initializes an empty list.
    name
        Name of the job.
    """

    def __init__(
        self,
        weight: int = 1,
        release_date: int = 0,
        deadline: int = MAX_VALUE,
        due_date: int | None = None,
        tasks: list[int] | None = None,
        *,
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
        The weight of the job, used as multiplicative factor in the objective
        function.
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
    def due_date(self) -> int | None:
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
    A machine resource is a specialized resource that only processes one task
    at a time and can handle sequencing constraints.

    Parameters
    ----------
    breaks
        List of time intervals during which tasks cannot be processed.
        Each interval is represented as a tuple (start_time, end_time).
        Default is an empty list (no breaks).
    no_idle
        Whether the machine must operate continuously without idle time between
        tasks. When ``True``, tasks are scheduled back-to-back with no gaps,
        except for required setup times. When ``False`` (default), the machine
        can remain idle between tasks. Cannot be used with machine breaks.
    name
        Name of the machine.
    """

    def __init__(
        self,
        breaks: list[tuple[int, int]] | None = None,
        no_idle: bool = False,
        *,
        name: str = "",
    ):
        if breaks is not None:
            for start, end in breaks:
                if start < 0 or start >= end:
                    raise ValueError("Break start < 0 or start > end.")

            for interval1, interval2 in pairwise(sorted(breaks)):
                if interval1[1] > interval2[0]:
                    raise ValueError("Break intervals must not overlap.")

        if breaks and no_idle:
            raise ValueError("Breaks not allowed with no_idle=True.")

        self._breaks = breaks or []
        self._no_idle = no_idle
        self._name = name

    @property
    def breaks(self) -> list[tuple[int, int]]:
        """
        List of time intervals during which tasks cannot be processed.
        """
        return self._breaks

    @property
    def no_idle(self) -> bool:
        """
        Whether the machine has no idle time constraints.
        """
        return self._no_idle

    @property
    def name(self) -> str:
        """
        Name of the machine.
        """
        return self._name


class Renewable:
    """
    A renewable resource that replenishes its capacity after each task
    completion.

    Parameters
    ----------
    capacity
        Capacity of the resource.
    breaks
        List of time intervals during which tasks cannot be processed.
        Each interval is represented as a tuple (start_time, end_time).
        Default is an empty list (no breaks).
    name
        Name of the resource.
    """

    def __init__(
        self,
        capacity: int,
        breaks: list[tuple[int, int]] | None = None,
        *,
        name: str = "",
    ):
        if capacity < 0:
            raise ValueError("Capacity must be non-negative.")

        if breaks is not None:
            for start, end in breaks:
                if start < 0 or start >= end:
                    raise ValueError("Break start < 0 or start > end.")

            for interval1, interval2 in pairwise(sorted(breaks)):
                if interval1[1] > interval2[0]:
                    raise ValueError("Break intervals must not overlap.")

        self._capacity = capacity
        self._breaks = breaks or []
        self._name = name

    @property
    def capacity(self) -> int:
        """
        Capacity of the resource.
        """
        return self._capacity

    @property
    def breaks(self) -> list[tuple[int, int]]:
        """
        List of time intervals during which tasks cannot be processed.
        """
        return self._breaks

    @property
    def name(self) -> str:
        """
        Name of the resource.
        """
        return self._name


class NonRenewable:
    """
    A non-renewable resource that does not replenish its capacity.

    Parameters
    ----------
    capacity
        Capacity of the resource.
    name
        Name of the resource.
    """

    def __init__(self, capacity: int, *, name: str = ""):
        if capacity < 0:
            raise ValueError("Capacity must be non-negative.")

        self._capacity = capacity
        self._name = name

    @property
    def capacity(self) -> int:
        """
        Capacity of the resource.
        """
        return self._capacity

    @property
    def name(self) -> str:
        """
        Name of the resource.
        """
        return self._name


Resource = Machine | Renewable | NonRenewable


class Task:
    """
    Simple dataclass for storing task related data.

    Parameters
    ----------
    job
        The index of the job that this task belongs to. None if the task
        does not belong to any job. Default ``None``.
    earliest_start
        Earliest start time of the task. Default ``0``.
    latest_start
        Latest start time of the task.
        Default :const:`~pyjobshop.constants.MAX_VALUE`.
    earliest_end
        Earliest end time of the task. Default ``0``.
    latest_end
        Latest end time of the task.
        Default :const:`~pyjobshop.constants.MAX_VALUE`.
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
        job: int | None = None,
        earliest_start: int = 0,
        latest_start: int = MAX_VALUE,
        earliest_end: int = 0,
        latest_end: int = MAX_VALUE,
        fixed_duration: bool = True,
        *,
        name: str = "",
    ):
        if earliest_start > latest_start:
            raise ValueError("earliest_start must be <= latest_start.")

        if earliest_end > latest_end:
            raise ValueError("earliest_end must be <= latest_end.")

        self._job = job
        self._earliest_start = earliest_start
        self._latest_start = latest_start
        self._earliest_end = earliest_end
        self._latest_end = latest_end
        self._fixed_duration = fixed_duration
        self._name = name

    @property
    def job(self) -> int | None:
        """
        The index of the job that this task belongs to. None if the task
        does not belong to any job.
        """
        return self._job

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
    Simple dataclass for storing processing mode data.

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
    name
        Name of the mode.
    """

    def __init__(
        self,
        task: int,
        resources: list[int],
        duration: int,
        demands: list[int] | None = None,
        *,
        name: str = "",
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
        self._name = name

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

    @property
    def name(self) -> str:
        return self._name

    def __eq__(self, other) -> bool:
        return (
            self.task == other.task
            and self.resources == other.resources
            and self.duration == other.duration
            and self.demands == other.demands
            and self.name == other.name
        )


class IterableMixin:
    """
    Mixin class for making dataclases iterable (and thus unpackable). This
    makes the implementation of constraints more concise and readable.
    """

    def __iter__(self):
        return iter(getattr(self, f.name) for f in fields(self))


@dataclass
class StartBeforeStart(IterableMixin):
    """
    Start task 1 (:math:`s_1`) before task 2 starts (:math:`s_2`), with an
    optional delay :math:`d`. That is,

    .. math::
        s_1 + d \\leq s_2.
    """

    task1: int
    task2: int
    delay: int = 0


@dataclass
class StartBeforeEnd(IterableMixin):
    """
    Start task 1 (:math:`s_1`) before task 2 ends (:math:`e_2`), with an
    optional delay :math:`d`. That is,

    .. math::
        s_1 + d \\leq e_2.
    """

    task1: int
    task2: int
    delay: int = 0


@dataclass
class EndBeforeStart(IterableMixin):
    """
    End task 1 (:math:`e_1`) before task 2 starts (:math:`s_2`), with an
    optional delay :math:`d`. That is,

    .. math::
        e_1 + d \\leq s_2.
    """

    task1: int
    task2: int
    delay: int = 0


@dataclass
class EndBeforeEnd(IterableMixin):
    """
    End task 1 (:math:`e_1`) before task 2 ends (:math:`e_2`), with an
    optional delay :math:`d`. That is,

    .. math::
        e_1 + d \\leq e_2.
    """

    task1: int
    task2: int
    delay: int = 0


@dataclass
class IdenticalResources(IterableMixin):
    """
    Select modes for task 1 and task 2 that use the same resources.

    Let :math:`m_1, m_2` be the selected modes of task 1 and task 2, and let
    :math:`R_m` denote the resources required by mode :math:`m`. This
    constraint ensures that

    .. math::
        R_{m_1} = R_{m_2}.
    """

    task1: int
    task2: int


@dataclass
class DifferentResources(IterableMixin):
    """
    Select modes for task 1 and task 2 that use different resources.

    Let :math:`m_1, m_2` be the selected modes of task 1 and task 2, and let
    :math:`R_m` denote the resources required by mode :math:`m`. This
    constraint ensures that

    .. math::
        R_{m_1} \\cap R_{m_2} = \\emptyset.
    """

    task1: int
    task2: int


@dataclass
class Consecutive(IterableMixin):
    """
    Sequence task 1 and task 2 consecutively on the machines they are both
    assigned to, meaning that no other task is allowed to be scheduled between
    them.

    Hand-waiving some details, let :math:`m_1, m_2` be the selected modes of
    task 1 and task 2, and let :math:`R` denote the machines that both modes
    require. This constraint ensures that

    .. math::
        m_1 \\to m_2 \\quad \\forall r \\in R,

    where :math:`\\to` means that :math:`m_1` is directly followed by
    :math:`m_2` and no other interval is scheduled between them.
    """

    task1: int
    task2: int


@dataclass
class SameSequence(IterableMixin):
    """
    Ensures that two machines process their assigned tasks in the same relative
    order. Both machines must have the same number of assigned tasks for this
    constraint to be valid.

    When ``tasks1`` and ``tasks2`` are not specified, the constraint applies to
    all tasks assigned to each machine, with ordering determined by their task
    indices in ascending order. For explicit control over the task sequence,
    use the ``tasks1`` and ``tasks2`` parameters.

    Example
    -------
    Assume that machine 1 can process tasks [1, 3] and machine 2 can process
    tasks [2, 4]. The default (by task indices) allows the following valid
    sequences:

    * (1→3, 2→4) or (3→1, 4→2)

    If passing arguments ``tasks1=[1, 3]`` and ``tasks2=[4, 2]``, then the
    following sequences are valid:

    * (1→3, 4→2) or (3→1, 2→4)
    """

    machine1: int
    machine2: int
    tasks1: list[int] | None = None
    tasks2: list[int] | None = None

    def __post_init__(self):
        if self.tasks1 is not None and self.tasks2 is not None:
            if len(self.tasks1) != len(self.tasks2):
                msg = "tasks1 and tasks2 must be same length."
                raise ValueError(msg)

            if len(set(self.tasks1)) != len(self.tasks1):
                raise ValueError("tasks1 contains duplicate values.")

            if len(set(self.tasks2)) != len(self.tasks2):
                raise ValueError("tasks2 contains duplicate values.")


@dataclass
class SetupTime(IterableMixin):
    """
    Sequence-dependent setup time between task 1 and task 2 on the given
    machine.

    Let :math:`e_1` be the end time of task 1 and let :math:`s_2` be the
    start time of task 2. If the selected modes of task 1 and task 2 both
    require the given machine, then this constraint ensures that

    .. math::
        e_1 + d \\leq s_2,

    where :math:`d` is the setup time duration. Note that this also implies
    an end-before-start relationship between task 1 and task 2.

    When using :attr:`Machine.breaks`, setup times are allowed to take place
    during the breaks.
    """

    machine: int
    task1: int
    task2: int
    duration: int

    def __post_init__(self):
        if self.duration < 0:
            raise ValueError("Setup time must be non-negative.")


@dataclass
class ModeDependency(IterableMixin):
    """
    Represents a dependency between task modes: if mode 1 is selected,
    then at least one of the modes in modes 2 must also be selected.

    Let :math:`m_1` be the Boolean variable indicating whether mode 1 is
    selected. Let :math:`M_2` be the set of Boolean variables corresponding
    to the modes in modes 2.

    The constraint is then expressed as:

    .. math::
        m_1 \\leq \\sum_{m \\in M_2} m
    """

    mode1: int
    modes2: list[int]

    def __post_init__(self):
        if len(self.modes2) == 0:
            raise ValueError("At least one mode in modes2 must be specified.")


@dataclass
class Constraints:
    """
    Simple container class for storing all constraints.
    """

    start_before_start: list[StartBeforeStart] = field(default_factory=list)
    start_before_end: list[StartBeforeEnd] = field(default_factory=list)
    end_before_start: list[EndBeforeStart] = field(default_factory=list)
    end_before_end: list[EndBeforeEnd] = field(default_factory=list)
    identical_resources: list[IdenticalResources] = field(default_factory=list)
    different_resources: list[DifferentResources] = field(default_factory=list)
    consecutive: list[Consecutive] = field(default_factory=list)
    same_sequence: list[SameSequence] = field(default_factory=list)
    setup_times: list[SetupTime] = field(default_factory=list)
    mode_dependencies: list[ModeDependency] = field(default_factory=list)

    def __len__(self) -> int:
        """
        Returns the total number of constraints across all types.
        """
        return sum(len(getattr(self, f.name)) for f in fields(self))

    def __str__(self) -> str:
        parts = []
        for f in fields(self):
            count = len(getattr(self, f.name))
            if count > 0:
                parts.append(f"{count} {f.name}")

        lines = [f"{len(self)} constraints"]
        for idx, part in enumerate(parts):
            symbol = "└─" if idx == len(parts) - 1 else "├─"
            lines.append(f"{symbol} {part}")

        return "\n".join(lines)


@dataclass
class Objective:
    r"""
    The objective class represents a weighted sum of objective functions :math:`f`, calculated as:
    :math:`\sum_f \text{weight}_f \cdot \text{value}_f` with :math:`\text{weight}_f \ge 0`.
    The objective functions :math:`f` are defined below.

    In the following, let :math:`J` denote the set of jobs, :math:`T` denote the set of tasks,
    :math:`C_j` denote the completion time of job :math:`j`, and :math:`C_t` denote the completion time of
    task :math:`t`.

    **Makespan** (:math:`C_{\max}`): The finish time of the latest task.
        .. math::
            C_{\max} = \max_{t \in T} C_t

    **Number of tardy jobs** (:math:`NTJ`): The weighted sum of all tardy jobs, where a job is tardy when it does not meet its due date :math:`d_j`.
        .. math::
            NTJ = \sum_{j \in J} w_j \mathbb{1}_{\{C_j - d_j > 0\}}

    where :math:`\mathbb{1}_{\{x\}}` is the indicator function.

    **Total flow time** (:math:`TFT`): The weighted sum of the length of stay in the system of each job, from their release date to their completion.
        .. math::
            TFT = \sum_{j \in J} w_j ( C_j - r_j )

    **Total tardiness** (:math:`TT`): The weighted sum of the tardiness of each job, where the tardiness is the difference between completion time and due date :math:`d_j` (0 if completed before due date).
        .. math::
            TT = \sum_{j \in J} w_j U_j

    **Total earliness** (:math:`TE`): The weighted sum of the earliness of each job, where earliness is the difference between due date :math:`d_j` and completion time (0 if completed after due date).
        .. math::
            TE = \sum_{j \in J} w_j (\max(d_j - C_j, 0))

    **Maximum tardiness** (:math:`U_{\max}`): The weighted maximum tardiness of all jobs.
        .. math::
            U_{\max} = \max_{j \in J} w_j (\max(C_j - d_j, 0))

    **Total setup time** (:math:`TST`): The sum of all sequence-dependent setup times between consecutive tasks on each machine, where :math:`R` denotes the set of machines, :math:`M^R_r` denotes the set of modes requiring :math:`r \in R`, :math:`s_{t_u, t_v, r}` denotes the setup time between tasks :math:`t_u` and :math:`t_v` on machine :math:`r` and :math:`b_{ruv}` is the binary variable indicating whether task :math:`t_u` is followed by task :math:`t_v` on machine :math:`r`.
        .. math::
            TST = \sum_{r \in R} \sum_{u, v \in M^R_r} s_{t_u, t_v, r} b_{ruv}

    .. note::
        Use :attr:`Job.weight` to set a specific job's weight (:math:`w_j`) in the
        objective function.
    """  # noqa: E501

    weight_makespan: int = 0
    weight_tardy_jobs: int = 0
    weight_total_flow_time: int = 0
    weight_total_tardiness: int = 0
    weight_total_earliness: int = 0
    weight_max_tardiness: int = 0
    weight_total_setup_time: int = 0

    def __post_init__(self):
        for f in fields(self):
            value = getattr(self, f.name)
            if value < 0:
                raise ValueError(f"{f.name} < 0 not understood.")

    def __str__(self) -> str:
        parts = []
        for f in fields(self):
            value = getattr(self, f.name)
            if value > 0:
                parts.append(f"{f.name}={value}")

        lines = ["objective"]
        for idx, part in enumerate(parts):
            symbol = "└─" if idx == len(parts) - 1 else "├─"
            lines.append(f"{symbol} {part}")

        if not parts:
            lines.append("└─ no weights")

        return "\n".join(lines)


class ProblemData:
    """
    Class that contains all data needed to solve the scheduling problem.

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
        The constraints of this problem data instance. Default is no
        constraints.
    objective
        The objective function. Default is minimizing the makespan.
    """

    def __init__(
        self,
        jobs: list[Job],
        resources: Sequence[Resource],
        tasks: list[Task],
        modes: list[Mode],
        constraints: Constraints | None = None,
        objective: Objective | None = None,
    ):
        self._jobs = jobs
        self._resources = resources
        self._tasks = tasks
        self._modes = modes
        self._constraints = (
            constraints if constraints is not None else Constraints()
        )
        self._objective = (
            objective
            if objective is not None
            else Objective(weight_makespan=1)
        )

        self._validate()

        # After validation, we can safely set the helper attributes.
        self._task2modes: list[list[int]] = [[] for _ in tasks]
        self._resource2modes: list[list[int]] = [[] for _ in resources]

        for mode_idx, mode in enumerate(self.modes):
            self._task2modes[mode.task].append(mode_idx)
            for res_idx in mode.resources:
                self._resource2modes[res_idx].append(mode_idx)

        self._machine_idcs: list[int] = []
        self._renewable_idcs: list[int] = []
        self._non_renewable_idcs: list[int] = []

        for idx, resource in enumerate(self.resources):
            if isinstance(resource, Machine):
                self._machine_idcs.append(idx)
            elif isinstance(resource, Renewable):
                self._renewable_idcs.append(idx)
            elif isinstance(resource, NonRenewable):
                self._non_renewable_idcs.append(idx)

    def __str__(self):
        lines = [
            f"{len(self.jobs)} jobs",
            f"{len(self.resources)} resources",
        ]

        parts = []
        if self.num_machines > 0:
            parts.append(f"{self.num_machines} machines")
        if self.num_renewables > 0:
            parts.append(f"{self.num_renewables} renewable")
        if self.num_non_renewables > 0:
            parts.append(f"{self.num_non_renewables} non_renewable")

        for idx, part in enumerate(parts):
            symbol = "└─" if idx == len(parts) - 1 else "├─"
            lines.append(f"{symbol} {part}")

        lines.extend(
            [
                f"{len(self.tasks)} tasks",
                f"{len(self.modes)} modes",
                str(self.constraints).rstrip(),
                str(self.objective).rstrip(),
            ]
        )

        return "\n".join(lines)

    def _validate(self):
        """
        Validates the problem data parameters.
        """
        for job_idx, job in enumerate(self.jobs):
            if len(job.tasks) == 0:
                msg = f"Job {job_idx} does not reference any task."
                raise ValueError(msg)

            for task_idx in job.tasks:
                if not (0 <= task_idx < self.num_tasks):
                    msg = f"Job {job_idx} references to unknown task index."
                    raise ValueError(msg)

                if job_idx != self.tasks[task_idx].job:
                    msg = (
                        f"Job {job_idx} contains task {task_idx}, but task "
                        f"belongs to job {self.tasks[task_idx].job}."
                    )
                    raise ValueError(msg)

        for idx, task in enumerate(self.tasks):
            if task.job is not None and not (0 <= task.job < self.num_jobs):
                msg = f"Task {idx} references to unknown job index."
                raise ValueError(msg)

        for idx, mode in enumerate(self.modes):
            if not (0 <= mode.task < self.num_tasks):
                raise ValueError(f"Mode {idx} references unknown task index.")

            for res_idx in mode.resources:
                if not (0 <= res_idx < self.num_resources):
                    msg = f"Mode {idx} references unknown resource index."
                    raise ValueError(msg)

        task_set = set(range(self.num_tasks))
        missing_tasks = task_set - {m.task for m in self.modes}
        for idx in sorted(missing_tasks):
            raise ValueError(f"Processing modes missing for task {idx}.")

        infeasible_modes = Counter()
        num_modes = Counter()

        for mode in self.modes:
            num_modes[mode.task] += 1
            infeasible_modes[mode.task] += any(
                # Assumes that machines have zero capacity.
                demand > getattr(self.resources[res], "capacity", 0)
                for demand, res in zip(mode.demands, mode.resources)
            )

        for task, count in num_modes.items():
            if infeasible_modes[task] == count:
                msg = f"All modes for task {task} have infeasible demands."
                raise ValueError(msg)

        task_pair_constraints = [
            (self.constraints.start_before_start, "start_before_start"),
            (self.constraints.start_before_end, "start_before_end"),
            (self.constraints.end_before_start, "end_before_start"),
            (self.constraints.end_before_end, "end_before_end"),
            (self.constraints.identical_resources, "identical_resources"),
            (self.constraints.different_resources, "different_resources"),
            (self.constraints.consecutive, "consecutive"),
        ]

        for constraints, name in task_pair_constraints:
            for idx1, idx2, *_ in constraints:
                if not (0 <= idx1 < self.num_tasks):
                    raise ValueError(f"Invalid task index {idx1} in {name}.")

                if not (0 <= idx2 < self.num_tasks):
                    raise ValueError(f"Invalid task index {idx2} in {name}.")

        res2tasks = defaultdict(set)
        for mode in self.modes:
            for res_idx in mode.resources:
                res2tasks[res_idx].add(mode.task)

        same_sequence = self.constraints.same_sequence
        for res_idx1, res_idx2, task_idcs1, task_idcs2 in same_sequence:
            if not (0 <= res_idx1 < self.num_resources):
                msg = f"Invalid resource index {res_idx1} in same_sequence."
                raise ValueError(msg)

            if not (0 <= res_idx2 < self.num_resources):
                msg = f"Invalid resource index {res_idx2} in same_sequence."
                raise ValueError(msg)

            if not isinstance(self.resources[res_idx1], Machine):
                msg = f"Resource {res_idx1} is not a machine in same_sequence."
                raise ValueError(msg)

            if not isinstance(self.resources[res_idx2], Machine):
                msg = f"Resource {res_idx2} is not a machine in same_sequence."
                raise ValueError(msg)

            res_tasks1 = res2tasks[res_idx1]
            res_tasks2 = res2tasks[res_idx2]

            if len(res_tasks1) != len(res_tasks2):
                msg = (
                    "Machines in same_sequence constraint must handle"
                    " the same number of tasks."
                )
                raise ValueError(msg)

            if task_idcs1 is None and task_idcs2 is None:
                continue

            for task_idx in task_idcs1:
                if not (0 <= task_idx < self.num_tasks):
                    msg = f"Invalid task index {task_idx} in same_sequence."
                    raise ValueError(msg)

            for task_idx in task_idcs2:
                if not (0 <= task_idx < self.num_tasks):
                    msg = f"Invalid task index {task_idx} in same_sequence."
                    raise ValueError(msg)

            if res_tasks1 != set(task_idcs1):
                msg = "tasks1 must exactly match tasks that require machine1."
                raise ValueError(msg)

            if res_tasks2 != set(task_idcs2):
                msg = "tasks2 must exactly match tasks that require machine2."
                raise ValueError(msg)

        for res_idx, task_idx1, task_idx2, _ in self.constraints.setup_times:
            if not (0 <= res_idx < self.num_resources):
                msg = f"Invalid resource index {res_idx} in setup_times."
                raise ValueError(msg)

            if not (0 <= task_idx1 < self.num_tasks):
                msg = f"Invalid task index in setup_times: {task_idx1}."
                raise ValueError(msg)

            if not (0 <= task_idx2 < self.num_tasks):
                msg = f"Invalid task index in setup_times: {task_idx2}."
                raise ValueError(msg)

            if not isinstance(self.resources[res_idx], Machine):
                raise ValueError("Setup times only allowed for machines.")

        for idx1, idcs2 in self.constraints.mode_dependencies:
            if not (0 <= idx1 < self.num_modes):
                msg = f"Invalid mode index {idx1} in mode dependencies."
                raise ValueError(msg)

            for idx in idcs2:
                if not (0 <= idx < self.num_modes):
                    msg = f"Invalid mode index {idx} in mode dependencies."
                    raise ValueError(msg)

            modes = [idx1, *idcs2]
            if len({self.modes[idx].task for idx in modes}) == 1:
                msg = (
                    f"All modes {modes} in mode dependency constraint"
                    " refer to the same task."
                )
                raise ValueError(msg)

        if (
            self.objective.weight_tardy_jobs > 0
            or self.objective.weight_total_tardiness > 0
            or self.objective.weight_total_earliness > 0
            or self.objective.weight_max_tardiness > 0
        ):
            if any(job.due_date is None for job in self.jobs):
                msg = "Job due dates required for due date-based objectives."
                raise ValueError(msg)

        if (
            self.objective.weight_total_setup_time > 0
            and not self.constraints.setup_times
        ):
            msg = "Setup times required for total setup times objective."
            raise ValueError(msg)

    def replace(
        self,
        jobs: list[Job] | None = None,
        resources: Sequence[Resource] | None = None,
        tasks: list[Task] | None = None,
        modes: list[Mode] | None = None,
        constraints: Constraints | None = None,
        objective: Objective | None = None,
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
            Optional constraints.
        objective
            Optional objective function.

        Returns
        -------
        ProblemData
            A new ProblemData instance with possibly replaced data.
        """

        def _deepcopy_if_none(value: _T | None, default: _T) -> _T:
            return value if value is not None else deepcopy(default)

        jobs = _deepcopy_if_none(jobs, self.jobs)
        resources = _deepcopy_if_none(resources, self.resources)
        tasks = _deepcopy_if_none(tasks, self.tasks)
        modes = _deepcopy_if_none(modes, self.modes)
        constraints = _deepcopy_if_none(constraints, self.constraints)
        objective = _deepcopy_if_none(objective, self.objective)

        return ProblemData(
            jobs=jobs,
            resources=resources,
            tasks=tasks,
            modes=modes,
            constraints=constraints,
            objective=objective,
        )

    @property
    def jobs(self) -> list[Job]:
        """
        Returns the job data of this problem instance.
        """
        return self._jobs

    @property
    def resources(self) -> Sequence[Resource]:
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
    def constraints(self) -> Constraints:
        """
        Returns the constraints of this problem instance.
        """
        return self._constraints

    @property
    def objective(self) -> Objective:
        """
        Returns the objective function of this problem instance.
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
    def num_machines(self) -> int:
        """
        Returns the number of machines in this instance.
        """
        return len(self._machine_idcs)

    @property
    def num_renewables(self) -> int:
        """
        Returns the number of renewable resources in this instance.
        """
        return len(self._renewable_idcs)

    @property
    def num_non_renewables(self) -> int:
        """
        Returns the number of non-renewable resources in this instance.
        """
        return len(self._non_renewable_idcs)

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

    @property
    def num_constraints(self) -> int:
        """
        Returns the number of constraints in this instance.
        """
        return len(self._constraints)

    @property
    def machine_idcs(self) -> list[int]:
        """
        Returns the list of resource indices corresponding to machines.
        """
        return self._machine_idcs

    @property
    def renewable_idcs(self) -> list[int]:
        """
        Returns the list of resource indices corresponding to renewable
        resources.
        """
        return self._renewable_idcs

    @property
    def non_renewable_idcs(self) -> list[int]:
        """
        Returns the list of resource indices corresponding to non-renewable
        resources.
        """
        return self._non_renewable_idcs

    def task2modes(self, task: int) -> list[int]:
        """
        Returns the list of mode indices corresponding to the given task.

        Parameters
        ----------
        task
            The task index.

        Returns
        -------
        list[int]
            The list of mode indices for the given task.
        """
        if not (0 <= task < self.num_tasks):
            raise ValueError(f"Invalid task index {task}.")
        return self._task2modes[task]

    def resource2modes(self, resource: int) -> list[int]:
        """
        Returns the list of mode indices corresponding to the given resource.

        Parameters
        ----------
        resource
            The resource index.

        Returns
        -------
        list[int]
            The list of mode indices for the given resource.
        """
        if not (0 <= resource < self.num_resources):
            raise ValueError(f"Invalid resource index {resource}.")
        return self._resource2modes[resource]
