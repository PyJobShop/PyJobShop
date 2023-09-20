def operation_variables(m, data):
    for op in data.operations:
        m.add_interval_var("O", op)


def assignment_variables(m, data):
    for op in data.operations:
        for idx, machine in enumerate(op.machines):
            var = m.add_interval_var("A", op, machine, optional=True)

            # The duration of the operation on the machine is at least the
            # duration of the operation; it could be longer due to blocking.
            m.add(m.size_of(var) >= op.durations[idx] * m.presence_of(var))

            # Operation may not start before the job's release date if present.
            m.add(m.start_of(var) >= op.job.release_date * m.presence_of(var))


def sequence_variables(m, data):
    for machine, ops in data.machine2ops.items():
        intervals = [m.get_var("A", op, machine) for op in ops]
        m.add_sequence_var("S", machine, vars=intervals)
