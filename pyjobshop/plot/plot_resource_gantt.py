from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

import matplotlib.patches as patches
import matplotlib.pyplot as plt
from ortools.sat.python.cp_model import (
    CpModel,
    CpSolver,
)

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution


@dataclass
class Rectangle:
    task: int
    machine: int
    start_x: int
    start_y: int
    end_x: int
    end_y: int


def plot_resource_gantt(
    data: ProblemData,
    solution: Solution,
    machine_order: Optional[list[int]] = None,
    plot_labels: bool = False,
    ax: Optional[plt.Axes] = None,
):
    """
    Plots a resource Gantt chart, which ...
    """
    rectangles = solution2rectangles(solution, data)
    _plot_resource_gantt(rectangles)

    pass


def _plot_resource_gantt(rectangles: list[Rectangle]):
    """
    Helper function that takes rectangles.
    """
    # Organize rectangles by machine
    machine_rectangles = defaultdict(list)
    for rect in rectangles:
        machine_rectangles[rect.machine].append(rect)

    # Number of subplots
    num_machines = len(machine_rectangles)

    # Create subplots
    fig, axes = plt.subplots(
        num_machines, 1, figsize=(10, 6 * num_machines), sharex=True
    )
    if num_machines == 1:
        axes = [axes]

    # Plotting each machine in a separate subplot
    for ax, (machine, rects) in zip(axes, machine_rectangles.items()):
        for rect in rects:
            x1, y1, x2, y2 = rect.start_x, rect.start_y, rect.end_x, rect.end_y
            color = rect.task
            rectPlot = patches.Rectangle(
                (x1, y1),
                x2 - x1,
                y2 - y1,
                edgecolor="black",
                facecolor=plt.cm.rainbow(color / len(rectangles)),
                zorder=3,
            )
            ax.add_patch(rectPlot)
            ax.annotate(
                str(rect.task),
                (x1 + (x2 - x1) / 2.0, y1 + (y2 - y1) / 2.0),
                color="black",
                weight="bold",
                fontsize=6,
                ha="center",
                va="center",
                zorder=4,
            )

        # Set axis limits and labels
        ax.set_xlim(0, max(rect.end_x for rect in rects) + 1)
        ax.set_ylim(0, max(rect.end_y for rect in rects) + 1)
        ax.set_xlabel("", zorder=2)
        ax.set_ylabel(f"Machine {machine}", zorder=2)

        # Set grid and axes behind the rectangles
        ax.set_axisbelow(True)
        ax.grid(True, zorder=1)

    plt.tight_layout()
    plt.show()


def solution2rectangles(solution, data):
    cp_model = CpModel()

    pairs_by_machine = defaultdict(list)
    for task_data in solution.tasks:
        mode = data.modes[task_data.mode]

        for machine, demand in zip(mode.machines, mode.demands):
            if demand == 0:
                continue  # skip tasks that don't require resources

            start_x = task_data.start
            end_x = task_data.end
            width = end_x - start_x  # task duration
            name = f"{mode.task}_{machine}"
            x = cp_model.new_interval_var(start_x, width, end_x, name)

            max_height = data.machines[machine].capacity
            start_y = cp_model.new_int_var(0, max_height, "")
            end_y = cp_model.new_int_var(0, max_height, "")
            height = demand  # task demand
            name = f"{mode.task}_{machine}"
            y = cp_model.new_interval_var(start_y, height, end_y, name)

            pairs_by_machine[machine].append((x, y))

    for _, pairs in pairs_by_machine.items():
        cp_model.add_no_overlap_2d(*zip(*pairs))

    solver = CpSolver()
    solver.parameters.log_search_progress = True
    _ = solver.Solve(cp_model)

    rectangles = []

    for machine, pairs in pairs_by_machine.items():
        for x, y in pairs:
            start_x = solver.Value(x.start_expr())
            width = solver.Value(x.size_expr())
            start_y = solver.Value(y.start_expr())
            height = solver.Value(y.size_expr())
            task, machine = map(int, x.name.split("_"))

            rectangles.append(
                Rectangle(
                    task,
                    machine,
                    start_x,
                    start_y,
                    start_x + width,
                    start_y + height,
                )
            )

    return rectangles
