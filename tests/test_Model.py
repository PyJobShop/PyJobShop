from numpy.testing import assert_equal

from fjsp import Model


def test_add_job_attributes():
    """
    Tests that adding a job to the model correctly sets the attributes.
    """
    model = Model()

    job = model.add_job(deadline=1, release_date=2, name="job")

    assert_equal(job.deadline, 1)
    assert_equal(job.release_date, 2)
    assert_equal(job.name, "job")


def test_add_machine_attributes():
    """
    Tests that adding a machine to the model correctly sets the attributes.
    """
    model = Model()

    machine = model.add_machine(name="machine")

    assert_equal(machine.name, "machine")


def test_add_operation_attributes():
    """
    Tests that adding an operation to the model correctly sets the attributes.
    """
    model = Model()

    operation = model.add_operation(1, 2, 3, 4, name="operation")

    assert_equal(operation.earliest_start, 1)
    assert_equal(operation.latest_start, 2)
    assert_equal(operation.earliest_end, 3)
    assert_equal(operation.latest_end, 4)
    assert_equal(operation.name, "operation")
