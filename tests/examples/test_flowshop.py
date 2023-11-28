import random

from numpy.testing import assert_equal

from fjsp import Model, TimingPrecedence

NUM_JOBS = 5
NUM_MACHINES = 5


def test_flowshop():
    """
    Blocking flowshop example.
    """
    random.seed(42)

    model = Model()
    jobs = [model.add_job() for _ in range(NUM_JOBS)]
    machines = [model.add_machine() for _ in range(NUM_MACHINES)]

    for idx in range(NUM_MACHINES - 1):
        model.add_access_constraint(machines[idx], machines[idx + 1], True)

    for job in jobs:
        # One operation per job and machine pair.
        operations = [model.add_operation() for _ in range(NUM_MACHINES)]
        model.assign_job_operations(job, operations)

        for machine, op in zip(machines, operations):
            model.assign_machine_operations(machine, [op])
            model.add_processing_time(op, machine, random.randint(1, 10))

        # Create precedence constraints between operations.
        for idx in range(len(operations) - 1):
            model.add_timing_precedence(
                operations[idx],
                operations[idx + 1],
                TimingPrecedence.END_AT_START,
            )

    result = model.solve()

    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 51)
