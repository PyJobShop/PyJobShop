import matplotlib.pyplot as plt
import numpy as np

from .ProblemData import ProblemData
from .Solution import Solution


def plot(data: ProblemData, solution: Solution, plot_labels: bool = False):
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
        ax.barh(machine, duration, left=start, **kwargs)

        if plot_labels:
            ax.text(
                start + duration / 2,
                machine,
                data.operations[op].name,
                ha="center",
                va="center",
            )

    labels = [
        machine.name or f"Machine {idx}"
        for idx, machine in enumerate(data.machines, 1)
    ]
    ax.set_yticks(ticks=range(len(data.machines)), labels=labels)
    ax.set_ylim(ax.get_ylim()[::-1])

    ax.set_xlim(0, ax.get_xlim()[1])  # start time at zero
    ax.set_xlabel("Time")
    ax.set_title("Solution")

    fig.tight_layout()
    plt.show()
