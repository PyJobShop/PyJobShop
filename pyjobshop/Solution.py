from dataclasses import dataclass


@dataclass
class TaskData:
    """
    Stores scheduling data related to a task.

    Parameters
    ----------
    machine
        The selected machine.
    start
        The start time.
    end
        The end time.
    """

    machine: int
    start: int
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
        self._tasks = tasks

    @property
    def tasks(self) -> list[TaskData]:
        """
        Returns the list of tasks and its scheduling data.
        """
        return self._tasks

    def __eq__(self, other) -> bool:
        return self.tasks == other.tasks
