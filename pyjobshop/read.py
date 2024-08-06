from pathlib import Path

import fjsplib

from .Model import Model
from .ProblemData import ProblemData


def read(loc: Path) -> ProblemData:
    """
    Reads an FJSPLIB instance and returns a ProblemData object.
    """
    instance = fjsplib.read(loc)

    m = Model()

    jobs = [m.add_job() for _ in range(instance.num_jobs)]
    machines = [m.add_machine() for _ in range(instance.num_machines)]

    for job_idx, tasks in enumerate(instance.jobs):
        for task_data in tasks:
            task = m.add_task(job=jobs[job_idx])

            for machine_idx, duration in task_data:
                m.add_processing_time(task, machines[machine_idx], duration)

    for frm, to in instance.precedences:
        m.add_end_before_start(m.tasks[frm], m.tasks[to])

    return m.data()
