import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProblemData:
    """
    Problem data class for the RCPSP based on PSPLIB files.

    Code taken from:
    https://alns.readthedocs.io/en/latest/examples/resource_constrained_project_scheduling_problem.html
    """

    num_jobs: int  # jobs in RCPSP are tasks in PyJobshop
    num_resources: int
    duration: list[int]
    successors: list[list[int]]
    predecessors: list[list[int]]
    demands: list[list[int]]
    capacities: list[int]

    @classmethod
    def read_instance(cls, path: str) -> "ProblemData":
        """
        Reads an instance of the RCPSP from a file.
        Assumes the data is in the PSPLib format.

        Loosely based on:
        https://github.com/baobabsoluciones/hackathonbaobab2020.
        """
        with open(path) as fh:
            lines = fh.readlines()

        prec_idx = lines.index("PRECEDENCE RELATIONS:\n")
        req_idx = lines.index("REQUESTS/DURATIONS:\n")
        avail_idx = lines.index("RESOURCEAVAILABILITIES:\n")

        successors = []

        for line in lines[prec_idx + 2 : req_idx - 1]:
            _, _, _, _, *jobs, _ = re.split(r"\s+", line)
            successors.append([int(x) - 1 for x in jobs])

        predecessors: list[list[int]] = [[] for _ in range(len(successors))]

        for job in range(len(successors)):
            for succ in successors[job]:
                predecessors[succ].append(job)

        demands = []
        durations = []

        for line in lines[req_idx + 3 : avail_idx - 1]:
            _, _, _, duration, *consumption, _ = re.split(r"\s+", line)
            demands.append(list(map(int, consumption)))
            durations.append(int(duration))

        _, *avail, _ = re.split(r"\s+", lines[avail_idx + 2])
        capacities = list(map(int, avail))

        return ProblemData(
            len(durations),
            len(capacities),
            durations,
            successors,
            predecessors,
            demands,
            capacities,
        )


if __name__ == "__main__":
    from pyjobshop import Model

    instance = ProblemData.read_instance("j9041_6.sm")

    model = Model()

    resources = [
        model.add_machine(capacity) for capacity in instance.capacities
    ]
    tasks = [model.add_task() for _ in range(instance.num_jobs)]

    for idx in range(instance.num_jobs):
        task = tasks[idx]
        duration = instance.duration[idx]
        demands = instance.demands[idx]

        model.add_mode(task, resources, duration, demands)

        for pred in instance.predecessors[idx]:
            model.add_end_before_start(tasks[pred], task)

        for succ in instance.successors[idx]:
            model.add_end_before_start(task, tasks[succ])

    result = model.solve("cpoptimizer")
