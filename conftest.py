import pytest

from pyjobshop import Model
from pyjobshop.ProblemData import (
    Consecutive,
    Constraints,
    DifferentResources,
    EndBeforeEnd,
    EndBeforeStart,
    IdenticalResources,
    Job,
    Machine,
    Mode,
    ModeDependency,
    NonRenewable,
    Objective,
    ProblemData,
    Renewable,
    SameSequence,
    SelectAllOrNone,
    SelectAtLeastOne,
    SelectExactlyOne,
    SetupTime,
    StartBeforeEnd,
    StartBeforeStart,
    Task,
)
from pyjobshop.Solution import Solution, TaskData


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
def complete_data():
    """
    A ProblemData object with almost all features of the library.
    """
    jobs = [Job(tasks=[2], due_date=1)]
    resources = [
        Machine(no_idle=True),
        Renewable(1),
        NonRenewable(1),
        Machine(),
        Machine(),
        Machine(breaks=[(1, 2)]),
    ]
    tasks = [
        Task(),
        Task(),
        Task(job=0),
        Task(),
        Task(),
        Task(),
        Task(optional=True),
        Task(allow_breaks=True),
    ]
    modes = [
        Mode(0, [0], 1),
        Mode(1, [0], 1),
        Mode(2, [1], 1, [1]),
        Mode(3, [1], 1, [1]),
        Mode(3, [2], 1, [1]),
        Mode(4, [3], 1),
        Mode(5, [3], 1),
        Mode(6, [4], 1),
        Mode(7, [5], 2),
    ]
    constraints = Constraints(
        start_before_start=[StartBeforeStart(0, 1)],
        start_before_end=[StartBeforeEnd(0, 1)],
        end_before_start=[EndBeforeStart(0, 1)],
        end_before_end=[EndBeforeEnd(0, 1)],
        identical_resources=[IdenticalResources(0, 1)],
        different_resources=[DifferentResources(0, 2)],
        consecutive=[Consecutive(0, 1)],
        same_sequence=[SameSequence(0, 3)],
        setup_times=[
            SetupTime(0, 0, 1, 1),
            SetupTime(0, 1, 1, 1),
            SetupTime(0, 1, 0, 1),
        ],
        mode_dependencies=[ModeDependency(0, [1])],
        select_all_or_none=[SelectAllOrNone([4])],
        select_at_least_one=[SelectAtLeastOne([0])],
        select_exactly_one=[SelectExactlyOne([0])],
    )
    objective = Objective(
        weight_makespan=2,
        weight_tardy_jobs=3,
        weight_total_tardiness=4,
        weight_total_flow_time=5,
        weight_total_earliness=6,
        weight_max_tardiness=7,
        weight_total_setup_time=8,
    )
    return ProblemData(
        jobs,
        resources,
        tasks,
        modes,
        constraints,
        objective,
    )


@pytest.fixture(scope="session")
def complete_sol():
    return Solution(
        [
            TaskData(0, [0], 0, 1),
            TaskData(1, [0], 2, 3),
            TaskData(2, [1], 1, 2),
            TaskData(4, [2], 0, 1),
            TaskData(5, [3], 0, 1),
            TaskData(6, [3], 2, 3),
            TaskData(-1, [], 0, 0, 0, 0, present=False),
            TaskData(8, [5], 0, 3, overlap=1),
        ]
    )


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


@pytest.fixture
def require_cpoptimizer(request):
    solvers = request.config.getoption("--solvers")
    if "cpoptimizer" not in solvers:
        pytest.skip("cpoptimizer not requested via --solvers")
