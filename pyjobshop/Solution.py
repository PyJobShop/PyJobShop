from dataclasses import dataclass

from pyjobshop.ProblemData import ProblemData


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
    """

    start: int
    end: int
    flow_time: int
    lateness: int = 0

    @property
    def duration(self) -> int:
        return self.end - self.start

    @property
    def is_tardy(self) -> bool:
        return self.lateness > 0

    @property
    def tardiness(self) -> int:
        return max(0, self.lateness)

    @property
    def earliness(self) -> int:
        return -min(0, self.lateness)


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
    """

    mode: int
    resources: list[int]
    start: int
    end: int

    @property
    def duration(self) -> int:
        return self.end - self.start


class Solution:
    """
    Solution to the problem.

    Parameters
    ----------
    data
        The problem data.
    tasks
        The list of scheduled tasks.
    """

    def __init__(self, data: ProblemData, tasks: list[TaskData]):
        self._data = data
        self._tasks = tasks
        self._jobs = self._make_job_data() if tasks else []

    def __eq__(self, other) -> bool:
        return self.tasks == other.tasks and self.jobs == other.jobs

    def _make_job_data(self) -> list[JobData]:
        jobs = []

        for job in self._data.jobs:
            tasks = [self._tasks[idx] for idx in job.tasks]
            start = min(task.start for task in tasks)
            end = max(task.end for task in tasks)
            flow_time = end - job.release_date
            lateness = (
                max(0, end - job.due_date) if job.due_date is not None else 0
            )
            jobs.append(JobData(start, end, flow_time, lateness))

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
        if not self.tasks:
            return 0
        return max(task.end for task in self.tasks)

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
        return max(
            self._data.jobs[idx].weight * job.tardiness
            for idx, job in enumerate(self._jobs)
        )

    @property
    def total_setup_time(self) -> int:
        """
        Returns the total setup time of all machines.
        """
        return 0  # TODO

    # def feasible(self) -> bool:
    #     """
    #     Returns True if the solution is feasible, False otherwise.
    #     """
    #     return all(
    #         feasible_jobs,
    #         feasible_tasks,
    #         feasible_machines,
    #         feasible_renewables,
    #         feasible_non_renewables,
    #         feasible_constraints,
    #     )

    # def feasible_jobs(self) -> bool:
    #     """
    #     Checks that all jobs have been scheduled.
    #     """
    #     return len(self._jobs) == len(self._data.jobs) and all(
    #         len(self._jobs[idx]) == len(job.tasks)
    #         for idx, job in enumerate(self._data.jobs)
    #     )
