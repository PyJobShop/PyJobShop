from enum import Enum
from pathlib import Path
from typing import Union

import fjsplib

from pyjobshop.parse.project import (
    ProjectInstance,
    parse_mplib,
    parse_patterson,
    parse_psplib,
)

from .Model import Model
from .ProblemData import ProblemData


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
    elif instance_format == InstanceFormat.PSPLIB:
        return _project_instance_to_data(parse_psplib(loc))
    elif instance_format == InstanceFormat.MPLIB:
        return _project_instance_to_data(parse_mplib(loc))
    elif instance_format == InstanceFormat.PATTERSON:
        return _project_instance_to_data(parse_patterson(loc))

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


def _project_instance_to_data(instance: ProjectInstance) -> ProblemData:
    """
    Converts a ProjectInstance to a ProblemData object.
    """
    model = Model()

    resources = [
        model.add_resource(capacity=res.capacity, renewable=res.renewable)
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
