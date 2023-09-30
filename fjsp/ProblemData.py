from enum import Enum, EnumMeta
from typing import Optional

import networkx as nx


class Job:
    def __init__(
        self,
        release_date: int = 0,
        deadline: Optional[int] = None,
        name: Optional[str] = None,
    ):
        self._release_date = release_date
        self._deadline = deadline
        self._name = name or "Job"

    @property
    def release_date(self) -> int:
        return self._release_date

    @property
    def deadline(self) -> Optional[int]:
        return self._deadline

    @property
    def name(self) -> str:
        return self._name

    def __str__(self) -> str:
        return self.name


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
    durations: list[int]
        Durations of the operation on each machine.
    name: Optional[str]
        Name of the operation.
    """

    def __init__(
        self,
        job: int,
        machines: list[int],
        durations: list[int],
        name: Optional[str] = None,
    ):
        self._job = job
        self._machines = machines
        self._durations = durations
        self._name = name

    @property
    def job(self) -> int:
        return self._job

    @property
    def machines(self) -> list[int]:
        return self._machines

    @property
    def durations(self) -> list[int]:
        return self._durations

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
        machine_graph: nx.DiGraph,
        operations_graph: nx.DiGraph,
    ):
        self._jobs = jobs
        self._machines = machines
        self._operations = operations
        self._machine_graph = machine_graph
        self._operations_graph = operations_graph

        self._job2ops: list[list[int]] = [[] for _ in range(self.num_jobs)]
        self._machine2ops: list[list[int]] = [
            [] for _ in range(self.num_machines)
        ]

        for op, op_data in enumerate(self.operations):
            self._job2ops[op_data.job].append(op)

            for m in op_data.machines:
                self._machine2ops[m].append(op)

    @property
    def jobs(self) -> list[Job]:
        return self._jobs

    @property
    def machines(self) -> list[Machine]:
        return self._machines

    @property
    def operations(self) -> list[Operation]:
        return self._operations

    @property
    def machine_graph(self) -> nx.DiGraph:
        return self._machine_graph

    @property
    def operations_graph(self) -> nx.DiGraph:
        return self._operations_graph

    @property
    def job2ops(self) -> list[list[int]]:
        return self._job2ops

    @property
    def machine2ops(self) -> list[list[int]]:
        return self._machine2ops

    @property
    def num_jobs(self) -> int:
        return len(self._jobs)

    @property
    def num_machines(self) -> int:
        return len(self._machines)

    @property
    def num_operations(self) -> int:
        return len(self._operations)
