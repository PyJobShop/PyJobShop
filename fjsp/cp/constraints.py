from itertools import product


def timing_precedence_constraints(m, data):
    for frm, to, attr in data.operations_graph.edges(data=True):
        frm = m.get_var("O", data.operations[frm])
        to = m.get_var("O", data.operations[to])

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


def assignment_precedence_constraints(m, data):
    # Obey the operation ordering precedence constraints.
    for machine, ops in data.machine2ops.items():
        seq_var = m.get_var("S", machine)

        for op1, op2 in product(ops, repeat=2):
            if op1 == op2:
                continue

            if (op1.idx, op2.idx) not in data.operations_graph.edges:
                continue

            var1 = m.get_var("A", op1, machine)
            var2 = m.get_var("A", op2, machine)
            edge = data.operations_graph.edges[op1.idx, op2.idx]

            for prec_type in edge["precedence_types"]:
                if prec_type == "previous":
                    m.add(m.previous(seq_var, var1, var2))
                elif prec_type == "same_unit":
                    m.add(m.presence_of(var1) == m.presence_of(var2))
                elif prec_type == "different_unit":
                    m.add(m.presence_of(var1) != m.presence_of(var2))


def alternative_constraints(m, data):
    # An operation must be scheduled on exactly one machine.
    for op in data.operations:
        must = m.get_var("O", op)
        optional = [m.get_var("A", op, mach) for mach in op.machines]
        m.add(m.alternative(must, optional))


def no_overlap_constraints(m, data):
    # Operations on a given machine cannot overlap.
    for machine in data.machines:
        m.add(m.no_overlap(m.get_var("S", machine)))


def machine_accessibility_constraints(m, data):
    # Impose machine accessibility restrictions on precedent operations.
    # If an operation is scheduled on a machine, the next operation can only
    # be scheduled on a machine that is accessible from the current machine.
    for i, j in data.operations_graph.edges:
        op1, op2 = data.operations[i], data.operations[j]

        for m1, m2 in product(op1.machines, op2.machines):
            if (m1.idx, m2.idx) not in data.machine_graph.edges:
                # If (m1 -> m2) is not an edge in the machine graph, then
                # we cannot schedule operation 1 on m1 and operation 2 on m2.
                frm_var = m.get_var("A", op1, m1)
                to_var = m.get_var("A", op2, m2)
                m.add(m.presence_of(frm_var) + m.presence_of(to_var) <= 1)
