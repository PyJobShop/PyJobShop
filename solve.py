import fjsplib
from fjsplib import read

import pyjobshop
from pyjobshop import Model


def instance2model(instance: fjsplib.Instance) -> pyjobshop.Model:
    m = Model()

    jobs = [m.add_job() for _ in range(instance.num_jobs)]
    machines = [m.add_machine() for _ in range(instance.num_machines)]

    for job_idx, tasks in enumerate(instance.jobs):
        for task_ in tasks:
            task = m.add_task(job=jobs[job_idx])

            for machine_idx, duration in task_:
                print(machine_idx, duration)
                m.add_processing_time(machines[machine_idx], task, duration)

    for frm, to in instance.precedences:
        m.add_constraint(m.tasks[frm], m.tasks[to], "end_before_start")

    return m


instance = read("instances/FJSP/Barnes/seti5xyz.fjs")
m = instance2model(instance)
m.solve(time_limit=10)
