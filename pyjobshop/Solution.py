from dataclasses import dataclass


@dataclass
class TaskData:
    """
    Stores scheduling data related to a task.

    Parameters
    ----------
    machine
        The assigned machine index.
    start
        The start time.
    duration
        The duration.
    end
        The end time.
    """

    machine: int
    start: int
    duration: int
    end: int


class Solution:
    """
    Solution to the problem.

    Parameters
    ----------
    tasks
        The list of scheduled tasks.
    """

    def __init__(self, tasks: list[TaskData]):
        self.tasks = tasks

    def __eq__(self, other) -> bool:
        return self.tasks == other.tasks
