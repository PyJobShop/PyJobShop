from dataclasses import dataclass

from .ProblemData import ProblemData


# TODO rename Task
@dataclass
class Task:
    """
    The Task class stores data related to scheduled tasks.

    Parameters
    ----------
    task
        The task index.
    machine
        The machine index to which the task is assigned.
    start
        The start time of the task.
    duration
        The duration of the task.
    """

    task: int
    machine: int
    start: int
    duration: int


class Solution:
    """
    Solution to the problem.

    Parameters
    ----------
    data
        The problem data instance.
    schedule
        A list of tasks.
    """

    def __init__(self, data: ProblemData, schedule: list[Task]):
        self.schedule = schedule  # TODO rename schedule
        self._validate(data)

    def __eq__(self, other) -> bool:
        return self.schedule == other.schedule

    def _validate(self, data: ProblemData):
        for task in self.schedule:
            task_ = task.task
            assigned = task.machine

            if assigned not in data.task2machines[task_]:
                msg = f"Task {task_} not allowed on machine {assigned}."
                raise ValueError(msg)
