from collections import defaultdict
from dataclasses import dataclass
from itertools import pairwise

from pyjobshop.ProblemData import ProblemData
from pyjobshop.solvers.utils import setup_times_matrix


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
        The due date of the job. Default None.
    """

    start: int
    end: int
    release_date: int = 0
    due_date: int | None = None

    @property
    def duration(self) -> int:
        """
        Returns the total duration of the job.
        """
        return self.end - self.start

    @property
    def flow_time(self) -> int:
        """
        Returns the flow time of the job.
        """
        return self.end - self.release_date

    @property
    def is_tardy(self) -> bool:
        """
        Returns whether the job is tardy. Not tardy if the job has no due date.
        """
        return self.end > self.due_date if self.due_date is not None else True

    @property
    def tardiness(self) -> int:
        """
        Returns the tardiness of the job. Zero if the job has no due date.
        """
        return (
            max(self.end - self.due_date, 0)
            if self.due_date is not None
            else 0
        )

    @property
    def earliness(self) -> int:
        """
        Returns the earliness of the job. Zero if the job has no due date.
        """
        return (
            max(self.due_date - self.end, 0)
            if self.due_date is not None
            else 0
        )


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
    data
        The problem data.
    tasks
        The list of scheduled tasks.

    .. warning::
       This class does not yet check the feasibility of the solution.
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
            tasks = [self._tasks[idx] for idx in job.tasks]
            start = min(task.start for task in tasks)
            end = max(task.end for task in tasks)
            jobs.append(JobData(start, end, job.release_date, job.due_date))

        return jobs

    @property
    def tasks(self) -> list[TaskData]:
        """
        Returns the list of tasks and its scheduling data.
        """
        return self._tasks

    @property
    def jobs(self) -> list[JobData]:
        """
        Returns the list of jobs and its scheduling data.
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
