from enum import Enum
from pathlib import Path
from typing import Union

import fjsplib
import psplib

from .Model import Model
from .ProblemData import NonRenewable, ProblemData, Renewable


class InstanceFormat(str, Enum):
    """
    Supported instance formats.
    """

    FJSPLIB = "fjsplib"
    PSPLIB = "psplib"
    MPLIB = "mplib"
    PATTERSON = "patterson"


def read(
    loc: Union[str, Path],
    instance_format: InstanceFormat = InstanceFormat.FJSPLIB,
) -> ProblemData:
    """
    Reads an FJSPLIB instance and returns a ProblemData object.
    """
    if instance_format == InstanceFormat.FJSPLIB:
        return _read_fjslib(loc)
    elif instance_format in [
        InstanceFormat.PSPLIB,
        InstanceFormat.MPLIB,
        InstanceFormat.PATTERSON,
    ]:
        instance = psplib.parse(loc, instance_format)
        return _project_instance_to_data(instance)

    raise ValueError(f"Unknown instance format: {instance_format}")


def _read_fjslib(loc: Union[str, Path]) -> ProblemData:
    """
    Reads an FJSPLIB instance and returns a ProblemData object.
    """
    instance = fjsplib.read(loc)

    m = Model()

    jobs = [m.add_job() for _ in range(instance.num_jobs)]
    resources = [m.add_machine() for _ in range(instance.num_machines)]

    for job_idx, tasks in enumerate(instance.jobs):
        for task_data in tasks:
            task = m.add_task(job=jobs[job_idx])

            for resource_idx, duration in task_data:
                m.add_mode(task, resources[resource_idx], duration)

    for frm, to in instance.precedences:
        m.add_end_before_start(m.tasks[frm], m.tasks[to])

    return m.data()


def _project_instance_to_data(instance: psplib.ProjectInstance) -> ProblemData:
    """
    Converts a ProjectInstance to a ProblemData object.
    """
    model = Model()

    resources: list[Union[Renewable, NonRenewable]] = [
        model.add_renewable(capacity=res.capacity)
        if res.renewable
        else model.add_non_renewable(capacity=res.capacity)
        for res in instance.resources
    ]

    for project in instance.projects:
        job = model.add_job(release_date=project.release_date)

        for _ in project.activities:
            model.add_task(job=job)

    for idx, activity in enumerate(instance.activities):
        for mode in activity.modes:
            model.add_mode(
                task=model.tasks[idx],
                resources=resources,
                duration=mode.duration,
                demands=mode.demands,
            )

    for idx, activity in enumerate(instance.activities):
        for succ in activity.successors:
            model.add_end_before_start(model.tasks[idx], model.tasks[succ])

    return model.data()
