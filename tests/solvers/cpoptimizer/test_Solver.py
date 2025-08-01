from numpy.testing import assert_

from pyjobshop.Solution import Solution, TaskData
from pyjobshop.solvers.ortools.Solver import Solver


def test_solve_initial_solution(complete, capfd):
    """
    Tests that the solver correctly hints the solution by checking that the
    display log is correct when an initial solution is provided.
    """
    solver = Solver(complete)
    init = Solution(
        [
            TaskData(0, [0], 0, 1),
            TaskData(1, [0], 2, 3),
            TaskData(2, [1], 1, 2),
            TaskData(4, [2], 0, 1),
        ]
    )
    solver.solve(display=True, initial_solution=init)

    msg = "The solution hint is complete and is feasible."
    printed = capfd.readouterr().out
    assert_(msg in printed)
