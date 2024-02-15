from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution, Task


def result2solution(data: ProblemData, cp_solver, assign) -> Solution:
    """
    Converts a result from a CP solver to a Solution object.

    Parameters
    ----------
    ...
    """
    schedule = []

    for (op, machine), var in assign.items():
        if cp_solver.Value(var.is_present):
            start = cp_solver.Value(var.start)
            duration = cp_solver.Value(var.duration)
            schedule.append(Task(op, machine, start, duration))

    return Solution(data, schedule)
