import argparse
import random
from itertools import product
from typing import Optional

from fjsp import Model, PrecedenceType, plot_solution

NUM_JOBS = 10
NUM_MACHINES = 5


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", default="ortools", type=str)
    parser.add_argument("--time_limit", default=10, type=int)
    parser.add_argument("--plot", action="store_true")
    return parser.parse_args()


def main(solver: str, time_limit: int, plot: Optional[bool]):
    random.seed(42)

    model = Model()
    jobs = [model.add_job() for _ in range(NUM_JOBS)]
    machines = [model.add_machine() for _ in range(NUM_MACHINES)]

    # Machine i can only access machine i+1; all other pairs are forbidden.
    for idx1, idx2 in product(range(NUM_MACHINES), range(NUM_MACHINES)):
        if idx1 != idx2 - 1:
            model.add_access_constraint(machines[idx1], machines[idx2])

    for job in jobs:
        # Create one operation per (job, machine) pair.
        ops = [model.add_operation(job, [machine]) for machine in machines]

        for op, machine in zip(ops, machines):
            model.add_processing_time(op, machine, random.randint(1, 10))

        # Create precedence constraints between operations.
        for idx in range(len(ops) - 1):
            model.add_precedence(
                ops[idx],
                ops[idx + 1],
                precedence_types=[PrecedenceType.END_AT_START],  # blocking
            )

    data = model.data()
    solution = model.solve(solver=solver, time_limit=time_limit)

    if plot:
        plot_solution(data, solution)


if __name__ == "__main__":
    main(**vars(parse_args()))
