from typing import Iterable, Optional

import networkx as nx

from .ProblemData import Job, Machine, Operation, PrecedenceType, ProblemData


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

    def add_job(
        self,
        release_date: int = 0,
        deadline: Optional[int] = None,
        name: Optional[str] = None,
    ) -> Job:
        """
        Adds a job to the model.

        Parameters
        ----------
        release_date: int
            Release date of the job. Defaults to 0.
        deadline: Optional[int]
            Optional deadline of the job.
        name: Optional[str]
            Optional name of the job.
        """
        job = Job(release_date=release_date, deadline=deadline, name=name)
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
        machine = Machine(name=name)

        self._machines.append(machine)
        self._machine_graph.add_node(len(self.machines))

        return machine

    def add_operation(
        self,
        job: Job,
        machines: list[Machine],
        durations: list[int],
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
        name: Optional[str]
            Optional name of the operation.
        """
        job_idx = self.jobs.index(job)
        machine_idcs = [self.machines.index(m) for m in machines]
        operation = Operation(job_idx, machine_idcs, durations, name)

        self._operations.append(operation)
        self._operations_graph.add_node(len(self.operations))

        return operation

    def add_operations_edge(
        self,
        operation1: Operation,
        operation2: Operation,
        precedence_types: Iterable[PrecedenceType] = (
            PrecedenceType.END_BEFORE_START,
        ),
    ):
        if any(pt not in PrecedenceType for pt in precedence_types):
            msg = "Precedence types must be of type PrecedenceType."
            raise ValueError(msg)

        self._operations_graph.add_edge(
            self.operations.index(operation1),
            self.operations.index(operation2),
            precedence_types=precedence_types,
        )

    def add_machines_edge(self, machine1: Machine, machine2: Machine):
        idx1 = self.machines.index(machine1)
        idx2 = self.machines.index(machine2)
        self._machine_graph.add_edge(idx1, idx2)
