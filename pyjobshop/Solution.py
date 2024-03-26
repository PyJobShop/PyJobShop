from dataclasses import dataclass

from .ProblemData import ProblemData


@dataclass
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

    operation: int
    machine: int
    start: int
    duration: int


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
