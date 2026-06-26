from numpy.testing import assert_, assert_equal

from pyjobshop import Model


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


def test_custom_model(require_cpoptimizer, small):
    """
    Tests that a custom CpModel can be provided.
    """
    from docplex.cp.model import CpoModel

    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    custom_model = CpoModel()
    custom_model.add(1 == 2)  # infeasible
    cp_model = CPModel(small, model=custom_model)
    result = cp_model.solve()

    assert_equal(result.status.value, "Infeasible")


def test_model_property(require_cpoptimizer, small):
    """
    Tests that the model property can be accessed.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    cp_model = CPModel(small)
    result = cp_model.solve()
    assert_equal(result.status.value, "Optimal")

    cp_model.model.add(1 == 2)
    result = cp_model.solve()
    assert_equal(result.status.value, "Infeasible")


def test_variables_property(require_cpoptimizer, small):
    """
    Tests that the variables property can be accessed.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    cp_model = CPModel(small)
    variables = cp_model.variables

    assert_equal(len(variables.job_vars), 1)
    assert_equal(len(variables.task_vars), 2)
    assert_equal(len(variables.mode_vars), 2)
    assert_equal(len(variables.sequence_vars), 1)


def test_no_warning_for_machine_without_modes(require_cpoptimizer, capfd):
    """
    Tests that no 'Unused sequence variable' warning is emitted when a
    machine exists but has no modes assigned to it.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    model = Model()
    job = model.add_job()
    machine = model.add_machine()
    model.add_machine()  # unused machine, no modes

    task = model.add_task(job=job)
    model.add_mode(task, machine, duration=1)

    cp_model = CPModel(model.data())
    cp_model.solve(display=True)

    captured = capfd.readouterr()
    output = captured.out + captured.err
    assert_("Unused sequence variable" not in output)
