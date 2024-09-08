# Patterson format
# Project scheduling format
# PSPLIB format

import re
from dataclasses import dataclass
from typing import NamedTuple


class Mode(NamedTuple):
    job: int
    duration: int
    demands: list[int]


def _find(lines: list[str], pattern: str) -> int:
    for idx, line in enumerate(lines):
        if pattern in line:
            return idx

    raise ValueError(f"Pattern '{pattern}' not found in lines.")


@dataclass(frozen=True)
class Instance:
    """
    MMLIB - these are slightly different from the PSPlIB format

    Problem instance class based on PSPLIB files.

    Code taken from:
    https://alns.readthedocs.io/en/latest/examples/resource_constrained_project_scheduling_problem.html
    """

    num_jobs: int  # jobs in RCPSP are tasks in PyJobshop
    num_resources: int
    successors: list[list[int]]
    predecessors: list[list[int]]
    modes: list[Mode]
    capacities: list[int]
    renewable: list[bool]

    @classmethod
    def read_instance(cls, path: str) -> "Instance":
        """
        Reads an instance of the RCPSP from a file.
        Assumes the data is in the PSPLIB format.
        """
        with open(path) as fh:
            lines = fh.readlines()

        prec_idx = _find(lines, "PRECEDENCE RELATIONS")
        req_idx = _find(lines, "REQUESTS/DURATIONS")
        avail_idx = _find(lines, "AVAILABILITIES")

        successors = []

        for line in lines[prec_idx + 2 : req_idx - 1]:
            _, _, _, *jobs = re.split(r"\s+", line)
            successors.append([int(x) - 1 for x in jobs if x])

        predecessors: list[list[int]] = [[] for _ in range(len(successors))]
        for job in range(len(successors)):
            for succ in successors[job]:
                predecessors[succ].append(job)

        mode_data = [
            re.split(r"\s+", line.strip())
            for line in lines[req_idx + 3 : avail_idx - 2]
        ]

        # Prepend the job index to mode data lines if it is missing.
        for idx in range(len(mode_data)):
            if idx == 0:
                continue

            prev = mode_data[idx - 1]
            curr = mode_data[idx]

            if len(curr) < len(prev):
                curr = prev[:1] + curr
                mode_data[idx] = curr

        modes = []
        for mode in mode_data:
            job_idx, _, duration, *consumption = mode
            demands = list(map(int, consumption))
            modes.append(Mode(int(job_idx) - 1, int(duration), demands))

        _, *avail, _ = re.split(r"\s+", lines[avail_idx + 2])
        capacities = list(map(int, avail))

        renewable = [
            x == "R"
            for x in lines[avail_idx + 1].strip().split()
            if x in ["R", "N"]  # R: renewable, N: non-renewable
        ]

        return Instance(
            int(job_idx),
            len(capacities),
            successors,
            predecessors,
            modes,
            capacities,
            renewable,
        )


if __name__ == "__main__":
    from pathlib import Path

    import tqdm

    from pyjobshop import Model

    instances = []
    instances += list(Path("tmp/MMLIB/").rglob("*.mm"))
    instances += list(Path("tmp/RCPLIB(1)/PSPLIB").rglob("*.sm"))

    for loc in tqdm.tqdm(instances):
        if loc.name.startswith("."):  # dotfiles
            continue

        instance = Instance.read_instance(loc)
        continue
        model = Model()

        # Not necessary to define jobs, but it will add coloring to the plot.
        jobs = [model.add_job() for _ in range(instance.num_jobs)]
        tasks = [
            model.add_task(job=jobs[idx]) for idx in range(instance.num_jobs)
        ]
        resources = [
            model.add_machine(capacity=capacity, renewable=renewable)
            for capacity, renewable in zip(
                instance.capacities, instance.renewable
            )
        ]

        for idx, duration, demands in instance.modes:
            model.add_mode(tasks[idx], resources, duration, demands)

        for idx in range(instance.num_jobs):
            task = tasks[idx]

            for pred in instance.predecessors[idx]:
                model.add_end_before_start(tasks[pred], task)

            for succ in instance.successors[idx]:
                model.add_end_before_start(task, tasks[succ])

        data = model.data()
        result = model.solve(time_limit=10, display=False)

        print(loc, result.objective, result.runtime)
