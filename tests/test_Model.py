from numpy.testing import assert_equal

from pyjobshop.constants import MAX_VALUE
from pyjobshop.Model import Model
from pyjobshop.ProblemData import Constraint, Objective


def test_model_to_data():
    """
    Tests that calling ``Model.data()`` returns a correct ProblemData instance.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task(job=job) for _ in range(2)]

    mach1, mach2 = machines
    task1, task2 = tasks

    model.add_processing_time(mach1, task1, 1)
    model.add_processing_time(mach2, task2, 2)

    model.add_constraint(task1, task2, Constraint.END_BEFORE_START)
    model.add_constraint(task1, task2, Constraint.START_BEFORE_END)
    model.add_constraint(task2, task1, Constraint.SAME_UNIT)
    model.add_constraint(task2, task1, Constraint.PREVIOUS)

    model.add_setup_time(mach1, task1, task2, 3)
    model.add_setup_time(mach2, task1, task2, 4)

    model.set_horizon(100)
    model.set_objective(Objective.TOTAL_COMPLETION_TIME)

    data = model.data()

    assert_equal(data.jobs, [job])
    assert_equal(data.machines, machines)
    assert_equal(data.tasks, tasks)
    assert_equal(data.processing_times, {(0, 0): 1, (1, 1): 2})
    assert_equal(
        data.constraints,
        {
            (0, 1): [
                Constraint.END_BEFORE_START,
                Constraint.START_BEFORE_END,
            ],
            (1, 0): [
                Constraint.SAME_UNIT,
                Constraint.PREVIOUS,
            ],
        },
    )
    assert_equal(data.setup_times, [[[0, 3], [0, 0]], [[0, 4], [0, 0]]])
    assert_equal(data.horizon, 100)
    assert_equal(data.objective, Objective.TOTAL_COMPLETION_TIME)


def test_model_to_data_default_values():
    """
    Tests ``Model.data()`` uses the correct default values.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job)

    data = model.data()

    assert_equal(data.jobs, [job])
    assert_equal(data.machines, [machine])
    assert_equal(data.tasks, [task])
    assert_equal(data.processing_times, {})
    assert_equal(data.constraints, {})
    assert_equal(data.setup_times, [[[0]]])
    assert_equal(data.horizon, MAX_VALUE)
    assert_equal(data.objective, Objective.MAKESPAN)


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

    machine = model.add_machine(allow_overlap=True, name="machine")

    assert_equal(machine.allow_overlap, True)
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
    assert_equal(model.objective, Objective.MAKESPAN)

    # Now we set the objective function to total tardiness.
    model.set_objective(Objective.TOTAL_TARDINESS)

    assert_equal(model.objective, Objective.TOTAL_TARDINESS)


def test_solve(solver: str):
    """
    Tests the solve method of the Model class.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task, duration in zip(tasks, [1, 2]):
        model.add_processing_time(machine, task, duration)

    result = model.solve(solver=solver)

    assert_equal(result.objective, 3)
    assert_equal(result.status.value, "Optimal")
