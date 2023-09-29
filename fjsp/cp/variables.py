from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar

from fjsp.ProblemData import ProblemData

from .CpModel import CpModel

AssignVars = dict[int, dict[int, CpoIntervalVar]]


def operation_variables(m: CpModel, data: ProblemData) -> list[CpoIntervalVar]:
    """
    Creates an interval variable for each operation in the problem.
    """
    return [m.add_interval_var("O", op) for op in data.operations]


def assignment_variables(m: CpModel, data: ProblemData) -> AssignVars:
    """
    Creates an optional interval variable for each operation and eligible
    machine pair.
    """
    variables = {}
    for op in data.operations:
        op_vars = {}

        for idx, machine in enumerate(op.machines):
            var = m.add_interval_var("A", op, machine, optional=True)
            op_vars[machine.idx] = var

            # The duration of the operation on the machine is at least the
            # duration of the operation; it could be longer due to blocking.
            m.add(m.size_of(var) >= op.durations[idx] * m.presence_of(var))

            # Operation may not start before the job's release date if present.
            m.add(m.start_of(var) >= op.job.release_date * m.presence_of(var))

        variables[op.idx] = op_vars

    return variables


def sequence_variables(
    m: CpModel, data: ProblemData, assign: AssignVars
) -> list[CpoSequenceVar]:
    """
    Creates a sequence variable for each machine, using the corresponding
    assignment variables.
    """
    variables = []

    for machine, ops in data.machine2ops.items():
        intervals = [assign[op.idx][machine.idx] for op in ops]
        variables.append(m.add_sequence_var("S", machine, vars=intervals))

    return variables
