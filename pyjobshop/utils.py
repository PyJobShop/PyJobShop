import bisect
from collections import defaultdict
from itertools import product

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


def machine2modes(data: ProblemData) -> list[list[int]]:
    """
    Returns the list of mode indices corresponding to each machine.

    Parameters
    ----------
    data
        The problem data instance.

    Returns
    -------
    list[list[int]]
        The list of mode indices for each machine.
    """
    result: list[list[int]] = [[] for _ in range(data.num_machines)]
    for idx, mode in enumerate(data.modes):
        for resource in mode.resources:
            bisect.insort(result[resource], idx)
    return result


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
        bisect.insort(result[mode.task], idx)
    return result


# --- ConstraintManager utilities ---


def find_modes_with_intersecting_machines(
    data: ProblemData, task1: int, task2: int
) -> list[tuple[int, int, list[int]]]:
    """
    Finds the intersection of machines for modes associated with two tasks.
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
        task and the machines they have in common.
    """
    modes1 = [mode for mode in data.modes if mode.task == task1]
    modes2 = [mode for mode in data.modes if mode.task == task2]
    intersecting = []

    for mode1 in modes1:
        machines1 = set(mode1.resources)
        for mode2 in modes2:
            in_common = sorted(machines1.intersection(set(mode2.resources)))
            if in_common:
                idx1 = data.modes.index(mode1)
                idx2 = data.modes.index(mode2)
                intersecting.append((idx1, idx2, in_common))

    return intersecting


def find_modes_with_identical_machines(
    data: ProblemData, task1: int, task2: int
) -> dict[int, list[int]]:
    """
    Finds the modes with identical machines for two tasks.

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
        identical machines.
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


def find_modes_with_disjoint_machines(
    data: ProblemData, task1: int, task2: int
) -> dict[int, list[int]]:
    """
    Finds the modes with disjoint machines for two tasks.

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
        disjoint machines.
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
