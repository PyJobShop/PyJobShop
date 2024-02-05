from numpy.testing import assert_, assert_equal
from pytest import raises as assert_raises

from pyjobshop.Model import Model
from pyjobshop.Solution import ScheduledOperation, Solution


def test_scheduled_operation_eq():
    """
    Tests the equality comparison of scheduled operations.
    """
    op1 = ScheduledOperation(0, 1, 2, 3)

    assert_equal(op1, ScheduledOperation(0, 1, 2, 3))
    assert_(op1 != ScheduledOperation(0, 1, 2, 4))


def test_solution_eq(small):
    """
    Tests the equality comparison of solutions.
    """
    schedule = [ScheduledOperation(0, 0, 0, 1), ScheduledOperation(1, 0, 1, 2)]
    sol1 = Solution(small, schedule)

    assert_equal(sol1, Solution(small, schedule))
    other = [ScheduledOperation(0, 0, 0, 1), ScheduledOperation(0, 0, 3, 2)]
    assert_(sol1 != Solution(small, other))


def test_solution_raises_invalid_schedule():
    """
    Tests that a ``ValueError`` is raised when a solution is created with an
    invalid schedule. In this case, it only checks whether operations are
    assigned to eligible machines.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine() for _ in range(2)]
    operations = [model.add_operation() for _ in range(2)]

    model.assign_job_operations(job, operations)

    for duration, (machine, op) in enumerate(zip(machines, operations), 1):
        model.add_processing_time(machine, op, duration)

    data = model.data()

    # Invalid schedule: operation 0 is scheduled on machine 1.
    schedule = [ScheduledOperation(0, 1, 0, 1), ScheduledOperation(1, 1, 1, 2)]

    with assert_raises(ValueError):
        Solution(data, schedule)
