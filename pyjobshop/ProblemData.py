import bisect
from enum import Enum
from typing import Optional

import enum_tools.documentation
import numpy as np

from pyjobshop.constants import MAX_VALUE

_CONSTRAINTS_TYPE = dict[tuple[int, int], list["Constraint"]]

# TODO


class Job:
    """
    Simple dataclass for storing all job-related data.

    Parameters
    ----------
    weight
        The job importance weight, used as multiplicative factor in the
        objective function.
    release_date
        The earliest time that the job can start processing. Default is zero.
    due_date
        The latest time that the job should be completed before incurring
        penalties. Default is None, meaning that there is no due date.
    deadline
        The latest time that the job must be completed. Note that a deadline
        is different from a due date; the latter does not constrain the latest
        completion time. Default is None, meaning that there is no deadline.
    name
        Name of the job.
    """

    def __init__(
        self,
        weight: int = 1,
        release_date: int = 0,
        due_date: Optional[int] = None,
        deadline: Optional[int] = None,
        name: str = "",
    ):
        if weight < 0:
            raise ValueError("Weight must be non-negative.")

        if release_date < 0:
            raise ValueError("Release date must be non-negative.")

        if due_date is not None and due_date < 0:
            raise ValueError("Due date must be non-negative.")

        if deadline is not None and deadline < 0:
            raise ValueError("Deadline must be non-negative.")

        if deadline is not None and release_date > deadline:
            raise ValueError("Must have release_date <= deadline.")

        self._weight = weight
        self._release_date = release_date
        self._due_date = due_date
        self._deadline = deadline
        self._name = name

    @property
    def weight(self) -> int:
        return self._weight

    @property
    def release_date(self) -> int:
        return self._release_date

    @property
    def due_date(self) -> Optional[int]:
        return self._due_date

    @property
    def deadline(self) -> Optional[int]:
        return self._deadline

    @property
    def name(self) -> str:
        return self._name


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
        Earliest start time of the task.
    latest_start
        Latest start time of the task.
    earliest_end
        Earliest end time of the task.
    latest_end
        Latest end time of the task.
    fixed_duration
        Whether the task has a fixed duration. A fixed duration means that
        the task duration is precisely the processing time (on a given
        machine). If the duration is not fixed, then the task duration
        can take longer than the processing time, e.g., due to blocking.
        Default is True.
    name
        Name of the task.
    """

    def __init__(
        self,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
        fixed_duration: bool = True,
        name: str = "",
    ):
        if (
            earliest_start is not None
            and latest_start is not None
            and earliest_start > latest_start
        ):
            raise ValueError("earliest_start must be <= latest_start.")

        if (
            earliest_end is not None
            and latest_end is not None
            and earliest_end > latest_end
        ):
            raise ValueError("earliest_end must be <= latest_end.")

        self._earliest_start = earliest_start
        self._latest_start = latest_start
        self._earliest_end = earliest_end
        self._latest_end = latest_end
        self._fixed_duration = fixed_duration
        self._name = name

    @property
    def earliest_start(self) -> Optional[int]:
        return self._earliest_start

    @property
    def latest_start(self) -> Optional[int]:
        return self._latest_start

    @property
    def earliest_end(self) -> Optional[int]:
        return self._earliest_end

    @property
    def latest_end(self) -> Optional[int]:
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
    job2ops
        List of task indices for each job.
    processing_times
        Processing times of tasks on machines. First index is the machine
        index, second index is the task index.
    constraints
        Dict indexed by task pairs with a list of constraints as values.
    setup_times
        Sequence-dependent setup times between tasks on a given machine.
        The first dimension of the array is indexed by the machine index. The
        last two dimensions of the array are indexed by task indices.
    planning_horizon
        The planning horizon value. Default is None, meaning that the planning
        horizon is unbounded.
    objective
        The objective function to be minimized. Default is the makespan.
    """

    def __init__(
        self,
        jobs: list[Job],
        machines: list[Machine],
        tasks: list[Task],
        job2ops: list[list[int]],
        processing_times: dict[tuple[int, int], int],
        constraints: _CONSTRAINTS_TYPE,
        setup_times: Optional[np.ndarray] = None,
        planning_horizon: int = MAX_VALUE,
        objective: Objective = Objective.MAKESPAN,
    ):
        self._jobs = jobs
        self._machines = machines
        self._tasks = tasks
        self._job2ops = job2ops
        self._processing_times = processing_times
        self._constraints = constraints

        num_mach = self.num_machines
        num_ops = self.num_tasks

        self._setup_times = (
            setup_times
            if setup_times is not None
            else np.zeros((num_mach, num_ops, num_ops), dtype=int)
        )
        self._planning_horizon = planning_horizon
        self._objective = objective

        self._machine2ops: list[list[int]] = [[] for _ in range(num_mach)]
        self._op2machines: list[list[int]] = [[] for _ in range(num_ops)]

        for machine, task in self.processing_times.keys():
            bisect.insort(self._machine2ops[machine], task)
            bisect.insort(self._op2machines[task], machine)

        self._validate_parameters()

    def _validate_parameters(self):
        """
        Validates the problem data parameters.
        """
        num_mach = self.num_machines
        num_ops = self.num_tasks

        if any(duration < 0 for duration in self.processing_times.values()):
            raise ValueError("Processing times must be non-negative.")

        if np.any(self.setup_times < 0):
            raise ValueError("Setup times must be non-negative.")

        if self.setup_times.shape != (num_mach, num_ops, num_ops):
            msg = "Setup times shape must be (num_machines, num_ops, num_ops)."
            raise ValueError(msg)

        if self.planning_horizon is not None and self.planning_horizon < 0:
            raise ValueError("Planning horizon must be non-negative.")

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
    def job2ops(self) -> list[list[int]]:
        """
        List of task indices for each job.

        Returns
        -------
        list[list[int]]
            List of task indices for each job.
        """
        return self._job2ops

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
    def planning_horizon(self) -> int:
        """
        The planning horizon of this instance.

        Returns
        -------
        int
            The planning horizon value.
        """
        return self._planning_horizon

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
    def machine2ops(self) -> list[list[int]]:
        """
        List of task indices for each machine. These are inferred from
        the (machine, task) pairs in the processing times dict.

        Returns
        -------
        list[list[int]]
            List of task indices for each machine.
        """
        return self._machine2ops

    @property
    def op2machines(self) -> list[list[int]]:
        """
        List of eligible machine indices for each task. These are inferred
        from the (machine, task) pairs in the processing times dict.

        Returns
        -------
        list[list[int]]
            List of eligible machine indices for each task.
        """
        return self._op2machines

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
