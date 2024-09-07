from dataclasses import dataclass, field


@dataclass
class Activity:
    duration: int
    demands: list[int]
    successors: list[str]


@dataclass
class Project:
    num_activities: int
    release_date: int
    uses_resources: list[int]
    activities: dict[str, Activity] = field(default_factory=dict)


@dataclass
class Portfolio:
    num_projects: int
    num_resources: int
    capacities: list[int]
    projects: dict[int, Project] = field(default_factory=dict)


def parse_rcmp(file_path: str) -> Portfolio:
    with open(file_path, "r") as f:
        lines = (line.strip() for line in f.readlines())

    num_projects = int(next(lines))
    num_resources = int(next(lines))
    capacities = list(map(int, next(lines).split()))
    portfolio = Portfolio(num_projects, num_resources, capacities)

    for project_idx in range(1, num_projects + 1):
        next(lines)  # empty line
        num_activities, release_date = map(int, next(lines).split())
        used_resources = list(map(int, next(lines).split()))
        project = Project(num_activities, release_date, used_resources)
        next(lines)  # empty line

        for activity_idx in range(1, num_activities + 1):
            activity = next(lines).split()
            idx = num_resources + 2
            duration, *demands, num_successors = list(map(int, activity[:idx]))
            successors = activity[idx:]
            assert len(successors) == num_successors
            name = f"{project_idx}:{activity_idx}"
            project.activities[name] = Activity(duration, demands, successors)

        portfolio.projects[project_idx] = project

    return portfolio


# Example usage
if __name__ == "__main__":
    from pathlib import Path

    def _order(string):
        return int(str(string).split("_")[2].split(".")[0])

    DATA_DIR = Path("tmp/instances3")
    for loc in sorted(DATA_DIR.glob("MPLIB1_*.rcmp"), key=_order):
        portfolio = parse_rcmp(loc)

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
