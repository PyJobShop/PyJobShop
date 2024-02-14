import bisect
from enum import Enum
from typing import Iterable, Optional

import numpy as np


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
    downtimes
        List of downtimes for the machine. A downtime is a time interval
        [start, end) during which the machine is unavailable for processing.
        Defaults to no downtimes.
    allow_overlap
        Whether it is allowed to schedule multiple operations on the machine
        at the same time. Default is False.
    name
        Name of the machine.
    """

    def __init__(
        self,
        downtimes: Iterable[tuple[int, int]] = (),
        allow_overlap: bool = False,
        name: str = "",
    ):
        for start, end in downtimes:
            if start > end:
                raise ValueError("Must have downtime start <= end.")

        self._downtimes = downtimes
        self._allow_overlap = allow_overlap
        self._name = name

    @property
    def downtimes(self) -> Iterable[tuple[int, int]]:
        return self._downtimes

    @property
    def allow_overlap(self) -> bool:
        return self._allow_overlap

    @property
    def name(self) -> str:
        return self._name


class Operation:
    """
    Simple dataclass for storing all operation-related data.

    Parameters
    ----------
    earliest_start
        Earliest start time of the operation.
    latest_start
        Latest start time of the operation.
    earliest_end
        Earliest end time of the operation.
    latest_end
        Latest end time of the operation.
    fixed_duration
        Whether the operation has a fixed duration. A fixed duration means that
        the operation duration is precisely the processing time (on a given
        machine). If the duration is not fixed, then the operation duration
        can take longer than the processing time, e.g., due to blocking.
        Default is True.
    optional
        Whether processing this operation is optional. Defaults to False.
    name
        Name of the operation.
    """

    def __init__(
        self,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
        fixed_duration: bool = True,
        optional: bool = False,
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
        self._optional = optional
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
    def optional(self) -> bool:
        return self._optional

    @property
    def name(self) -> str:
        return self._name


class Objective(str, Enum):
    """
    Choices for objective functions (to be minimized).

    - makespan:               Maximum completion time of all jobs.
    - tardy_jobs:             Number of tardy jobs.
    - total_completion_time:  Sum of completion times of all jobs.
    - total_tardiness:        Sum of tardiness of all jobs.

    """

    MAKESPAN = "makespan"
    TARDY_JOBS = "tardy_jobs"
    TOTAL_COMPLETION_TIME = "total_completion_time"
    TOTAL_TARDINESS = "total_tardiness"


class TimingPrecedence(str, Enum):
    """
    Types of precedence constraints between two operations $i$ and $j$.
    Let $s(i)$ and $f(i)$ be the start and finish times of operation $i$,
    and let $s(j)$ and $f(j)$ be defined similarly for operation $j$. The
    following precedence constraints are supported (in CPLEX terminology):

    - start_at_start:        $s(i) == s(j)$
    - start_at_end:          $s(i) == f(j)$
    - start_before_start:    $s(i) <= s(j)$
    - start_before_end:      $s(i) <= f(j)$
    - end_at_start:          $f(i) == s(j)$
    - end_at_end:            $f(i) == f(j)$
    - end_before_start:      $f(i) <= s(j)$
    - end_before_end:        $f(i) <= f(j)$

    Timing precedence constraints are combined with delays: a delay of $d$
    is added to the left-hand side of the constraint. For example, the
    constraint `start_at_start` with delay $d$ is then $s(i) + d == s(j)$.
    """

    START_AT_START = "start_at_start"
    START_AT_END = "start_at_end"
    START_BEFORE_START = "start_before_start"
    START_BEFORE_END = "start_before_end"
    END_AT_START = "end_at_start"
    END_AT_END = "end_at_end"
    END_BEFORE_START = "end_before_start"
    END_BEFORE_END = "end_before_end"


class AssignmentPrecedence(str, Enum):
    """
    Types of assignment precedence constraints between two operations $i$ and
    $j$.

    - previous:              i is previous to j in sequence variable.
    - same_unit:             i and j are processed on the same unit.
    - different_unit:        i and j are processed on different units.
    """

    PREVIOUS = "previous"
    SAME_UNIT = "same_unit"
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
    operations
        List of operations.
    job2ops
        List of operation indices for each job.
    processing_times
        Processing times of operations on machines. First index is the machine
        index, second index is the operation index.
    timing_precedences
        Dict indexed by operation pairs with list of timing precedence
        constraints and delays.
    assignment_precedences
        Dict indexed by operation pairs with list of assignment precedence
        constraints.
    setup_times
        Sequence-dependent setup times between operations on a given machine.
        The first dimension of the array is indexed by the machine index. The
        last two dimensions of the array are indexed by operation indices.
    process_plans
        List of processing plans. Each process plan represents a list
        containing lists of operation indices, one of which is selected to be
        scheduled. All operations from the selected list are then scheduled,
        while operations from unselected lists will not be scheduled.
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
        operations: list[Operation],
        job2ops: list[list[int]],
        processing_times: dict[tuple[int, int], int],
        timing_precedences: dict[
            tuple[int, int], list[tuple[TimingPrecedence, int]]
        ],
        assignment_precedences: Optional[
            dict[tuple[int, int], list[AssignmentPrecedence]]
        ] = None,
        setup_times: Optional[np.ndarray] = None,
        process_plans: Optional[list[list[list[int]]]] = None,
        planning_horizon: Optional[int] = None,
        objective: Objective = Objective.MAKESPAN,
    ):
        self._jobs = jobs
        self._machines = machines
        self._operations = operations
        self._job2ops = job2ops
        self._processing_times = processing_times
        self._timing_precedences = timing_precedences
        self._assignment_precedences = (
            assignment_precedences
            if assignment_precedences is not None
            else {}
        )

        num_mach = self.num_machines
        num_ops = self.num_operations

        self._setup_times = (
            setup_times
            if setup_times is not None
            else np.zeros((num_mach, num_ops, num_ops), dtype=int)
        )
        self._process_plans = (
            process_plans if process_plans is not None else []
        )
        self._planning_horizon = planning_horizon
        self._objective = objective

        self._machine2ops: list[list[int]] = [[] for _ in range(num_mach)]
        self._op2machines: list[list[int]] = [[] for _ in range(num_ops)]

        for machine, operation in self.processing_times.keys():
            bisect.insort(self._machine2ops[machine], operation)
            bisect.insort(self._op2machines[operation], machine)

        self._validate_parameters()

    def _validate_parameters(self):
        """
        Validates the problem data parameters.
        """
        num_mach = self.num_machines
        num_ops = self.num_operations

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
    def operations(self) -> list[Operation]:
        """
        Returns the operation data of this problem instance.
        """
        return self._operations

    @property
    def job2ops(self) -> list[list[int]]:
        """
        List of operation indices for each job.

        Returns
        -------
        list[list[int]]
            List of operation indices for each job.
        """
        return self._job2ops

    @property
    def processing_times(self) -> dict[tuple[int, int], int]:
        """
        Processing times of operations on machines.

        Returns
        -------
        dict[tuple[int, int], int]
            Processing times of operations on machines. First index is
            the machine index, second index is the operation index.
        """
        return self._processing_times

    @property
    def timing_precedences(
        self,
    ) -> dict[tuple[int, int], list[tuple[TimingPrecedence, int]]]:
        """
        Timing precedence constraints between operations.

        Returns
        -------
        dict[tuple[int, int], list[tuple[TimingPrecedence, int]]]
            Dict indexed by operation pairs with list of timing precedence
            constraints and delays.
        """
        return self._timing_precedences

    @property
    def assignment_precedences(
        self,
    ) -> dict[tuple[int, int], list[AssignmentPrecedence]]:
        """
        Assignment precedence constraints between operations.

        Returns
        -------
        dict[tuple[int, int], list[AssignmentPrecedence]]
            Dict indexed by operation pairs with list of assignment precedence
            constraints.
        """
        return self._assignment_precedences

    @property
    def setup_times(self) -> np.ndarray:
        """
        Sequence-dependent setup times between operations on a given machine.

        Returns
        -------
        np.ndarray
            Sequence-dependent setup times between operations on a given
            machine. The first dimension of the array is indexed by the machine
            index. The last two dimensions of the array are indexed by
            operation indices.
        """
        return self._setup_times

    @property
    def process_plans(self) -> list[list[list[int]]]:
        """
        List of process plans. Each process plan represents a list containing
        lists of operation indices, one of which is selected to be scheduled.
        All operations from the selected list are then scheduled, while
        operations from unselected lists will not be scheduled.

        Returns
        -------
        list[list[list[int]]]
            List of processing plans.
        """
        return self._process_plans

    @property
    def planning_horizon(self) -> Optional[int]:
        """
        The planning horizon of this instance.

        Returns
        -------
        Optional[int]
            The planning horizon value. If None, then the planning horizon
            is unbounded.
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
        List of operation indices for each machine. These are inferred from
        the (machine, operation) pairs in the processing times dict.

        Returns
        -------
        list[list[int]]
            List of operation indices for each machine.
        """
        return self._machine2ops

    @property
    def op2machines(self) -> list[list[int]]:
        """
        List of eligible machine indices for each operation. These are inferred
        from the (machine, operation) pairs in the processing times dict.

        Returns
        -------
        list[list[int]]
            List of eligible machine indices for each operation.
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
    def num_operations(self) -> int:
        """
        Returns the number of operations in this instance.
        """
        return len(self._operations)
