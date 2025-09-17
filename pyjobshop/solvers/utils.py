from collections import defaultdict
from itertools import pairwise, product

import numpy as np
from ortools.sat.python.cp_model import Domain

from pyjobshop.ProblemData import ProblemData

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


def merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]:
    """
    Merges overlapping intervals into non-overlapping ones.

    Parameters
    ----------
    intervals
        A list of (start, end) tuples representing intervals.

    Returns
    -------
    list[tuple[int, int]]
        A list of merged non-overlapping intervals, sorted by start time.
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


def analyze_break_domains(
    breaks: list[tuple[int, int]], task_duration: int
) -> dict[int, Domain]:
    """
    Analyzes breaks to determine how much time a task overlaps with breaks.
    This function partitions the task start times into domains based on the
    total break overlap.

    Parameters
    ----------
    breaks
        A list of (start, end) tuples representing breaks.
    task_duration
        The duration of the task to be scheduled.

    Returns
    -------
    dict[int, Domain]
        A dict mapping duration to domains, where each domain represents
        the possible start times for the task that has total break overlap
        of the given duration.
    """
    # Find critical points. This is the earliest time that starting this
    # task will result in overlap with the considered break. We process breaks
    # in reverse order to account for previous breaks that would also overlap.
    break_intervals = [(start, end) for start, end in breaks]
    reversed_breaks = list(reversed(break_intervals))
    critical_intervals = []

    for idx, (start, _) in enumerate(reversed_breaks):
        point = max(0, start - task_duration + 1)
        for prev_start, prev_end in reversed_breaks[idx + 1 :]:
            if point < prev_end:
                # This previous break overlaps with the current critical point
                # so we need to move the critical point back by the duration.
                prev_duration = prev_end - prev_start
                point = max(0, point - prev_duration)
            else:
                break

        # If a task starts in this interval, it will overlap with this break.
        critical_intervals.append((point, start))

    # Next, we partition the start times. We identify all breakpoints and
    # analyze the segments between them, finding which breaks will be
    # overlapped if the task starts in that segment.
    partition = defaultdict(list)
    breakpoints = sorted(set(p for cp in critical_intervals for p in cp))

    for point1, point2 in pairwise(breakpoints):
        segment = (point1, point2)
        overlapping = []

        for idx, (earliest, latest) in enumerate(critical_intervals):
            if earliest <= segment[0] and segment[1] <= latest:
                overlapping.append(reversed_breaks[idx])

        if overlapping:
            total_duration = sum(end - start for (start, end) in overlapping)
            partition[total_duration].append(segment)

    domains = {}
    for duration, intervals in partition.items():
        # Convert half-open to closed intervals, which represent the domain.
        closed = [[start, end - 1] for start, end in intervals]
        domains[duration] = Domain.from_intervals(closed)

    domain = Domain.from_intervals([])  # empty
    for other in domains.values():
        domain = Domain.union_with(domain, other)
    domains[0] = domain.complement()

    # Postprocess to exclude start times to fall within breaks.
    def subtract(dom1, dom2):
        # A - B = A \cap complement(B)
        return dom1.intersection_with(dom2.complement())

    breaks_domain = Domain.from_intervals(
        [[start, end - 1] for (start, end) in breaks]
    )
    for duration, domain in domains.items():
        domains[duration] = subtract(domain, breaks_domain)

    return domains
