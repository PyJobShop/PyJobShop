from typing import Optional

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution


def plot_task_gantt(
    solution: Solution,
    data: ProblemData,
    task_order: Optional[list[int]] = None,
    plot_labels: bool = False,
    ax: Optional[Axes] = None,
):
    """
    Plots a task Gantt chart, which shows each task as horizontal bar
    on a separate row.

    Parameters
    ----------
    solution
        Solution to plot.
    data
        The corresponding problem data.
    task_order
        The order in which to plot the tasks. If ``None``, the tasks are
        plotted in the order they appear in the data.
    """
    if ax is None:
        _, ax = plt.subplots()

    if task_order is None:
        task_order = list(range(len(solution.tasks)))

    colors = plt.cm.tab20.colors  # Use a qualitative colormap for task colors

    for row_idx, task_idx in enumerate(task_order):
        task = solution.tasks[task_idx]
        start = task.start
        end = task.end
        duration = task.end - task.start

        ax.barh(
            row_idx,
            duration,
            left=start,
            align="center",
            color=colors[row_idx % len(colors)],
            edgecolor="black",
            linewidth=0.5,
        )

        if plot_labels:
            ax.text(
                x=(start + end) / 2,
                y=row_idx + 0.1,
                s=data.tasks[task_idx].name or f"{task_idx}",
                va="center",
                ha="center",
                color="black",
            )

    ax.set_xlim(0, solution.makespan)
    ax.set_ylabel("Tasks", fontsize=12)
    ax.set_title("Task Gantt Chart", fontsize=14)
    ax.invert_yaxis()
