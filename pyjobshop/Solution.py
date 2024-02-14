from .ProblemData import ProblemData


class Task:
    """
    The Task class stores data related to scheduled operations.

    Parameters
    ----------
    operation
        The operation index.
    machine
        The machine to which the operation is assigned.
    start
        The start time of the operation.
    duration
        The duration of the operation.
    """

    def __init__(
        self, operation: int, machine: int, start: int, duration: int
    ):
        self._operation = operation
        self._machine = machine
        self._start = start
        self._duration = duration

    def __eq__(self, other) -> bool:
        return (
            self.operation == other.operation
            and self.machine == other.machine
            and self.start == other.start
            and self.duration == other.duration
        )

    @property
    def operation(self) -> int:
        return self._operation

    @property
    def machine(self) -> int:
        return self._machine

    @property
    def start(self) -> int:
        return self._start

    @property
    def duration(self) -> int:
        return self._duration


class Solution:
    """
    Solution class.

    Parameters
    ----------
    data
        The problem data instance.
    schedule
        A list of tasks.
    """

    def __init__(self, data: ProblemData, schedule: list[Task]):
        self.schedule = schedule
        self._validate(data)

    def __eq__(self, other) -> bool:
        return self.schedule == other.schedule

    def _validate(self, data: ProblemData):
        for task in self.schedule:
            op = task.operation
            assigned = task.machine

            if assigned not in data.op2machines[op]:
                msg = f"Operation {op} not allowed on machine {assigned}."
                raise ValueError(msg)

    # TODO Add classmethod based on machine sequences (see #8).
