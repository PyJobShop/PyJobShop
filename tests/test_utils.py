from numpy.testing import assert_equal

from pyjobshop.ProblemData import Job, Machine, Mode, ProblemData, Task
from pyjobshop.utils import compute_task_durations, machine2modes, task2modes


def test_compute_task_durations():
    """
    Tests that the task durations are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Machine(), Machine()],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
        constraints={},
    )

    task_durations = compute_task_durations(data)

    # First task has processing times 1 and 10, whereas the second task has
    # only one processing time of 0.
    assert_equal(task_durations[0], [1, 10])
    assert_equal(task_durations[1], [0])


def test_machine2modes():
    """
    Tests that the mode indices corresponding to each machine are correctly
    computed.
    """
    data = ProblemData(
        [Job()],
        [Machine(), Machine()],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
        constraints={},
    )

    mapper = machine2modes(data)
    assert_equal(mapper[0], [0])
    assert_equal(mapper[1], [1, 2])


def test_task2modes():
    """
    Tests that the mode indices corresponding to each task are correctly
    computed.
    """
    data = ProblemData(
        [Job()],
        [Machine(), Machine()],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
        constraints={},
    )

    mapper = task2modes(data)
    assert_equal(mapper[0], [0, 1])
    assert_equal(mapper[1], [2])
