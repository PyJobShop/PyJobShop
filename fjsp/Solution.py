from .ProblemData import Operation, ProblemData


class ScheduledOperation:
    """
    The ScheduledOperation class stores data related to scheduled operations.

    Parameters
    ----------
    op: Operation
        The scheduled operation.
    assigned_machine: int
        The machine to which the operation is assigned.
    start: int
        The start time of the operation.
    duration: int
        The duration of the operation.
    """

    def __init__(
        self, op: Operation, assigned_machine: int, start: int, duration: int
    ):
        self._op = op
        self._assigned_machine = assigned_machine
        self._start = start
        self._duration = duration

        if assigned_machine not in list(op.machines):
            msg = f"Operation {op} not allowed on machine {assigned_machine}."
            raise ValueError(msg)

    @property
    def op(self) -> Operation:
        return self._op

    @property
    def assigned_machine(self) -> int:
        return self._assigned_machine

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
    data: ProblemData
        The problem data.
    schedule: list[ScheduledOperation]
        A list of scheduled operations.
    """

    def __init__(self, data: ProblemData, schedule: list[ScheduledOperation]):
        self.data = data
        self.schedule = schedule

    # TODO Add checks.
    # TODO Add classmethod based on machine sequences (see #8).
