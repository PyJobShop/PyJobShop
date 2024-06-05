from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

AssignVars = dict[tuple[int, int], CpoIntervalVar]


def job_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each job in the problem.
    """
    return [m.interval_var(name=f"J{idx}") for idx in range(data.num_jobs)]


def task_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each task in the problem.
    """
    return [m.interval_var(name=f"O{idx}") for idx in range(data.num_tasks)]


def assignment_variables(m: CpoModel, data: ProblemData) -> AssignVars:
    """
    Creates an optional interval variable for each task and eligible
    machine pair, i.e., a task.
    """
    return {
        (task, machine): m.interval_var(
            name=f"A{task}_{machine}", optional=True
        )
        for task in range(data.num_tasks)
        for machine in data.task2machines[task]
    }


def sequence_variables(
    m: CpoModel, data: ProblemData, assign: AssignVars
) -> list[CpoSequenceVar]:
    """
    Creates a sequence variable for each machine, using the corresponding
    assignment variables.
    """
    variables = []

    for machine, tasks in enumerate(data.machine2tasks):
        intervals = [assign[task, machine] for task in tasks]
        variables.append(m.sequence_var(name=f"S{machine}", vars=intervals))

    return variables
