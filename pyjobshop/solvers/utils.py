from itertools import product

import numpy as np

from pyjobshop.ProblemData import ProblemData


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


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merges overlapping or touching intervals.

    Parameters
    ----------
    intervals
        A list of (start, end) tuples representing time intervals.

    Returns
    -------
    list[tuple[int, int]]
        A list of merged intervals, such that no interval overlaps or touches,
        sorted by start time.
    """
    intervals = sorted(intervals)
    merged: list[tuple[int, int]] = []

    for start, end in intervals:
        if not merged or start > merged[-1][1]:
            merged.append((start, end))  # no overlap
        else:
            new_end = max(merged[-1][1], end)  # overlap -> merge with last
            merged[-1] = (merged[-1][0], new_end)

    return merged
