import pytest
from numpy.testing import assert_equal

from pyjobshop import Model


@pytest.mark.parametrize(
    "extra_modes",
    [(0, 0), (1, 0), (0, 1), (1, 1), (1, 2), (2, 1), (2, 0), (0, 2)],
)
@pytest.mark.parametrize("explicit", [False, True])
def test_same_sequence_multiple_modes_ortools(extra_modes, explicit):
    """Default correspondence uses unique tasks, not their number of modes."""
    model = Model()
    machines = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task() for _ in range(4)]

    for idx, task in enumerate(tasks):
        model.add_mode(task, machines[idx // 2], duration=1)

    for machine_idx, count in enumerate(extra_modes):
        for mode_idx in range(count):
            model.add_mode(
                tasks[2 * machine_idx],
                machines[machine_idx],
                duration=mode_idx + 2,
            )

    model.add_end_before_start(tasks[0], tasks[1])
    model.add_end_before_start(tasks[2], tasks[3])

    if explicit:
        model.add_same_sequence(*machines, tasks[:2], tasks[2:])
    else:
        model.add_same_sequence(*machines)

    result = model.solve(solver="ortools", display=False)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)

    # A concrete feasible schedule attains the lower bound of two unit tasks
    # on each machine: T0/T2 at [0, 1), followed by T1/T3 at [1, 2).
    for idx, task in enumerate(result.best.tasks):
        assert_equal(task.resources, [idx // 2])
        assert_equal(task.start, idx % 2)
        assert_equal(task.end, idx % 2 + 1)


@pytest.mark.parametrize(
    "extra_modes", [(0, 0), (1, 0), (0, 1), (1, 2), (2, 1)]
)
def test_same_sequence_multiple_modes_rejects_opposite_order(extra_modes):
    """Extra modes must not allow the machines to use opposite task orders."""
    model = Model()
    machines = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task() for _ in range(4)]

    for idx, task in enumerate(tasks):
        model.add_mode(task, machines[idx // 2], duration=1)

    for machine_idx, count in enumerate(extra_modes):
        for mode_idx in range(count):
            model.add_mode(
                tasks[2 * machine_idx],
                machines[machine_idx],
                duration=mode_idx + 2,
            )

    model.add_end_before_start(tasks[0], tasks[1])
    model.add_end_before_start(tasks[3], tasks[2])
    model.add_same_sequence(*machines)

    result = model.solve(solver="ortools", display=False)
    assert_equal(result.status.value, "Infeasible")
