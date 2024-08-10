from pyjobshop import Model

# A job consists of tasks, which is a tuple (machine_id, processing_time).
jobs_data = [
    [(0, 3), (1, 2), (2, 2)],  # Job0
    [(0, 2), (2, 1), (1, 4)],  # Job1
    [(4, 4), (2, 3)],  # Job2
    [(5, 3), (1, 4), (0, 8)],  # Job3
    [(5, 3), (1, 4), (0, 8)],  # Job3
    [(5, 3), (1, 4), (0, 8)],  # Job3
    [(6, 3), (0, 4), (2, 2)],  # Job4
    [(6, 3), (0, 4), (2, 2)],  # Job4
    [(6, 3), (0, 4), (2, 2)],  # Job4
    [(9, 3)],  # Job5
    [(11, 3)],  # Job5
    [(1, 3)],  # Job5
    [(1, 3)],  # Job5
    [(1, 3)],  # Job5
    [(8, 3)],  # Job5
    [(1, 3)],  # Job5
] * 500
num_jobs = len(jobs_data)

model = Model()
jobs = [model.add_job() for _ in range(num_jobs)]
machines = [model.add_machine() for _ in range(20)]

for job_idx, task_data in enumerate(jobs_data):
    tasks = [model.add_task(job=jobs[job_idx]) for _ in task_data]

    # Add processing times.
    for idx, (machine_idx, duration) in enumerate(task_data):
        model.add_processing_time(tasks[idx], machines[machine_idx], duration)

    # Impose linear routing precedence constraints.
    for task_idx in range(1, len(tasks)):
        task1, task2 = tasks[task_idx - 1], tasks[task_idx]
        model.add_end_before_start(task1, task2)

num_jobs = len(jobs)
num_machines = len(machines)
num_tasks = len(model.tasks)

print(f"Building model with: {num_jobs=}, {num_machines=}, {num_tasks=}")

result = model.solve(
    solver="cpoptimizer",
    time_limit=1,
    display=True,
    num_workers=8,
)
