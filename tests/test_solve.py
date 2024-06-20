import pytest
from numpy.testing import assert_, assert_equal

from pyjobshop import Model, solve
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


def test_solve_initial_solution(small, capfd):
    init = Solution([TaskData(0, 0, 1, 1), TaskData(0, 1, 2, 3)])
    solve(
        small,
        "ortools",
        log=True,
        initial_solution=init,
        fix_variables_to_their_hinted_value=True,
    )
    printed = capfd.readouterr().out

    # Not all variables are hinted (only job/task/task_alt) so this message
    # is correct.
    assert_("The solution hint is incomplete" in printed)

    # TODO CP Optimizer?


def test_cp_opt(small, capfd):
    init = Solution([TaskData(0, 0, 1, 1), TaskData(0, 1, 2, 3)])

    solve(small, "cpoptimizer", log=True, initial_solution=init)
    printed = capfd.readouterr().out

    msg = "Starting point is complete and consistent with constraints."
    assert_(msg in printed)


def test_solve_initial_solution_setup(capfd):
    init = Solution([TaskData(0, 0, 2, 2), TaskData(0, 6, 2, 8)])
    model = Model()
    job = model.add_job()
    machine = model.add_machine()
    task1 = model.add_task(job=job)
    task2 = model.add_task(job=job)

    model.add_processing_time(task1, machine, 2)
    model.add_processing_time(task2, machine, 2)
    model.add_setup_time(machine, task1, task2, 2)
    model.add_previous(task1, task2)

    result = solve(
        model.data(),
        "ortools",
        log=True,
        initial_solution=init,
        fix_variables_to_their_hinted_value=True,
    )
    printed = capfd.readouterr().out

    assert_("The solution hint is incomplete" in printed)
    assert_equal(result.objective, 8)

    # Don't fix
    result = solve(model.data(), "ortools", log=True, initial_solution=init)
    printed = capfd.readouterr().out

    assert_("The solution hint is incomplete" in printed)
    assert_equal(result.objective, 6)


def describe_solve_set_default_parameters():
    """
    Tests `solve` when setting the default parameters.
    """

    def log(small, solver, capfd):
        """
        Checks that setting the log flag correctly show solver output.
        """
        solve(small, solver, log=True)
        printed = capfd.readouterr().out
        assert_(printed != "")

        solve(small, solver, log=False)
        printed = capfd.readouterr().out
        assert_equal(printed, "")

    def time_limit(small, capfd):
        """
        Checks the log that the time limit is set. No test for CP Optimizer
        because it does not log this setting.
        """
        solve(small, "ortools", time_limit=1.2, log=True)
        printed = capfd.readouterr().out
        assert_("max_time_in_seconds: 1.2" in printed)

    @pytest.mark.parametrize(
        "solver_, msg",
        [
            ("ortools", "num_workers: 2"),
            ("cpoptimizer", "Using parallel search with 2 workers."),
        ],
    )
    def num_workers(small, solver_, msg, capfd):
        """
        Checks the log that the ``num_workers`` parameter is correctly set.
        """
        solve(small, solver_, num_workers=2, log=True)
        printed = capfd.readouterr().out
        assert_(msg in printed)


@pytest.mark.parametrize(
    "solver_, param, value",
    [
        ("ortools", "log_search_progress", True),
        ("cpoptimizer", "LogVerbosity", "Terse"),
    ],
)
def test_solve_additional_params(small, capfd, solver_, param, value):
    """
    Tests the solve method with additional parameters can override the
    parameters supported by ``solve``.
    """
    # Let's test that setting log to False will not print anything.
    solve(small, solver_, log=False)
    printed = capfd.readouterr().out
    assert_equal(printed, "")

    # Now we set the corresponding log parameter using the additional keyword
    # argument, which will override the earlier setting of log being False.
    solve(small, solver_, log=False, **{param: value})
    printed = capfd.readouterr().out
    assert_(printed != "")
