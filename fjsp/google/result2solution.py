from fjsp.Solution import ScheduledOperation, Solution


def result2solution(data, cp_solver, assign):
    schedule = []
    for (op, machine), var in assign.items():
        if cp_solver.Value(var.is_present):
            schedule.append(
                ScheduledOperation(
                    op,
                    machine,
                    cp_solver.Value(var.start),
                    cp_solver.Value(var.duration),
                )
            )

    return Solution(data, schedule)
