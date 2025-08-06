from numpy.testing import assert_equal

from pyjobshop.ProblemData import Mode, ProblemData, Renewable, Task
from pyjobshop.solvers.utils import (
    compute_task_durations,
    different_modes,
    identical_modes,
    intersecting_modes,
)


def test_compute_task_durations():
    """
    Tests that the task durations are correctly computed.
    """
    data = ProblemData(
        [],
        [Renewable(0), Renewable(0)],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
    )

    task_durations = compute_task_durations(data)

    # First task has processing times 1 and 10, whereas the second task has
    # only one processing time of 0.
    assert_equal(task_durations[0], [1, 10])
    assert_equal(task_durations[1], [0])


def test_identical_modes():
    """
    Tests that the modes with identical resources are correctly computed.
    """
    data = ProblemData(
        [],
        [Renewable(0), Renewable(0), Renewable(0)],
        [Task(), Task(), Task()],
        [
            Mode(0, [0], 1),
            Mode(0, [0, 1], 10),
            Mode(1, [0, 1], 0),
            Mode(1, [2], 0),
            Mode(2, [0], 1),
        ],
    )

    # Task 1 has two modes (0 and 1) and task 2 has two modes (2 and 3). The
    # first mode of task 1 does not have any identical resources with any mode
    # of task 2. The second mode of task 1 has the same resources as the first
    # mode of task 2.
    task1, task2 = (0, 1)
    identical = identical_modes(data, task1, task2)
    assert_equal(identical, [(0, []), (1, [2])])

    # Task 1 has two modes (0 and 1) and task 2 has one mode (4). The first
    # mode of task 1 has the same resources as the only mode of task 2. The
    # second mode of task 1 does not have any identical resources with any mode
    # of task 2.
    task1, task2 = (0, 2)
    identical = identical_modes(data, task1, task2)
    assert_equal(identical, [(0, [4]), (1, [])])


def test_different_modes():
    """
    Tests that the modes with different resources are correctly computed.
    """
    data = ProblemData(
        [],
        [Renewable(0), Renewable(0), Renewable(0)],
        [Task(), Task(), Task()],
        [
            Mode(0, [0], 1),
            Mode(0, [0, 1], 10),
            Mode(1, [0, 1], 0),
            Mode(1, [2], 0),
            Mode(2, [0], 1),
        ],
    )

    # Task 1 has two modes (0 and 1) and task 2 has two modes (2 and 3). The
    # first mode of task 1 has resources disjoint from the first mode of
    # task 2. The second mode of task 1 has the resources disjiont from the
    # second mode of task 2.
    task1, task2 = (0, 1)
    different = different_modes(data, task1, task2)
    assert_equal(different, [(0, [3]), (1, [3])])

    # Task 1 has two modes (0 and 1) and task 2 has one mode (4). Both modes
    # of task 1 are not disjoint with the only mode of task 2.
    task1, task2 = (0, 2)
    different = different_modes(data, task1, task2)
    assert_equal(different, [(0, []), (1, [])])


def test_intersecting_modes():
    """
    Tests that the intersecting modes between two tasks are correctly computed.
    """
    data = ProblemData(
        [],
        [Renewable(0), Renewable(0), Renewable(0)],
        [Task(), Task(), Task()],
        modes=[
            Mode(0, [0], 1),
            Mode(0, [0, 1], 10),
            Mode(1, [0, 1], 0),
            Mode(1, [2], 0),
            Mode(2, [0], 1),
        ],
    )

    task1, task2 = (0, 1)
    intersecting = intersecting_modes(data, task1, task2)
    assert_equal(
        intersecting,
        [
            (0, 2, [0]),
            (0, 3, []),
            (1, 2, [0, 1]),
            (1, 3, []),
        ],
    )
