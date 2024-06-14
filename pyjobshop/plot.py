from collections import defaultdict
from typing import Optional

import matplotlib
import matplotlib.pyplot as plt

from .ProblemData import ProblemData
from .Solution import Solution


def plot(
    data: ProblemData,
    solution: Solution,
    machine_order: Optional[list[int]] = None,
    plot_labels: bool = False,
    ax: Optional[plt.Axes] = None,
):
    """
    Plots a Gantt chart of the solution. Each unique job is associated with a
    distinct color (up to 92 unique colors, after which the colors are cycled).

    Parameters
    ----------
    data
        The problem data instance.
    solution
        A solution to the problem.
    machine_order
        The machines (by index) to plot and in which order they should appear
        (from top to bottom). Defaults to all machines in the data instance.
    plot_labels
        Whether to plot the task names as labels.
    ax
        Axes object to draw the plot on. One will be created if not provided.
    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(12, 8))
        assert ax is not None  # for linting

    # Custom ordering of machines to plot.
    if machine_order is not None:
        order = {machine: idx for idx, machine in enumerate(machine_order)}
    else:
        order = {idx: idx for idx in range(len(data.machines))}

    # Tasks belonging to the same job get the same color. Task that do not
    # belong to a job are colored grey.
    task2color = defaultdict(lambda: "grey")
    colors = _get_colors()

    for job_idx, job in enumerate(data.jobs):
        for task in job.tasks:
            task2color[task] = colors[job_idx % len(colors)]

    for idx, task_data in enumerate(solution.tasks):
        kwargs = {
            "color": task2color[idx],
            "linewidth": 1,
            "edgecolor": "black",
            "alpha": 0.75,
        }

        if task_data.machine in order:
            ax.barh(
                order[task_data.machine],
                task_data.duration,
                left=task_data.start,
                **kwargs,
            )

        if plot_labels:
            ax.text(
                task_data.start + task_data.duration / 2,
                order[task_data.machine],
                data.tasks[idx].name,
                ha="center",
                va="center",
            )

    labels = [data.machines[idx].name for idx in order.keys()]

    ax.set_yticks(ticks=range(len(labels)), labels=labels)
    ax.set_ylim(ax.get_ylim()[::-1])

    ax.set_xlim(0, ax.get_xlim()[1])  # start time at zero
    ax.set_xlabel("Time")
    ax.set_title("Solution")


def _get_colors() -> list[str]:
    """
    Color sequence based on concatenation of different common color maps.
    """
    names = ["tab20c", "Dark2", "Set1", "tab20b", "Set2", "tab20", "Accent"]
    cmaps = [matplotlib.colormaps[name] for name in names]
    colors = [color for cmap in cmaps for color in cmap.colors]

    return list(dict.fromkeys(colors))  # unique colors
