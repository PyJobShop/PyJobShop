from numpy.testing import assert_equal

from fjsp import Model, default_model

# TODO refactor with Solution


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


def test_latest_start():
    """
    Tests that an operation starts no later than its latest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [
        model.add_operation(),
        model.add_operation(latest_start=1),
    ]

    for operation in operations:
        model.add_processing_time(operation, machine, duration=2)

    model.assign_job_operations(job, operations)
    model.assign_machine_operations(machine, operations)

    model.add_setup_time(operations[1], operations[0], machine, 10)

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    # Operation 1 (processing time of 2) cannot start before operation 2,
    # otherwise operation 2 cannot start before time 1. So operation 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and operation 1 is processed from 12 to 14.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 14)


def test_fixed_start():
    """
    Tests that an operation starts at its fixed start time when earliest
    and latest start times are equal.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_start=42, latest_start=42)

    model.assign_job_operations(job, [operation])
    model.assign_machine_operations(machine, [operation])
    model.add_processing_time(operation, machine, duration=1)

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    # Operation starts at time 42 and takes 1 time unit, so the makespan is 43.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 43)


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


def test_latest_end():
    """
    Tests that an operation ends no later than its latest end time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [
        model.add_operation(),
        model.add_operation(latest_end=2),
    ]

    for operation in operations:
        model.add_processing_time(operation, machine, duration=2)

    model.assign_job_operations(job, operations)
    model.assign_machine_operations(machine, operations)

    model.add_setup_time(operations[1], operations[0], machine, 10)

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    # Operation 1 (processing time of 2) cannot start before operation 2,
    # otherwise operation 2 cannot end before time 2. So operation 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and operation 1 is processed from 12 to 14.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 14)


def test_fixed_end():
    """
    Tests that an operation ends at its fixed end time when earliest
    and latest end times are equal.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_end=42, latest_end=42)

    model.assign_job_operations(job, [operation])
    model.assign_machine_operations(machine, [operation])
    model.add_processing_time(operation, machine, duration=1)

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    # Operation ends at 42, so the makespan is 42.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 42)
