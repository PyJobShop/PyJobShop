import argparse
from pathlib import Path

import fjsplib
import numpy as np

import pyjobshop
from pyjobshop import Constraint, Model, solve


def parse_args():
    parser = argparse.ArgumentParser()

    msg = "Location of the instance file."
    parser.add_argument("instances", nargs="+", type=Path, help=msg)

    msg = "Solver to use."
    parser.add_argument(
        "--solver",
        type=str,
        default="ortools",
        choices=["ortools", "cpoptimizer"],
        help=msg,
    )

    msg = "Time limit for solving the instance, in seconds."
    parser.add_argument(
        "--time_limit", type=float, default=float("inf"), help=msg
    )

    msg = "Whether to log the solver output."
    parser.add_argument("--log", action="store_true", help=msg)

    msg = "Number of workers to use for parallel solving."
    parser.add_argument("--num_workers", type=int, default=8, help=msg)

    return parser.parse_args()


def tabulate(headers: list[str], rows: np.ndarray) -> str:
    """
    Creates a simple table from the given header and row data.
    """
    # These lengths are used to space each column properly.
    lens = [len(header) for header in headers]

    for row in rows:
        for idx, cell in enumerate(row):
            lens[idx] = max(lens[idx], len(str(cell)))

    header = [
        "  ".join(f"{hdr:<{ln}s}" for ln, hdr in zip(lens, headers)),
        "  ".join("-" * ln for ln in lens),
    ]

    content = [
        "  ".join(f"{c!s:>{ln}s}" for ln, c in zip(lens, r)) for r in rows
    ]

    return "\n".join(header + content)


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

    m.set_planning_horizon(4500)
    return m.data()


def _solve(
    instance_loc: Path,
    solver: str,
    time_limit: float,
    log: bool,
    num_workers: int,
) -> tuple[str, bool, float, float]:
    """
    Solves a single instance.
    """
    instance = fjsplib.read(instance_loc)
    data = instance2data(instance)
    result = solve(data, solver, time_limit, log, num_workers)

    return (
        instance_loc.name,
        result.status.value in ["Optimal", "Feasible"],
        result.objective,
        round(result.runtime, 2),
    )


def benchmark(instances: list[Path], **kwargs):
    results = [_solve(instance, **kwargs) for instance in instances]
    dtypes = [
        ("inst", "U37"),
        ("feas", "U1"),
        ("obj", float),
        ("time", float),
    ]

    data = np.asarray(results, dtype=dtypes)
    headers = ["Instance", "Feas.", "Obj.", "Time (s)"]

    print("\n", tabulate(headers, data), "\n", sep="")
    print(f"     Avg. objective: {data['obj'].mean():.0f}")
    print(f"      Avg. run-time: {data['time'].mean():.2f}s")
    print(f"       Total infeas: {np.count_nonzero(data['feas'])}")


def main():
    benchmark(**vars(parse_args()))


if __name__ == "__main__":
    main()
