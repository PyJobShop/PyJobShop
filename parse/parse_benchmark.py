import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from pyjobshop import Model, default_model, result2solution

MAX_INT = 2**25


def parser(loc: Path | str, instance_format: str) -> Model:
    lines = file2lines(loc)

    if instance_format == "fjsp":
        data = parse_fjsp(lines)
    elif instance_format == "fjsp_sdst":
        data = parse_fjsp_sdst(lines)
    elif instance_format == "fajsp":
        data = parse_fajsp(lines)
    elif instance_format == "naderi2022":
        data = parse_naderi2022(lines)
    elif instance_format == "kasapidis2021":
        data = parse_kasapidis2021(lines)
    else:
        raise ValueError(f"Unknown instance_format: {instance_format}")

    return convert_to_model(data)


@dataclass
class OperationData:
    machine: int
    processing_time: int


@dataclass
class ParsedData:
    """
    Dataclass to hold the parsed data from the benchmark instances.

    Parameters
    ----------
    num_machines
        The number of machines in the instance.
    jobs
        A list of jobs, where each job is a list of operations. Each operation
        is a dictionary with the keys "machine" and "processing_time".
    precedence
        A list of tuples (from, to) representing the precedence relationships
        among operations. From and to are the indices of the operations.
    """

    num_machines: int
    jobs: list[list[list[OperationData]]]
    precedence: list[tuple[int, int]]
    setup_times: Optional[np.ndarray] = None


