import pytest
from numpy.testing import assert_, assert_equal

from pyjobshop import Model, solve

from .utils import read


def test_jsp_lawrence(solver: str):
    """
    Job shop problem instance from https://github.com/tamy0612/JSPLIB

    Lawrence 10x5 instance la01 (Table 3, instance 1);
    also called (setf1) or (F1).
    """
    # A job consists of tasks, which is a tuple (machine_id, processing_time).
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
            model.add_processing_time(tasks[t_idx], machines[m_idx], duration)

        # Linear routing precedence constraints.
        for task_idx in range(1, len(tasks)):
            task1, task2 = tasks[task_idx - 1], tasks[task_idx]
            model.add_end_before_start(task1, task2)

    result = model.solve(solver=solver)

    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 666)


@pytest.mark.parametrize(
    "loc, objective",
    [
        ["data/MFJS1.fjs", 468],
        ["data/Mk01.fjs", 40],
        ["data/edata-car1.fjs", 6176],
    ],
)
def test_fjsp_classic(solver: str, loc: str, objective: int):
    """
    Classic flexible job shop problem instances that are quickly solved to
    optimality.
    """
    data = read(loc)
    result = solve(data, solver=solver)

    assert_equal(result.objective, objective)
    assert_equal(result.status.value, "Optimal")
    assert_(result.runtime < 1)
