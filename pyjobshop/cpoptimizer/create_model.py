from typing import Optional

from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution

from .constraints import (
    job_spans_tasks,
    no_overlap_and_setup_times,
    select_one_task_alternative,
    task_alt_graph,
    task_graph,
)
from .objectives import add_objective
from .variables import (
    job_variables,
    sequence_variables,
    set_initial_solution,
    task_alternative_variables,
    task_variables,
)


def create_model(
    data: ProblemData,
    initial_solution: Optional[Solution] = None,
) -> CpoModel:
    """
    Creates a CP Optimizer model for the given problem data.

    Parameters
    ----------
    data
        The problem data instance.
    initial_solution
        An initial solution to start the solver from. Default is no solution.

    Returns
    -------
    CpoModel
        The constraint programming model for the given problem data.
    """
    model = CpoModel()

    job_vars = job_variables(model, data)
    task_vars = task_variables(model, data)
    task_alt_vars = task_alternative_variables(model, data)
    seq_vars = sequence_variables(model, data, task_alt_vars)

    if initial_solution is not None:
        set_initial_solution(
            model, data, initial_solution, job_vars, task_vars, task_alt_vars
        )

    add_objective(model, data, job_vars, task_vars)

    job_spans_tasks(model, data, job_vars, task_vars)
    no_overlap_and_setup_times(model, data, seq_vars)
    select_one_task_alternative(model, data, task_vars, task_alt_vars)
    task_graph(model, data, task_vars)
    task_alt_graph(model, data, task_alt_vars, seq_vars)

    return model
