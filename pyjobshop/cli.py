import argparse
import warnings
from functools import partial
from multiprocessing import cpu_count
from pathlib import Path
from typing import Optional

import numpy as np
import tomli
from tqdm.contrib.concurrent import process_map

from pyjobshop import read, solve


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

    msg = "Whether to display the solver output."
    parser.add_argument("--display", action="store_true", help=msg)

    msg = (
        "Number of worker threads to use for solving a single instance."
        "Default is the number of available CPU cores."
    )
    parser.add_argument("--num_workers_per_instance", type=int, help=msg)

    msg = "Number of instances to solve in parallel. Default is 1."
    parser.add_argument(
        "--num_parallel_instances", type=int, default=1, help=msg
    )

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


def _solve(
    instance_loc: Path,
    solver: str,
    time_limit: float,
    display: bool,
    num_workers_per_instance: int,
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

    data = read(instance_loc)
    result = solve(
        data, solver, time_limit, display, num_workers_per_instance, **params
    )

    return (
        instance_loc.name,
        result.status.value,
        result.objective,
        round(result.runtime, 2),
    )


def _check_cpu_usage(
    num_parallel_instances: int, num_workers_per_instance: Optional[int]
):
    """
    Warns if the number of workers per instance times the number of parallel
    instances is greater than the number of available CPU cores
    """
    num_cpus = cpu_count()
    num_workers_per_instance = (
        num_workers_per_instance
        if num_workers_per_instance is not None
        else num_cpus  # uses all CPUs if not set
    )

    if num_workers_per_instance * num_parallel_instances > num_cpus:
        warnings.warn(
            f"Number of workers per instance ({num_workers_per_instance}) "
            f"times number of parallel instances ({num_parallel_instances}) "
            f"is greater than the number of available CPU cores ({num_cpus}). "
            "This may lead to suboptimal performance.",
            stacklevel=2,
        )


def benchmark(instances: list[Path], num_parallel_instances: int, **kwargs):
    """
    Solves the list of instances and prints a table of the results.
    """
    _check_cpu_usage(
        num_parallel_instances, kwargs.get("num_workers_per_instance")
    )

    args = sorted(instances)
    func = partial(_solve, **kwargs)

    if len(instances) == 1:
        results = [func(args[0])]
    else:
        results = process_map(
            func, args, max_workers=num_parallel_instances, unit="instance"
        )

    dtypes = [
        ("inst", "U37"),
        ("feas", "U37"),
        ("obj", float),
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
