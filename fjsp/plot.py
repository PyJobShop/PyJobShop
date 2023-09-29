import matplotlib.pyplot as plt
import numpy as np

from .ProblemData import ProblemData
from .Solution import Solution


def plot(data: ProblemData, solution: Solution, plot_labels: bool = True):
    """
    Plots a Gantt chart of the solver result.

    Parameters
    ----------
    data: ProblemData
        The problem data instance.
    solution: Solution
        A solution to the problem.
    """
    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Use a gradiant color map to assign a unique color to each job.
    colors = plt.cm.tab20c(np.linspace(0, 1, len(data.jobs)))

    for scheduled_op in solution.schedule:
        op, machine, start, duration = (
            scheduled_op.op,
            scheduled_op.assigned_machine,
            scheduled_op.start,
            scheduled_op.duration,
        )

        # Plot each scheduled operation as a single horizontal bar (interval).
        color = colors[op.job]
        kwargs = {"color": color, "linewidth": 1, "edgecolor": "black"}
        ax.barh(machine, duration, left=start, **kwargs)

        if plot_labels:
            # Add the operation ID at the center of the interval.
            center = start + duration / 2
            ax.text(center, machine, op.name, ha="center", va="center")

    labels = [str(machine) for machine in data.machines]
    ax.set_yticks(ticks=range(len(data.machines)), labels=labels)
    ax.set_ylim(ax.get_ylim()[::-1])

    ax.set_xlim(0, ax.get_xlim()[1])  # start time at zero
    ax.set_xlabel("Time")
    ax.set_title("Solution")

    fig.tight_layout()
    plt.show()
