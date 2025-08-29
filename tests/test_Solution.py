from numpy.testing import assert_, assert_equal

from pyjobshop.ProblemData import (
    Job,
    Machine,
    Mode,
    Objective,
    ProblemData,
    Task,
)
from pyjobshop.Solution import JobData, Solution, TaskData


def test_job_data_attributes():
    """
    Tests the attributes of JobData.
    """
    job = JobData(start=1, end=3, flow_time=2, lateness=1)

    assert_equal(job.duration, 2)
    assert_equal(job.is_tardy, True)
    assert_equal(job.tardiness, 1)
    assert_equal(job.earliness, 0)

    # Also test non-negative earliness.
    job = JobData(start=1, end=3, flow_time=2, lateness=-1)
    assert_equal(job.earliness, 1)


def test_job_data_from_objectives_example():
    """
    Test JobData using the example from objectives.ipynb.

    The example has two jobs with the following data:
    Job 1: weight=3, release_date=1, start=2, end=4, due_date=3
    Job 2: weight=1, release_date=0, start=0, end=2, due_date=4
    """
    # Create job data as shown in the objectives.ipynb example
    job1_data = JobData(
        start=2,
        end=4,
        flow_time=3,  # end - release_date = 4 - 1 = 3
        lateness=1,  # end - due_date = 4 - 3 = 1
    )

    job2_data = JobData(
        start=0,
        end=2,
        flow_time=2,  # end - release_date = 2 - 0 = 2
        lateness=-2,  # end - due_date = 2 - 4 = -2
    )

    # Test Job 1 properties
    assert_equal(job1_data.duration, 2)
    assert_equal(job1_data.is_tardy, True)
    assert_equal(job1_data.tardiness, 1)
    assert_equal(job1_data.earliness, 0)

    # Test Job 2 properties
    assert_equal(job2_data.duration, 2)
    assert_equal(job2_data.is_tardy, False)
    assert_equal(job2_data.tardiness, 0)
    assert_equal(job2_data.earliness, 2)


def test_task_data_attributes():
    """
    Tests the attributes of TaskData.
    """
    task = TaskData(mode=0, resources=[0], start=1, end=3)
    assert_equal(task.duration, 2)


def test_solution_eq(small):
    """
    Tests the equality comparison of solutions.
    """
    tasks = [TaskData(0, [0], 0, 1), TaskData(0, [0], 1, 3)]
    sol1 = Solution(small, tasks)

    assert_equal(sol1, Solution(small, tasks))

    other = [TaskData(0, [0], 2, 3), TaskData(1, [0], 0, 1)]
    assert_(sol1 != Solution(small, other))


def test_solution_jobs_and_objectives():
    """
    Test that the objective of the solution is correctly calculated.
    """
    jobs = [
        Job(weight=3, release_date=1, due_date=3, tasks=[0]),
        Job(weight=1, release_date=0, due_date=4, tasks=[1]),
    ]
    tasks = [Task(job=0), Task(job=1)]
    modes = [
        Mode(task=0, resources=[0], duration=2),
        Mode(task=1, resources=[0], duration=2),
    ]

    data = ProblemData(
        jobs=jobs,
        tasks=tasks,
        modes=modes,
        resources=[Machine()],
        objective=Objective(),
    )

    task_data = [
        TaskData(mode=0, resources=[0], start=2, end=4),
        TaskData(mode=1, resources=[0], start=0, end=2),
    ]
    solution = Solution(data, task_data)
    assert_equal(len(solution.jobs), 2)

    job1_data = solution.jobs[0]
    assert_equal(job1_data.start, 2)
    assert_equal(job1_data.end, 4)
    assert_equal(job1_data.flow_time, 3)
    assert_equal(job1_data.tardiness, 1)
    assert_equal(job1_data.earliness, 0)
    assert_equal(job1_data.is_tardy, True)

    job2_data = solution.jobs[1]
    assert_equal(job2_data.start, 0)
    assert_equal(job2_data.end, 2)
    assert_equal(job2_data.flow_time, 2)
    assert_equal(job2_data.tardiness, 0)
    assert_equal(job2_data.earliness, 2)
    assert_equal(job2_data.is_tardy, False)

    # Test objective component calculations.
    assert_equal(solution.makespan, 4)
    assert_equal(solution.tardy_jobs, 3)  # 3*1 + 1*0 = 3
    assert_equal(solution.total_flow_time, 11)  # 3*3 + 1*2 = 11
    assert_equal(solution.total_tardiness, 3)  # 3*1 + 1*0 = 3
    assert_equal(solution.total_earliness, 2)  # 3*0 + 1*2 = 2
    assert_equal(solution.max_tardiness, 3)  # max(3*1, 1*0) = 3
    assert_equal(solution.total_setup_time, 0)  # TODO


def test_solution_makespan(small):
    """
    Tests the makespan calculation of a solution.
    """
    tasks = [TaskData(0, [0], 0, 0), TaskData(0, [1], 0, 100)]
    sol = Solution(small, tasks)

    assert_equal(sol.makespan, 100)
