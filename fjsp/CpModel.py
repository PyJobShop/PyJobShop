from itertools import product

import docplex.cp.model as docp
from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.solution import CpoSolveResult

from .ProblemData import ProblemData
from .Solution import ScheduledOperation, Solution


class CpModel(docp.CpoModel):
    """
    Light wrapper around ``docplex.cp.model.CpoModel``.
    """

    def __init__(self):
        super().__init__()

        self._variables = {}

    @property
    def variables(self):
        return self._variables

    def add_interval_var(self, **kwargs) -> CpoIntervalVar:
        """
        Wrapper around ``docplex.cp.model.CpoModel.interval_var``. Adds the
        variable to the internal variables dictionary.
        """
        var = self.interval_var(**kwargs)
        self._variables[var.name] = var
        return var

    def add_sequence_var(
        self, variables: list[CpoIntervalVar], **kwargs
    ) -> CpoSequenceVar:
        """
        Wrapper around ``docplex.cp.model.CpoModel.sequence_var``. Adds the
        variable to the internal variables dictionary.
        """
        var = self.sequence_var(vars=variables, **kwargs)
        self._variables[var.name] = var
        return var


def create_cp_model(data: ProblemData) -> CpModel:
    """
    Creates a CP model for the given problem data.
    """
    m = CpModel()

    for op in data.operations:
        m.add_interval_var(name=f"O_{op.idx}")

        for idx, machine in enumerate(op.machines):
            var = m.add_interval_var(
                optional=True,
                name=f"A_{op.idx}_{machine.idx}",
                size=op.durations[idx],
            )
            # The duration of the operation on the machine is at least the
            # duration of the operation; it could be longer due to blocking.
            m.add(m.size_of(var) >= op.durations[idx] * m.presence_of(var))

            # Operations may not start before the job's release date, if given.
            m.add(m.start_of(var) >= op.job.release_date)

    for machine, ops in data.machine2ops.items():
        variables = [m.variables[(f"A_{op.idx}_{machine.idx}")] for op in ops]
        m.add_sequence_var(variables, name=f"S_{machine.idx}")

    # Objective: minimize the makespan
    completion_times = [
        m.end_of(m.variables[f"O_{op.idx}"]) for op in data.operations
    ]
    m.add(m.minimize(m.max(completion_times)))

    # Obey the operation timing precedence constraints.
    for frm, to, attr in data.operations_graph.edges(data=True):
        frm = m.variables[f"O_{frm}"]
        to = m.variables[f"O_{to}"]

        for prec_type in attr["precedence_types"]:
            if prec_type == "start_at_start":
                m.add(m.start_at_start(frm, to))
            elif prec_type == "start_at_end":
                m.add(m.start_at_end(frm, to))
            elif prec_type == "start_before_start":
                m.add(m.start_before_start(frm, to))
            elif prec_type == "start_before_end":
                m.add(m.start_before_end(frm, to))
            elif prec_type == "end_at_start":
                m.add(m.end_at_start(frm, to))
            elif prec_type == "end_at_end":
                m.add(m.end_at_end(frm, to))
            elif prec_type == "end_before_start":
                m.add(m.end_before_start(frm, to))
            elif prec_type == "end_before_end":
                m.add(m.end_before_end(frm, to))

    # Obey the operation ordering precedence constraints.
    for machine, ops in data.machine2ops.items():
        seq_var = m.variables[f"S_{machine.idx}"]

        for op1, op2 in product(ops, repeat=2):
            if op1 == op2:
                continue

            if (op1.idx, op2.idx) not in data.operations_graph.edges:
                continue

            var1 = m.variables[f"A_{op1.idx}_{machine.idx}"]
            var2 = m.variables[f"A_{op2.idx}_{machine.idx}"]
            edge = data.operations_graph.edges[op1.idx, op2.idx]

            for prec_type in edge["precedence_types"]:
                if prec_type == "previous":
                    m.add(m.previous(seq_var, var1, var2))
                elif prec_type == "before":
                    m.add(m.before(seq_var, var1, var2))
                elif prec_type == "same_unit":
                    m.add(m.presence_of(var1) == m.presence_of(var2))

    # An operation must be scheduled on exactly one machine.
    for op in data.operations:
        must = m.variables[f"O_{op.idx}"]
        optional = [
            m.variables[f"A_{op.idx}_{mach.idx}"] for mach in op.machines
        ]
        m.add(m.alternative(must, optional))

    # Operations on a given machine cannot overlap.
    for machine in data.machines:
        seq_var = m.variables[(f"S_{machine.idx}")]
        m.add(m.no_overlap(seq_var))

    # We can only schedule an operation on a given machine if it is
    # connected to the previous operation on that machine.
    for i, j in data.operations_graph.edges:
        edges = product(
            data.operations[i].machines, data.operations[j].machines
        )
        for frm_mach, to_mach in edges:  # BUG this is not correct
            if (frm_mach.idx, to_mach.idx) in data.machine_graph.edges:
                # An edge implies that the operation can move `frm -> to`, so
                # if `frm` is scheduled, `to` can be too.
                frm_var = m.variables[f"A_{i}_{frm_mach.idx}"]
                to_var = m.variables[f"A_{j}_{to_mach.idx}"]
                m.add(m.presence_of(frm_var) >= m.presence_of(to_var))

    # Same sequence on machines that are related.
    for k, l, attr in data.machine_graph.edges(data=True):
        if attr["same_sequence"]:
            seq_k = m.variables[f"S_{k}"]
            seq_l = m.variables[f"S_{l}"]
            m.add(m.same_sequence(seq_k, seq_l))

    return m


def result2solution(data: ProblemData, result: CpoSolveResult) -> Solution:
    """
    Maps a ``CpoSolveResult`` object to a ``Solution`` object.
    """
    schedule = []

    for var in result.get_all_var_solutions():
        name = var.get_name()

        # Scheduled operations are inferred from variables start with an "A"
        # (assignment) and that are present in the solution.
        if name.startswith("A") and var.is_present():
            op_idx, mach_idx = [int(num) for num in name.split("_")[1:]]
            op = data.operations[op_idx]
            start = var.start
            duration = var.size

            schedule.append(ScheduledOperation(op, mach_idx, start, duration))

    return Solution(data, schedule)
