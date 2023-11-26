from numpy.testing import assert_equal

from fjsp import Model


def test_solve():
    """
    Tests the solve method of the Model class.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [model.add_operation() for _ in range(3)]

    model.assign_job_operations(job, operations)
    model.assign_machine_operations(machine, operations)

    for operation, duration in zip(operations, [1, 2, 3]):
        model.add_processing_time(operation, machine, duration)

    result = model.solve()

    assert_equal(result.get_objective_value(), 6)
