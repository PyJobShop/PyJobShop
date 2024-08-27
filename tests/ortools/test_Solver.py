from numpy.testing import assert_equal

from pyjobshop.Model import Model
from pyjobshop.ortools.Solver import Solver
from pyjobshop.Solution import Solution, TaskData


def test_subsequent_solve_clears_hint(small):
    """
    Tests that subsequent solve calls clear the previous hint.
    """
    solver = Solver(small)

    # We first solve the model with init1 as initial solution.
    init1 = Solution([TaskData(0, 0, 1), TaskData(0, 1, 3)])
    result = solver.solve(initial_solution=init1)
    assert_equal(result.status.value, "Optimal")

    # Next we solve the model with a different initial solution. If
    # the hint was not cleared, OR-Tools will throw a ``MODEL_INVALID``
    # error because the model contains duplicate hints.
    init2 = Solution([TaskData(1, 0, 1), TaskData(1, 1, 3)])
    result = solver.solve(initial_solution=init2)
    assert_equal(result.status.value, "Optimal")


def test_empty_circuit_not_allowed_bug():
    """
    This solves the bug identified in #178, where it was not possible to leave
    a machine empty because empty circuits were not allowed.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task(job=job) for _ in range(2)]

    durations = [[2, 2], [5, 5]]
    for machine_idx, machine in enumerate(machines):
        for task_idx, task in enumerate(tasks):
            duration = durations[machine_idx][task_idx]
            model.add_processing_time(task, machine, duration)

    model.add_previous(*tasks)  # this activates the circuit constraints

    solver = Solver(model.data())
    result = solver.solve()

    # Optimal solution schedules both tasks on machine 1, achieving makespan 4.
    # Before the fix, empty circuits weren't allowed, forcing tasks onto
    # separate machines and resulting in a longer makespan of 5.
    assert_equal(result.objective, 4)
