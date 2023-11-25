import random

from fjsp import Model, PrecedenceType, default_model, plot, result2solution

NUM_JOBS = 10
NUM_MACHINES = 5


def main():
    random.seed(42)

    model = Model()
    jobs = [model.add_job() for _ in range(NUM_JOBS)]
    machines = [model.add_machine() for _ in range(NUM_MACHINES)]

    for idx in range(NUM_MACHINES - 1):
        model.add_access_constraint(machines[idx], machines[idx + 1])

    for job in jobs:
        operations = [model.add_operation() for _ in range(NUM_MACHINES)]
        model.assign_job_operations(job, operations)

        for idx, op in enumerate(operations):
            model.assign_machine_operations(machines[idx], [op])
            model.add_processing_time(op, machines[idx], random.randint(1, 10))

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
    solution = result2solution(data, result)

    plot(data, solution)


if __name__ == "__main__":
    main()
