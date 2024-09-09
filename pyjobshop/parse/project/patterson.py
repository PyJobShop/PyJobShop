from pathlib import Path
from typing import Union

from .ProjectInstance import Activity, Mode, Project, ProjectInstance, Resource


def parse_patterson(loc: Union[str, Path]) -> ProjectInstance:
    """
    Reads a Patterson-formatted instance. This format is used for pure
    resource-constrained project scheduling problem (RCPSP) instances.

    Parameters
    ----------
    loc
        The location of the instance.

    Returns
    -------
    ProjectInstance
        The parsed project instance.
    """
    with open(loc, "r") as fh:
        # Strip all lines and ignore all empty lines.
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    num_activities, num_resources = map(int, next(lines).split())

    # Instances without resources do not have an availability line.
    capacities = list(map(int, next(lines).split())) if num_resources else []
    resources = [Resource(capacity=cap, renewable=False) for cap in capacities]

    # Most instances are not nicely formatted since a single activity data
    # may be split over multiple lines. The way to deal with this is to iterate
    # over all values instead of parsing line-by-line.
    values = iter([val for line in lines for val in line.split()])
    activities = []

    for _ in range(num_activities):
        duration = int(next(values))
        demands = [int(next(values)) for _ in range(num_resources)]
        num_successors = int(next(values))
        successors = [int(next(values)) for _ in range(num_successors)]
        activities.append(Activity([Mode(duration, demands)], successors))

    project = Project(list(range(num_activities)))  # only one project
    return ProjectInstance(resources, [project], activities)


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    import tqdm

    DATA_DIR = Path("/Users/leonlan/Dropbox/PyJobShop/tmp/RCPLIB(1)/ALL/ALL/")
    for loc in tqdm.tqdm(DATA_DIR.rglob("*.rcp")):
        try:
            project = parse_patterson(loc)
        except Exception as e:
            print(f"Error parsing {loc}: {e}")
            continue
