from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import networkx as nx


@dataclass(frozen=True, eq=True)
class Job:
    idx: int
    name: Optional[str] = None

    def __str__(self):
        return self.name if self.name else f"Job {self.idx}"


@dataclass(frozen=True, eq=True)
class Machine:
    """
    A machine is a resource that can process operations.

    Parameters
    ----------
    idx: int
        Unique identifier of the machine.
    name: Optional[str]
        Name of the machine. If not provided, the name will be "Machine {idx}".
    """

    idx: int
    name: Optional[str] = None

    def __str__(self):
        return self.name if self.name else f"Machine {self.idx}"


@dataclass(frozen=True, eq=True)
class Operation:
    """
    An operation is a task that must be processed by a machine.

    Parameters
    ----------
    idx: int
        Unique identifier of the operation.
    job: Job
        Job to which the operation belongs.
    machines: list[Machine]
        Machines that can process the operation.
    durations: list[int]
        Durations of the operation on each machine.
    name: Optional[str]
        Name of the operation. If not provided, the name will be
        "Operation {idx}".
    """

    idx: int
    job: Job
    machines: list[Machine]
    durations: list[int]
    name: Optional[str] = None

    def __str__(self):
        return self.name if self.name else f"Operation {self.idx}"


class PrecedenceType(str, Enum):
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
    - before:                i comes before j in sequence variable.
    - previous:              i is previous to j in sequence variable.
    - same_unit:             i and j are processed on the same unit.
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
    BEFORE = "before"
    SAME_UNIT = "same_unit"


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
        self._machine_graph = machine_graph  # TODO can we replace digraph?
        self._operations_graph = operations_graph

        self._job2ops = defaultdict(list)
        self._machine2ops = defaultdict(list)

        for op in operations:
            self._job2ops[op.job].append(op)

            for m in op.machines:
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
    def machine_graph(self):
        return self._machine_graph

    @property
    def operations_graph(self):
        return self._operations_graph

    @property
    def job2ops(self) -> dict[Job, list[Operation]]:
        return self._job2ops

    @property
    def machine2ops(self) -> dict[Machine, list[Operation]]:
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
