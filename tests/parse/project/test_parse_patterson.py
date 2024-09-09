from numpy.testing import assert_equal

from pyjobshop.parse.project import parse_patterson

from .utils import relative


def test_rg300():
    """
    Tests that the instance ``RG300_1.rcp`` is correctly parsed.
    """
    instance = parse_patterson(relative("data/RG300_1.rcp"))

    capacities = [res.capacity for res in instance.resources]
    renewables = [res.renewable for res in instance.resources]

    assert_equal(instance.num_resources, 4)
    assert_equal(capacities, [10, 10, 10, 10])
    assert_equal(renewables, [True, True, True, True])

    assert_equal(instance.num_projects, 1)
    assert_equal(instance.projects[0].num_activities, 302)
    assert_equal(instance.num_activities, 302)

    activity = instance.activities[1]  # second activity

    successors = (
        "59, 79, 88, 95, 104, 113, 125, 128, 138, 141, 145, 146, 151, "
        "153, 155, 156, 159, 161, 163, 169, 171, 174, 176, 178, 180, "
        "201, 204, 212, 285, 287, 289, 291, 292"
    )
    successors = list(map(int, successors.split(", ")))
    assert_equal(activity.successors, successors)

    assert_equal(activity.num_modes, 1)
    assert_equal(activity.modes[0].demands, [0, 1, 0, 0])
    assert_equal(activity.modes[0].duration, 3)
