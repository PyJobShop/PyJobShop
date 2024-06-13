from numpy.testing import assert_equal

from pyjobshop.ProblemData import Job, Machine, ProblemData, Task
from pyjobshop.utils import compute_min_max_durations


def test_compute_min_max_durations():
    """
    Tests that the minimum and maximum durations are correctly computed.
    """
    data = ProblemData(
        [Job()],
        [Machine(), Machine()],
        [Task(), Task()],
        processing_times={(0, 0): 1, (0, 1): 10, (1, 1): 0},
        constraints={},
    )

    min_durations, max_durations = compute_min_max_durations(data)

    # First task has processing times 1 and 10, whereas the second task has
    # only one processing time of 0.
    assert_equal(min_durations, [1, 0])
    assert_equal(max_durations, [10, 0])
