# Example from https://developers.google.com/optimization/scheduling/job_shop
# Partially modified.

from itertools import product

from fjsp import Model, PrecedenceType, default_model, plot, result2solution

# A job consists of tasks, which is a tuple (machine_id, processing_time).
jobs_data = [
    [(0, 3), (1, 2), (2, 2)],  # Job0
    [(0, 2), (2, 1), (1, 4)],  # Job1
    [(1, 4), (2, 3)],  # Job2
    [(2, 3), (1, 4), (0, 8)],  # Job3
    [(1, 3), (0, 4), (2, 2)],  # Job4
    [(1, 3)],  # Job5
]
num_jobs = len(jobs_data)

model = Model()
jobs = [model.add_job() for _ in range(num_jobs)]
machines = [model.add_machine() for _ in range(3)]

for job_idx, tasks in enumerate(jobs_data):
    ops = []

    for machine_idx, _ in tasks:
        op = model.add_operation(jobs[job_idx], [machines[machine_idx]])
        ops.append(op)

    for idx, (machine_idx, duration) in enumerate(tasks):
        model.add_processing_time(ops[idx], machines[machine_idx], duration)

    for op_idx in range(1, len(ops)):
        # Impose linear routing precedence constraints.
        op1, op2 = ops[op_idx - 1], ops[op_idx]
        model.add_operations_edge(
            op1, op2, precedence_types=[PrecedenceType.END_BEFORE_START]
        )

# 1 duration setup times between each pair of operations and machine.
for op1, op2 in product(model.operations, model.operations):
    for machine in machines:
        model.add_setup_time(op1, op2, machine, 1)

# All machines can access each other.
for m1 in machines:
    for m2 in machines:
        model.add_machines_edge(m1, m2)

data = model.data()
cp_model = default_model(data)
result = cp_model.solve(TimeLimit=10)
solution = result2solution(data, result)

plot(data, solution)
