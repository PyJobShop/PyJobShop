from numpy.testing import assert_equal

from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution


def test_result_attributes():
    """
    Test that the attributes of a Result object are set correctly.
    """
    solution = Solution([])
    result = Result(SolveStatus.OPTIMAL, 123.45, solution, 100)

    assert_equal(result.status, SolveStatus.OPTIMAL)
    assert_equal(result.runtime, 123.45)
    assert_equal(result.best, solution)
    assert_equal(result.objective, 100)


def test_result_string_representation():
    """
    Test that the string representation of a Result object is correct.
    """
    solution = Solution([])
    result = Result(SolveStatus.OPTIMAL, 123.45, solution, 100)
    expected = (
        "Solver results\n"
        "==============\n"
        "   status: OPTIMAL\n"
        "  runtime: 100\n"
        "objective: 123.45"
    )

    assert_equal(result, expected)
