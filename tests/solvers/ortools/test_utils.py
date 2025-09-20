import pytest
from numpy.testing import assert_, assert_equal

from pyjobshop.constants import MAX_VALUE
from pyjobshop.solvers.ortools.utils import (
    partition_task_start_by_break_overlap,
)


def test_partition_no_breaks():
    """
    Tests that an instance with no breaks results in a single partition.
    """
    breaks = []
    task_duration = 5
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    assert_equal(len(partitions), 1)
    assert_equal(partitions[0].flattened_intervals(), [0, MAX_VALUE])


def test_partition_zero_task_duration():
    """
    Tests edge case with zero duration task.
    """
    breaks = [(10, 15)]
    task_duration = 0
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    assert_equal(len(partitions), 1)
    assert_equal(partitions[0].flattened_intervals(), [0, 9, 15, MAX_VALUE])


def test_partition_break_at_zero():
    """
    Tests with break starting at time 0.
    """
    breaks = [(0, 5)]
    task_duration = 3
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    # Only one partition because we cannot start before time = 0, so there
    # cannot be overlap with the first break.
    assert_equal(len(partitions), 1)
    assert_equal(partitions[0].flattened_intervals(), [5, MAX_VALUE])


def test_partition_single_break():
    """
    Tests that an instance with a single break results in two partitions.
    """
    breaks = [(10, 15)]
    task_duration = 3
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    assert_equal(len(partitions), 2)

    # Starting at 8 or 9 results in overlap with the break.
    assert_equal(partitions[5].flattened_intervals(), [8, 9])

    # Break times are not part of the domain.
    assert_equal(partitions[0].flattened_intervals(), [0, 7, 15, MAX_VALUE])


def test_partition_multiple_breaks():
    """
    Tests multiple breaks creating different partitions.
    """
    breaks = [(5, 6), (11, 13)]  # two breaks of duration 1 and 2
    task_duration = 5
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    assert_equal(len(partitions), 3)

    # Starting in [1, 4] results in overlap with the first break.
    assert_equal(partitions[1].flattened_intervals(), [1, 4])

    # Starting in [7, 10] results in overlap with the second break.
    assert_equal(partitions[2].flattened_intervals(), [7, 10])

    # All other starting times result in no overlaps.
    intervals = partitions[0].flattened_intervals()
    assert_equal(intervals, [0, 0, 6, 6, 13, MAX_VALUE])


def test_partition_task_spans_multiple_breaks():
    """
    Tests multiple breaks with a task that can overlap with both.
    """
    breaks = [(5, 6), (11, 13)]  # two breaks of duration 1 and 2
    task_duration = 10
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    assert_equal(len(partitions), 4)

    # Starting in [1, 4] results in overlap with both breaks.
    assert_equal(partitions[3].flattened_intervals(), [1, 4])

    # Starting in [6, 10] results in overlap with the second break.
    assert_equal(partitions[2].flattened_intervals(), [6, 10])

    # Starting in [0, 0] results in overlap with the first break.
    assert_equal(partitions[1].flattened_intervals(), [0, 0])

    # All other starting times result in no overlap times
    assert_equal(partitions[0].flattened_intervals(), [13, MAX_VALUE])


@pytest.mark.parametrize(
    "breaks,task_duration",
    [
        ([(5, 10), (15, 20)], 3),
        ([(0, 5), (10, 15)], 2),
        ([(10, 12), (20, 22)], 5),
        ([(t, t + 2) for t in range(0, 20, 5)], 10),
    ],
)
def test_partition_no_start_during_breaks(breaks, task_duration):
    """
    Tests that partitions do not contain break periods.
    """
    partitions = partition_task_start_by_break_overlap(breaks, task_duration)

    for domain in partitions.values():
        for start, end in breaks:
            for t in range(start, end):
                # Should not be able to start during any break
                assert_(not domain.contains(t))
