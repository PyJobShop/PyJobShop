from numpy.testing import assert_equal

from pyjobshop.ProblemData import Job, Mode, ProblemData, Resource, Task
from pyjobshop.solvers.utils import (
    compute_task_durations,
    find_modes_with_disjoint_resources,
    find_modes_with_identical_resources,
    find_modes_with_intersecting_resources,
    resource2modes,
    task2modes,
)


def test_compute_task_durations():
    """
    Tests that the task durations are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Resource(0), Resource(0)],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
        constraints={},
    )

    task_durations = compute_task_durations(data)

    # First task has processing times 1 and 10, whereas the second task has
    # only one processing time of 0.
    assert_equal(task_durations[0], [1, 10])
    assert_equal(task_durations[1], [0])


def test_resource2modes():
    """
    Tests that the mode indices corresponding to each resource are correctly
    computed.
    """
    data = ProblemData(
        [Job()],
        [Resource(0), Resource(0)],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
        constraints={},
    )

    mapper = resource2modes(data)
    assert_equal(mapper[0], [0])
    assert_equal(mapper[1], [1, 2])


def test_task2modes():
    """
    Tests that the mode indices corresponding to each task are correctly
    computed.
    """
    data = ProblemData(
        [Job()],
        [Resource(0), Resource(0)],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
        constraints={},
    )

    mapper = task2modes(data)
    assert_equal(mapper[0], [0, 1])
    assert_equal(mapper[1], [2])


def test_find_modes_with_intersecting_resources():
    """
    Tests that the intersecting modes between two tasks are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Resource(0), Resource(0), Resource(0)],
        [Task(), Task()],
        modes=[
            Mode(0, [0], 1),
            Mode(0, [0, 1], 10),
            Mode(1, [0, 1], 0),
            Mode(1, [2], 0),
        ],
    )
    intersecting = find_modes_with_intersecting_resources(data, 0, 1)

    # Task 1 has two modes, which both intersect with the first mode of task 2.
    # The last mode of task 2 does not intersect with any mode of task 1, so
    # it does not appear in the result.
    assert_equal(intersecting, [(0, 2, [0]), (1, 2, [0, 1])])


def test_find_modes_with_identical_resources():
    """
    Tests that the modes with identical resources are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Resource(0), Resource(0), Resource(0)],
        [Task(), Task()],
        modes=[
            Mode(0, [0], 1),
            Mode(0, [0, 1], 10),
            Mode(1, [0, 1], 0),
            Mode(1, [2], 0),
        ],
    )
    identical = find_modes_with_identical_resources(data, 0, 1)

    # The second mode of task 1 has the same resources as the first mode of
    # task 2. The other modes do not have identical resources.
    assert_equal(identical, {1: [2]})


def test_find_disjoint_resources():
    """
    Tests that the modes with disjoint resources are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Resource(0), Resource(0), Resource(0)],
        [Task(), Task()],
        modes=[
            Mode(0, [0], 1),
            Mode(0, [0, 1], 10),
            Mode(1, [0, 1], 0),
            Mode(1, [2], 0),
        ],
    )
    disjoint = find_modes_with_disjoint_resources(data, 0, 1)

    # Both modes of task 1 have disjoint resources with the second mode of
    # task 2.
    assert_equal(disjoint, {0: [3], 1: [3]})
