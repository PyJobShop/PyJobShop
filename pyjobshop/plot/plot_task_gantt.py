import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution


def plot_task_gantt(
    solution: Solution,
    data: ProblemData,
    tasks: list[int] | None = None,
    plot_labels: bool = False,
    ax: Axes | None = None,
):
    """
    Plots a task Gantt chart, which plots each task on a separate row.

    Parameters
    ----------
    solution
        Solution to plot.
    data
        The corresponding problem data.
    tasks
        The tasks (by index) to plot and in which order they should appear
        (from top to bottom). Defaults to all tasks in the data instance.
    plot_labels
        Whether to plot task labels on the chart.
    ax
        The matplotlib axes to plot on. If ``None``, a new figure is created.
    """
    if ax is None:
        _, ax = plt.subplots()

    if tasks is None:
        tasks = list(range(len(solution.tasks)))

    colors = plt.cm.tab20.colors  # Use a qualitative colormap for task colors
    present_tasks = [task for task in tasks if solution.tasks[task].present]

    for row_idx, task_idx in enumerate(present_tasks):
        sol_task = solution.tasks[task_idx]
        ax.barh(
            row_idx,
            sol_task.duration,
            left=sol_task.start,
            align="center",
            color=colors[row_idx % len(colors)],
            edgecolor="black",
            linewidth=0.5,
        )

        if plot_labels:
            ax.text(
                x=(sol_task.start + sol_task.end) / 2,
                y=row_idx + 0.1,
                s=data.tasks[task_idx].name or f"{task_idx}",
                va="center",
                ha="center",
                color="black",
            )

    ax.set_xlim(0, solution.makespan)
    ax.set_xlabel("Time")
    ax.set_ylabel("Tasks", fontsize=12)
    ax.set_title("Task Gantt Chart", fontsize=14)
    ax.set_yticks([])
    ax.invert_yaxis()
