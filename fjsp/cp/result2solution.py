from docplex.cp.solution import CpoSolveResult

from fjsp.ProblemData import ProblemData
from fjsp.Solution import ScheduledOperation, Solution


def result2solution(data: ProblemData, result: CpoSolveResult) -> Solution:
    """
    Maps a ``CpoSolveResult`` object to a ``Solution`` object.
    """
    schedule = []

    for var in result.get_all_var_solutions():
        name = var.get_name()

        # Scheduled operations are inferred from variables start with an "A"
        # (assignment) and that are present in the solution.
        if name.startswith("A") and var.is_present():
            op_idx, mach_idx = [int(num) for num in name.split("_")[1:]]
            op = data.operations[op_idx]
            start = var.start
            duration = var.size

            schedule.append(ScheduledOperation(op, mach_idx, start, duration))

    return Solution(data, schedule)
