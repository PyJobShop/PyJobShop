from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from psplib.ProjectInstance import Mode, ProjectInstance, Resource

from pyjobshop import Model


@dataclass
class Activity:
    """
    Activity class.

    Parameters
    ----------
    modes
        The processing modes of this activity.
    successors
        The indices of successor activities.
    delays
        The delay for each successor activity. If delays are specified, then
        the length of this list must be equal to the length of `successors`.
        Moreover, delays are used for RCPSP/max instances, where the
        precedence is defined as ``start(pred) + delay <= start(succ)``.
    name
        Optional name of the activity to identify this activity. This is
        helpful to map this activity back to the original problem instance.
    """

    modes: list[Mode]
    successors: list[int]
    delays: Optional[list[int]]
    name: str = ""

    def __post_init__(self):
        if self.delays and len(self.successors) != len(self.delays):
            raise ValueError("Length of successors and delays must be equal.")

    @property
    def num_modes(self):
        return len(self.modes)


def parse_rcpsp_max(loc: str | Path) -> list[ProjectInstance]:
    with open(loc, "r") as fh:
        lines = iter(line.strip() for line in fh.readlines() if line.strip())

    num_activities, num_renewables, *_ = map(int, next(lines).split())
    num_activities += 2  # source and target
    activities = []

    succ_lines = [next(lines).split() for _ in range(num_activities)]
    activity_lines = [next(lines).split() for _ in range(num_activities)]

    for idx in range(num_activities):
        _, _, num_successors, *succ = succ_lines[idx]
        successors = list(map(int, succ[: int(num_successors)]))
        delays = [int(val.strip("[]")) for val in succ[int(num_successors) :]]

        _, _, duration, *demands = map(int, activity_lines[idx])

        activity = Activity([Mode(duration, demands)], successors, delays)
        activities.append(activity)

    capacities = map(int, next(lines).split())
    resources = [Resource(capacity, renewable=True) for capacity in capacities]

    return ProjectInstance(resources, [], activities)


def _project_instance_to_model(instance: ProjectInstance) -> Model:
    model = Model()

    resources = [
        model.add_renewable(capacity=res.capacity)
        for res in instance.resources
    ]

    for _ in instance.activities:
        model.add_task()

    for idx, activity in enumerate(instance.activities):
        for mode in activity.modes:
            model.add_mode(
                task=model.tasks[idx],
                resources=resources,
                duration=mode.duration,
                demands=mode.demands,
            )

    for idx, activity in enumerate(instance.activities):
        assert activity.delays is not None
        for succ_idx, delay in zip(activity.successors, activity.delays):
            j = model.tasks[idx]
            l = model.tasks[succ_idx]
            model.add_start_before_start(j, l, delay)  # s(j) <= s(l) + delay

    return model


if __name__ == "__main__":
    DATA_DIR = Path("tmp/ubo500")
    for loc in DATA_DIR.glob("*.sch"):
        instance = parse_rcpsp_max(loc)
        model = _project_instance_to_model(instance)
        solver = "ortools"
        # solver = "cpoptimizer"
        model.solve(display=True, solver=solver, num_workers=8)
