import re
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import networkx as nx
from psplib.ProjectInstance import Mode, Project, ProjectInstance, Resource

from pyjobshop import Model


def natural_keys(text):
    text = text.stem
    return [int(c) if c.isdigit() else c for c in re.split(r"(\d+)", text)]


@dataclass
class Activity:
    modes: list[Mode]
    successors: list[int]
    groups: list[list[int]]  # new
    optional: bool  # new


def parse_rcpsp_ps(instance_loc: Union[str, Path]):
    """
    Parses a RCPSP-PS formatted instance from Van der Beek et al. (2024).
    """
    with open(instance_loc, "r") as fh:
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    num_activities, num_renewable, _ = map(int, next(lines).split())
    capacities = list(map(int, next(lines).split()))
    fixed = list(map(int, next(lines).split()))

    resources = [
        Resource(capacity, idx < num_renewable)
        for idx, capacity in enumerate(capacities)
    ]
    activities = []

    for idx in range(num_activities):
        duration, *demands = map(int, next(lines).split())
        line = map(int, next(lines).split())

        groups = []
        num_groups = next(line)
        for _ in range(num_groups):
            num_successors = next(line)
            groups.append([next(line) for _ in range(num_successors)])

        num_successors, *successors = map(int, next(lines).split())
        activities.append(
            Activity(
                [Mode(duration, demands)],
                successors,
                groups,
                optional=idx not in fixed,
            )
        )

    project = Project(list(range(num_activities)))
    return ProjectInstance(resources, [project], activities)


def check_solution(solution, instance):
    """
    Check that there is indeed an (s, t)-path with present activities.
    """
    present = [idx for idx, task in enumerate(solution.tasks) if task.present]

    G = nx.DiGraph()
    for idx, activity in enumerate(instance.activities):
        for succ in activity.successors:
            if idx in present and succ in present:
                G.add_edge(idx, succ)

    source = 0
    target = len(instance.activities) - 1
    nx.shortest_path(G, source, target)


if __name__ == "__main__":
    loc = "tmp/rcpsp-ps/instances/ASLIB0"
    path = Path(loc)
    # for instance_loc in sorted(path.rglob("*.txt"), key=natural_keys):
    for idx in range(0, 36000):
        instance_loc = path / f"aslib0_{idx}a.txt"
        instance = parse_rcpsp_ps(instance_loc)

        model = Model()

        for res in instance.resources:
            if res.renewable:
                model.add_renewable(capacity=res.capacity)
            else:
                model.add_non_renewable(capacity=res.capacity)

        tasks = [
            model.add_task(optional=activity.optional)
            for activity in instance.activities
        ]

        for idx, activity in enumerate(instance.activities):
            model.add_mode(
                tasks[idx],
                model.resources,
                activity.modes[0].duration,
                activity.modes[0].demands,
            )

            for succ in activity.successors:
                model.add_end_before_start(tasks[idx], model.tasks[succ])

            for successors in activity.groups:
                model.add_if_then(
                    tasks[idx], [tasks[succ] for succ in successors]
                )

        result = model.solve(display=False, time_limit=100, solver="ortools")

        res = (
            instance_loc.stem,
            result.objective,
            result.status,
            round(result.runtime, 2),
        )

        print(res)
        with open("other2.txt", "a") as fh:
            fh.write(" ".join(map(str, res)) + "\n")

        check_solution(result.best, instance)
