from numpy.testing import assert_

from pyjobshop.solvers.cpoptimizer.Solver import Solver


def test_solve_initial_solution(complete_data, complete_sol, capfd):
    """
    Tests that the solver correctly hints the solution by checking that the
    display log is correct when an initial solution is provided.
    """
    solver = Solver(complete_data)
    solver.solve(display=True, initial_solution=complete_sol)

    msg = "Starting point is complete and consistent with constraints."
    printed = capfd.readouterr().out
    assert_(msg in printed)
