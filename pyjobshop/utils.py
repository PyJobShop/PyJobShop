import bisect

from pyjobshop.ProblemData import ProblemData


def compute_min_max_durations(
    data: ProblemData,
) -> tuple[list[int], list[int]]:
    """
    Compute the minimum and maximum durations for each task. This is used to
    improve the duration bounds of the corresponding interval variables.

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
        task, duration = mode.task, mode.duration
        durations[task].append(duration)

    min_durations = [min(durations[task]) for task in range(data.num_tasks)]
    max_durations = [max(durations[task]) for task in range(data.num_tasks)]

    return min_durations, max_durations


def machine2modes(data):
    result = [[] for _ in range(data.num_machines)]
    for idx, mode in enumerate(data.modes):
        bisect.insort(result[mode.machine], idx)
    return result


def task2modes(data):
    result = [[] for _ in range(data.num_tasks)]
    for idx, mode in enumerate(data.modes):
        bisect.insort(result[mode.task], idx)
    return result
