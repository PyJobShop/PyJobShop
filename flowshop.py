import random

from fjsp import Model, PrecedenceType, create_cp_model, plot

NUM_JOBS = 10
NUM_MACHINES = 5


def main():
    random.seed(42)

    model = Model()
    jobs = [model.add_job() for _ in range(NUM_JOBS)]
    machines = [model.add_machine() for _ in range(NUM_MACHINES)]

    for idx in range(NUM_MACHINES - 1):
        model.add_machines_edge(
            machines[idx], machines[idx + 1], same_sequence=True
        )

    for job in jobs:
        # Create one operation per (job, machine) pair.
        ops = [
            model.add_operation(job, [machine], [random.randint(1, 10)])
            for machine in machines
        ]

        # Create precedence constraints between operations.
        for idx in range(len(ops) - 1):
            model.add_operations_edge(
                ops[idx],
                ops[idx + 1],
                precedence_types=[PrecedenceType.END_AT_START],  # blocking
            )

    cp_model = create_cp_model(model.data())
    result = cp_model.solve(TimeLimit=10)
    plot(model, result)


if __name__ == "__main__":
    main()
