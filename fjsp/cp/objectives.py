def makespan(m, data):
    completion_times = [m.end_of(m.get_var("O", op)) for op in data.operations]
    return m.minimize(m.max(completion_times))


def total_completion_time(m, data):
    completion_times = []

    for _, operations in data.job2ops.items():
        expr = m.max([m.end_of(m.get_var("O", op)) for op in operations])
        completion_times.append(expr)

    return m.minimize(m.sum(completion_times))


def total_tardiness(m, data):
    objective = []

    for _, operations in data.job2ops.items():
        expr = m.max([m.end_of(m.get_var("O", op)) for op in operations])
        tardiness = m.max(0, expr - data.deadline)
        objective.append(tardiness)

    return m.minimize(m.sum(objective))
