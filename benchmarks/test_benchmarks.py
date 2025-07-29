from itertools import pairwise

import numpy as np
import pytest

from pyjobshop import Model
from tests.utils import read


def test_jsp_lawrence(benchmark, solver: str):
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

    benchmark(model.solve, solver)


@pytest.mark.parametrize(
    "loc",
    [
        "data/MFJS1.fjs",
        "data/Mk01.fjs",
        "data/edata-car1.fjs",
    ],
)
def test_fjsp_classic(benchmark, solver: str, loc: str):
    """
    Classic flexible job shop problem instances that are quickly solved to
    optimality.
    """
    data = read(loc)
    model = Model.from_data(data)
    benchmark(model.solve, solver)


def test_pfsp(benchmark, solver: str):
    """
    Benchmark a small permutation flow shop problem instance (1.txt) from
    http://soa.iti.es/problem-instances. It's the first Taillard instance.
    """
    DURATIONS = np.array(
        [
            [54, 79, 16, 66, 58],
            [83, 3, 89, 58, 56],
            [15, 11, 49, 31, 20],
            [71, 99, 15, 68, 85],
            [77, 56, 89, 78, 53],
            [36, 70, 45, 91, 35],
            [53, 99, 60, 13, 53],
            [38, 60, 23, 59, 41],
            [27, 5, 57, 49, 69],
            [87, 56, 64, 85, 13],
            [76, 3, 7, 85, 86],
            [91, 61, 1, 9, 72],
            [14, 73, 63, 39, 8],
            [29, 75, 41, 41, 49],
            [12, 47, 63, 56, 47],
            [77, 14, 47, 40, 87],
            [32, 21, 26, 54, 58],
            [87, 86, 75, 77, 18],
            [68, 5, 77, 51, 68],
            [94, 77, 40, 31, 28],
        ]
    )
    num_jobs, num_machines = DURATIONS.shape

    model = Model()
    machines = [model.add_machine() for _ in range(num_machines)]

    # Create tasks for each job and machine, and add modes with durations.
    tasks = np.empty((num_jobs, num_machines), dtype=object)
    for job_idx in range(num_jobs):
        for machine_idx, machine in enumerate(machines):
            task = model.add_task()
            tasks[job_idx, machine_idx] = task

            duration = DURATIONS[job_idx, machine_idx]
            model.add_mode(task, machine, duration=duration)

    # Precedence constraints between tasks of the same job.
    for job_tasks in tasks:
        for task1, task2 in pairwise(job_tasks):
            model.add_end_before_start(task1, task2)

    # Permutation constraints between tasks of different machines.
    for idx1, idx2 in pairwise(range(num_machines)):
        model.add_same_sequence(
            machines[idx1],
            machines[idx2],
            tasks[:, idx1].tolist(),
            tasks[:, idx2].tolist(),
        )

    benchmark(model.solve, solver, time_limit=60)


def test_dpfsp(benchmark, solver: str):
    """
    Benchmark a small distributed permutation flow shop problem instance
    (35.txt) from https://github.com/INFORMSJoC/2021.0326.
    """
    DURATIONS = np.array(
        [
            [15, 28, 77, 1, 45],
            [64, 4, 36, 59, 73],
            [64, 43, 57, 95, 59],
            [48, 93, 15, 49, 63],
            [9, 1, 81, 90, 54],
            [91, 81, 82, 78, 98],
            [27, 77, 98, 3, 39],
            [34, 69, 97, 69, 75],
            [42, 52, 12, 99, 33],
            [3, 28, 35, 41, 8],
            [11, 28, 84, 73, 86],
            [54, 77, 70, 28, 41],
            [27, 42, 27, 99, 41],
            [30, 53, 37, 13, 22],
            [9, 46, 59, 59, 43],
            [15, 49, 42, 47, 34],
            [88, 15, 57, 8, 80],
            [55, 43, 16, 92, 16],
            [50, 65, 11, 87, 37],
            [57, 41, 34, 62, 94],
        ]
    )
    num_jobs, num_machines = DURATIONS.shape
    num_factories = 6  # from instance data

    model = Model()
    jobs = [model.add_job() for _ in range(num_jobs)]
    machines = [
        [model.add_machine() for _ in range(num_machines)]
        for _ in range(num_factories)
    ]

    # Create tasks for each job and machine.
    tasks = np.empty((num_jobs, num_machines), dtype=object)
    for job_idx in range(num_jobs):
        for machine_idx in range(num_machines):
            task = model.add_task(job=jobs[job_idx])
            tasks[job_idx, machine_idx] = task

    # Create a mode for each (task, machine) pair in each factory.
    modes = np.empty((num_factories, num_jobs, num_machines), dtype=object)
    for factory_idx in range(num_factories):
        for machine_idx in range(num_machines):
            for job_idx in range(num_jobs):
                task = tasks[job_idx, machine_idx]
                machine = machines[factory_idx][machine_idx]
                duration = DURATIONS[job_idx, machine_idx]
                mode = model.add_mode(task, machine, duration=duration)
                modes[factory_idx, job_idx, machine_idx] = mode

    # Modes can only be select if the task is selected in that factory.
    for factory_idx in range(num_factories):
        for job_idx in range(num_jobs):
            for mode1, mode2 in pairwise(modes[factory_idx, job_idx, :]):
                model.add_mode_dependency(mode1, [mode2])

    # Precedence constraints between tasks of the same job.
    for job_tasks in tasks:
        for task1, task2 in pairwise(job_tasks):
            model.add_end_before_start(task1, task2)

    # Permutation constraints between tasks of different machines.
    for factory_idx in range(num_factories):
        for idx1, idx2 in pairwise(range(num_machines)):
            model.add_same_sequence(
                machines[factory_idx][idx1],
                machines[factory_idx][idx2],
                tasks[:, idx1].tolist(),
                tasks[:, idx2].tolist(),
            )

    benchmark(model.solve, solver)
