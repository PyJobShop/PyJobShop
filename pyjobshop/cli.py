import argparse
import warnings
from functools import partial
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np
import tomli
from tqdm.contrib.concurrent import process_map

from pyjobshop import Result, read, solve
from pyjobshop.read import InstanceFormat


def parse_args():
    parser = argparse.ArgumentParser()

    msg = "Location of the instance file."
    parser.add_argument("instances", nargs="+", type=Path, help=msg)

    msg = "File format of the instance."
    parser.add_argument(
        "--instance_format",
        type=InstanceFormat,
        default=InstanceFormat.FJSPLIB,
        choices=[f.value for f in InstanceFormat],
        help=msg,
    )

    msg = "Directory to store best-found solutions (one file per instance)."
    parser.add_argument("--sol_dir", type=Path, help=msg)

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


def write_solution(instance_loc: Path, sol_dir: Path, result: Result):
    with open(sol_dir / (instance_loc.stem + ".sol"), "w") as fh:
        fh.write(f"instance: {instance_loc.name}\n")
        fh.write(f"status: {result.status.value}\n")
        fh.write(f"objective: {result.objective}\n")
        fh.write(f"lower_bound: {result.lower_bound}\n")
        fh.write(f"runtime: {result.runtime}\n")
        fh.write("\n")

        fh.write("task,mode,start,end\n")
        for idx, task in enumerate(result.best.tasks):
            if task is not None:
                fh.write(f"{idx},{task.mode},{task.start},{task.end}\n")
            else:
                fh.write(f"{idx},-1,-1,-1\n")


def _solve(
    instance_loc: Path,
    instance_format: InstanceFormat,
    solver: str,
    time_limit: float,
    display: bool,
    num_workers_per_instance: int,
    config_loc: Path | None,
    sol_dir: Path | None,
) -> tuple[str, str, float, float, float]:
    """
    Solves a single instance.
    """
    if config_loc is not None:
        with open(config_loc, "rb") as fh:
            params = tomli.load(fh)
    else:
        params = {}

    data = read(instance_loc, instance_format=instance_format)
    result = solve(
        data=data,
        solver=solver,
        time_limit=time_limit,
        display=display,
        num_workers=num_workers_per_instance,
        **params,
    )
    if sol_dir:
        sol_dir.mkdir(parents=True, exist_ok=True)  # just in case
        write_solution(instance_loc, sol_dir, result)

    return (
        instance_loc.name,
        result.status.value,
        result.objective,
        result.lower_bound,
        round(result.runtime, 2),
    )


def _check_cpu_usage(
    num_parallel_instances: int, num_workers_per_instance: int | None
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
        ("status", "U37"),
        ("obj", float),
        ("lb", float),
        ("time", float),
    ]
    data = np.asarray(results, dtype=dtypes)
    headers = ["Instance", "Status", "Obj.", "LB", "Time (s)"]

    avg_objective = data["obj"].mean()
    avg_runtime = data["time"].mean()

    num_instances = data["status"].size
    num_optimal = np.count_nonzero(data["status"] == "Optimal")
    num_feas = np.count_nonzero(data["status"] == "Feasible") + num_optimal
    num_infeas = num_instances - num_feas

    print("\n", tabulate(headers, data), "\n", sep="")
    print(f"     Avg. objective: {avg_objective:.2f}")
    print(f"      Avg. run-time: {avg_runtime:.2f}s")
    print(f"      Total optimal: {num_optimal}")
    print(f"       Total infeas: {num_infeas}")


def main():
    benchmark(**vars(parse_args()))


if __name__ == "__main__":
    main()
