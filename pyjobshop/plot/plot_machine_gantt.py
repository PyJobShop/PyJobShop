from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib.axes import Axes

from pyjobshop.ProblemData import ProblemData, Renewable, NonRenewable
from pyjobshop.Solution import Solution

from .utils import get_colors as _get_colors


def plot_machine_gantt(
    solution: Solution,
    data: ProblemData,
    resources: list[int] | None = None,
    plot_labels: bool = False,
    ax: Axes | None = None,
):
    """
    Plots a Gantt chart of the solution, where each row represents a machine
    and each bar represents a task processed on that machine.

    Parameters
    ----------
    solution
        A solution to the problem.
    data
        The problem data instance.
    resources
        The resources (by index) to plot and in which order they should appear
        (from top to bottom). Defaults to all resources in the data instance.
    plot_labels
        Whether to plot the task names as labels.
    ax
        Axes object to draw the plot on. One will be created if not provided.
    """
    if ax is None:
        _, ax = plt.subplots(1, 1, figsize=(12, 8))
        assert ax is not None  # for linting

    if resources is None:
        resources = list(range(data.num_resources))

    # Tasks belonging to the same job get the same color. Task that do not
    # belong to a job are colored grey.
    task2color = defaultdict(lambda: "grey")
    colors = _get_colors()
    for idx, task in enumerate(data.tasks):
        if task.job is not None:
            task2color[idx] = colors[task.job % len(colors)]

    # Calculate the base y-position for each resource
    resource_base_y = {}
    resource_lanes = {}  # For each resource, track the occupation of each lane
    for resource_idx in resources:
        resource = data.resources[resource_idx]
        capacity = resource.capacity if isinstance(resource, (Renewable, NonRenewable)) else 1
        resource_base_y[resource_idx] = sum(
            data.resources[r].capacity if isinstance(data.resources[r], (Renewable, NonRenewable)) else 1
            for r in resources if r < resource_idx
        )
        # For each lane, keep a list of (start, end) tuples
        resource_lanes[resource_idx] = [[] for _ in range(capacity)]

    # Sort tasks by start time to process them in chronological order
    sorted_tasks = sorted(enumerate(solution.tasks), key=lambda x: x[1].start)

    for task_idx, task_data in sorted_tasks:
        kwargs = {
            "color": task2color[task_idx],
            "linewidth": 1,
            "edgecolor": "black",
            "alpha": 0.75,
        }
        duration = task_data.end - task_data.start
        mode = data.modes[task_data.mode]

        for resource_idx, demand in zip(mode.resources, mode.demands):
            if resource_idx not in resources:
                continue  # skip resources not in the order

            resource = data.resources[resource_idx]
            capacity = resource.capacity if isinstance(resource, (Renewable, NonRenewable)) else 1

            # Calculate the height of this task bar
            if capacity > 1:
                height = demand / capacity
            else:
                height = 1.0

            # Assign the task to the first available lane for its entire duration
            lane_found = False
            for lane_idx, lane in enumerate(resource_lanes[resource_idx]):
                # Check if this lane is free for the entire duration
                if all(task_data.end <= s or task_data.start >= e for (s, e) in lane):
                    lane.append((task_data.start, task_data.end))
                    lane_found = True
                    break
            if not lane_found:
                # Should not happen if demand <= capacity and model is feasible
                lane_idx = 0  # fallback to first lane
                resource_lanes[resource_idx][lane_idx].append((task_data.start, task_data.end))

            base_y = resource_base_y[resource_idx]
            y_position = base_y + lane_idx
            height = 1.0  # always use full height for each lane

            ax.barh(
                y_position,
                duration,
                left=task_data.start,
                height=height,
                **kwargs,
            )

            if plot_labels:
                ax.text(
                    task_data.start + duration / 2,
                    y_position + height / 2,
                    data.tasks[task_idx].name or f"{task_idx}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )

    # Set y-axis ticks and labels
    y_ticks = []
    y_labels = []
    current_y = 0
    for resource_idx in resources:
        resource = data.resources[resource_idx]
        capacity = resource.capacity if isinstance(resource, (Renewable, NonRenewable)) else 1
        base_y = current_y
        y_ticks.append(base_y)
        resource_name = resource.name or f"Machine {resource_idx}"
        if capacity > 1:
            y_labels.append(f"{resource_name} (cap={capacity})")
        else:
            y_labels.append(resource_name)
        current_y += capacity

    ax.set_yticks(ticks=y_ticks, labels=y_labels)
    ax.set_ylim(current_y + 0.5, -0.5)  # Ensure all bars are fully visible, including the first and last

    ax.set_xlim(0, ax.get_xlim()[1])  # start time at zero
    ax.set_xlabel("Time")
    ax.set_title("Solution")
