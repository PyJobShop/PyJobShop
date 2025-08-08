from collections import defaultdict
from dataclasses import dataclass
from itertools import product

import numpy as np

from pyjobshop.ProblemData import ProblemData


def compute_task_durations(data: ProblemData) -> list[list[int]]:
    """
    Computes the set of processing time durations belong to each task. This is
    used to restrict the domain of the corresponding interval variables.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    tuple[list[int], list[int]]
        The minimum and maximum durations for each task.
    """
    durations: list[list[int]] = [[] for _ in range(data.num_tasks)]
    for mode in data.modes:
        durations[mode.task].append(mode.duration)

    return durations


# --- Constraints utilities ---


def identical_modes(
    data: ProblemData, task1: int, task2: int
) -> list[tuple[int, list[int]]]:
    """
    Returns the mode combinations with identical resources for both tasks.
    Helper function for the identical resources constraints.

    Parameters
    ----------
    data
        The problem data instance.
    task1
        The first task index.
    task2
        The second task index.

    Returns
    -------
    list[tuple[int, list[int]]]
        A list of tuples, one for each mode of the first task. Each tuple
        contains the mode index of the first task and the mode indices of the
        second task that have identical resources. In particular, if a mode of
        the first task has no identical resources with any mode of the second
        task, the list of mode indices of the second task will be empty.
    """
    modes1 = [(idx, m) for idx, m in enumerate(data.modes) if m.task == task1]
    modes2 = [(idx, m) for idx, m in enumerate(data.modes) if m.task == task2]
    result = []

    for idx1, mode1 in modes1:
        res1 = set(mode1.resources)
        idcs2 = [idx for idx, mode2 in modes2 if res1 == set(mode2.resources)]
        result.append((idx1, idcs2))

    return result


def different_modes(
    data: ProblemData, task1: int, task2: int
) -> list[tuple[int, list[int]]]:
    """
    Returns the mode combinations with disjoint resources for both tasks.
    Helper function for the different resources constraints.

    Parameters
    ----------
    data
        The problem data instance.
    task1
        The first task index.
    task2
        The second task index.

    Returns
    -------
    list[tuple[int, list[int]]]
        A list of tuples, one for each mode of the first task. Each tuple
        contains the mode index of the first task and the mode indices of the
        second task that have disjoint resources. In particular, if a mode of
        the first task has no disjoint resources with any mode of the second
        task, the list of mode indices of the second task will be empty.
    """
    modes1 = [(idx, m) for idx, m in enumerate(data.modes) if m.task == task1]
    modes2 = [(idx, m) for idx, m in enumerate(data.modes) if m.task == task2]
    result = []

    for idx1, mode1 in modes1:
        res1 = set(mode1.resources)
        idcs2 = [
            idx for idx, mode2 in modes2 if res1.isdisjoint(mode2.resources)
        ]
        result.append((idx1, idcs2))

    return result


def intersecting_modes(
    data: ProblemData, task1: int, task2: int
) -> list[tuple[int, int, list[int]]]:
    """
    Returns the mode combinations with intersecting resources for both tasks.
    Helper function for the consecutive constraints.

    Parameters
    ----------
    data
        The problem data instance.
    task1
        The first task index.
    task2
        The second task index.

    Returns
    -------
    list[tuple[int, int, list[int]]]
        A list of tuples containing the mode indices of the first and second
        task and the indices of resources they have in common. In particular,
        if two modes have no intersecting resources, the list of common
        resources will be empty.
    """
    modes1 = [(idx, m) for idx, m in enumerate(data.modes) if m.task == task1]
    modes2 = [(idx, m) for idx, m in enumerate(data.modes) if m.task == task2]
    result = []

    for (idx1, mode1), (idx2, mode2) in product(modes1, modes2):
        resources = set(mode1.resources).intersection(set(mode2.resources))
        result.append((idx1, idx2, sorted(resources)))  # sort for determinism

    return result


def setup_times_matrix(data: ProblemData) -> np.ndarray | None:
    """
    Transforms the setup times constraints to a setup times matrix if there
    are setup times, otherwise return None.
    """
    if not data.constraints.setup_times:
        return None

    num_res = len(data.resources)
    num_tasks = len(data.tasks)
    setup = np.zeros((num_res, num_tasks, num_tasks), dtype=int)

    for res, task1, task2, duration in data.constraints.setup_times:
        setup[res, task1, task2] = duration

    return setup


@dataclass
class Component:
    machines: set[int]
    tasks: set[int]


def redundant_cumulative(data: ProblemData) -> list[Component]:
    """
    Find connected components in an undirected graph formed by machines.
    An edge (u, v) exists if there is a task that has two modes
    resources u and v. This is used to determine which resources are

    Parameters
    ----------
    adj_list:
        Dict where keys are nodes and values are sets of neighbors.

    Returns
    -------
    A tuple consisting of two lists, where the first list contains sets of
    machine indices representing connected components, and the second list
    contains the set of task indices that could be assigned to the
    machines of the corresponding component.
    """
    graph = defaultdict(set)

    for task_idx in range(data.num_tasks):
        mode_idcs = data.task2modes(task_idx)
        resource_idcs = {
            res_idx
            for mode_idx in mode_idcs
            for res_idx in data.modes[mode_idx].resources
        }
        machine_idcs = resource_idcs & set(data.machine_idcs)

        for idx1, idx2 in product(machine_idcs, repeat=2):
            graph[idx1].add(idx2)

        for mode_idx1, mode_idx2 in product(mode_idcs, repeat=2):
            resources1 = data.modes[mode_idx1].resources
            resources2 = data.modes[mode_idx2].resources

            for res1 in resources1:
                graph[res1].update(resources2)

    nodes = set(graph.keys())
    visited = set()
    components: list[set[int]] = []

    def dfs(node, component):
        visited.add(node)
        component.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                dfs(neighbor, component)

    for node in nodes:
        if node not in visited:
            component: set[int] = set()
            dfs(node, component)
            components.append(component)

    tasks: list[set[int]] = [set() for _ in components]

    for task_idx in range(data.num_tasks):
        task_modes = data.task2modes(task_idx)
        task_resources = {
            res for mode in task_modes for res in data.modes[mode].resources
        }

        for comp_idx, component in enumerate(components):
            if component & task_resources:
                tasks[comp_idx].add(task_idx)

    return [Component(x, y) for x, y in zip(components, tasks)]
