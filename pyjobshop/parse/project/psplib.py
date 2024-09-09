import re

from .ProjectInstance import Activity, Mode, Project, ProjectInstance, Resource


def _find(lines: list[str], pattern: str) -> int:
    for idx, line in enumerate(lines):
        if pattern in line:
            return idx

    raise ValueError(f"Pattern '{pattern}' not found in lines.")


def read_instance(path: str) -> "ProjectInstance":
    """
    Reads an instance of the RCPSP from a file.
    Assumes the data is in the PSPLIB format.
    """
    with open(path) as fh:
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

        activities.append(Activity(successors, modes))

    idcs = list(range(len(activities)))
    project = Project(idcs)  # only one project with all activities

    return ProjectInstance(resources, [project], activities)


if __name__ == "__main__":
    from pathlib import Path

    import tqdm

    from pyjobshop import Model

    instances = []
    instances += list(Path("tmp/MMLIB/").rglob("*.mm"))
    instances += list(Path("tmp/RCPLIB(1)/PSPLIB").rglob("*.sm"))
    instances += list(Path("tmp/PSPLIB").rglob("*.[sm]m"))

    for loc in tqdm.tqdm(instances):
        if loc.name.startswith("."):  # dotfiles
            continue

        if not loc.is_file():
            continue

        instance = read_instance(loc)
        continue
        model = Model()

        # Not necessary to define jobs, but it will add coloring to the plot.
        resources = [
            model.add_machine(capacity=res.capacity, renewable=res.renewable)
            for res in instance.resources
        ]

        for idx in range(instance.num_jobs):
            job = model.add_job()
            task = model.add_task(job=job)

            for mode in instance.activities[idx].modes:
                model.add_mode(task, resources, mode.duration, mode.demands)

        for idx in range(instance.num_jobs):
            task = model.tasks[idx]

            for succ in instance.activities[idx].successors:
                model.add_end_before_start(task, model.tasks[succ])

        try:
            data = model.data()
        except:
            breakpoint()
        result = model.solve(time_limit=10, display=False)

        print(loc, result.objective, result.runtime)
