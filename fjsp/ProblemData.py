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
    job: int
        Index of the job to which the operation belongs.
    machines: list[int]
        Indices of machines that can process the operation.
    name: Optional[str]
        Name of the operation.
    """

    def __init__(
        self, job: int, machines: list[int], name: Optional[str] = None
    ):
        if not machines:
            raise ValueError("Machines must not be empty.")

        self._job = job
        self._machines = machines
        self._name = name

    @property
    def job(self) -> int:
        return self._job

    @property
    def machines(self) -> list[int]:
        return self._machines

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
        processing_times: np.ndarray,
        precedences: dict[tuple[int, int], list[PrecedenceType]],
        access_matrix: Optional[np.ndarray] = None,
        setup_times: Optional[np.ndarray] = None,
    ):
        self._jobs = jobs
        self._machines = machines
        self._operations = operations
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

        self._job2ops: list[list[int]] = [[] for _ in range(self.num_jobs)]
        self._machine2ops: list[list[int]] = [[] for _ in range(num_mach)]

        for op, op_data in enumerate(self.operations):
            self._job2ops[op_data.job].append(op)

            for m in op_data.machines:
                self._machine2ops[m].append(op)

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
