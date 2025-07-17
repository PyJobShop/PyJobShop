from typing import Optional
from datetime import datetime, timedelta

import matplotlib.colors as mcolors
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from ..ProblemData import ProblemData


def get_plotly_colors():
    """
    Returns a list of RGB colors for Plotly, converting from Matplotlib's
    'tab20' colormap.
    """
    tableau_colors = mcolors.TABLEAU_COLORS
    plotly_colors = [
        f"rgb({int(r*255)}, {int(g*255)}, {int(b*255)})"
        for r, g, b, _ in mcolors.to_rgba_array(
            [tableau_colors[name] for name in tableau_colors]
        )
    ]
    return plotly_colors


def plot_combined_plotly(
    result: "Result",
    data: ProblemData,
    resources: Optional[list[int]] = None,
):
    """
    Plots a machine-based Gantt chart of the solution using Plotly Express.

    Parameters
    ----------
    result
        A result object from the solver, containing the solution.
    data
        The problem data instance.
    resources
        The resources (by index) to plot. Defaults to all resources.

    Returns
    -------
    plotly.graph_objects.Figure
        A Plotly figure object containing the Gantt chart.
    """
    solution = result.best

    if resources is None:
        resources = list(range(data.num_resources))

    timeline_data = []
    colors = get_plotly_colors()
    job_color_map = {}
    now = datetime.now()

    for task_idx, sol_task in enumerate(solution.tasks):
        if sol_task.start == sol_task.end:
            continue

        task_info = data.tasks[task_idx]
        task_name = task_info.name or f"Task {task_idx}"
        job_name = "Unassigned"

        if task_info.job is not None:
            job_name = data.jobs[task_info.job].name
            if job_name not in job_color_map:
                job_color_map[job_name] = colors[task_info.job % len(colors)]

        mode = data.modes[sol_task.mode]
        for resource_idx in mode.resources:
            if resource_idx in resources:
                resource_name = (
                    data.resources[resource_idx].name
                    or f"Resource {resource_idx}"
                )
                duration = sol_task.end - sol_task.start
                timeline_data.append(
                    dict(
                        Task=task_name,
                        Start=now + timedelta(minutes=sol_task.start),
                        Finish=now + timedelta(minutes=sol_task.end),
                        Resource=resource_name,
                        Job=job_name,
                        Duration=f"{duration}m",
                    )
                )

    if not timeline_data:
        return go.Figure().update_layout(title_text="No tasks to display.")

    df = pd.DataFrame(timeline_data)

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Resource",
        color="Job",
        hover_name="Task",
        hover_data=["Duration"],
        color_discrete_map=job_color_map,
        title="Machine Gantt Chart",
    )

    fig.update_yaxes(autorange="reversed")
    fig.update_layout(
        xaxis_title="Time",
        yaxis_title="Machines",
        height=30 * len(df["Resource"].unique()) + 150,
    )

    return fig 