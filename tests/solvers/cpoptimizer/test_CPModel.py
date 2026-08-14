from numpy.testing import assert_, assert_equal

from pyjobshop import Model


def test_setup_matrix_is_built_once(
    require_cpoptimizer,
    complete_data,
    monkeypatch,
):
    """
    Tests that the setup matrix is shared by constraints and the objective.
    """
    import pyjobshop.solvers.utils as utils
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    original = utils.setup_times_matrix
    calls = 0

    def counted(data):
        nonlocal calls
        calls += 1
        return original(data)

    monkeypatch.setattr(utils, "setup_times_matrix", counted)
    CPModel(complete_data, global_setup_matrix=True)

    assert_equal(calls, 1)


def test_machine_local_sequence_types(require_cpoptimizer, complete_data):
    """
    Tests that sequence types are dense and local to each machine.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    variables = CPModel(complete_data).variables

    for res_idx, task_types in variables.sequence_task_types.items():
        task_idcs = {
            complete_data.modes[idx].task
            for idx in complete_data.resource2modes(res_idx)
        }
        assert_equal(set(task_types), task_idcs)
        assert_equal(set(task_types.values()), set(range(len(task_idcs))))


def test_machine_local_setup_matrices(require_cpoptimizer, complete_data):
    """
    Tests that local setup matrices preserve every setup time.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    variables = CPModel(complete_data).variables

    for (
        res_idx,
        task1,
        task2,
        duration,
    ) in complete_data.constraints.setup_times:
        task_types = variables.sequence_task_types[res_idx]
        matrix = variables.setup_matrices[res_idx]
        assert_equal(matrix[task_types[task1], task_types[task2]], duration)


def test_global_setup_matrix_uses_task_indices(
    require_cpoptimizer,
    complete_data,
):
    """
    Tests the global setup encoding used by search-sensitive models.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    variables = CPModel(
        complete_data,
        global_setup_matrix=True,
    ).variables

    for task_types in variables.sequence_task_types.values():
        assert_equal(task_types, {idx: idx for idx in task_types})

    for matrix in variables.setup_matrices.values():
        assert_equal(matrix.shape, (complete_data.num_tasks,) * 2)


def test_break_constraints_only_for_modes_with_breaks(
    require_cpoptimizer,
    complete_data,
):
    """
    Tests that modes without resource breaks get no break constraints.
    """
    from pyjobshop.solvers.cpoptimizer.CPModel import CPModel

    model = CPModel(complete_data).model.get_cpo_string()

    assert_equal(model.count("forbidStart"), 1)
    assert_equal(model.count("forbidEnd"), 1)
    assert_equal(model.count("forbidExtent"), 0)


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
