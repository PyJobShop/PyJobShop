from .ProblemData import ProblemData


class ScheduledOperation:
    """
    The ScheduledOperation class stores data related to scheduled operations.

    Parameters
    ----------
    op: int
        The scheduled operation index.
    assigned_machine: int
        The machine to which the operation is assigned.
    start: int
        The start time of the operation.
    duration: int
        The duration of the operation.
    """

    def __init__(
        self, op: int, assigned_machine: int, start: int, duration: int
    ):
        self._op = op
        self._assigned_machine = assigned_machine
        self._start = start
        self._duration = duration

    @property
    def op(self) -> int:
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
        self.schedule = schedule
        self._validate(data)

    def _validate(self, data: ProblemData):
        for scheduled_op in self.schedule:
            op = scheduled_op.op
            op_data = data.operations[op]
            assigned = scheduled_op.assigned_machine

            if assigned not in op_data.machines:
                msg = f"Operation {op} not allowed on machine {assigned}."
                raise ValueError(msg)

    # TODO Add classmethod based on machine sequences (see #8).
