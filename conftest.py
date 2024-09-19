import pytest

from pyjobshop import Model


@pytest.fixture(scope="session")
def small():
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task, duration in zip(tasks, [1, 2]):
        model.add_mode(task, machine, duration)

    return model.data()


@pytest.fixture(scope="session")
def fjsp():
    """
    A small flexible jobshop instance with 3 jobs, 3 resources and 9 tasks.
    """
    DATA = [  # task = (processing_time, resource_id)
        [
            [(3, 0), (1, 1), (5, 2)],  # task 0 with 3 alternatives
            [(2, 0), (4, 1), (6, 2)],  # task 1 with 3 alternatives
            [(2, 0), (3, 1), (1, 2)],  # task 2 with 3 alternatives
        ],
        [
            [(2, 0), (3, 1), (4, 2)],
            [(1, 0), (5, 1), (4, 2)],
            [(2, 0), (1, 1), (4, 2)],
        ],
        [
            [(2, 0), (1, 1), (4, 2)],
            [(2, 0), (3, 1), (4, 2)],
            [(3, 0), (1, 1), (5, 2)],
        ],
    ]

    model = Model()

    machines = [model.add_machine() for _ in range(3)]
    jobs = {}
    tasks = {}

    for job_idx, job_data in enumerate(DATA):
        jobs[job_idx] = model.add_job()

        for idx in range(len(job_data)):
            task_idx = (job_idx, idx)
            tasks[task_idx] = model.add_task(jobs[job_idx])

        for idx, task_data in enumerate(job_data):
            task = tasks[(job_idx, idx)]

            for duration, resource_idx in task_data:
                machine = machines[resource_idx]
                model.add_mode(task, machine, duration)

        for idx in range(len(job_data) - 1):
            first = tasks[(job_idx, idx)]
            second = tasks[(job_idx, idx + 1)]
            model.add_end_before_start(first, second)

    return model.data()


def pytest_addoption(parser):
    parser.addoption(
        "--solvers",
        nargs="+",
        default=["ortools", "cpoptimizer"],
        choices=["ortools", "cpoptimizer"],
        help="Solvers to test.",
    )


def pytest_generate_tests(metafunc):
    if "solver" in metafunc.fixturenames:
        metafunc.parametrize("solver", metafunc.config.getoption("solvers"))
