import pytest
from numpy.testing import assert_, assert_equal

from pyjobshop import solve


def describe_solve_set_default_parameters():
    """
    Tests `solve` when setting the default parameters.
    """

    def log(small, solver, capsys):
        """
        Set the log parameter.
        """
        if solver == "ortools":  # TODO fix cpoptiimzer
            solve(small, solver, log=True)
            printed = capsys.readouterr().out
            assert_(printed != "")

            solve(small, solver, log=False)
            printed = capsys.readouterr().out
            assert_equal(printed, "")

    def time_limit(small, capsys):
        """
        TODO Ignore CP Optimizer because it does not set it.
        """
        solve(small, "ortools", time_limit=1.2, log=True)
        printed = capsys.readouterr().out
        assert_("max_time_in_seconds: 1.2" in printed)

    def num_workers(small, solver, capsys):
        """
        Test that ``num_workers`` parameter is correctly set.
        """
        solve(small, solver, num_workers=1, log=True)

        # We test this by checking the solver log about num workers.
        printed = capsys.readouterr().out

        if solver == "ortools":
            assert_("num_workers: 1" in printed)
        elif solver == "cpoptimizer":
            pass  # TODO


@pytest.mark.parametrize(
    "solver_, param, value",
    [
        ("ortools", "log_search_progress", True),
        # ("cpoptimizer", "LogVerbosity", "Quiet"), # TODO
    ],
)
def test_solve_additional_params(small, capsys, solver_, param, value):
    """
    Tests the solve method with additional parameters can override the
    parameters supported by ``solve``.
    """
    # Let's test that setting log to False will not print anything.
    solve(small, solver_, log=False)
    printed = capsys.readouterr().out
    assert_equal(printed, "")

    # Now we set the corresponding log parameter using the additional keyword
    # argument, which will override the earlier setting of log being False.
    solve(small, solver_, log=False, **{param: value})
    printed = capsys.readouterr().out
    assert_(printed != "")
