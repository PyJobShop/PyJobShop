import argparse
from pathlib import Path

import fjsplib
from fjsplib import read

import pyjobshop
from pyjobshop import Constraint, Model, solve


def parse_args():
    parser = argparse.ArgumentParser()

    msg = "Location of the instance file."
    parser.add_argument("instance_loc", type=Path, help=msg)

    msg = "Solver to use."
    parser.add_argument(
        "--solver",
        type=str,
        default="ortools",
        choices=["ortools", "cpoptimizer"],
        help=msg,
    )

    msg = "Time limit for solving the instance, in seconds."
    parser.add_argument("--time_limit", type=float, default=10, help=msg)

    msg = "Whether to log the solver output."
    parser.add_argument("--log", action="store_true", help=msg)

    msg = "Number of workers to use for parallel solving."
    parser.add_argument("--num_workers", type=int, default=8, help=msg)

    return parser.parse_args()


def instance2data(instance: fjsplib.Instance) -> pyjobshop.ProblemData:
    """
    Converts an FJSPLIB instance to a ProblemData object.
    """
    m = Model()

    jobs = [m.add_job() for _ in range(instance.num_jobs)]
    machines = [m.add_machine() for _ in range(instance.num_machines)]

    for job_idx, tasks in enumerate(instance.jobs):
        for task_data in tasks:
            task = m.add_task(job=jobs[job_idx])

            for machine_idx, duration in task_data:
                m.add_processing_time(machines[machine_idx], task, duration)

    for frm, to in instance.precedences:
        m.add_constraint(
            m.tasks[frm],
            m.tasks[to],
            Constraint.END_BEFORE_START,
        )

    return m.data()


def benchmark(
    instance_loc: Path,
    solver: str,
    time_limit: float,
    log: bool,
    num_workers: int,
):
    instance = read(instance_loc)
    data = instance2data(instance)
    result = solve(data, solver, time_limit, log, num_workers)
    print(result)


def main():
    benchmark(**vars(parse_args()))


if __name__ == "__main__":
    main()
