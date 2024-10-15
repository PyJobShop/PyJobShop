from numpy.testing import assert_equal

from pyjobshop.parse.project import parse_psplib

from .utils import relative


def test_instance_single_mode():
    """
    Tests an PSPLIB instance with a single mode (aka RCPSP).
    """
    instance = parse_psplib(relative("data/m11_1.mm"))

    capacities = [res.capacity for res in instance.resources]
    renewables = [res.renewable for res in instance.resources]

    assert_equal(instance.num_resources, 4)
    assert_equal(capacities, [12, 9, 37, 53])
    assert_equal(renewables, [True, True, False, False])

    assert_equal(instance.num_projects, 1)
    assert_equal(instance.projects[0].num_activities, 18)
    assert_equal(instance.num_activities, 18)

    activity = instance.activities[1]  # second activity (jobnr. 2)
    successors = [4, 8]
    assert_equal(activity.successors, successors)

    assert_equal(activity.num_modes, 1)
    assert_equal(activity.modes[0].duration, 2)
    assert_equal(activity.modes[0].demands, [0, 4, 8, 0])


def test_instance_mmlib():
    """
    Tests an PSPLIB-style instance from MMLIB, which are formatted slightly
    different with header names.
    """
    instance = parse_psplib(relative("data/Jall1_1.mm"))

    capacities = [res.capacity for res in instance.resources]
    renewables = [res.renewable for res in instance.resources]

    assert_equal(instance.num_resources, 4)
    assert_equal(capacities, [33, 33, 247, 248])
    assert_equal(renewables, [True, True, False, False])

    assert_equal(instance.num_projects, 1)
    assert_equal(instance.projects[0].num_activities, 52)

    assert_equal(instance.num_activities, 52)

    activity = instance.activities[1]  # second activity (jobnr. 2)
    successors = [50, 49, 47, 24, 22, 20, 19, 17, 16, 13]
    assert_equal(activity.successors, successors)

    assert_equal(activity.num_modes, 3)
    assert_equal(activity.modes[0].duration, 2)
    assert_equal(activity.modes[0].demands, [8, 8, 2, 8])
    assert_equal(activity.modes[1].duration, 3)
    assert_equal(activity.modes[1].demands, [5, 5, 2, 6])
    assert_equal(activity.modes[2].duration, 4)
    assert_equal(activity.modes[2].demands, [4, 5, 2, 6])
