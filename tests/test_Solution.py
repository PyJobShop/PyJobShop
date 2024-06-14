from numpy.testing import assert_, assert_equal

from pyjobshop.Solution import Solution, TaskData


def test_task_eq():
    """
    Tests the equality comparison of tasks.
    """
    task1 = TaskData(0, 1, 2, 3)

    assert_equal(task1, TaskData(0, 1, 2, 3))
    assert_(task1 != TaskData(0, 1, 2, 4))


def test_solution_eq():
    """
    Tests the equality comparison of solutions.
    """
    tasks = [TaskData(0, 0, 0, 1), TaskData(1, 0, 1, 2)]
    sol1 = Solution(tasks)

    assert_equal(sol1, Solution(tasks))
    other = [TaskData(0, 0, 0, 1), TaskData(0, 0, 3, 2)]
    assert_(sol1 != Solution(other))
