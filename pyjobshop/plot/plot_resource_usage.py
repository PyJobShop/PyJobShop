from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.axes import Axes

from pyjobshop import ProblemData, Solution


def plot_resource_usage(
    solution: Solution,
    data: ProblemData,
    resources: Optional[list[int]] = None,
    axes: Optional[list[Axes]] = None,
):
    """
    Plots the resource usage for each resource and time step.

    Parameters
    ----------
    solution
        The solution to plot.
    data
        The problem data.
    resources
        The resources (by index) to plot and in which order they should appear
        (from top to bottom). Defaults to all resources in the data instance.
    axes
        The matplotlib axes to use for plotting. It must have at least length
        ``data.num_resources``. If not provided, a new set of axes will be
        created.
    """
    if axes is None:
        _, axes = plt.subplots(data.num_resources, sharex=True)
        assert axes is not None  # make mypy happy

    if len(axes) < data.num_resources:
        msg = "The number of axes must be at least the number of resources."
        raise ValueError(msg)

    if resources is None:
        resources = list(range(data.num_resources))

    usages = _compute_usage(solution, data)
    for resource in resources:
        usage = usages[resource]
        ax = axes[resource]
        time = np.arange(len(usage))
        label = data.resources[resource].name or f"Resource {resource}"

        ax.bar(time, usage)
        ax.set_ylabel(label)
        ax.set_xlim(0, solution.makespan)


def _compute_usage(solution: Solution, data: ProblemData) -> np.ndarray:
    """
    Computes the resource usage for each resource and time step.
    """
    usages = np.zeros((data.num_resources, solution.makespan))

    for task in solution.tasks:
        mode = data.modes[task.mode]

        for resource, demand in zip(mode.resources, mode.demands):
            usages[resource, task.start : task.end] += demand

    return usages
