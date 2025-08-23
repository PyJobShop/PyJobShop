from numpy.testing import assert_


def test_solve_initial_solution(
    require_cpoptimizer,
    complete_data,
    complete_sol,
    capfd,
):
    """
    Tests that the solver correctly hints the solution by checking that the
    display log is correct when an initial solution is provided.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    cp_model = CPModel(complete_data)
    cp_model.solve(display=True, initial_solution=complete_sol)

    msg = "Starting point is complete and consistent with constraints."
    printed = capfd.readouterr().out
    assert_(msg in printed)
