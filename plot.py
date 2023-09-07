from typing import NamedTuple

import matplotlib.pyplot as plt
import numpy as np
from docplex.cp.solution import CpoSolveResult

from Model import Model, Operation


class ScheduledOperation(NamedTuple):
    op: Operation
    assigned_machine: int
    start: int
    duration: int


def result2schedule(
    data: Model, result: CpoSolveResult
) -> list[ScheduledOperation]:
    """
    Maps a ``CpoSolveResult`` object to a list of scheduled operations.
    """
    schedule = []

    for var in result.get_all_var_solutions():
        name = var.get_name()

        # Scheduled operations are inferred from variables start with an "A"
        # (assignment) and that are present in the solution.
        if name.startswith("A") and var.is_present():
            op_id, mach_id = [int(num) for num in name.split("_")[1:]]
            op = data.operations[op_id]
            start = var.start
            duration = var.size

            schedule.append(ScheduledOperation(op, mach_id, start, duration))

    return schedule


def plot(data: Model, result: CpoSolveResult):
    """
    Plots a Gantt chart of the solver result.
    """
    schedule = result2schedule(data, result)

    fig, ax = plt.subplots(1, 1, figsize=(12, 8))

    # Use a gradiant color map to assign a unique color to each job.
    colors = plt.cm.tab20c(np.linspace(0, 1, len(data.jobs)))

    for op, machine, start, duration in schedule:
        # Plot each scheduled operation as a single horizontal bar (interval).
        kwargs = {"color": colors[op.job.id], "linewidth": 1, "edgecolor": "k"}
        ax.barh(machine, duration, left=start, **kwargs)

        # Add the operation ID at the center of the interval.
        midpoint = start + duration / 2
        ax.text(midpoint, machine, op.id, ha="center", va="center")

    ax.set_yticks(
        ticks=range(len(data.machines)),
        labels=[str(machine) for machine in data.machines],
    )
    ax.set_xlabel("Time")
    ax.set_title("Solution")

    fig.tight_layout()
    plt.show()
