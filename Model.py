from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import networkx as nx


@dataclass(frozen=True, eq=True)
class Job:
    id: int
    name: Optional[str] = None

    def __str__(self):
        text = self.id if self.name is None else self.name
        return f"Job({text})"


@dataclass(frozen=True, eq=True)
class Machine:
    id: int
    name: Optional[str] = None

    def __str__(self):
        text = self.id if self.name is None else self.name
        return f"Machine({text})"


@dataclass(frozen=True, eq=True)
class Operation:
    id: int
    job: Job
    machines: list[Machine]
    durations: list[int]
    name: Optional[str] = None

    def __str__(self):
        text = self.id if self.name is None else self.name
        return f"Operation({text})"


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
        edge_type: Optional[str] = None,
    ):
        self._operations_graph.add_edge(
            operation1.id, operation2.id, edge_type=edge_type
        )

    def add_machines_edge(
        self,
        machine1: Machine,
        machine2: Machine,
        edge_type: Optional[str] = None,
    ):
        self._machine_graph.add_edge(
            machine1.id, machine2.id, edge_type=edge_type
        )
