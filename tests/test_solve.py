from numpy.testing import assert_, assert_equal

from pyjobshop import solve


def test_solve_ortools_log(small, capsys):
    """
    Tests the solve method with the log parameter set to True displays output.
    """
    solve(small, "ortools", time_limit=1, log=True)
    printed = capsys.readouterr().out
    assert_(printed != "")

    solve(small, "ortools", time_limit=1, log=False)
    printed = capsys.readouterr().out
    assert_equal(printed, "")


def test_solve_ortools_num_workers(small, capsys):
    """
    Tests the solve method with the num_workers parameter set.
    """
    solve(small, "ortools", time_limit=1, num_workers=1, log=True)
    printed = capsys.readouterr().out

    assert_("num_workers: 1" in printed)
    # TODO Test OR Tools and CP Optimizer separately.


def test_solve_additional_params(small, capsys):
    """
    Tests the solve method with additional parameters.
    """
    pass  # TODO


def test_solve_ortools_additional_params_override(small, capsys):
    """
    Tests the solve method with additional parameters can override the
    parameters supported by ``solve``.
    """
    # Let's test that setting log to False will not print anything.
    solve(small, "ortools", time_limit=1, log=False)
    printed = capsys.readouterr().out
    assert_equal(printed, "")

    # Now we set log_search_progress to True, which overrides the earlier
    # setting of log being False. The explicit solve parameters are
    # overriden by the addiitonal parameters.
    solve(small, "ortools", time_limit=1, log=False, log_search_progress=True)
    printed = capsys.readouterr().out
    assert_(printed != "")


def test_solve_cpoptimizer_additional_params_override(small, capsys):
    pass  # TODO
