import matplotlib.pyplot as plt
import numpy as np

from .ProblemData import ProblemData
from .Solution import Solution


def plot(data: ProblemData, solution: Solution):
    """
    Plots a Gantt chart of the solver result.
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
        kwargs = {
            "color": colors[op.job.idx],
            "linewidth": 1,
            "edgecolor": "k",
        }
        ax.barh(machine, duration, left=start, **kwargs)

        # Add the operation ID at the center of the interval.
        midpoint = start + duration / 2
        ax.text(midpoint, machine, op.idx, ha="center", va="center")

    ax.set_yticks(
        ticks=range(len(data.machines)),
        labels=[str(machine) for machine in data.machines],
    )
    ax.set_xlabel("Time")
    ax.set_title("Solution")

    fig.tight_layout()
    plt.show()
