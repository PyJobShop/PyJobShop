import argparse
from pathlib import Path

import numpy as np

from pyjobshop import Model, default_model, result2solution

MAX_INT = 2**25


def parser(loc: Path | str, instance_format: str) -> Model:
    lines = file2lines(loc)

    if instance_format == "jsp":
        data = parse_jsp(lines)
        return convert_to_model(data)
    elif instance_format == "fjsp":
        data = parse_fjsp(lines)
        return convert_to_model(data)
    elif instance_format == "fjsp_sdst":
        data = parse_fjsp_sdst(lines)
        return convert_to_model(data)
    elif instance_format == "fajsp":
        data = parse_fajsp(lines)
        return convert_to_model(data)
    elif instance_format == "naderi2022":
        return parse_naderi2022(lines)
    elif instance_format == "yfjs":
        return parse_yfjs(lines)
    elif instance_format == "Kasapidis2021":
        return parse_kasapidis2021(lines)
    else:
        raise ValueError(f"Unknown instance_format: {instance_format}")


def parse_jsp(lines: list[list[float]]) -> dict:
    """
    Parses a job shop problem instance.
    """
    data = {"jobs": [], "precedence": []}

    # First line contains metadata.
    num_jobs, num_machines = lines[0]
    data["num_jobs"] = num_jobs
    data["num_machines"] = num_machines

    # Remaining lines contain operation data per job.
    for job, line in enumerate(lines[1:]):
        num_operations = len(line) // 2
        operations = []

        for idx in range(num_operations):
            machine = line[idx * 2]
            processing_time = line[idx * 2 + 1]
            operations.append(
                [{"machine": machine, "processing_time": processing_time}]
            )

        data["jobs"].append(operations)

    # Precedence relationships among jobs.
    data["precedence"] = []
    op_idx = 0
    for ops in data["jobs"]:
        for _ in range(len(ops) - 1):
            data["precedence"].append((op_idx, op_idx + 1))
            op_idx += 1

        op_idx += 1

    return data


def parse_fjsp_job_operation_data_line(
    line: list[float],
) -> list[dict[str, float]]:
    """
    Parses a standard instance_formatted FJSP job-operation data line:
    - The first number is the number of operations (n >= 1) of that job.
    - Repeat for n times:
        - First a number k >= 1 that represents the number of machines that can
          process the operation.
        - Then there are k pairs of numbers (machine, processing time) that
          specify which are the machines and the processing times.
    """
    num_operations = line[0]
    operations = []
    idx = 1

    while idx < len(line):
        num_eligible_machines = int(line[idx])
        idx += 1
        operation = []

        for _ in range(num_eligible_machines):
            machine = line[idx]
            processing_time = line[idx + 1]
            operation.append(
                {"machine": machine, "processing_time": processing_time}
            )
            idx += 2

        operations.append(operation)

    assert len(operations) == num_operations

    return operations


def parse_fjsp(lines: list[list[float]]) -> dict:
    """
    Parses a flexible job shop problem instance that has the classical FJSP
    benchmark instance instance_format.
    """
    data: dict[str, float | str | list] = {"jobs": [], "precedence": []}

    # First line contains metadata.
    num_jobs, num_machines, _ = lines[0]
    data["num_jobs"] = num_jobs
    data["num_machines"] = num_machines

    for job, line in enumerate(lines[1:]):
        data["jobs"].append(parse_fjsp_job_operation_data_line(line))

    # Precedence relationships among operations.
    op_idx = 0
    for ops in data["jobs"]:
        for _ in range(len(ops) - 1):
            data["precedence"].append((op_idx, op_idx + 1))
            op_idx += 1

        op_idx += 1

    return data


def parse_fjsp_sdst(lines: list[list[float]]) -> dict:
    """
    Parses a flexible job shop problem with sequence-dependent setup times
    instance.
    """
    # The first part of the file is the same as the classic FJSP instance_format.
    num_jobs, _, _ = lines[0]
    data = parse_fjsp(lines[: num_jobs + 1])

    # The remaining lines contain the setup times, which are represented
    # as a matrix of size num_operations x num_operations for each machine.
    setup_times = np.array(lines[num_jobs + 1 :])
    splits = np.array_split(setup_times, data["num_machines"])
    data["setup_times"] = np.stack(splits)

    return data


def parse_fajsp(lines: list[list[float]]) -> dict:
    """
    Parses a flexible assembly job shop problem instance.
    """
    data: dict[str, float | str | list] = {"jobs": [], "precedence": []}

    num_operations, num_arcs, num_machines = lines[0]
    data["num_operations"] = num_operations
    data["num_arcs"] = num_arcs
    data["num_machines"] = num_machines

    for line in lines[1 : num_arcs + 1]:
        data["precedence"].append(tuple(line))  # to -> from

    operations = []
    for line in lines[num_arcs + 1 :]:
        operation = []
        num_eligible_machines = int(line[0])

        for idx in range(num_eligible_machines):
            machine = line[(idx * 2) + 1]
            processing_time = line[(idx * 2) + 2]
            operation.append(
                {"machine": machine, "processing_time": processing_time}
            )

        operations.append(operation)

    # One job that contains all operations.
    data["jobs"].append(operations)
    data["num_jobs"] = 1

    return data