def parse_fjsp_job_operation_data_line(
    line: list[float],
) -> list[list[OperationData]]:
    """
    Parses a standard formatted FJSP job-operation data line:
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
            machine = int(line[idx])
            processing_time = int(line[idx + 1])
            operation.append(OperationData(machine, processing_time))
            idx += 2

        operations.append(operation)

    assert len(operations) == num_operations

    return operations


def parse_fjsp(lines: list[list[float]]) -> ParsedData:
    """
    Parses a flexible job shop problem instance that has the classical FJSP
    benchmark instance format.
    """
    # First line contains metadata.
    num_jobs, num_machines, avg_ops_per_job = lines[0]

    # The remaining lines contain the job-operation data, where each line
    # represents a job and its operations.
    jobs = [parse_fjsp_job_operation_data_line(line) for line in lines[1:]]

    # Precedence relationships between operations can be assumed from FJSP
    # problem definition, where operations are processed in sequence of their
    # appearance in the job-operation data.
    precedences = []
    idx = 0
    for operations in jobs:
        num_operations = len(operations)

        for _ in range(num_operations - 1):
            precedences.append((idx, idx + 1))
            idx += 1

        idx += 1  # skip to the next job

    return ParsedData(int(num_machines), jobs, precedences)


def parse_fjsp_sdst(lines: list[list[float]]) -> ParsedData:
    """
    Parses a flexible job shop problem with sequence-dependent setup times
    instance.
    """
    # The first part of the file is the same as the classic FJSP format.
    num_jobs, _, _ = lines[0]
    data = parse_fjsp(lines[: num_jobs + 1])

    # The remaining lines contain the setup times, which are represented
    # as a matrix of size num_operations x num_operations for each machine.
    setup_times = np.array(lines[num_jobs + 1 :])
    splits = np.array_split(setup_times, data.num_machines)
    data.setup_times = np.stack(splits)

    return data


def parse_fajsp(lines: list[list[float]]) -> ParsedData:
    """
    Parses a flexible assembly job shop problem instance from
    Birgin et al. (2014). These are the "DAFJS" named instances.
    """
    num_operations, num_arcs, num_machines = lines[0]

    precedence = []
    for line in lines[1 : num_arcs + 1]:
        precedence.append(tuple(line))  # to -> from

    operations = []
    for line in lines[num_arcs + 1 :]:
        operation = []
        num_eligible_machines = int(line[0])

        for idx in range(num_eligible_machines):
            machine = int(line[(idx * 2) + 1])
            processing_time = int(line[(idx * 2) + 2])
            operation.append(OperationData(machine, processing_time))

        operations.append(operation)

    # There are no jobs defined in this instance format, so we just store the
    # operations as a single job.
    jobs = [operations]

    return ParsedData(num_machines, jobs, precedence)


def parse_yfjs(lines: list[list[float]]) -> ParsedData:
    """
    Parses a flexible job shop problem instance with complex precedence
    constraints from Birgin et al. (2014).
    """

    # First four lines contain metadata about the number of jobs,
    # operation per job, number of machines and machines/operation.
    def _parse_metadata(line: list[float]):
        return int(line.split(":")[-1].strip())

    metadata = lines[:4]
    num_jobs = _parse_metadata(metadata[0])
    num_operations_per_job = _parse_metadata(metadata[1])
    num_machines = _parse_metadata(metadata[2])
    num_machines_per_operation = _parse_metadata(metadata[3])

    # The rest is mostly the same as the `fajsp` format, but
    # there are multiple jobs to be completed.
    OFFSET = 3
    _, num_arcs, _ = lines[1 + OFFSET]

    precedence = []
    for line in lines[2 + OFFSET : num_arcs + 2 + OFFSET]:
        precedence.append(tuple(line))  # to -> from

    jobs = []
    operations = []
    for op_idx, line in enumerate(lines[num_arcs + 2 + OFFSET :], 1):
        operation = []
        num_eligible_machines = int(line[0])

        for idx in range(num_eligible_machines):
            machine = line[(idx * 2) + 1]
            processing_time = line[(idx * 2) + 2]
            operation.append(OperationData(machine, processing_time))

        operations.append(operation)

        # Store every `num_operations_per_job` operations as a single job.
        if op_idx % num_operations_per_job == 0:
            jobs.append(operations)
            operations = []

    return ParsedData(num_machines, jobs, precedence)


def parse_naderi2022(lines: list[list[float]]) -> ParsedData:
    """
    Parses an FJSP instance from Naderi et al. (2022).
    """
    num_jobs = lines[0][0]
    num_machines = lines[1][0]

    num_operations_per_job = lines[2]
    num_operations = sum(num_operations_per_job)

    # The rest of the lines contain the processing times for each operation
    # and machine pair.
    processing_times = np.array(lines[3:])

    jobs = []
    indices = np.cumsum([0] + num_operations_per_job)

    for start, end in zip(indices[:-1], indices[1:]):
        operations = []
        for durations in processing_times[start:end, :]:
            operation = []
            for machine in np.flatnonzero(durations):
                operation.append(OperationData(machine, durations[machine]))

            operations.append(operation)

        jobs.append(operations)

    # Arc for each sequential operation pair for each job.
    precedence = [
        (op, op + 1)
        for idx in range(num_jobs)
        for op in range(indices[idx], indices[idx + 1] - 1)
    ]

    return ParsedData(num_machines, jobs, precedence)


def parse_kasapidis2021(lines: list[list[float]]) -> ParsedData:
    """
    Parses an FJSP instance with complex precedence constraints
    from Kasapidis et al. (2021).
    """
    num_jobs, num_machines, _, _, _ = lines[0]

    jobs = []
    for line in lines[1 : num_jobs + 1]:
        jobs.append(parse_fjsp_job_operation_data_line(line))

    precedence = set()
    for op_idx, line in enumerate(lines[num_jobs + 1 :]):
        num_predecessors = line[0]
        num_successors = line[num_predecessors + 1]

        for pred in line[1 : num_predecessors + 1]:
            precedence.add((pred, op_idx))

        for succ in line[num_predecessors + 2 :]:
            precedence.add((op_idx, succ))

    return ParsedData(num_machines, jobs, precedence)


def file2lines(loc: Path | str) -> list[list[float]]:
    with open(loc, "r") as fh:
        lines = [line for line in fh.readlines() if line.strip()]

    return [[parse_num(x) for x in line.split()] for line in lines]


def parse_num(c: str) -> int | float:
    return float(c) if "." in c else int(c)


def convert_to_model(data: ParsedData) -> Model:
    """
    Converts the parsed data to a Model instance.
    """
    m = Model()

    jobs = [m.add_job() for _ in range(len(data.jobs))]
    machines = [m.add_machine() for _ in range(data.num_machines)]
    operations = []

    for job_idx, job_data in enumerate(data.jobs):
        job = jobs[job_idx]

        for operation in job_data:
            op = m.add_operation(job=job)
            operations.append(op)

            for op_data in operation:
                machine = machines[op_data.machine - 1]
                duration = op_data.processing_time
                m.add_processing_time(machine, op, duration)

    for frm, to in data.precedence:
        m.add_timing_precedence(operations[frm], operations[to])

    return m


if __name__ == "__main__":
    argparser = argparse.ArgumentParser()
    argparser.add_argument("instances", type=Path, nargs="+")
    argparser.add_argument("--instance_format", default="fjsp")
    argparser.add_argument("--time_limit", type=int, default=2)

    args = argparser.parse_args()

    for instance in args.instances:
        print(f"Processing {instance}... ", end="")
        model = parser(instance, args.instance_format)
        data = model.data()
        cp_model = default_model(data)
        result = cp_model.solve(
            TimeLimit=args.time_limit,
            LogVerbosity="Quiet",
        )
        print(result.solve_status, round(result.get_solve_time(), 2))

        solution = result2solution(data, result)
