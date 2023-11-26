from numpy.testing import assert_equal

from fjsp import Model, default_model


def test_earliest_start():
    """
    Tests that an operation starts no earlier than its earliest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_start=1)

    model.assign_job_operations(job, [operation])
    model.assign_machine_operations(machine, [operation])
    model.add_processing_time(operation, machine, duration=1)

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    # Operation starts at time 1 and takes 1 time unit, so the makespan is 2.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 2)


def test_earliest_end():
    """
    Tests that an operation end no earlier than its earliest end time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_end=2)

    model.assign_job_operations(job, [operation])
    model.assign_machine_operations(machine, [operation])
    model.add_processing_time(operation, machine, duration=1)

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    # Operation cannot end before time 2, so it starts at time 1 with
    # duration 1, thus the makespan is 2.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 2)
