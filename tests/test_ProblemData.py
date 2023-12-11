from typing import Optional

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_equal, assert_raises

from pyjobshop.ProblemData import (
    AssignmentPrecedence,
    Job,
    Machine,
    Operation,
    ProblemData,
    TimingPrecedence,
)


def test_job_attributes():
    """
    Tests that the attributes of the Job class are set correctly.
    """
    # Let's first test the default values.
    job = Job()

    assert_equal(job.release_date, 0)
    assert_equal(job.deadline, None)
    assert_equal(job.name, None)

    # Now test with some values.
    job = Job(5, 10, "test")

    assert_equal(job.release_date, 5)
    assert_equal(job.deadline, 10)
    assert_equal(job.name, "test")


def test_machine_attributes():
    """
    Tests that the attributes of the Machine class are set correctly.
    """
    # Let's first test the default values.
    machine = Machine()

    assert_equal(machine.name, None)

    # Now test with some values.
    machine = Machine("TestMachine")

    assert_equal(machine.name, "TestMachine")


def test_operation_attributes():
    """
    Tests that the attributes of the Operation class are set correctly.
    """
    operation = Operation(1, 2, 3, 4, name="TestOperation")

    assert_equal(operation.earliest_start, 1)
    assert_equal(operation.latest_start, 2)
    assert_equal(operation.earliest_end, 3)
    assert_equal(operation.latest_end, 4)
    assert_equal(operation.name, "TestOperation")

    # Also test that default values are set correctly.
    operation = Operation()

    assert_equal(operation.earliest_start, None)
    assert_equal(operation.latest_start, None)
    assert_equal(operation.earliest_end, None)
    assert_equal(operation.latest_end, None)
    assert_equal(operation.name, None)


@pytest.mark.parametrize(
    "earliest_start, latest_start, earliest_end, latest_end",
    [
        (1, 0, None, None),  # earliest_start > latest_start
        (None, None, 1, 0),  # earliest_end > latest_end
    ],
)
def test_operation_attributes_raises_invalid_parameters(
    earliest_start: Optional[int],
    latest_start: Optional[int],
    earliest_end: Optional[int],
    latest_end: Optional[int],
):
    """
    Tests that an error is raised when invalid parameters are passed to the
    Operation class.
    """
    with assert_raises(ValueError):
        Operation(
            earliest_start,
            latest_start,
            earliest_end,
            latest_end,
        )


def test_problem_data_input_parameter_attributes():
    """
    Tests that the input parameters of the ProblemData class are set correctly
    as attributes.
    """
    jobs = [Job() for _ in range(5)]
    machines = [Machine() for _ in range(5)]
    operations = [Operation() for _ in range(5)]
    job2ops = [[0], [1], [2], [3], [4]]
    processing_times = {(i, j): 1 for i in range(5) for j in range(5)}
    timing_precedences = {
        key: [TimingPrecedence.END_BEFORE_START]
        for key in ((0, 1), (2, 3), (4, 5))
    }
    assignment_precedences = {(0, 1): [AssignmentPrecedence.PREVIOUS]}
    access_matrix = np.full((5, 5), True)
    setup_times = np.ones((5, 5, 5), dtype=int)

    data = ProblemData(
        jobs,
        machines,
        operations,
        job2ops,
        processing_times,
        timing_precedences,
        assignment_precedences,
        access_matrix,
        setup_times,
    )

    assert_equal(data.jobs, jobs)
    assert_equal(data.machines, machines)
    assert_equal(data.operations, operations)
    assert_equal(data.job2ops, job2ops)
    assert_equal(data.processing_times, processing_times)
    assert_equal(data.timing_precedences, timing_precedences)
    assert_equal(data.assignment_precedences, assignment_precedences)
    assert_equal(data.access_matrix, access_matrix)
    assert_allclose(data.setup_times, setup_times)


def test_problem_data_non_input_parameter_attributes():
    """
    Tests that attributes that are not input parameters of the ProblemData
    class are set correctly.
    """
    jobs = [Job() for _ in range(1)]
    machines = [Machine() for _ in range(3)]
    operations = [Operation() for _ in range(3)]
    job2ops = [[0, 1, 2]]
    processing_times = {(1, 2): 1, (2, 1): 1, (0, 1): 1, (2, 0): 1}

    data = ProblemData(
        jobs, machines, operations, job2ops, processing_times, {}
    )

    # The lists in machine2ops and op2machines are sorted.
    machine2ops = [[1], [2], [0, 1]]
    op2machines = [[2], [0, 2], [1]]
    assert_equal(data.machine2ops, machine2ops)
    assert_equal(data.op2machines, op2machines)

    assert_equal(data.num_jobs, 1)
    assert_equal(data.num_machines, 3)
    assert_equal(data.num_operations, 3)


def test_problem_data_default_values():
    """
    Tests that the default values of the ProblemData class are set correctly.
    """
    jobs = [Job() for _ in range(1)]
    machines = [Machine() for _ in range(1)]
    operations = [Operation() for _ in range(1)]
    job2ops = [[0]]
    timing_precedences = {(0, 1): [TimingPrecedence.END_BEFORE_START]}
    processing_times = {(0, 0): 1}
    data = ProblemData(
        jobs,
        machines,
        operations,
        job2ops,
        processing_times,
        timing_precedences,
    )

    assert_equal(data.assignment_precedences, {})
    assert_allclose(data.access_matrix, np.full((1, 1), True))
    assert_allclose(data.setup_times, np.zeros((1, 1, 1), dtype=int))


@pytest.mark.parametrize(
    "processing_times, access_matrix, setup_times",
    [
        # Negative processing times.
        ({(0, 0): -1}, np.full((1, 1), True), np.ones((1, 1, 1))),
        # Negative setup times.
        ({(0, 0): 1}, np.full((1, 1), True), np.ones((1, 1, 1)) * -1),
        # Invalid setup times shape.
        ({(0, 0): 1}, np.full((1, 1), True), np.ones((2, 2, 2))),
        # Invalid access matrix shape.
        ({(0, 0): 1}, np.full((2, 2), True), np.ones((1, 1, 1))),
    ],
)
def test_problem_data_raises_when_invalid_arguments(
    processing_times: dict[tuple[int, int], int],
    access_matrix: np.ndarray,
    setup_times: np.ndarray,
):
    """
    Tests that the ProblemData class raises an error when invalid arguments are
    passed.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job()],
            [Machine()],
            [Operation()],
            [[0]],
            processing_times,
            {},
            {},
            access_matrix.astype(int),
            setup_times.astype(int),
        )
