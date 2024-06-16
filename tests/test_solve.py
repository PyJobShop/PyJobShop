from numpy.testing import assert_, assert_equal

from pyjobshop import solve


def test_solve_additional_params_override(small, capsys):
    """
    Tests the solve method with additional parameters can override the
    parameters supported by ``solve``.
    """
    # Let's test that setting log to False will not print anything.
    solve(small, time_limit=1, log=False)
    printed = capsys.readouterr().out
    assert_equal(printed, "")

    # Now we set log_search_progress to True, which overrides the earlier
    # setting of log being False. The explicit solve parameters are
    # overriden by the addiitonal parameters.
    solve(small, time_limit=1, log=False, log_search_progress=True)
    printed = capsys.readouterr().out
    assert_(printed != "")
