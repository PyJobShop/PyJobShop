from numpy.testing import assert_, assert_equal

from pyjobshop.Model import Model
from pyjobshop.Solution import Solution, TaskData
from pyjobshop.solvers.ortools.Solver import Solver


def test_solve_initial_solution(complete_data, complete_sol, capfd):
    """
    Tests that the solver correctly hints the solution by checking that the
    display log is correct when an initial solution is provided.
    """
    solver = Solver(complete_data)
    solver.solve(display=True, initial_solution=complete_sol)

    msg = "The solution hint is complete and is feasible."
    printed = capfd.readouterr().out
    assert_(msg in printed)


def test_subsequent_solve_clears_hint(small):
    """
    Tests that subsequent solve calls clear the previous hint.
    """
    solver = Solver(small)

    # We first solve the model with init1 as initial solution.
    init1 = Solution([TaskData(0, [0], 0, 1), TaskData(0, [0], 1, 3)])
    result = solver.solve(initial_solution=init1)
    assert_equal(result.status.value, "Optimal")

    # Next we solve the model with a different initial solution. If
    # the hint was not cleared, OR-Tools will throw a ``MODEL_INVALID``
    # error because the model contains duplicate hints.
    init2 = Solution([TaskData(0, [1], 0, 1), TaskData(0, [1], 1, 3)])
    result = solver.solve(initial_solution=init2)
    assert_equal(result.status.value, "Optimal")


def test_empty_circuit_not_allowed_bug():
    """
    This solves the bug identified in #178, where it was not possible to leave
    a resource empty because empty circuits were not allowed.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task(job=job) for _ in range(2)]

    durations = [[2, 2], [5, 5]]
    for mach_idx, machine in enumerate(machines):
        for task_idx, task in enumerate(tasks):
            duration = durations[mach_idx][task_idx]
            model.add_mode(task, machine, duration)

    model.add_consecutive(*tasks)  # this activates the circuit constraints

    solver = Solver(model.data())
    result = solver.solve()

    # Optimal solution is to schedule both tasks on resource 1, achieving
    # makespan 4. Before the fix, empty circuits weren't allowed, forcing
    # tasks onto separate resources and resulting in a longer makespan of 5.
    assert_equal(result.objective, 4)
