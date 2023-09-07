from typing import NamedTuple

from .ProblemData import Operation, ProblemData


class ScheduledOperation(NamedTuple):
    op: Operation
    assigned_machine: int
    start: int
    duration: int


class Solution:
    """
    # TODO
    """

    def __init__(self, data: ProblemData, schedule: list[ScheduledOperation]):
        self.data = data
        self.schedule = schedule

    # TODO Add checks.
