from enum import Enum, EnumMeta
from typing import Optional

import numpy as np


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
    name: Optional[str]
        Name of the operation.
    """

    def __init__(
        self,
        earliest_start: Optional[int] = None,
        latest_start: Optional[int] = None,
        earliest_end: Optional[int] = None,
        latest_end: Optional[int] = None,
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
    def name(self) -> Optional[str]:
        return self._name


class PrecedenceTypeMeta(EnumMeta):
    def __contains__(cls, item):
        return item in cls._value2member_map_ or item in cls.__members__


class PrecedenceType(str, Enum, metaclass=PrecedenceTypeMeta):
    """
    Types of precendence constraints between two operations $i$ and $j$.
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
    - previous:              i is previous to j in sequence variable.
    - same_unit:             i and j are processed on the same unit.
    - different_unit:        i and j are processed on different units.
    """

    START_AT_START = "start_at_start"
    START_AT_END = "start_at_end"
    START_BEFORE_START = "start_before_start"
    START_BEFORE_END = "start_before_end"
    END_AT_START = "end_at_start"
    END_AT_END = "end_at_end"
    END_BEFORE_START = "end_before_start"
    END_BEFORE_END = "end_before_end"
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
        machine2ops: list[list[int]],
        processing_times: np.ndarray,
        precedences: dict[tuple[int, int], list[PrecedenceType]],
        access_matrix: Optional[np.ndarray] = None,
        setup_times: Optional[np.ndarray] = None,
    ):
        self._jobs = jobs
        self._machines = machines
        self._operations = operations
        self._job2ops = job2ops
        self._machine2ops = machine2ops

        self._op2machines: list[list[int]] = [
            [] for _ in range(self.num_operations)
        ]
        for machine, ops in enumerate(self.machine2ops):
            for operation in ops:
                self._op2machines[operation].append(machine)

        self._processing_times = processing_times
        self._precedences = precedences

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
            else np.zeros((num_ops, num_ops, num_mach), dtype=int)
        )

        self._validate_parameters()

    def _validate_parameters(self):
        num_mach = self.num_machines
        num_ops = self.num_operations

        if np.any(self.processing_times < 0):
            raise ValueError("Processing times must be non-negative.")

        if self.processing_times.shape != (num_ops, num_mach):
            msg = "Processing times shape must be (num_ops, num_machines)."
            raise ValueError(msg)

        if np.any(self.setup_times < 0):
            raise ValueError("Setup times must be non-negative.")

        if self.setup_times.shape != (num_ops, num_ops, num_mach):
            msg = "Setup times shape must be (num_ops, num_ops, num_machines)."
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
    def machine2ops(self) -> list[list[int]]:
        """
        List of operation indices for each machine.

        Returns
        -------
        list[list[int]]
            List of operation indices for each machine.
        """
        return self._machine2ops

    @property
    def op2machines(self) -> list[list[int]]:
        """
        List of eligible machine indices for each operation.

        Returns
        -------
        list[list[int]]
            List of eligible machine indices for each operation.
        """
        return self._op2machines

    @property
    def processing_times(self) -> np.ndarray:
        """
        Processing times of operations on machines.

        Returns
        -------
        np.ndarray
            Processing times of operations on machines indexed by operation
            and machine indices.
        """
        return self._processing_times

    @property
    def precedences(self) -> dict[tuple[int, int], list[PrecedenceType]]:
        """
        Precedence constraints between operations.

        Returns
        -------
        dict[tuple[int, int], list[PrecedenceType]]
            Dict of precedence constraints between operations. Each precedence
            constraint is a list of precedence types.
        """
        return self._precedences

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
            machine. The first two dimensions of the array are indexed by
            operation indices, and the third dimension is indexed by machine.
        """
        return self._setup_times

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
