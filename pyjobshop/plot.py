from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap

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
        Whether to plot the operation names as labels.
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

    colors = _get_colors()

    for task in solution.schedule:
        op, machine, start, duration = (
            task.operation,
            task.machine,
            task.start,
            task.duration,
        )

        # Operations belonging to the same job get the same unique color.
        job = [job for job, ops in enumerate(data.job2ops) if op in ops][0]
        kwargs = {
            "color": colors[job % len(colors)],
            "linewidth": 1,
            "edgecolor": "black",
            "alpha": 0.75,
        }

        if machine in order:
            ax.barh(order[machine], duration, left=start, **kwargs)

        if plot_labels:
            ax.text(
                start + duration / 2,
                order[machine],
                data.operations[op].name,
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
    cmaps = [get_cmap(name) for name in names]
    colors = [color for cmap in cmaps for color in cmap.colors]

    return list(dict.fromkeys(colors))  # unique colors
