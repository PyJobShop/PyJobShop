from typing import Optional

from docplex.cp.solution import CpoSolveResult

import pyjobshop.cpoptimizer as cpoptimizer
import pyjobshop.ortools as ortools
from ortools.sat.python.cp_model import CpSolver
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result


def solve(
    data: ProblemData,
    solver: str,
    time_limit: Optional[int] = None,
    log: bool = False,
) -> Result:
    if solver == "ortools":
        ort_model, op_vars, assign_vars = ortools.default_model(data)

        cp_solver = CpSolver()

        if time_limit is not None:
            cp_solver.parameters.max_time_in_seconds = time_limit

        status_code = cp_solver.Solve(ort_model)
        status = cp_solver.StatusName(status_code)
        objective = cp_solver.ObjectiveValue()
        print(f"Solve status: {status}")
        print(f"Optimal objective value: {objective}")

        if status != "INFEASIBLE":
            solution = ortools.result2solution(data, cp_solver, assign_vars)
        else:
            solution = None

        return Result(
            status.capitalize(),
            cp_solver.WallTime(),
            solution,
            objective,
        )

    elif solver == "cpoptimizer":
        cp_model = cpoptimizer.default_model(data)

        log_verbosity = "Terse" if log else "Quiet"
        kwargs = {"TimeLimit": time_limit, "LogVerbosity": log_verbosity}
        cp_result: CpoSolveResult = cp_model.solve(**kwargs)  # type: ignore

        solve_status = cp_result.get_solve_status()
        runtime = cp_result.get_solve_time()

        if solve_status == "Infeasible":
            solution = None
            objective_value = None
        else:
            solution = cpoptimizer.result2solution(data, cp_result)
            objective_value = cp_result.get_objective_value()

        return Result(solve_status, runtime, solution, objective_value)

    else:
        raise ValueError(f"Unknown solver: {solver}.")
