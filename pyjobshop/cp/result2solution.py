from docplex.cp.solution import CpoSolveResult

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution, Task


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
            op, machine = [int(num) for num in name[1:].split("_")]
            start = var.start
            duration = var.size

            schedule.append(Task(op, machine, start, duration))

    return Solution(data, schedule)
