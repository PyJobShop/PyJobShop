import pytest

from pyjobshop import Model


@pytest.fixture(scope="session")
def small():
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [model.add_operation() for _ in range(2)]

    model.assign_job_operations(job, operations)

    for operation, duration in zip(operations, [1, 2]):
        model.add_processing_time(machine, operation, duration)

    return model.data()
