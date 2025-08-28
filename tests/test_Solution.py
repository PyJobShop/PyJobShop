from numpy.testing import assert_, assert_equal

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


def test_solution_makespan(small):
    """
    Tests the makespan calculation of a solution.
    """
    tasks = [TaskData(0, [0], 0, 0), TaskData(0, [1], 0, 100)]
    sol = Solution(small, tasks)

    assert_equal(sol.makespan, 100)
