import bisect

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
