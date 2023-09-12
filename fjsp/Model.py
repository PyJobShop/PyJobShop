from typing import Iterable, Optional

import networkx as nx

from .ProblemData import (
    Job,
    Machine,
    Operation,
    PrecedenceType,
    ProblemData,
    Silo,
)


class Model:
    """
    Model class to build a problem instance step-by-step.
    """

    def __init__(self):
        self._jobs = []
        self._machines = []
        self._operations = []
        self._machine_graph = nx.DiGraph()
        self._operations_graph = nx.DiGraph()

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

    def data(self) -> ProblemData:
        """
        Returns a ProblemData object containing the problem instance.
        """
        return ProblemData(
            self.jobs,
            self.machines,
            self.operations,
            self.machine_graph,
            self.operations_graph,
        )

    def add_job(self, name: Optional[str] = None) -> Job:
        """
        Adds a job to the model.

        Parameters
        ----------
        name: Optional[str]
            Optional name of the job.
        """
        job = Job(len(self.jobs), name)
        self._jobs.append(job)
        return job

    def add_machine(self, name: Optional[str] = None) -> Machine:
        """
        Adds a machine to the model.

        Parameters
        ----------
        name: Optional[str]
            Optional name of the machine.
        """
        machine = Machine(len(self.machines), name)

        self._machines.append(machine)
        self._machine_graph.add_node(machine.idx)

        return machine

    def add_silo(self, capacity: int, name: Optional[str] = None) -> Silo:
        """
        Adds a silo to the model.

        Parameters
        ----------
        capacity: int
            Capacity of the silo.
        name: Optional[str]
            Optional name of the silo.
        """
        silo = Silo(len(self.machines), name, capacity=capacity)

        self._machines.append(silo)
        self._machine_graph.add_node(silo.idx)

        return silo

    def add_operation(
        self,
        job: Job,
        machines: list[Machine],
        durations: list[int],
        load: int = 0,
        product_type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Operation:
        """
        Adds an operation to the model.

        Parameters
        ----------
        job: Job
            Job to which the operation belongs.
        machines: list[Machine]
            Eligible machines that can process the operation.
        durations: list[int]
            Durations of the operation on each machine.
        product_type: Optional[str]
            Optional product type of the operation.
        load: int
            Load of the operation.
        product_type: Optional[str]
            Optional product type of the operation.
        name: Optional[str]
            Optional name of the operation.
        """
        operation = Operation(
            len(self.operations),
            job,
            machines,
            durations,
            load=load,
            product_type=product_type,
            name=name,
        )

        self._operations.append(operation)
        self._operations_graph.add_node(operation.idx)

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
        if any(pt not in PrecedenceType for pt in precedence_types):
            msg = "Precedence types must be of type PrecedenceType."
            raise ValueError(msg)

        self._operations_graph.add_edge(
            operation1.idx,
            operation2.idx,
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
            machine1.idx,
            machine2.idx,
            same_sequence=same_sequence,
            edge_type=edge_type,
        )
