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
    operations = [model.add_operation(job=job) for _ in range(2)]

    mach1, mach2 = machines
    op1, op2 = operations

    model.add_processing_time(mach1, op1, 1)
    model.add_processing_time(mach2, op2, 2)

    model.add_constraint(op1, op2, Constraint.END_BEFORE_START)
    model.add_constraint(op1, op2, Constraint.START_BEFORE_END)
    model.add_constraint(op2, op1, Constraint.SAME_UNIT)
    model.add_constraint(op2, op1, Constraint.PREVIOUS)

    model.add_setup_time(mach1, op1, op2, 3)
    model.add_setup_time(mach2, op1, op2, 4)

    model.set_planning_horizon(100)
    model.set_objective(Objective.TOTAL_COMPLETION_TIME)

    data = model.data()

    assert_equal(data.jobs, [job])
    assert_equal(data.machines, machines)
    assert_equal(data.operations, operations)
    assert_equal(data.job2ops, [[0, 1]])
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
    assert_equal(data.planning_horizon, 100)
    assert_equal(data.objective, Objective.TOTAL_COMPLETION_TIME)


def test_model_to_data_default_values():
    """
    Tests ``Model.data()`` uses the correct default values.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(job=job)

    data = model.data()

    assert_equal(data.jobs, [job])
    assert_equal(data.machines, [machine])
    assert_equal(data.operations, [operation])
    assert_equal(data.job2ops, [[0]])
    assert_equal(data.processing_times, {})
    assert_equal(data.constraints, {})
    assert_equal(data.setup_times, [[[0]]])
    assert_equal(data.planning_horizon, MAX_VALUE)
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


def test_add_operation_attributes():
    """
    Tests that adding an operation to the model correctly sets the attributes.
    """
    model = Model()

    operation = model.add_operation(
        earliest_start=1,
        latest_start=2,
        earliest_end=3,
        latest_end=4,
        fixed_duration=True,
        name="operation",
    )

    assert_equal(operation.earliest_start, 1)
    assert_equal(operation.latest_start, 2)
    assert_equal(operation.earliest_end, 3)
    assert_equal(operation.latest_end, 4)
    assert_equal(operation.fixed_duration, True)
    assert_equal(operation.name, "operation")


def test_model_attributes():
    """
    Tests that the model attributes are correctly.
    """
    model = Model()

    jobs = [model.add_job() for _ in range(10)]
    machines = [model.add_machine() for _ in range(20)]
    operations = [model.add_operation() for _ in range(30)]

    assert_equal(model.jobs, jobs)
    assert_equal(model.machines, machines)
    assert_equal(model.operations, operations)


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


def test_solve():
    """
    Tests the solve method of the Model class.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [model.add_operation(job=job) for _ in range(2)]

    for operation, duration in zip(operations, [1, 2]):
        model.add_processing_time(machine, operation, duration)

    result = model.solve()

    assert_equal(result.objective_value, 3)
    assert_equal(result.solve_status, "Optimal")
