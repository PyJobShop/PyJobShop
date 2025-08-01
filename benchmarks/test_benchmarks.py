import numpy as np
import pytest
from numpy.testing import assert_equal

from pyjobshop import Model, solve
from pyjobshop.constants import MAX_VALUE
from tests.utils import read


def test_jsp_lawrence(benchmark, solver):
    """
    Job shop problem instance from https://github.com/tamy0612/JSPLIB

    Lawrence 10x5 instance la01 (Table 3, instance 1);
    also called (setf1) or (F1).
    """
    # A job consists of tasks, which is a tuple (resource_id, processing_time).
    jobs_data = [
        [(1, 21), (0, 53), (4, 95), (3, 55), (2, 34)],
        [(0, 21), (3, 52), (4, 16), (2, 26), (1, 71)],
        [(3, 39), (4, 98), (1, 42), (2, 31), (0, 12)],
        [(1, 77), (0, 55), (4, 79), (2, 66), (3, 77)],
        [(0, 83), (3, 34), (2, 64), (1, 19), (4, 37)],
        [(1, 54), (2, 43), (4, 79), (0, 92), (3, 62)],
        [(3, 69), (4, 77), (1, 87), (2, 87), (0, 93)],
        [(2, 38), (0, 60), (1, 41), (3, 24), (4, 83)],
        [(3, 17), (1, 49), (4, 25), (0, 44), (2, 98)],
        [(4, 77), (3, 79), (2, 43), (1, 75), (0, 96)],
    ]
    num_jobs = len(jobs_data)

    model = Model()
    jobs = [model.add_job() for _ in range(num_jobs)]
    machines = [model.add_machine() for _ in range(5)]

    for job_idx, tasks_data in enumerate(jobs_data):
        num_tasks = len(tasks_data)
        tasks = [model.add_task(job=jobs[job_idx]) for _ in range(num_tasks)]

        for t_idx, (m_idx, duration) in enumerate(tasks_data):
            model.add_mode(tasks[t_idx], machines[m_idx], duration)

        # Linear routing precedence constraints.
        for task_idx in range(1, len(tasks)):
            task1, task2 = tasks[task_idx - 1], tasks[task_idx]
            model.add_end_before_start(task1, task2)

    result = benchmark(model.solve, solver=solver, time_limit=10)
    assert_equal(result.objective, 666)


@pytest.mark.parametrize(
    "loc, objective",
    [
        ["data/MFJS1.fjs", 468],
        ["data/Mk01.fjs", 40],
        ["data/edata-car1.fjs", 6176],
    ],
)
def test_fjsp_classic(benchmark, solver, loc, objective):
    """
    Classic flexible job shop problem instances that are quickly solved to
    optimality.
    """
    data = read(loc)
    result = benchmark(solve, data, solver=solver, time_limit=10)
    assert_equal(result.objective, objective)


def test_tsp(benchmark, solver):
    """
    Traveling Salesman Problem (TSP) instance from OR-Tools examples.
    https://developers.google.com/optimization/routing/tsp
    """
    # fmt: off
    DURATIONS = [
        [0, 2451, 713, 1018, 1631, 1374, 2408, 213, 2571, 875, 1420, 2145, 1972], # noqa: E501
        [2451, 0, 1745, 1524, 831, 1240, 959, 2596, 403, 1589, 1374, 357, 579],
        [713, 1745, 0, 355, 920, 803, 1737, 851, 1858, 262, 940, 1453, 1260],
        [1018, 1524, 355, 0, 700, 862, 1395, 1123, 1584, 466, 1056, 1280, 987],
        [1631, 831, 920, 700, 0, 663, 1021, 1769, 949, 796, 879, 586, 371],
        [1374, 1240, 803, 862, 663, 0, 1681, 1551, 1765, 547, 225, 887, 999],
        [2408, 959, 1737, 1395, 1021, 1681, 0, 2493, 678, 1724, 1891, 1114, 701],  # noqa: E501
        [213, 2596, 851, 1123, 1769, 1551, 2493, 0, 2699, 1038, 1605, 2300, 2099],  # noqa: E501
        [2571, 403, 1858, 1584, 949, 1765, 678, 2699, 0, 1744, 1645, 653, 600],
        [875, 1589, 262, 466, 796, 547, 1724, 1038, 1744, 0, 679, 1272, 1162],
        [1420, 1374, 940, 1056, 879, 225, 1891, 1605, 1645, 679, 0, 1017, 1200],  # noqa: E501
        [2145, 357, 1453, 1280, 586, 887, 1114, 2300, 653, 1272, 1017, 0, 504],
        [1972, 579, 1260, 987, 371, 999, 701, 2099, 600, 1162, 1200, 504, 0],
    ]
    DURATIONS = np.array(DURATIONS)
    # fmt: on

    num_clients = len(DURATIONS) - 1
    model = Model()
    machine = model.add_machine()

    # Create one task for departing from depot and one for arriving at depot,
    # plus one task for each client.
    depart = model.add_task()
    arrive = model.add_task()
    tasks = [model.add_task() for _ in range(num_clients)]

    for task in model.tasks:  # no processing duration for all tasks
        model.add_mode(task, machine, duration=0)

    for idx1, task1 in enumerate(tasks, 1):
        model.add_setup_time(machine, depart, task1, DURATIONS[0, idx1])
        model.add_setup_time(machine, task1, arrive, DURATIONS[idx1, 0])

        # Disallow going from task to departure or from arrival to task.
        model.add_setup_time(machine, task1, depart, MAX_VALUE)
        model.add_setup_time(machine, arrive, task1, MAX_VALUE)

        for idx2, task2 in enumerate(tasks, 1):
            model.add_setup_time(machine, task1, task2, DURATIONS[idx1, idx2])
            model.add_setup_time(machine, task2, task1, DURATIONS[idx1, idx2])

    # Disallow going directly from departure to arrival and vice versa.
    model.add_setup_time(machine, arrive, depart, duration=MAX_VALUE)
    model.add_setup_time(machine, depart, arrive, duration=MAX_VALUE)

    if solver == "ortools":
        # OR-Tools works much faster with this objective to solve TSPs.
        model.set_objective(weight_total_setup_time=1)

    result = benchmark(model.solve, solver=solver, time_limit=10)
    assert_equal(result.objective, 7293)
