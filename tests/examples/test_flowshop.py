import random

from numpy.testing import assert_equal

from fjsp import Model, PrecedenceType, default_model

NUM_JOBS = 5
NUM_MACHINES = 5


def test_flowshop():
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
            model.add_precedence(
                operations[idx],
                operations[idx + 1],
                precedence_types=[PrecedenceType.END_AT_START],  # blocking
            )

    data = model.data()
    cp_model = default_model(data)
    result = cp_model.solve(TimeLimit=10)

    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 51)
