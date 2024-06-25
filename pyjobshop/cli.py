import argparse
from pathlib import Path
from typing import Optional

import fjsplib
import numpy as np
import tomli
from progiter import ProgIter

import pyjobshop
from pyjobshop import Model, solve


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
    parser.add_argument("--num_workers", type=int, help=msg)

    msg = """
    Optional parameter configuration file (in TOML format). These parameters
    are passed to the solver as additional solver parameters.
    """
    parser.add_argument("--config_loc", type=Path, help=msg)

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
                m.add_processing_time(task, machines[machine_idx], duration)

    for frm, to in instance.precedences:
        m.add_end_before_start(m.tasks[frm], m.tasks[to])

    return m.data()


def _solve(
    instance_loc: Path,
    solver: str,
    time_limit: float,
    log: bool,
    num_workers: int,
    config_loc: Optional[Path],
) -> tuple[str, str, float, float]:
    """
    Solves a single instance.
    """
    if config_loc is not None:
        with open(config_loc, "rb") as fh:
            params = tomli.load(fh)
    else:
        params = {}

    instance = fjsplib.read(instance_loc)
    data = instance2data(instance)
    result = solve(data, solver, time_limit, log, num_workers, **params)

    return (
        instance_loc.name,
        result.status.value,
        result.objective,
        round(result.runtime, 2),
    )


def benchmark(instances: list[Path], **kwargs):
    """
    Solves the list of instances and prints a table of the results.
    """
    results = [_solve(instance, **kwargs) for instance in ProgIter(instances)]

    dtypes = [
        ("inst", "U37"),
        ("feas", "U37"),
        ("obj", int),
        ("time", float),
    ]
    data = np.asarray(results, dtype=dtypes)
    headers = ["Instance", "Status", "Obj.", "Time (s)"]

    avg_objective = data["obj"].mean()
    avg_runtime = data["time"].mean()
    num_optimal = np.count_nonzero(data["feas"] == "Optimal")
    num_feas = np.count_nonzero(data["feas"] == "Feasible") + num_optimal
    num_infeas = np.count_nonzero(data["feas"].size - num_feas)

    print("\n", tabulate(headers, data), "\n", sep="")
    print(f"     Avg. objective: {avg_objective:.2f}")
    print(f"      Avg. run-time: {avg_runtime:.2f}s")
    print(f"      Total optimal: {num_optimal}")
    print(f"       Total infeas: {num_infeas}")


def main():
    benchmark(**vars(parse_args()))


if __name__ == "__main__":
    main()
