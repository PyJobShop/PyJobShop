import re
from pathlib import Path
from typing import Union

from .ProjectInstance import Activity, Mode, Project, ProjectInstance, Resource


def _find(lines: list[str], pattern: str) -> int:
    for idx, line in enumerate(lines):
        if pattern in line:
            return idx

    raise ValueError(f"Pattern '{pattern}' not found in lines.")


def parse_psplib(loc: Union[str, Path]) -> ProjectInstance:
    """
    Parses an PSPLIB-formatted instance from a file.

    Parameters
    ----------
    loc
        The location of the instance.

    Returns
    -------
    Instance
        The parsed instance.
    """
    with open(loc) as fh:
        lines = [line.strip() for line in fh.readlines() if line.strip()]

    prec_idx = _find(lines, "PRECEDENCE RELATIONS")
    req_idx = _find(lines, "REQUESTS/DURATIONS")
    avail_idx = _find(lines, "AVAILABILITIES")

    capacities = list(map(int, re.split(r"\s+", lines[avail_idx + 2])))
    renewable = [
        char == "R"
        for char in lines[avail_idx + 1].strip().split()
        if char in ["R", "N"]  # R: renewable, N: non-renewable
    ]
    resources = [
        Resource(capacity, is_renewable)
        for capacity, is_renewable in zip(capacities, renewable)
    ]
    num_resources = len(resources)

    mode_data = [
        list(map(int, re.split(r"\s+", line)))
        for line in lines[req_idx + 3 : avail_idx - 1]
    ]

    mode_idx = 0
    activities = []
    for line in lines[prec_idx + 2 : req_idx - 1]:
        _, num_modes, _, *jobs = list(map(int, re.split(r"\s+", line)))
        successors = [val - 1 for val in jobs if val]

        modes = []
        for idx in range(mode_idx, mode_idx + num_modes):
            # Mode data is parsed starting from the end of the line because
            # the data is ragged as some lines do not contain job indices.
            duration = mode_data[idx][-num_resources - 1]
            demands = mode_data[idx][-num_resources:]
            modes.append(Mode(duration, demands))
            mode_idx += 1

        activities.append(Activity(modes, successors))

    idcs = list(range(len(activities)))
    project = Project(idcs)  # only one project with all activities

    return ProjectInstance(resources, [project], activities)
