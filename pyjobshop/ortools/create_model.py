from typing import Optional

from ortools.sat.python.cp_model import CpModel

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution

from .constraints import (
    activate_setup_times,
    enforce_circuit,
    job_spans_tasks,
    no_overlap_machines,
    select_one_task_alternative,
    task_graph,
)
from .objectives import (
    makespan,
    tardy_jobs,
    total_completion_time,
    total_tardiness,
)
from .variables import (
    AssignmentVar,
    add_hint_to_vars,
    assignment_variables,
    job_variables,
    sequence_variables,
    task_variables,
)


def create_model(
    data: ProblemData,
    initial_solution: Optional[Solution] = None,
) -> tuple[CpModel, dict[tuple[int, int], AssignmentVar]]:
    """
    Creates an OR-Tools model for the given problem.

    Parameters
    ----------
    data
        The problem data instance.
    initial_solution
        An initial solution to start the solver from. Default is no solution.

    Returns
    -------
    tuple[CpModel, dict[tuple[int, int], AssignmentVar]]
        The constraint programming model and the assignment variables.
    """
    model = CpModel()

    job_vars = job_variables(model, data)
    task_vars = task_variables(model, data)
    assign_vars = assignment_variables(model, data)
    seq_vars = sequence_variables(model, data, assign_vars)

    if data.objective == "makespan":
        makespan(model, data, task_vars, initial_solution)
    elif data.objective == "tardy_jobs":
        tardy_jobs(model, data, job_vars)
    elif data.objective == "total_tardiness":
        total_tardiness(model, data, job_vars)
    elif data.objective == "total_completion_time":
        total_completion_time(model, data, job_vars)
    else:
        raise ValueError(f"Unknown objective: {data.objective}")

    job_spans_tasks(model, data, job_vars, task_vars)
    select_one_task_alternative(model, data, task_vars, assign_vars)
    no_overlap_machines(model, data, seq_vars)
    activate_setup_times(model, data, seq_vars)
    task_graph(model, data, task_vars, assign_vars, seq_vars)

    # From here onwards we know which sequence constraints are active.
    enforce_circuit(model, data, seq_vars)

    if initial_solution is not None:
        add_hint_to_vars(
            model,
            data,
            initial_solution,
            job_vars,
            task_vars,
            assign_vars,
            seq_vars,
        )

    return model, assign_vars
