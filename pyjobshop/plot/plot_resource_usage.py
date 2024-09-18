from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from pyjobshop import ProblemData, Solution


def plot_resource_usage(
    solution: Solution,
    data: ProblemData,
    _ax: Optional[Axes] = None,
):
    usages = _compute_usage(solution, data)
    _, axes = plt.subplots(
        data.num_resources,
        figsize=(10, 2 * data.num_resources),
        sharex=True,
    )

    for resource, usage in enumerate(usages):
        ax = axes[resource]
        time = np.arange(len(usage))
        label = f"Resource {resource}"

        ax.bar(time, usage, label=label)
        ax.set_xlabel("Time")
        ax.set_ylabel("Usage")
        ax.legend()

    plt.tight_layout()
    plt.show()

    ax.set_xlabel("Time")
    ax.set_ylabel("Usage")


def _compute_usage(solution: Solution, data: ProblemData) -> np.ndarray:
    """
    Computes the resource usage for each resource and time step.
    """
    makespan = max(task.end for task in solution.tasks if task is not None)
    usages = np.zeros((data.num_resources, makespan))

    for task in solution.tasks:
        mode = data.modes[task.mode]

        for resource, demand in zip(mode.resources, mode.demands):
            usages[resource, task.start : task.end] += demand

    return usages
