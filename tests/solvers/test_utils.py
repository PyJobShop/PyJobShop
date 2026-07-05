from numpy.testing import assert_equal

from pyjobshop.Model import Model
from pyjobshop.ProblemData import Mode, ProblemData, Renewable, Task
from pyjobshop.solvers.utils import (
    intersecting_modes,
    redundant_cumulative_components,
)


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


def test_redundant_cumulative_components_empty():
    """
    Tests that the redundant cumulative components are empty when an instance
    has no machines.
    """
    model = Model()
    resources = [
        model.add_renewable(capacity=10),
        model.add_consumable(capacity=10),
    ]
    tasks = [model.add_task() for _ in range(10)]

    for task in tasks:
        for resource in resources:
            model.add_mode(task, resource, 1)

    components = redundant_cumulative_components(model.data())

    # No machines, so no components.
    assert_equal(len(components), 0)


def test_redundant_cumulative_components_hybrid_flow_shop():
    """
    Tests that the redundant cumulative components are correctly identified
    for a hybrid flow shop problem.
    """
    num_stages = 2
    num_machines = 3
    num_jobs = 4

    model = Model()
    machines = [
        [model.add_machine() for _ in range(num_machines)]
        for _ in range(num_stages)
    ]
    tasks = [
        [model.add_task() for _ in range(num_stages)] for _ in range(num_jobs)
    ]

    for job_tasks in tasks:
        for stage_idx, task in enumerate(job_tasks):
            for machine in machines[stage_idx]:
                model.add_mode(task, machine, 1)

    components = redundant_cumulative_components(model.data())
    assert_equal(len(components), 2)

    # First stage components. Notice that the tasks belonging to this
    # stage have even indices, because that's how we created a job's task.
    assert_equal(components[0].machines, {0, 1, 2})
    assert_equal(components[0].tasks, {0, 2, 4, 6})

    # Second stage components.
    assert_equal(components[1].machines, {3, 4, 5})
    assert_equal(components[1].tasks, {1, 3, 5, 7})


def test_redundant_cumulative_components_multiple_modes():
    """
    Tests that redundant cumulative components also work when tasks can be
    assigned to different machines simultaneously.
    """
    model = Model()
    machines = [model.add_machine() for _ in range(10)]
    task1 = model.add_task()
    task2 = model.add_task()

    model.add_mode(task1, machines[:6], 1)
    model.add_mode(task2, machines[4:], 1)

    components = redundant_cumulative_components(model.data())

    # One big component with all machines and tasks.
    assert_equal(len(components), 1)
    assert_equal(components[0].machines, set(range(10)))
    assert_equal(components[0].tasks, {0, 1})
