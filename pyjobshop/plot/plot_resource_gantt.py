from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from ortools.sat.python.cp_model import CpModel, CpSolver

from pyjobshop.ProblemData import Machine, ProblemData
from pyjobshop.Solution import Solution

from . import utils


@dataclass
class Rectangle:
    task: int
    resource: int
    start_x: int
    start_y: int
    end_x: int
    end_y: int

    @property
    def width(self):
        return self.end_x - self.start_x

    @property
    def height(self):
        return self.end_y - self.start_y

    @property
    def bottom_left(self):
        return self.start_x, self.start_y

    @property
    def midpoint_x(self):
        return self.start_x + self.width / 2

    @property
    def midpoint_y(self):
        return self.start_y + self.height / 2


def plot_resource_gantt(
    solution: Solution,
    data: ProblemData,
    resource_order: Optional[list[int]] = None,
    plot_labels: bool = False,
    axes: Optional[list[Axes]] = None,
):
    """
    Plots a resource Gantt chart, which shows how resources are used over time
    for each task in the solution.

    Parameters
    ----------
    solution
        Solution to plot.
    data
        The corresponding problem data.
    resource_order
        The order in which resources should be plotted. If not provided,
        resources are plotted in the order they appear in the data.
    plot_labels
        Whether to plot labels on the Gantt chart.
    axes
        The matplotlib axes to use for plotting. It must have at least length
        ``data.num_resources``. If not provided, a new set of axes will be
        created.
    """
    rectangles = _solution2rectangles(solution, data)

    if axes is None:
        _, axes = plt.subplots(data.num_resources, sharex=True)
        assert axes is not None

    if len(axes) < data.num_resources:
        msg = "The number of axes must be at least the number of resources."
        raise ValueError(msg)

    if resource_order is None:
        resource_order = list(range(data.num_resources))

    # Tasks belonging to the same job get the same color. Task that do not
    # belong to a job are colored grey.
    task2color = defaultdict(lambda: "grey")
    colors = utils.get_colors()
    for job_idx, job in enumerate(data.jobs):
        for task in job.tasks:
            task2color[task] = colors[job_idx % len(colors)]

    resource2rectangles = defaultdict(list)
    for rectangle in rectangles:
        resource2rectangles[rectangle.resource].append(rectangle)

    for resource in resource_order:
        ax = axes[resource]
        rectangles = resource2rectangles[resource]

        for rectangle in rectangles:
            patch = patches.Rectangle(
                rectangle.bottom_left,
                rectangle.width,
                rectangle.height,
                edgecolor="black",
                facecolor=task2color[rectangle.task],
                zorder=3,
            )
            ax.add_patch(patch)

            if plot_labels:
                ax.annotate(
                    data.tasks[rectangle.task].name or str(rectangle.task),
                    (rectangle.midpoint_x, rectangle.midpoint_y),
                    color="black",
                    ha="center",
                    va="center",
                    zorder=4,
                )

        ax.set_xlim(0, solution.makespan)
        capacity = (
            data.resources[resource].capacity
            if not isinstance(data.resources[resource], Machine)
            else 1
        )
        ax.set_ylim(0, capacity)
        ax.set_ylabel(f"Resource {resource}", zorder=2)

        ax.set_axisbelow(True)


def _solution2rectangles(solution: Solution, data: ProblemData):
    """
    Converts a solution to a list of rectangles that can be plotted.
    We use OR-Tools to solve the packing problem, because a greedy
    stacking solution is not guaranteed to be feasible.
    """
    cp_model = CpModel()

    pairs_by_resource = defaultdict(list)
    for task_data in solution.tasks:
        mode = data.modes[task_data.mode]

        for resource, demand in zip(mode.resources, mode.demands):
            if isinstance(data.resources[resource], Machine):
                # For machine resources, we assume unit demand and capacity.
                demand = 1
                max_height = 1
            elif demand == 0:
                continue  # skip tasks that don't require resources
            else:
                max_height = data.resources[resource].capacity

            start_x = task_data.start
            end_x = task_data.end
            width = end_x - start_x  # task duration
            name = f"{mode.task}_{resource}"
            x = cp_model.new_interval_var(start_x, width, end_x, name)

            start_y = cp_model.new_int_var(0, max_height, "")
            end_y = cp_model.new_int_var(0, max_height, "")
            height = demand  # task demand
            name = f"{mode.task}_{resource}"
            y = cp_model.new_interval_var(start_y, height, end_y, name)

            pairs_by_resource[resource].append((x, y))

    for _, pairs in pairs_by_resource.items():
        cp_model.add_no_overlap_2d(*zip(*pairs))

    solver = CpSolver()
    status_code = solver.Solve(cp_model)
    status = solver.status_name(status_code)

    if status not in ["OPTIMAL", "FEASIBLE"]:
        raise ValueError("Could not find a feasible packing solution.")

    rectangles = []
    for resource, pairs in pairs_by_resource.items():
        for x, y in pairs:
            start_x = solver.Value(x.start_expr())
            width = solver.Value(x.size_expr())
            start_y = solver.Value(y.start_expr())
            height = solver.Value(y.size_expr())
            task, resource = map(int, x.name.split("_"))

            rectangles.append(
                Rectangle(
                    task,
                    resource,
                    start_x,
                    start_y,
                    start_x + width,
                    start_y + height,
                )
            )

    return rectangles
