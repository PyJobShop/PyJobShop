from numpy.testing import assert_equal

from pyjobshop.ProblemData import Mode, ProblemData, Renewable, Task
from pyjobshop.solvers.utils import intersecting_modes


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
