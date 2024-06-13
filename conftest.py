import pytest

from pyjobshop import Model


@pytest.fixture(scope="session")
def small():
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task, duration in zip(tasks, [1, 2]):
        model.add_processing_time(task, machine, duration)

    return model.data()


def pytest_addoption(parser):
    parser.addoption(
        "--solvers",
        nargs="+",
        default=["ortools"],
        choices=["ortools", "cpoptimizer"],
        help="Solvers to test.",
    )


def pytest_generate_tests(metafunc):
    if "solver" in metafunc.fixturenames:
        metafunc.parametrize("solver", metafunc.config.getoption("solvers"))
