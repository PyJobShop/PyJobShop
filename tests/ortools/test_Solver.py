from numpy.testing import assert_

from pyjobshop.ortools.Solver import Solver
from pyjobshop.Solution import Solution, TaskData


def test_subsequent_solve_clears_hint(small):
    """
    Tests that subsequent solve calls clear the previous hint.
    """
    solver = Solver(small)

    # We first solve the model with init1 as initial solution.
    init1 = Solution([TaskData(0, 0, 1, 1), TaskData(0, 1, 2, 3)])
    result = solver.solve(initial_solution=init1)
    assert_(result.status == "Optimal")

    # Next we solve the model with a different initial solution. If
    # the hint was not cleared, OR-Tools will throw a ``MODEL_INVALID``
    # error because the model contains duplicate hints.
    init2 = Solution([TaskData(1, 0, 1, 1), TaskData(1, 1, 2, 3)])
    result = solver.solve(initial_solution=init2)
    assert_(result.status == "Optimal")
