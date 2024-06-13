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
    for (_, task), duration in data.processing_times.items():
        durations[task].append(duration)

    min_durations, max_durations = [], []
    for task in range(data.num_tasks):
        if durations[task]:
            min_durations.append(min(durations[task]))
            max_durations.append(max(durations[task]))
        else:  # TODO This is a strange case, see #135.
            min_durations.append(0)
            max_durations.append(data.horizon)

    return min_durations, max_durations
