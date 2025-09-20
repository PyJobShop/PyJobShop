from collections import defaultdict
from itertools import pairwise

from ortools.sat.python.cp_model import Domain

from pyjobshop.constants import MAX_VALUE


def partition_task_start_by_break_overlap(
    breaks: list[tuple[int, int]], task_duration: int
) -> dict[int, Domain]:
    """
    Partitions task start times based on the total break overlap duration.

    This function partitions all possible start times into equivalence classes,
    where start times in the same class result in the same total duration of
    overlap with breaks. The partitioning accounts for tasks that may span
    multiple breaks.

    Parameters
    ----------
    breaks
        A list of (start, end) tuples representing break intervals.
        Must be non-overlapping and sorted.
    task_duration
        The duration of the task to be scheduled.

    Returns
    -------
    dict[int, Domain]
        Mapping from break_overlap_duration -> valid_start_time_domain.
        Each domain contains all start times that result in the given overlap.
    """
    # Find critical points. This is the earliest time that starting this
    # task will result in overlap with the considered break. We process breaks
    # in reverse order to account for previous breaks that would also overlap.
    reversed_breaks = list(reversed(breaks))
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
    # analyze the intervals between them. For each interval, we check if it is
    # contained in a break's critical interval, which then determines the total
    # overlap duration.
    partition = defaultdict(list)
    breakpoints = sorted(
        set(point for points in critical_intervals for point in points)
    )

    for interval in pairwise(breakpoints):
        overlapping = []

        for brk, crit in zip(reversed_breaks, critical_intervals):
            if crit[0] <= interval[0] and interval[1] <= crit[1]:
                overlapping.append(brk)

        if overlapping:
            total_duration = sum(end - start for (start, end) in overlapping)
            partition[total_duration].append(interval)

    # Now convert each partition to a Domain object, which is equivalent to
    # the closed interval.
    domains = {
        dur: Domain.from_intervals([[s, e - 1] for s, e in intervals])
        for dur, intervals in partition.items()
    }

    # Include the zero-overlap domain as the complement of all others.
    domain = Domain.from_intervals([])
    for other in domains.values():
        domain = Domain.union_with(domain, other)
    domain = domain.complement()
    domains[0] = domain.intersection_with(Domain(0, MAX_VALUE))

    # Postprocess to exclude start times to fall within breaks.
    breaks_domain = Domain.from_intervals([[s, e - 1] for s, e in breaks])
    return {
        dur: domain.intersection_with(breaks_domain.complement())  # \setminus
        for dur, domain in domains.items()
    }
