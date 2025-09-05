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
    idle
        The time that this task is not processing, excluding breaks.
    breaks
        The total time that this task is interrupted by resource breaks.
    present
        Whether the task is present in the solution.
    """

    mode: int
    resources: list[int]
    start: int
    end: int
    idle: int = 0
    breaks: int = 0
    present: bool = True

    @property
    def duration(self) -> int:
        """
        Returns the total duration of the task.
        """
        return self.end - self.start

    @property
    def processing(self) -> int:
        """
        Returns the processing time of the task.
        """
        return self.duration - self.breaks - self.idle


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
