from numpy.testing import assert_equal

from pyjobshop.Model import Model


def test_mode_dependencies_cpoptimizer():

    model = Model()

    job = model.add_job()
    machines = [model.add_machine() for _ in range(5)]
    task1 = model.add_task(job=job)
    task2 = model.add_task(job=job)

    mode1 = model.add_mode(task=task1, resources=machines[0], duration=5)
    mode2 = model.add_mode(task=task2, resources=machines[1], duration=2)
    mode3 = model.add_mode(task=task2, resources=machines[2], duration=10)
    mode4 = model.add_mode(task=task2, resources=machines[3], duration=10)

    # First we solve the model without the mode dependency constraint, we
    # expect to get an optimal solution with a makespan of 7.
    model.add_end_before_start(task1, task2)
    result = model.solve(solver="cpoptimizer")
    assert_equal(result.objective, 7)

    # Now we add the mode dependency and we see that enforce that if mode1
    # gets selected for task 1 (only option in this test case) then we need
    # to enforce that mode3 or mode 4 gets selected for task 2. Since these
    # modes have both duration 10 instead of 2, the makespan now equals 15.
    model.add_mode_dependency(mode1, [mode3, mode4])
    result = model.solve(solver="cpoptimizer")
    assert_equal(result.objective, 15)


"""
THIS TEST CAN BE ACTIVATED ONCE THE MODE DEPENDENCIES ARE ALSO IMPLEMENTED FOR 
GOOGLE OR-TOOLS
def test_mode_dependencies_ortools():

    model = Model()

    job = model.add_job()
    machines = [model.add_machine() for _ in range(5)]
    task1 = model.add_task(job=job)
    task2 = model.add_task(job=job)

    mode1 = model.add_mode(task=task1, resources=machines[0], duration=5)
    mode2 = model.add_mode(task=task2, resources=machines[1], duration=2)
    mode3 = model.add_mode(task=task2, resources=machines[2], duration=10)
    mode4 = model.add_mode(task=task2, resources=machines[3], duration=10)

    # First we solve the model without the mode dependency constraint, we
    # expect to get an optimal solution with a makespan of 7.
    model.add_end_before_start(task1, task2)
    result = model.solve()
    assert_equal(result.objective, 7)

    # Now we add the mode dependency and we see that enforce that if mode1
    # gets selected for task 1 (only option in this test case) then we need
    # to enforce that mode3 or mode 4 gets selected for task 2. Since these
    # modes have both duration 10 instead of 2, the makespan now equals 15.
    model.add_mode_dependency(mode1, [mode3, mode4])
    result = model.solve()
    assert_equal(result.objective, 15)
"""