def parse_yfjs(lines: list[list[float]]) -> Model:
    # First four lines contain metadata about the number of jobs,
    # operation per job, number of machines and machines/operation.
    def _parse_metadata(line: list[float]):
        return int(line.split(":")[-1].strip())

    data = {"jobs": [], "precedence": []}

    metadata = lines[:4]
    data["num_jobs"] = _parse_metadata(metadata[0])
    data["num_operations_per_job"] = _parse_metadata(metadata[1])
    data["num_machines"] = _parse_metadata(metadata[2])
    data["num_machines_per_operation"] = _parse_metadata(metadata[3])

    # The rest is mostly the same as the `fajsp` instance_format, but
    # there are multiple jobs to be completed.
    OFFSET = 3
    _, num_arcs, _ = lines[1 + OFFSET]

    for line in lines[2 + OFFSET : num_arcs + 2 + OFFSET]:
        data["precedence"].append(tuple(line))  # to -> from

    operations = []
    for op_idx, line in enumerate(lines[num_arcs + 2 + OFFSET :], 1):
        operation = []
        num_eligible_machines = int(line[0])

        for idx in range(num_eligible_machines):
            machine = line[(idx * 2) + 1]
            processing_time = line[(idx * 2) + 2]
            operation.append(
                {"machine": machine, "processing_time": processing_time}
            )

        operations.append(operation)

        # Store every `num_operations_per_job` operations as a single job.
        if op_idx % data["num_operations_per_job"] == 0:
            data["jobs"].append(operations)
            operations = []

    return convert_to_model(data)


def parse_naderi2022(lines: list[list[float]]) -> Model:
    data = {}

    data["num_jobs"] = lines[0][0]
    data["num_machines"] = lines[1][0]

    num_operations_per_job = lines[2]
    data["num_operations"] = sum(num_operations_per_job)

    processing_times = np.array(lines[3:])
    data["processing_times"] = np.where(
        processing_times, processing_times, MAX_INT
    )

    # Arc for each sequential operation pair for each job.
    cumul = np.cumsum([0] + num_operations_per_job)
    data["precedence"] = [
        (op, op + 1)
        for idx in range(data["num_jobs"])
        for op in range(cumul[idx], cumul[idx + 1] - 1)
    ]

    # Convert to Model.
    model = Model()

    jobs = [model.add_job() for _ in range(data["num_jobs"])]
    machines = [model.add_machine() for _ in range(data["num_machines"])]

    operations = []
    for idx, job in enumerate(jobs):
        for _ in range(cumul[idx], cumul[idx + 1]):
            operations.append(model.add_operation(job, machines))

    for op_idx, op in enumerate(operations):
        for m_idx, machine in enumerate(machines):
            model.add_processing_time(
                machine, op, data["processing_times"][op_idx][m_idx]
            )

    return model


def parse_kasapidis2021(lines: list[list[float]]) -> Model:
    """
    Parses an FJSP instance with complex precedence constraints
    from Kasapidis et al. (2021).
    """
    data = {"jobs": [], "precedence": set()}

    num_jobs, num_machines, _, _, _ = lines[0]
    data["num_jobs"] = num_jobs
    data["num_machines"] = num_machines

    for line in lines[1 : num_jobs + 1]:
        data["jobs"].append(parse_fjsp_job_operation_data_line(line))

    for op_idx, line in enumerate(lines[num_jobs + 1 :]):
        num_predecessors = line[0]
        num_successors = line[num_predecessors + 1]

        for pred in line[1 : num_predecessors + 1]:
            data["precedence"].add((pred, op_idx))

        for succ in line[num_predecessors + 2 :]:
            data["precedence"].add((op_idx, succ))

    return convert_to_model(data)


def file2lines(loc: Path | str) -> list[list[float]]:
    with open(loc, "r") as fh:
        lines = [line for line in fh.readlines() if line.strip()]

    return [
        [parse_num(x) for x in line.split()]
        if not line.startswith("#")  # Shitty hack to deal with yfjsp
        else line
        for line in lines
    ]


def parse_num(c: str) -> int | float:
    return float(c) if "." in c else int(c)


def convert_to_model(data: dict) -> Model:
    m = Model()

    jobs = [m.add_job() for _ in range(data["num_jobs"])]
    machines = [m.add_machine() for _ in range(data["num_machines"])]
    operations = []

    for job_idx, ops in enumerate(data["jobs"]):
        job = jobs[job_idx]

        for op_data in ops:
            op = m.add_operation(job=job)
            operations.append(op)

            for item in op_data:
                machine = machines[item["machine"] - 1]
                duration = item["processing_time"]
                m.add_processing_time(machine, op, duration)

    for frm, to in data["precedence"]:
        m.add_timing_precedence(operations[frm], operations[to])

    return m


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("instances", type=Path, nargs="+")
    argparser.add_argument("--instance_format", default="pyjobshop")
    argparser.add_argument("--time_limit", type=int, default=2)

    args = argparser.parse_args()

    for instance in args.instances:
        print(f"Processing {instance}... ", end="")
        model = parser(instance, args.instance_format)
        data = model.data()
        cp_model = default_model(data)
        result = cp_model.solve(
            TimeLimit=args.time_limit, LogVerbosity="Terse"
        )
        print(result.solve_status)

        solution = result2solution(data, result)
        # plot(data, solution)

# poetry run python parse/parse_benchmark.py data/raw/fjsp/3_DauzerePaulli/01a.fjs --time_limit 20
# poetry run python parse_benchmark.py data/raw/Kasapidis2021/CPC_MEDIUM_INSTANCES/scpc01.fjs --instance_format Kasapidis2021 --time_limit 20
# poetry run python parse_benchmark.py data/raw/Kasapidis2021/CPC_LARGE_INSTANCES/bcpc10.fjs --instance_format Kasapidis2021 --time_limit 100
