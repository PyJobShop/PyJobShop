from collections import defaultdict
from pathlib import Path

from pyjobshop.ProblemData import ProblemData


def write(where: Path, data: ProblemData):
    """
    Writes a problem data instance to FJSPLIB formatted instance.

    Parameters
    ----------
    where
        Location to write the instance to.
    data
        The problem data instance.
    """
    lines = []

    flexibility = len(data.operations) / (data.num_machines)
    lines.append(f"{data.num_jobs} {data.num_machines} {flexibility}")

    eligible = defaultdict(list)  # machines + duration for each operation
    for (machine, operation), duration in data.processing_times.items():
        # Machine indices are 1-indexed in FJSPLIB
        eligible[operation].append((machine + 1, duration))

    for idx in range(len(data.jobs)):
        num_ops = len(data.job2ops[idx])
        line = [num_ops]

        for op in data.job2ops[idx]:
            num_eligible = len(eligible[op])
            line.append(num_eligible)

            for machine, duration in eligible[op]:
                line.extend([machine, duration])

        lines.append(" ".join(str(val) for val in line))

    formatted = "\n".join(lines)

    with open(where, "w") as fh:
        fh.write(formatted)
