from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from pyjobshop.ProblemData import ProblemData

AssignVars = dict[tuple[int, int], CpoIntervalVar]


def job_variables(m: CpoModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each job in the problem.
    """
    return [m.interval_var(name=f"J{job}") for job in range(data.num_jobs)]


def operation_variables(
    m: CpoModel, data: ProblemData
) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each operation in the problem.
    """
    return [
        m.interval_var(name=f"O{idx}", optional=operation.optional)
        for idx, operation in enumerate(data.operations)
    ]


def task_variables(m: CpoModel, data: ProblemData) -> AssignVars:
    """
    Creates an optional interval variable for each operation and eligible
    machine pair, i.e., a task.
    """
    return {
        (op, machine): m.interval_var(name=f"A{op}_{machine}", optional=True)
        for op in range(data.num_operations)
        for machine in data.op2machines[op]
    }


def sequence_variables(
    m: CpoModel, data: ProblemData, assign: AssignVars
) -> list[CpoSequenceVar]:
    """
    Creates a sequence variable for each machine, using the corresponding
    assignment variables.
    """
    variables = []

    for machine, operations in enumerate(data.machine2ops):
        intervals = [assign[op, machine] for op in operations]
        variables.append(m.sequence_var(name=f"S{machine}", vars=intervals))

    return variables
