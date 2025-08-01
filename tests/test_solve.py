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


def test_solve_unknown_solver(small):
    """
    Tests that an unknown solver raises a ValueError.
    """
    with pytest.raises(ValueError):
        solve(small, "unknown")


def test_solve_display(small, solver, capfd):
    """
    Tests that setting the display flag correctly show solver output.
    """
    solve(small, solver, display=True)
    printed = capfd.readouterr().out
    assert_(printed != "")
    assert_("PyJobShop v" in printed)
    assert_("Solving an instance with:" in printed)
    assert_("START SOLVER LOG" in printed)
    assert_("END SOLVER LOG" in printed)

    # Disabling display should not print anything.
    solve(small, solver, display=False)
    printed = capfd.readouterr().out
    assert_equal(printed, "")


def test_solve_time_limit(small, capfd):
    """
    Tests that the time limit is set by checking the display log. No test
    for CP Optimizer because it does not display this setting.
    """
    solve(small, "ortools", time_limit=1.2, display=True)
    printed = capfd.readouterr().out
    assert_("max_time_in_seconds: 1.2" in printed)


def test_solve_num_workers(small, solver, capfd):
    """
    Tests the display log that the ``num_workers`` parameter is correctly set.
    """
    solver2msg = {
        "ortools": "num_workers: 2",
        "cpoptimizer": "Using parallel search with 2 workers.",
    }
    msg = solver2msg[solver]

    solve(small, solver, num_workers=2, display=True)
    printed = capfd.readouterr().out
    assert_(msg in printed)


def test_solve_initial_solution(small, solver, capfd):
    """
    Tests that the display log is correct when an initial solution is provided.
    """
    solver2msg = {
        "ortools": "The solution hint is complete and is feasible.",
        "cpoptimizer": "Starting point is complete and consistent with constraints.",  # noqa
    }
    msg = solver2msg[solver]

    init = Solution([TaskData(0, [0], 0, 1), TaskData(1, [0], 1, 3)])
    solve(small, solver, display=True, initial_solution=init)
    printed = capfd.readouterr().out
    assert_(msg in printed)


def test_solve_additional_params(small, solver, capfd):
    """
    Tests the solve method with additional parameters can override the
    parameters supported by ``solve``.
    """
    solver2param_value = {
        "ortools": ("log_search_progress", True),
        "cpoptimizer": ("LogVerbosity", "Terse"),
    }
    param, value = solver2param_value[solver]

    # Let's test that setting display to ``False`` will not print anything.
    solve(small, solver, display=False)
    printed = capfd.readouterr().out
    assert_equal(printed, "")

    # Now we set the corresponding log parameter using the additional keyword
    # argument, which will override the earlier setting of log being False.
    solve(small, solver, display=False, **{param: value})
    printed = capfd.readouterr().out
    assert_(printed != "")
