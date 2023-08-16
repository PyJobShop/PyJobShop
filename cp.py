from itertools import product

import docplex.cp.model as docp

from Model import Model


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

    def add_interval_var(self, **kwargs):
        """
        Wrapper around ``docplex.cp.model.CpoModel.interval_var``. Adds the
        variable to the internal variables dictionary.
        """
        var = self.interval_var(**kwargs)
        self._variables[var.name] = var
        return var

    def add_sequence_var(self, **kwargs):
        """
        Wrapper around ``docplex.cp.model.CpoModel.sequence_var``. Adds the
        variable to the internal variables dictionary.
        """
        var = self.sequence_var(**kwargs)
        self._variables[var.name] = var
        return var


def create_cp_model(data: Model):
    """
    Creates a CP model for the given problem data.
    """
    m = CpModel()

    for op in data.operations:
        m.add_interval_var(name=f"O_{op.id}")

        for idx, machine in enumerate(op.machines):
            var = m.add_interval_var(
                optional=True, name=f"A_{op.id}_{machine.id}"
            )
            # The duration of the operation on the machine is at least the
            # duration of the operation; it could be longer due to blocking.
            m.add(m.size_of(var) >= op.durations[idx])

    for machine, ops in data.machine2ops.items():
        vars = [m.variables[(f"A_{op.id}_{machine.id}")] for op in ops]
        m.add_sequence_var(vars=vars, name=f"S_{machine.id}")

    # Objective: minimize the makespan
    completion_times = [
        m.end_of(m.variables[f"O_{op.id}"]) for op in data.operations
    ]
    m.add(m.minimize(m.max(completion_times)))

    # Obey the operation precedence constraints.
    for frm, to, attr in data.operations_graph.edges(data=True):
        frm = m.variables[f"O_{frm}"]
        to = m.variables[f"O_{to}"]

        for pt in attr["precedence_types"]:
            if pt == "start_at_start":
                m.add(m.start_at_start(frm, to))
            elif pt == "start_at_end":
                m.add(m.start_at_end(frm, to))
            elif pt == "start_before_start":
                m.add(m.start_before_start(frm, to))
            elif pt == "start_before_end":
                m.add(m.start_before_end(frm, to))
            elif pt == "end_at_start":
                m.add(m.end_at_start(frm, to))
            elif pt == "end_at_end":
                m.add(m.end_at_end(frm, to))
            elif pt == "end_before_start":
                m.add(m.end_before_start(frm, to))
            elif pt == "end_before_end":
                m.add(m.end_before_end(frm, to))
            else:
                raise ValueError(f"Unknown precedence type: {pt}")

    # An operation must be scheduled on exactly one machine.
    for op in data.operations:
        must = m.variables[f"O_{op.id}"]
        optional = [
            m.variables[f"A_{op.id}_{mach.id}"] for mach in op.machines
        ]
        m.add(m.alternative(must, optional))

    # Operations on a given machine cannot overlap.
    for machine in data.machines:
        seq_var = m.variables[(f"S_{machine.id}")]
        m.add(m.no_overlap(seq_var))

    # We can only schedule an operation on a given machine if it is
    # connected to the previous operation on that machine.
    for i, j in data.operations_graph.edges:
        edges = product(
            data.operations[i].machines, data.operations[j].machines
        )
        for frm_mach, to_mach in edges:  # BUG this is not correct
            if (frm_mach.id, to_mach.id) in data.machine_graph.edges:
                # An edge implies that the operation can move `frm -> to`, so
                # if `frm` is scheduled, `to` can be too.
                frm_var = m.variables[f"A_{i}_{frm_mach.id}"]
                to_var = m.variables[f"A_{j}_{to_mach.id}"]
                m.add(m.presence_of(frm_var) >= m.presence_of(to_var))

    # Same sequence on machines that are related.
    for k, l, attr in data.machine_graph.edges(data=True):
        if attr["same_sequence"]:
            seq_k = m.variables[f"S_{k}"]
            seq_l = m.variables[f"S_{l}"]
            m.add(m.same_sequence(seq_k, seq_l))

    return m
