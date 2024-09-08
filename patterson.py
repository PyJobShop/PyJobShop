from dataclasses import dataclass, field


@dataclass
class Activity:
    duration: int
    demands: list[int]
    successors: list[int]


@dataclass
class Project:
    num_activities: int
    num_resources: int
    capacities: list[int]
    activities: dict[int, Activity] = field(default_factory=dict)


def parse_patterson(file_path: str) -> Project:
    with open(file_path, "r") as fh:
        # Strip all lines and ignore all empty lines.
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    num_activities, num_resources = map(int, next(lines).split())

    # Instances without resources do not have an availability line.
    capacities = list(map(int, next(lines).split())) if num_resources else []
    project = Project(num_activities, num_resources, capacities)

    # Most instances do not perfectly follow the Patterson format because
    # a single activity may be split over multiple lines. The way to deal with
    # this is to iterate over all values (instead of lines).
    values = iter([val for line in lines for val in line.split()])
    activity_idx = 0

    while activity_idx < num_activities:
        duration = int(next(values))
        demands = [int(next(values)) for _ in range(num_resources)]
        num_successors = int(next(values))
        successors = [int(next(values)) for _ in range(num_successors)]
        project.activities[activity_idx] = Activity(
            duration, demands, successors
        )
        activity_idx += 1

    return project


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
