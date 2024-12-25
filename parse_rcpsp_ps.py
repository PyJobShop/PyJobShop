import re
from dataclasses import dataclass
from pathlib import Path
from typing import Union

from pyjobshop import Model


def natural_keys(text):
    text = text.stem
    return [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", text)]


@dataclass
class Resource:
    capacity: int
    renewable: bool


@dataclass
class Task:
    duration: int
    demands: list[int]
    successors: list[int]
    groups: list[list[int]]
    optional: bool


@dataclass
class ProjectInstance:
    resources: list[Resource]
    tasks: list[Task]


def parse_rcpsp_ps(instance_loc: Union[str, Path]):
    with open(instance_loc, "r") as fh:
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    num_activities, num_renewable, num_non_renewable = map(
        int, next(lines).split()
    )
    capacities = list(map(int, next(lines).split()))
    fixed = list(map(int, next(lines).split()))

    resources = [
        Resource(capacity, idx < num_renewable)
        for idx, capacity in enumerate(capacities)
    ]
    tasks = []

    for idx in range(num_activities):
        duration, *demands = map(int, next(lines).split())
        line = map(int, next(lines).split())

        groups = []
        num_groups = next(line)
        for _ in range(num_groups):
            num_successors = next(line)
            groups.append([next(line) for _ in range(num_successors)])

        num_successors, *successors = map(int, next(lines).split())
        tasks.append(
            Task(
                duration,
                demands,
                successors,
                groups,
                optional=idx not in fixed,
            )
        )

    return ProjectInstance(resources, tasks)


if __name__ == "__main__":
    loc = "tmp/rcpsp-ps/instances/ASLIB0"
    path = Path(loc)
    # for instance_loc in sorted(path.rglob("*.txt"), key=natural_keys):
    for idx in range(975, 36000):
        instance_loc = path / f"aslib0_{idx}a.txt"
        instance = parse_rcpsp_ps(instance_loc)

        model = Model()

        for res in instance.resources:
            model.add_resource(capacity=res.capacity, renewable=res.renewable)

        tasks = [
            model.add_task(optional=task.optional) for task in instance.tasks
        ]
        groups = {}

        for idx, task_data in enumerate(instance.tasks):
            if (idx,) not in groups:
                groups[(idx,)] = model.add_task_group(
                    [tasks[idx]], optional=True
                )

            for group in task_data.groups:
                if tuple(group) not in groups:
                    succs = [model.tasks[succ] for succ in group]
                    groups[tuple(group)] = model.add_task_group(
                        succs, optional=True, mutually_exclusive=True
                    )

        for idx, task_data in enumerate(instance.tasks):
            model.add_mode(
                tasks[idx],
                model.resources,
                task_data.duration,
                task_data.demands,
            )

            for succ in task_data.successors:
                model.add_end_before_start(tasks[idx], model.tasks[succ])

            for successors in task_data.groups:
                group1 = groups[(idx,)]
                group2 = groups[tuple(successors)]
                model.add_if_then(group1, group2)

        result = model.solve(
            display=True, time_limit=1000, solver="cpoptimizer"
        )
        # result = model.solve(display=True, time_limit=1000, solver="ortools")

        res = (
            instance_loc.stem,
            result.objective,
            result.status,
            round(result.runtime, 2),
        )

        print(res)
        with open("other2.txt", "a") as fh:
            fh.write(" ".join(map(str, res)) + "\n")
