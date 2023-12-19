import bisect
from typing import Optional

import numpy as np
from strenum import StrEnum


class Job:
    def __init__(
        self,
        release_date: int = 0,
        deadline: Optional[int] = None,
        name: Optional[str] = None,
    ):
        self._release_date = release_date
        self._deadline = deadline
        self._name = name

    @property
    def release_date(self) -> int:
        return self._release_date

    @property
    def deadline(self) -> Optional[int]:
        return self._deadline

    @property
    def name(self) -> Optional[str]:
        return self._name


class Machine:
    """
    A machine represents a resource that can process operations.

    Parameters
    ----------
    name: Optional[str]
        Optional name of the machine.
    """

    def __init__(self, name: Optional[str] = None):
        self._name = name

    @property
    def name(self) -> Optional[str]:
        return self._name


class Operation:
    """
    An operation is a task that must be processed by a machine.

    Parameters
    ----------
    earliest_start: Optional[int]
        Earliest start time of the operation.
    latest_start: Optional[int]
        Latest start time of the operation.
    earliest_end: Optional[int]
        Earliest end time of the operation.
    latest_end: Optional[int]
        Latest end time of the operation.
    optional: bool
        Whether processing this operation is optional. Defaults to False.
    name: Optional[str]
        Name of the operation.
    """

    def __init__(
        self,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
        optional: bool = False,
        name: Optional[str] = None,
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
    def optional(self) -> bool:
        return self._optional

    @property
    def name(self) -> Optional[str]:
        return self._name


class TimingPrecedence(StrEnum):
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


class AssignmentPrecedence(StrEnum):
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
        access_matrix: Optional[np.ndarray] = None,
        setup_times: Optional[np.ndarray] = None,
        process_plans: Optional[list[list[list[int]]]] = None,
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

        self._access_matrix = (
            access_matrix
            if access_matrix is not None
            else np.ones((num_mach, num_mach), dtype=bool)
        )
        self._setup_times = (
            setup_times
            if setup_times is not None
            else np.zeros((num_mach, num_ops, num_ops), dtype=int)
        )
        self._process_plans = (
            process_plans if process_plans is not None else []
        )

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

        if self.access_matrix.shape != (num_mach, num_mach):
            msg = "Access matrix shape must be (num_machines, num_machines)."
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
    def access_matrix(self) -> np.ndarray:
        """
        Returns the machine accessibility matrix of this problem instance.

        Returns
        -------
        np.ndarray
            Accessibility matrix. The (i, j)-th entry of the matrix is True if
            machine i can be used to process operations of job j.
        """
        return self._access_matrix

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
