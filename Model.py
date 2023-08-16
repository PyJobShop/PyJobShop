from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional

import networkx as nx


class PrecedenceType(Enum):
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
    """

    START_AT_START = "start_at_start"
    START_AT_END = "start_at_end"
    START_BEFORE_START = "start_before_start"
    START_BEFORE_END = "start_before_end"
    END_AT_START = "end_at_start"
    END_AT_END = "end_at_end"
    END_BEFORE_START = "end_before_start"
    END_BEFORE_END = "end_before_end"


@dataclass(frozen=True, eq=True)
class Job:
    id: int
    name: Optional[str] = None

    def __str__(self):
        return self.name if self.name else f"Job {self.id}"


@dataclass(frozen=True, eq=True)
class Machine:
    id: int
    name: Optional[str] = None

    def __str__(self):
        return self.name if self.name else f"Machine {self.id}"


@dataclass(frozen=True, eq=True)
class Operation:
    id: int
    job: Job
    machines: list[Machine]
    durations: list[int]
    name: Optional[str] = None

    def __str__(self):
        return self.name if self.name else f"Operation {self.id}"


class Model:
    def __init__(self):
        self._jobs = []
        self._machines = []
        self._operations = []
        self._machine_graph = nx.DiGraph()
        self._operations_graph = nx.DiGraph()
        self._job2ops = defaultdict(list)
        self._machine2ops = defaultdict(list)

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

    def add_job(self, name: Optional[str] = None) -> Job:
        job = Job(len(self.jobs), name)
        self._jobs.append(job)
        return job

    def add_machine(self, name: Optional[str] = None) -> Machine:
        machine = Machine(len(self.machines), name)

        self._machines.append(machine)
        self._machine_graph.add_node(machine.id)

        return machine

    def add_operation(
        self,
        job: Job,
        machines: list[Machine],
        durations: list[int],
        name: Optional[str] = None,
    ) -> Operation:
        operation = Operation(
            len(self.operations), job, machines, durations, name
        )

        self._operations.append(operation)
        self._operations_graph.add_node(operation.id)
        self._job2ops[job].append(operation)

        for machine in machines:
            self._machine2ops[machine].append(operation)

        return operation

    def add_operations_edge(
        self,
        operation1: Operation,
        operation2: Operation,
        precedence_types: Iterable[PrecedenceType] = (
            PrecedenceType.END_BEFORE_START,
        ),
        edge_type: Optional[str] = None,
    ):
        self._operations_graph.add_edge(
            operation1.id,
            operation2.id,
            precedence_types=precedence_types,
            edge_type=edge_type,
        )

    def add_machines_edge(
        self,
        machine1: Machine,
        machine2: Machine,
        same_sequence: bool = False,
        edge_type: Optional[str] = None,
    ):
        self._machine_graph.add_edge(
            machine1.id,
            machine2.id,
            same_sequence=same_sequence,
            edge_type=edge_type,
        )
