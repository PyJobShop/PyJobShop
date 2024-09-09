from numpy.testing import assert_equal

from pyjobshop.parse.project import parse_mplib

from .utils import relative


def test_mplib_set1():
    """
    Tests that the instance ``MPLIB1_Set1_0.rcmp`` is correctly parsed.
    """
    instance = parse_mplib(relative("data/MPLIB1_Set1_0.rcmp"))

    capacities = [res.capacity for res in instance.resources]
    renewables = [res.renewable for res in instance.resources]

    assert_equal(instance.num_resources, 4)
    assert_equal(capacities, [56, 56, 56, 56])
    assert_equal(renewables, [True, True, True, True])

    assert_equal(instance.num_projects, 6)
    for project in instance.projects:
        assert_equal(project.num_activities, 62)
        assert_equal(project.release_date, 0)

    assert_equal(instance.num_activities, 6 * 62)

    activity = instance.activities[0]

    # Successors are 1:2, 1:3, 1:4 -> activity indices 1, 2, 3
    assert_equal(activity.successors, [1, 2, 3])

    assert_equal(activity.num_modes, 1)
    assert_equal(activity.modes[0].demands, [0, 0, 0, 0])
    assert_equal(activity.modes[0].duration, 0)


def test_mplib_set2():
    """
    Tests that the instance ``MPLIB2_Set1_0.rcmp`` is correctly parsed.
    """
    instance = parse_mplib(relative("data/MPLIB2_Set1_0.rcmp"))

    capacities = [res.capacity for res in instance.resources]
    renewables = [res.renewable for res in instance.resources]

    assert_equal(instance.num_resources, 5)
    assert_equal(capacities, [48, 48, 46, 50, 48])
    assert_equal(renewables, [True, True, True, True, True])

    assert_equal(instance.num_projects, 10)
    for project in instance.projects:
        assert_equal(project.num_activities, 52)
        assert_equal(project.release_date, 0)

    assert_equal(instance.num_activities, 10 * 52)

    activity = instance.activities[-51]  # second activity of last project

    # Successors are 10:14 10:13 10:12 10:9.
    successors = [(9 * 52) + idx - 1 for idx in [14, 13, 12, 9]]
    assert_equal(activity.successors, successors)

    assert_equal(activity.num_modes, 1)
    assert_equal(activity.modes[0].demands, [8, 4, 3, 5, 1])
    assert_equal(activity.modes[0].duration, 7)
