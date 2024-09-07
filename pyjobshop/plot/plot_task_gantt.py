from typing import Optional

import matplotlib.pyplot as plt

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution


def plot_task_gantt(
    data: ProblemData,
    solution: Solution,
    task_order: Optional[list[int]] = None,
    plot_labels: bool = False,
    ax: Optional[plt.Axes] = None,
):
    """
    Plots a task Gantt chart.
    """
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))

    if task_order is None:
        task_order = list(range(len(solution.tasks)))

    colors = plt.cm.tab20.colors  # Use a qualitative colormap for task colors

    num_tasks = len(task_order)
    dynamic_fontsize = max(4, 20 - num_tasks // 5)  # Adjust font size
    dynamic_bar_height = max(
        0.6, min(1.2, 6.0 / num_tasks)
    )  # Adjust bar height

    for idx, task_id in enumerate(task_order):
        task = solution.tasks[task_id]
        start, end = task.start, task.end
        ax.barh(
            idx,
            end - start,
            left=start,
            height=dynamic_bar_height,
            align="center",
            color=colors[idx % len(colors)],
            edgecolor="black",
            linewidth=0.5,  # Thinner border
        )

        if plot_labels:
            ax.text(
                x=(start + end) / 2,
                y=idx,
                s=f"{task_id}",
                va="center",
                ha="center",
                color="black",
                fontsize=dynamic_fontsize,  # Dynamic font size
                weight="bold",
            )

    ax.set_yticks(range(len(task_order)))
    ax.set_yticklabels([f"{task_id}" for task_id in task_order])
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Tasks", fontsize=12)
    ax.set_title("Task Gantt Chart", fontsize=14)
    ax.invert_yaxis()
    ax.grid(axis="x", linestyle="--", linewidth=0.5)

    # Adjust x-limit
    xlim = ax.get_xlim()
    xlim_length = xlim[1] - xlim[0]
    ax.set_xlim(xlim[0], xlim[1] + 0.01 * xlim_length)

    plt.tight_layout()
    plt.show()
