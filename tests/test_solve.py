import pytest
from numpy.testing import assert_, assert_equal

from pyjobshop import solve
from pyjobshop.Solution import Solution, TaskData


def test_solve(small, solver):
    """
    Tests that solve returns the expected result.
    """
    result = solve(small, solver)

    assert_equal(result.status.value, "Optimal")
    assert_(result.runtime < 1)
    assert_equal(result.objective, 3)


def test_unknown_solver(small):
    """
    Tests that an unknown solver raises a ValueError.
    """
    with pytest.raises(ValueError):
        solve(small, "unknown")


def test_solve_initial_solution(small, capsys):
    init = Solution([TaskData(0, 0, 1, 1), TaskData(0, 1, 2, 3)])
    solve(
        small,
        "ortools",
        log=True,
        initial_solution=init,
        fix_variables_to_their_hinted_value=True,
    )
    printed = capsys.readouterr().out

    assert_("The solution hint is complete and is feasible." in printed)

    # OR Tools shows [hint]
    # CP Optimizer? I don't know.
    pass


# def describe_solve_set_default_parameters():
#     """
#     Tests `solve` when setting the default parameters.
#     """

#     def log(small, solver, capsys):
#         """
#         Checks that setting the log flag correctly show solver output.
#         """
#         if solver == "cpoptimizer":
#             return  # TODO See #152.

#         solve(small, solver, log=True)
#         printed = capsys.readouterr().out
#         assert_(printed != "")

#         solve(small, solver, log=False)
#         printed = capsys.readouterr().out
#         assert_equal(printed, "")

#     def time_limit(small, capsys):
#         """
#         Checks the log that the time limit is set. No test for CP Optimizer
#         because it does not log this setting.
#         """
#         solve(small, "ortools", time_limit=1.2, log=True)
#         printed = capsys.readouterr().out
#         assert_("max_time_in_seconds: 1.2" in printed)

#     def num_workers(small, solver, capsys):
#         """
#         Checks the log that the ``num_workers`` parameter is correctly set.
#         """
#         if solver == "cpoptimizer":
#             return  # TODO See #152.

#         solve(small, solver, num_workers=1, log=True)
#         printed = capsys.readouterr().out
#         assert_("num_workers: 1" in printed)


# @pytest.mark.parametrize(
#     "solver_, param, value",
#     [
#         ("ortools", "log_search_progress", True),
#         # ("cpoptimizer", "LogVerbosity", "Quiet"), # TODO See #152.
#     ],
# )
# def test_solve_additional_params(small, capsys, solver_, param, value):
#     """
#     Tests the solve method with additional parameters can override the
#     parameters supported by ``solve``.
#     """
#     # Let's test that setting log to False will not print anything.
#     solve(small, solver_, log=False)
#     printed = capsys.readouterr().out
#     assert_equal(printed, "")

#     # Now we set the corresponding log parameter using the additional keyword
#     # argument, which will override the earlier setting of log being False.
#     solve(small, solver_, log=False, **{param: value})
#     printed = capsys.readouterr().out
#     assert_(printed != "")
