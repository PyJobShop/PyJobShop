from typing import Optional

import pyjobshop.cpoptimizer as cpoptimizer
import pyjobshop.ortools as ortools
from pyjobshop.ProblemData import ProblemData
from pyjobshop.Result import Result


def solve(
    data: ProblemData,
    solver: str,
    time_limit: Optional[int] = None,
    log: bool = False,
) -> Result:
    if solver == "ortools":
        return ortools.solve(data, time_limit, log)
    elif solver == "cpoptimizer":
        return cpoptimizer.solve(data, time_limit, log)

    else:
        raise ValueError(f"Unknown solver: {solver}.")
