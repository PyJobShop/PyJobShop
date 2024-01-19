from typing import Optional

import matplotlib.pyplot as plt
import numpy as np

from .ProblemData import ProblemData
from .Solution import Solution


def plot(
    data: ProblemData,
    solution: Solution,
    machines_to_plot: Optional[list[int]] = None,
    plot_labels: bool = False,
    ax: Optional[plt.Axes] = None,
):
    """
    Plots a Gantt chart of the solver result.

    Parameters
    ----------
    data: ProblemData
        The problem data instance.
    solution: Solution
        A solution to the problem.
    machines_to_plot: Optional[list[int]]
        The machines to plot (by index) and in which order they should appear
        (from top to bottom). Defaults to all machines in the data instance.
    plot_labels: bool
        Whether to plot the operation names as labels.
    ax
        Axes object to draw the plot on. One will be created if not provided.
    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Custom ordering of machines to plot.
    if machines_to_plot is not None:
        order = {machine: idx for idx, machine in enumerate(machines_to_plot)}
    else:
        order = {idx: idx for idx in range(len(data.machines))}

    # Operations belonging to the same job get the same unique color.
    colors = plt.cm.tab20c(np.linspace(0, 1, len(data.jobs)))

    for scheduled_op in solution.schedule:
        op, machine, start, duration = (
            scheduled_op.op,
            scheduled_op.assigned_machine,
            scheduled_op.start,
            scheduled_op.duration,
        )

        job = [job for job, ops in enumerate(data.job2ops) if op in ops][0]
        kwargs = {"color": colors[job], "linewidth": 1, "edgecolor": "black"}
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
