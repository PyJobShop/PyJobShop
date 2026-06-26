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

    The algorithm works in three steps:

    1. **Critical intervals**: For each break, compute the range of task start
       times that would cause the task to overlap with that break. A task
       overlaps a break ``[b_s, b_e)`` if it starts before ``b_s`` and its
       processing (plus any earlier overlapping breaks) extends past ``b_s``.
       The critical interval for a break is ``[earliest_start, b_s)``.

    2. **Partitioning**: The boundaries of all critical intervals form a set
       of breakpoints that divide the timeline into sub-intervals. For each
       sub-interval, determine which breaks' critical intervals contain it.
       The total overlap duration is the sum of those breaks' durations.

    3. **Domain construction**: Group sub-intervals by their total overlap
       duration into ``Domain`` objects. Start times not covered by any
       critical interval have zero overlap. Finally, exclude start times
       that fall inside breaks themselves.

    Example
    -------
    Consider breaks ``[(5, 8), (12, 14)]`` and ``task_duration = 10``.
    A task starting at time 0 spans ``[0, 10)`` and overlaps break
    ``[5, 8)`` for 3 units. A task starting at 3 spans ``[3, 13)`` and
    overlaps both breaks for ``3 + 1 = 4`` units. The function returns a
    mapping like ``{0: Domain(...), 3: Domain(...), 4: Domain(...), ...}``.

    Parameters
    ----------
    breaks
        A list of (start, end) tuples representing break intervals.
        Must be non-overlapping and sorted.
    task_duration
        The processing duration of the task to be scheduled.

    Returns
    -------
    dict[int, Domain]
        Mapping from break_overlap_duration -> valid_start_time_domain.
        Each domain contains all start times that result in the given overlap.
    """
    # For each break, compute the critical interval: the range of start
    # times for which the task would overlap with that break. We process
    # breaks in reverse order to account for earlier breaks that extend
    # the task's span (a task that overlaps an earlier break takes longer,
    # making it more likely to also overlap later breaks).
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

    # Partition the start times. The boundaries of all critical intervals
    # form a sorted set of breakpoints that divide the timeline into
    # sub-intervals. For each sub-interval, we check which breaks' critical
    # intervals fully contain it, and sum their durations to get the total
    # overlap.
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
