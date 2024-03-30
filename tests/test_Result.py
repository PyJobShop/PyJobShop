from numpy.testing import assert_equal

from pyjobshop.Result import Result
from pyjobshop.Solution import Solution


def test_result_attributes(small):
    """
    Test that the attributes of a Result object are set correctly.
    """
    solution = Solution(small, [])
    result = Result("Optimal", 123.45, solution, 100)

    assert_equal(result.solve_status, "Optimal")
    assert_equal(result.runtime, 123.45)
    assert_equal(result.best, solution)
    assert_equal(result.objective_value, 100)
