from pathlib import Path
from typing import Union

from .ProjectInstance import Activity, Mode, Project, ProjectInstance, Resource


def parse_mprcpsp(loc: Union[str, Path]) -> ProjectInstance:
    """
    Parses a multi-project resource-constrained project scheduling instance.

    Parameters
    ----------
    loc
        The location of the instance.

    Returns
    -------
    Instance
        The parsed instance.
    """
    with open(loc, "r") as fh:
        # Strip all lines and ignore all empty lines.
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    num_projects = int(next(lines))
    num_resources = int(next(lines))

    capacities = list(map(int, next(lines).split()))
    resources = [Resource(capacity=cap, renewable=False) for cap in capacities]

    projects = []
    activities = []
    for project_idx in range(1, num_projects + 1):
        num_activities, release_date = map(int, next(lines).split())
        _ = list(map(int, next(lines).split()))  # used resources => demand > 0
        idcs = [len(activities) + idx for idx in range(num_activities)]

        for activity_idx in range(1, num_activities + 1):
            activity = next(lines).split()
            idx = num_resources + 2
            duration, *demands, num_successors = list(map(int, activity[:idx]))
            successors = activity[idx:]
            assert len(successors) == num_successors
            mode = Mode(duration, demands)
            name = f"{project_idx}:{activity_idx}"  # original activity id
            activities.append(Activity(mode, successors, name))

        projects.append(Project(idcs, release_date))

    return ProjectInstance(resources, projects, activities)


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    import tqdm

    DATA_DIR = Path("tmp/MPLIB")
    for loc in tqdm.tqdm(sorted(DATA_DIR.rglob("MPLIB*.rcmp"))):
        portfolio = parse_mprcpsp(loc)
        continue

        from pyjobshop import Model

        model = Model()

        resources = [
            model.add_machine(capacity=capacity)
            for capacity in portfolio.capacities
        ]

        activities = {}  # activity_label -> activity
        for project_idx, project in portfolio.projects.items():
            job = model.add_job(
                release_date=project.release_date,
                name=f"Project {project_idx}",
            )

            for activity_label, activity in project.activities.items():
                task = model.add_task(
                    job=job, name=f"Activity {activity_label}"
                )
                activities[activity_label] = task
                model.add_mode(
                    task,
                    resources,
                    activity.duration,
                    activity.demands,
                )

            for activity_label, activity in project.activities.items():
                task = activities[activity_label]
                for successor_label in activity.successors:
                    successor = activities[successor_label]
                    model.add_end_before_start(task, successor)

        result = model.solve(time_limit=10)
        print(loc.stem, result.objective, result.runtime)
