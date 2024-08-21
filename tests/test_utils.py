from numpy.testing import assert_equal

from pyjobshop.ProblemData import Job, Machine, Mode, ProblemData, Task
from pyjobshop.utils import compute_task_durations


def test_compute_task_durations():
    """
    Tests that the task durations are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Machine(), Machine()],
        [Task(), Task()],
        modes=[Mode(0, 1, [0]), Mode(0, 10, [1]), Mode(1, 0, [1])],
        constraints={},
    )

    task_durations = compute_task_durations(data)

    # First task has processing times 1 and 10, whereas the second task has
    # only one processing time of 0.
    assert_equal(task_durations[0], [1, 10])
    assert_equal(task_durations[1], [0])
