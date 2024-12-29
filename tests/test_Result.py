from numpy.testing import assert_equal

from pyjobshop.Result import Result, SolveStatus
from pyjobshop.Solution import Solution


def test_result_attributes():
    """
    Test that the attributes of a Result object are set correctly.
    """
    solution = Solution([])
    result = Result(
        objective=100,
        lower_bound=100,
        status=SolveStatus.OPTIMAL,
        runtime=123.45,
        best=solution,
    )

    assert_equal(result.objective, 100)
    assert_equal(result.lower_bound, 100)
    assert_equal(result.status, SolveStatus.OPTIMAL)
    assert_equal(result.runtime, 123.45)
    assert_equal(result.best, solution)


def test_result_string_representation():
    """
    Test that the string representation of a Result object is correct.
    """
    solution = Solution([])
    result = Result(
        objective=123.45,
        lower_bound=float("-inf"),
        status=SolveStatus.OPTIMAL,
        runtime=100.00001,
        best=solution,
    )
    expected = (
        "Solution results\n"
        "================\n"
        "  objective: 123.45\n"
        "lower bound: -inf\n"
        "     status: Optimal\n"
        "    runtime: 100.00 seconds"
    )

    assert_equal(str(result), expected)
