from numpy.testing import assert_, assert_equal

from pyjobshop import (
    EndBeforeStart,
    Mode,
    SelectAtLeastOne,
    StartBeforeStart,
)
from tests.utils import read


def test_rcpsp_max():
    """
    Tests that reading an RCPSP/max instance works correctly.
    """
    loc = "data/UBO10_01.sch"
    data = read(loc, instance_format="rcpsp_max")

    assert_equal(data.num_renewables, 5)
    assert_equal(data.num_tasks, 12)
    assert_equal(data.num_modes, 12)

    for res in data.resources:
        assert_equal(res.capacity, 10)

    assert_(not data.tasks[0].optional)
    assert_(not data.tasks[1].optional)

    assert_equal(data.modes[0], Mode(0, [0, 1, 2, 3, 4], 0))
    assert_equal(data.modes[2], Mode(2, [0, 1, 2, 3, 4], 9, [10, 8, 0, 8, 10]))

    # Check precedence constraints.
    pairs = [(2, 4, 5), (2, 11, 9), (2, 7, 0)]

    for task1, task2, delay in pairs:
        constraint = StartBeforeStart(task1, task2, delay)
        assert_(constraint in data.constraints.start_before_start)


def test_aslib():
    """
    Tests that reading an ASLIB instance works correctly.
    """
    loc = "data/aslib0_0.rcp"
    data = read(loc, instance_format="aslib")

    assert_equal(data.num_renewables, 5)
    assert_equal(data.num_tasks, 122)
    assert_equal(data.num_modes, 122)

    for res in data.resources:
        assert_equal(res.capacity, 10)

    assert_(not data.tasks[0].optional)
    assert_(data.tasks[1].optional)

    assert_equal(data.modes[0], Mode(0, [0, 1, 2, 3, 4], 0))

    # Check precedence constraints.
    pairs = [(0, 1), (0, 13), (0, 25), (0, 37), (0, 49), (2, 9), (2, 8)]

    for task1, task2 in pairs:
        constraint = EndBeforeStart(task1, task2)
        assert_(constraint in data.constraints.end_before_start)

    # Check selection group constraints.
    groups = [(0, [1, 13, 25, 37, 49]), (2, [9]), (2, [8])]

    for task1, tasks2 in groups:
        constraint = SelectAtLeastOne(tasks2, task1)
        assert_(constraint in data.constraints.select_at_least_one)
