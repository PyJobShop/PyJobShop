from collections import defaultdict
from itertools import product
from typing import Optional

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


def resource2modes(data: ProblemData) -> list[list[int]]:
    """
    Returns the list of mode indices corresponding to each resource.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    list[list[int]]
        The list of mode indices for each resource.
    """
    result: list[list[int]] = [[] for _ in range(data.num_resources)]

    for idx, mode in enumerate(data.modes):
        for resource in mode.resources:
            result[resource].append(idx)

    return result


def resource2modes_demands(
    data: ProblemData,
) -> tuple[list[list[int]], list[list[int]]]:
    """
    Returns the list of mode indices and the list of corresponding demands
    for each resource.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    tuple[list[list[int]], list[list[int]]]
        The list of mode indices and corresponding demands for each resource.
    """
    modes: list[list[int]] = [[] for _ in range(data.num_resources)]
    demands: list[list[int]] = [[] for _ in range(data.num_resources)]

    for idx, mode in enumerate(data.modes):
        for resource, demand in zip(mode.resources, mode.demands):
            modes[resource].append(idx)
            demands[resource].append(demand)

    return modes, demands


def task2modes(data: ProblemData) -> list[list[int]]:
    """
    Returns the list of mode indices corresponding to each task.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    list[list[int]]
        The list of mode indices for each task.
    """
    result: list[list[int]] = [[] for _ in range(data.num_tasks)]

    for idx, mode in enumerate(data.modes):
        result[mode.task].append(idx)

    return result


# --- Constraints utilities ---


def find_modes_with_intersecting_resources(
    data: ProblemData, task1: int, task2: int
) -> list[tuple[int, int, list[int]]]:
    """
    Finds the intersection of resources for modes associated with two tasks.
    Specific utility function for creating sequencing constraints.

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
        task and the resources they have in common.
    """
    modes1 = [mode for mode in data.modes if mode.task == task1]
    modes2 = [mode for mode in data.modes if mode.task == task2]
    intersecting = []

    for mode1 in modes1:
        resources1 = set(mode1.resources)
        for mode2 in modes2:
            in_common = sorted(resources1.intersection(set(mode2.resources)))
            if in_common:
                idx1 = data.modes.index(mode1)
                idx2 = data.modes.index(mode2)
                intersecting.append((idx1, idx2, in_common))

    return intersecting


def find_modes_with_identical_resources(
    data: ProblemData, task1: int, task2: int
) -> dict[int, list[int]]:
    """
    Finds the modes with identical resources for two tasks.

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
    dict[int, list[int]]
        A dictionary where the keys are the mode indices of the first task
        and the values are the mode indices of the second task that have
        identical resources.
    """
    modes1 = [mode for mode in data.modes if mode.task == task1]
    modes2 = [mode for mode in data.modes if mode.task == task2]

    same = defaultdict(list)
    for mode1, mode2 in product(modes1, modes2):
        if set(mode1.resources) == set(mode2.resources):
            idx1 = data.modes.index(mode1)
            idx2 = data.modes.index(mode2)
            same[idx1].append(idx2)

    return same


def find_modes_with_disjoint_resources(
    data: ProblemData, task1: int, task2: int
) -> dict[int, list[int]]:
    """
    Finds the modes with disjoint resources for two tasks.

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
    dict[int, list[int]]
        A dictionary where the keys are the mode indices of the first task
        and the values are the mode indices of the second task that have
        disjoint resources.
    """
    modes1 = [mode for mode in data.modes if mode.task == task1]
    modes2 = [mode for mode in data.modes if mode.task == task2]

    disjoint = defaultdict(list)
    for mode1, mode2 in product(modes1, modes2):
        if set(mode1.resources).isdisjoint(mode2.resources):
            idx1 = data.modes.index(mode1)
            idx2 = data.modes.index(mode2)
            disjoint[idx1].append(idx2)

    return disjoint


def setup_times_matrix(data: ProblemData) -> Optional[np.ndarray]:
    """
    Transforms the setup times constraints to a setup times matrix if there
    are setup times, otherwise return None.
    """
    if data.constraints.setup_times is None:
        return None

    num_res = len(data.resources)
    num_tasks = len(data.tasks)
    setup = np.zeros((num_res, num_tasks, num_tasks), dtype=int)

    for res, task1, task2, duration in data.constraints.setup_times:
        setup[res, task1, task2] = duration

    return setup
