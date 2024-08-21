from numpy.testing import assert_equal

from pyjobshop.constants import MAX_VALUE
from pyjobshop.Model import Model
from pyjobshop.ProblemData import Constraint, Mode, Objective
from pyjobshop.Solution import Solution, TaskData


def test_model_to_data():
    """
    Tests that calling ``Model.data()`` returns a correct ProblemData instance.
    """
    model = Model()

    job = model.add_job()
    machine1, machine2 = [model.add_machine() for _ in range(2)]
    task1, task2 = [model.add_task(job=job) for _ in range(2)]

    model.add_processing_time(task1, machine1, 1)
    model.add_processing_time(task2, machine2, 2)

    model.add_start_at_start(task1, task2)
    model.add_start_at_end(task1, task2)
    model.add_start_before_start(task1, task2)
    model.add_start_before_end(task1, task2)
    model.add_end_at_start(task1, task2)
    model.add_end_at_end(task1, task2)
    model.add_end_before_end(task1, task2)
    model.add_end_before_start(task1, task2)
    model.add_same_machine(task2, task1)
    model.add_different_machine(task2, task1)
    model.add_previous(task2, task1)
    model.add_before(task2, task1)

    model.add_setup_time(machine1, task1, task2, 3)
    model.add_setup_time(machine2, task1, task2, 4)

    model.set_horizon(100)
    model.set_objective(weight_total_completion_time=1)

    data = model.data()

    assert_equal(data.jobs, [job])
    assert_equal(data.machines, [machine1, machine2])
    assert_equal(data.tasks, [task1, task2])
    assert_equal(
        data.modes,
        [
            Mode(task=0, duration=1, resources=[0]),
            Mode(task=1, duration=2, resources=[1]),
        ],
    )
    assert_equal(
        data.constraints,
        {
            (0, 1): [
                Constraint.START_AT_START,
                Constraint.START_AT_END,
                Constraint.START_BEFORE_START,
                Constraint.START_BEFORE_END,
                Constraint.END_AT_START,
                Constraint.END_AT_END,
                Constraint.END_BEFORE_END,
                Constraint.END_BEFORE_START,
            ],
            (1, 0): [
                Constraint.SAME_MACHINE,
                Constraint.DIFFERENT_MACHINE,
                Constraint.PREVIOUS,
                Constraint.BEFORE,
            ],
        },
    )
    assert_equal(data.setup_times, [[[0, 3], [0, 0]], [[0, 4], [0, 0]]])
    assert_equal(data.horizon, 100)
    assert_equal(data.objective, Objective.total_completion_time())


def test_from_data(fjsp):
    """
    Tests that initializing from a data instance returns a valid model
    representation of that instance.
    """
    data = fjsp
    model = Model.from_data(data)
    m_data = model.data()

    assert_equal(m_data.num_jobs, data.num_jobs)
    assert_equal(m_data.num_machines, data.num_machines)
    assert_equal(m_data.num_tasks, data.num_tasks)
    assert_equal(m_data.modes, data.modes)
    assert_equal(m_data.constraints, data.constraints)
    assert_equal(m_data.setup_times, data.setup_times)
    assert_equal(m_data.horizon, data.horizon)
    assert_equal(m_data.objective, data.objective)


def test_model_to_data_default_values():
    """
    Tests ``Model.data()`` uses the correct default values.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job)
    model.add_processing_time(task, machine, 1)

    data = model.data()

    assert_equal(data.jobs, [job])
    assert_equal(data.machines, [machine])
    assert_equal(data.tasks, [task])
    assert_equal(data.modes, [Mode(task=0, duration=1, resources=[0])])
    assert_equal(data.constraints, {})
    assert_equal(data.setup_times, [[[0]]])
    assert_equal(data.horizon, MAX_VALUE)
    assert_equal(data.objective, Objective.makespan())


def test_add_job_attributes():
    """
    Tests that adding a job to the model correctly sets the attributes.
    """
    model = Model()

    job = model.add_job(
        weight=0, release_date=1, due_date=2, deadline=3, name="job"
    )

    assert_equal(job.weight, 0)
    assert_equal(job.release_date, 1)
    assert_equal(job.due_date, 2)
    assert_equal(job.deadline, 3)
    assert_equal(job.name, "job")


def test_add_machine_attributes():
    """
    Tests that adding a machine to the model correctly sets the attributes.
    """
    model = Model()

    machine = model.add_machine(name="machine")

    assert_equal(machine.name, "machine")


def test_add_task_attributes():
    """
    Tests that adding an task to the model correctly sets the attributes.
    """
    model = Model()

    task = model.add_task(
        earliest_start=1,
        latest_start=2,
        earliest_end=3,
        latest_end=4,
        fixed_duration=True,
        name="task",
    )

    assert_equal(task.earliest_start, 1)
    assert_equal(task.latest_start, 2)
    assert_equal(task.earliest_end, 3)
    assert_equal(task.latest_end, 4)
    assert_equal(task.fixed_duration, True)
    assert_equal(task.name, "task")


def test_model_attributes():
    """
    Tests that the model attributes are correctly.
    """
    model = Model()

    jobs = [model.add_job() for _ in range(10)]
    machines = [model.add_machine() for _ in range(20)]
    tasks = [model.add_task() for _ in range(30)]

    assert_equal(model.jobs, jobs)
    assert_equal(model.machines, machines)
    assert_equal(model.tasks, tasks)


def test_model_set_objective():
    """
    Tests that setting the objective changes.
    """
    model = Model()

    # The default objective function is the makespan.
    assert_equal(model.objective, Objective.makespan())

    # Now we set the objective function to a weighted combination
    # this should overwrite the previously set objective.
    model.set_objective(
        weight_makespan=1,
        weight_tardy_jobs=2,
        weight_total_tardiness=3,
        weight_total_completion_time=4,
        weight_total_earliness=5,
    )

    assert_equal(model.objective.weight_makespan, 1)
    assert_equal(model.objective.weight_tardy_jobs, 2)
    assert_equal(model.objective.weight_total_tardiness, 3)
    assert_equal(model.objective.weight_total_completion_time, 4)
    assert_equal(model.objective.weight_total_earliness, 5)


def test_solve(solver: str):
    """
    Tests the solve method of the Model class.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task, duration in zip(tasks, [1, 2]):
        model.add_processing_time(task, machine, duration)

    result = model.solve(solver=solver)

    assert_equal(result.objective, 3)
    assert_equal(result.status.value, "Optimal")


def test_solve_initial_solution_fixed(small):
    """
    Tests that Model.solve() correctly takes the initial solution and passes
    additional kwargs to the solver, fixing the solution.
    """
    model = Model.from_data(small)
    init = Solution([TaskData(0, 0, 1, 1), TaskData(0, 3, 2, 5)])
    result = model.solve(
        "ortools",
        initial_solution=init,
        fix_variables_to_their_hinted_value=True,
    )

    # The initial solution has makespan 5 and is fixed, even though this
    # instance admits a better solution with makespan 3.
    assert_equal(result.objective, 5)
    assert_equal(result.status.value, "Optimal")
