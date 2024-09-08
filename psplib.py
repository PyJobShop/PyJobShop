import re
from dataclasses import dataclass
from typing import NamedTuple


def _find(lines: list[str], pattern: str) -> int:
    for idx, line in enumerate(lines):
        if pattern in line:
            return idx

    raise ValueError(f"Pattern '{pattern}' not found in lines.")


@dataclass
class Mode:
    duration: int
    demands: list[int]


@dataclass
class Activity:
    successors: list[int]
    modes: list[Mode]


class Resource(NamedTuple):
    capacity: int
    renewable: bool


@dataclass(frozen=True)
class Instance:
    """
    Problem instance class based on PSPLIB files.
    Multi-mode resource- project scheduling.

    Code taken from:
    https://alns.readthedocs.io/en/latest/examples/resource_constrained_project_scheduling_problem.html
    """

    num_jobs: int  # jobs in RCPSP are tasks in PyJobshop
    num_resources: int
    resources: list[Resource]
    activities: list[Activity]

    @classmethod
    def read_instance(cls, path: str) -> "Instance":
        """
        Reads an instance of the RCPSP from a file.
        Assumes the data is in the PSPLIB format.
        """
        with open(path) as fh:
            lines = [line.strip() for line in fh.readlines() if line.strip()]

        prec_idx = _find(lines, "PRECEDENCE RELATIONS")
        req_idx = _find(lines, "REQUESTS/DURATIONS")
        avail_idx = _find(lines, "AVAILABILITIES")

        capacities = list(map(int, re.split(r"\s+", lines[avail_idx + 2])))
        renewable = [
            char == "R"
            for char in lines[avail_idx + 1].strip().split()
            if char in ["R", "N"]  # R: renewable, N: non-renewable
        ]
        resources = [
            Resource(capacity, is_renewable)
            for capacity, is_renewable in zip(capacities, renewable)
        ]
        num_resources = len(resources)

        mode_data = [
            list(map(int, re.split(r"\s+", line)))
            for line in lines[req_idx + 3 : avail_idx - 1]
        ]

        mode_idx = 0
        activities = []
        for line in lines[prec_idx + 2 : req_idx - 1]:
            _, num_modes, _, *jobs = list(map(int, re.split(r"\s+", line)))
            successors = [val - 1 for val in jobs if val]

            modes = []
            for idx in range(mode_idx, mode_idx + num_modes):
                data = mode_data[idx]
                demands = data[-num_resources:]
                duration = data[-num_resources - 1]
                modes.append(Mode(duration, demands))
                mode_idx += 1

            activities.append(Activity(successors, modes))

        return Instance(len(activities), len(resources), resources, activities)


if __name__ == "__main__":
    from pathlib import Path

    import tqdm

    from pyjobshop import Model

    instances = []
    # instances += list(Path("tmp/MMLIB/").rglob("*.mm"))
    # instances += list(Path("tmp/RCPLIB(1)/PSPLIB").rglob("*.sm"))
    instances += list(Path("tmp/PSPLIB").rglob("*.[sm]m"))

    for loc in tqdm.tqdm(instances):
        if loc.name.startswith("."):  # dotfiles
            continue

        if not loc.is_file():
            continue

        instance = Instance.read_instance(loc)
        breakpoint()
        model = Model()

        # Not necessary to define jobs, but it will add coloring to the plot.
        resources = [
            model.add_machine(
                capacity=resource.capacity, renewable=resource.renewable
            )
            for resource in (instance.resources)
        ]

        for idx in range(instance.num_jobs):
            job = model.add_job()
            task = model.add_task(job=job)

            for mode in instance.activities[idx].modes:
                model.add_mode(task, resources, mode.duration, mode.demands)

        for idx in range(instance.num_jobs):
            task = model.tasks[idx]

            for succ in instance.activities[idx].successors:
                model.add_end_before_start(task, model.tasks[succ])

        data = model.data()
        result = model.solve(time_limit=10, display=False)

        print(loc, result.objective, result.runtime)
