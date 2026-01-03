from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise

from pyjobshop.ProblemData import ProblemData
from pyjobshop.solvers.utils import setup_times_matrix


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


@dataclass
class JobData:
    """
    Stores scheduling data related to a job.

    Parameters
    ----------
    start
        The start time of the job.
    end
        The end time of the job.
    release_date
        The release date of the job. Default 0.
    due_date
        The due date of the job. Default ``None``.
    present
        Whether at least one of the job's tasks is present in the solution. If
        ``False``, all job attributes are zero or ``False``. Default ``True``.
    """

    start: int
    end: int
    release_date: int = 0
    due_date: int | None = None
    present: bool = True

    @property
    def duration(self) -> int:
        """
        Returns the total duration of the job.
        """
        if not self.present:
            return 0

        return self.end - self.start

    @property
    def flow_time(self) -> int:
        """
        Returns the flow time of the job.
        """
        if not self.present:
            return 0

        return self.end - self.release_date

    @property
    def is_tardy(self) -> bool:
        """
        Returns whether the job is tardy. If the job has no due date,
        returns ``False``.
        """
        if not self.present or self.due_date is None:
            return False

        return self.end > self.due_date

    @property
    def tardiness(self) -> int:
        """
        Returns the tardiness of the job. If the job has no due date,
        returns 0.
        """
        if not self.present or self.due_date is None:
            return 0

        return max(self.end - self.due_date, 0)

    @property
    def earliness(self) -> int:
        """
        Returns the earliness of the job. If the job has no due date,
        returns 0.
        """
        if not self.present or self.due_date is None:
            return 0

        return max(self.due_date - self.end, 0)


class Solution:
    """
    Solution to the scheduling problem.

    Parameters
    ----------
    data
        The problem data instance.
    tasks
        The list of TaskData objects, one for each task in the problem,
        or an empty list if a dummy solution is to be created.


    .. note::
       This class does **not** validate whether the solution is feasible. When
       instantiated directly, it assumes that the provided task data represent
       a feasible solution, or an empty solution if no tasks are provided.
    """

    def __init__(self, data: ProblemData, tasks: list[TaskData]):
        self._data = data
        self._tasks = tasks
        self._jobs = self._make_job_data() if tasks else []

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Solution)
            and self.tasks == other.tasks
            and self.jobs == other.jobs
        )

    def _make_job_data(self) -> list[JobData]:
        jobs = []

        for job in self._data.jobs:
            # Calculate job data based on its present tasks.
            tasks_data = [
                self._tasks[idx]
                for idx in job.tasks
                if self._tasks[idx].present
            ]
            start = min([task.start for task in tasks_data], default=0)
            end = max([task.end for task in tasks_data], default=0)
            present = bool(tasks_data)
            jobs.append(
                JobData(start, end, job.release_date, job.due_date, present)
            )

        return jobs

    @property
    def tasks(self) -> list[TaskData]:
        """
        Returns the list of task data.
        """
        return self._tasks

    @property
    def jobs(self) -> list[JobData]:
        """
        Returns the list of job data.
        """
        return self._jobs

    @property
    def objective(self) -> int:
        """
        Returns the objective value of this solution.
        """
        objective = self._data.objective
        return (
            objective.weight_makespan * self.makespan
            + objective.weight_tardy_jobs * self.tardy_jobs
            + objective.weight_total_flow_time * self.total_flow_time
            + objective.weight_total_tardiness * self.total_tardiness
            + objective.weight_total_earliness * self.total_earliness
            + objective.weight_max_tardiness * self.max_tardiness
            + objective.weight_total_setup_time * self.total_setup_time
        )

    @property
    def makespan(self) -> int:
        """
        Returns the makespan of the solution.
        """
        return max((task.end for task in self.tasks), default=0)

    @property
    def tardy_jobs(self) -> int:
        """
        Returns the weighted number of tardy jobs.
        """
        return sum(
            self._data.jobs[idx].weight * job.is_tardy
            for idx, job in enumerate(self._jobs)
        )

    @property
    def total_flow_time(self) -> int:
        """
        Returns the total weighted flow time of all jobs.
        """
        return sum(
            self._data.jobs[idx].weight * job.flow_time
            for idx, job in enumerate(self._jobs)
        )

    @property
    def total_tardiness(self) -> int:
        """
        Returns the total weighted tardiness of all jobs.
        """
        return sum(
            self._data.jobs[idx].weight * job.tardiness
            for idx, job in enumerate(self._jobs)
        )

    @property
    def total_earliness(self) -> int:
        """
        Returns the total weighted earliness of all jobs.
        """
        return sum(
            self._data.jobs[idx].weight * job.earliness
            for idx, job in enumerate(self._jobs)
        )

    @property
    def max_tardiness(self) -> int:
        """
        Returns the maximum tardiness of all jobs.
        """
        if not self._jobs:
            return 0

        return max(
            self._data.jobs[idx].weight * job.tardiness
            for idx, job in enumerate(self._jobs)
        )

    @property
    def total_setup_time(self) -> int:
        """
        Returns the total setup time of all machines.
        """
        matrix = setup_times_matrix(self._data)
        if matrix is None:
            return 0

        resource2tasks = defaultdict(list)
        for idx, sol_task in enumerate(self._tasks):
            for res in sol_task.resources:
                resource2tasks[res].append((idx, sol_task))

        setup_times = 0
        for machine_idx in self._data.machine_idcs:
            tasks = resource2tasks[machine_idx]
            tasks = sorted(tasks, key=lambda item: item[1].start)
            sequence = [idx for idx, _ in tasks]

            for task_idx1, task_idx2 in pairwise(sequence):
                setup_times += matrix[machine_idx, task_idx1, task_idx2]

        return setup_times
