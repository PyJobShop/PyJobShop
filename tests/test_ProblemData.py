import networkx as nx
import numpy as np
from numpy.testing import assert_allclose, assert_equal

from fjsp import Job, Machine, Operation, ProblemData


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
    operation = Operation(1, [0, 1], "TestOperation")

    assert_equal(operation.job, 1)
    assert_equal(operation.machines, [0, 1])
    assert_equal(operation.name, "TestOperation")

    # Also test that default values are set correctly.
    operation = Operation(1, [1])

    assert_equal(operation.name, None)


# TODO test PrecedenceType


def test_problem_data_attributes():
    """
    Tests that the attributes of the ProblemData class are set correctly.
    """
    jobs = [Job() for _ in range(5)]
    machines = [Machine() for _ in range(5)]
    operations = [Operation(idx, [idx]) for idx in range(5)]

    machine_graph = nx.DiGraph()
    machine_graph.add_nodes_from(range(5))

    operations_graph = nx.DiGraph()
    operations_graph.add_nodes_from(range(5))

    processing_times = np.ones((5, 5), dtype=int)
    setup_times = np.ones((5, 5, 5), dtype=int)

    data = ProblemData(
        jobs,
        machines,
        operations,
        machine_graph,
        operations_graph,
        processing_times,
        setup_times,
    )

    assert_equal(data.jobs, jobs)
    assert_equal(data.machines, machines)
    assert_equal(data.operations, operations)
    assert_equal(data.machine_graph, machine_graph)
    assert_equal(data.operations_graph, operations_graph)
    assert_allclose(data.processing_times, processing_times)
    assert_allclose(data.setup_times, setup_times)

    assert_equal(data.job2ops, [[0], [1], [2], [3], [4]])
    assert_equal(data.machine2ops, [[0], [1], [2], [3], [4]])
    assert_equal(data.num_jobs, 5)
    assert_equal(data.num_machines, 5)
    assert_equal(data.num_operations, 5)
