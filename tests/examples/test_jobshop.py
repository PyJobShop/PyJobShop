from numpy.testing import assert_equal

from fjsp import Model, TimingPrecedence


def test_jobshop():
    """
    Tests a simple job shop problem with 3 machines and 6 jobs.

    Example from https://developers.google.com/optimization/scheduling/job_shop
    """

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
        operations = [model.add_operation() for _ in tasks]
        model.assign_job_operations(jobs[job_idx], operations)

        # Add processing times.
        for idx, (machine_idx, duration) in enumerate(tasks):
            model.add_processing_time(
                machines[machine_idx], operations[idx], duration
            )

        # Impose linear routing precedence constraints.
        for op_idx in range(1, len(operations)):
            op1, op2 = operations[op_idx - 1], operations[op_idx]
            model.add_timing_precedence(
                op1, op2, TimingPrecedence.END_BEFORE_START
            )

    result = model.solve()

    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 20)
