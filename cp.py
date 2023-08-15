from itertools import product

import docplex.cp.model as docp

from Model import Model


class CpModel(docp.CpoModel):
    """
    Light wrapper around docplex.cp.model.CpoModel.
    """

    def __init__(self):
        super().__init__()

        self._variables = {}

    @property
    def variables(self):
        return self._variables

    def add_interval_var(self, **kwargs):
        """
        Wrapper around docplex.cp.model.CpoModel.interval_var. Adds the
        variable to the internal dictionary.
        """
        var = self.interval_var(**kwargs)
        self._variables[var.name] = var


def create_cp_model(data: Model):
    m = CpModel()

    for op in data.operations:
        m.add_interval_var(name=f"O_{op.id}")

        for idx, machine in enumerate(op.machines):
            m.add_interval_var(
                size=op.durations[idx],
                optional=True,
                name=f"A_{op.id}_{machine.id}",
            )

    # Objective: minimize the makespan
    completion_times = [
        m.end_of(m.variables[f"O_{op.id}"]) for op in data.operations
    ]
    m.add(m.minimize(m.max(completion_times)))

    # Obey the operation precedence constraints.
    for frm, to in data.operations_graph.edges:
        frm = m.variables[f"O_{frm}"]
        to = m.variables[f"O_{to}"]
        m.add(m.end_before_start(frm, to))

    # An operation must be scheduled on exactly one machine.
    for op in data.operations:
        main = m.variables[f"O_{op.id}"]
        optional = [
            m.variables[f"A_{op.id}_{mach.id}"] for mach in op.machines
        ]
        m.add(m.alternative(main, optional))

    # Operations on a given machine cannot overlap.
    for machine, ops in data.machine2ops.items():
        intervals = [m.variables[(f"A_{op.id}_{machine.id}")] for op in ops]
        if intervals:
            m.add(m.no_overlap(intervals))

    # We can only schedule an operation on a given machine if it is
    # connected to the previous operation on that machine.
    for i, j in data.operations_graph.edges:
        edges = product(
            data.operations[i].machines, data.operations[j].machines
        )
        for frm_mach, to_mach in edges:
            if (frm_mach.id, to_mach.id) in data.machine_graph.edges:
                # An edge implies that the operation can move from `frm` to `to`,
                # so if if `frm` is scheduled, `to` can be too.
                frm_var = m.variables[f"A_{i}_{frm_mach.id}"]
                to_var = m.variables[f"A_{j}_{to_mach.id}"]
                m.add(m.presence_of(frm_var) >= m.presence_of(to_var))

    return m
