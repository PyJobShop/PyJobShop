from dataclasses import dataclass


@dataclass
class TaskData:
    """
    Stores scheduling data related to a task.

    Parameters
    ----------
    mode
        The selected mode.
    resources
        The selected resources.
    start
        The start time.
    end
        The end time.
    overlap
        Duration of overlap with other tasks on shared resources.
    idle
        Duration of idle time before the task starts on shared resources.
    present
        Whether the task is present in the solution.
    """

    mode: int
    resources: list[int]
    start: int
    end: int
    overlap: int = 0
    idle: int = 0
    present: bool = True

    @property
    def duration(self) -> int:
        """
        Returns the duration of the task.
        """
        return self.end - self.start

    @property
    def processing(self) -> int:
        """
        Returns the processing time of the task.
        """
        return self.duration - self.overlap - self.idle


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

    @property
    def makespan(self) -> int:
        """
        Returns the makespan of the solution.
        """
        return max(task.end for task in self.tasks)
