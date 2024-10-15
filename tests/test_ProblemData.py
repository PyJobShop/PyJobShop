import numpy as np
import pytest
from numpy.testing import assert_, assert_equal, assert_raises

from pyjobshop.constants import MAX_VALUE
from pyjobshop.Model import Model
from pyjobshop.ProblemData import (
    Constraint,
    Job,
    Machine,
    Mode,
    Objective,
    ProblemData,
    Resource,
    Task,
)
from pyjobshop.Solution import TaskData as TaskData
from pyjobshop.solve import solve


def test_job_attributes():
    """
    Tests that the attributes of the Job class are set correctly.
    """
    job = Job(
        weight=0,
        release_date=1,
        due_date=2,
        deadline=3,
        tasks=[0],
        name="test",
    )

    assert_equal(job.weight, 0)
    assert_equal(job.release_date, 1)
    assert_equal(job.due_date, 2)
    assert_equal(job.deadline, 3)
    assert_equal(job.tasks, [0])
    assert_equal(job.name, "test")


def test_job_default_attributes():
    """
    Tests that the default attributes of the Job class are set correctly.
    """
    job = Job()

    assert_equal(job.weight, 1)
    assert_equal(job.release_date, 0)
    assert_equal(job.deadline, MAX_VALUE)
    assert_equal(job.due_date, None)
    assert_equal(job.tasks, [])
    assert_equal(job.name, "")


@pytest.mark.parametrize(
    "weight, release_date, due_date, deadline, tasks, name",
    [
        (-1, 0, 0, 0, [], ""),  # weight < 0
        (0, -1, 0, 0, [], ""),  # release_date < 0
        (0, 0, -1, 0, [], ""),  # deadline < 0
        (0, 10, 0, 0, [], ""),  # release_date > deadline
        (0, 0, 0, -1, [], ""),  # due_date < 0
    ],
)
def test_job_attributes_raises_invalid_parameters(
    weight: int,
    release_date: int,
    deadline: int,
    due_date: int,
    tasks: list[int],
    name: str,
):
    """
    Tests that a ValueError is raised when invalid parameters are passed to
    Job.
    """
    with assert_raises(ValueError):
        Job(
            weight=weight,
            release_date=release_date,
            deadline=deadline,
            due_date=due_date,
            tasks=tasks,
            name=name,
        )


def test_resource_attributes():
    """
    Tests that the attributes of the Resource class are set correctly.
    """
    # Let's first test the default values.
    resource = Resource(capacity=1)
    assert_equal(resource.renewable, True)
    assert_equal(resource.name, "")

    # Now test with some values.
    resource = Resource(capacity=1, renewable=False, name="TestResource")
    assert_equal(resource.capacity, 1)
    assert_equal(resource.renewable, False)
    assert_equal(resource.name, "TestResource")


@pytest.mark.parametrize(
    "capacity",
    [
        (-1),  # capacity < 0
    ],
)
def test_resource_raises_invalid_parameters(capacity: int):
    """
    Tests that a ValueError is raised when invalid parameters are passed to
    the Resource class.
    """
    with assert_raises(ValueError):
        Resource(capacity=capacity)


def test_machine_attributes():
    """
    Tests that the attributes of the Machine class are set correctly.
    """
    machine = Machine(name="Machine")

    # Inherited attributes from Resource, but unsused.
    assert_equal(machine.capacity, 0)
    assert_equal(machine.renewable, True)
    assert_equal(machine.name, "Machine")


def test_task_attributes():
    """
    Tests that the attributes of the Task class are set correctly.
    """
    task = Task(
        earliest_start=1,
        latest_start=2,
        earliest_end=3,
        latest_end=4,
        fixed_duration=False,
        name="TestTask",
    )

    assert_equal(task.earliest_start, 1)
    assert_equal(task.latest_start, 2)
    assert_equal(task.earliest_end, 3)
    assert_equal(task.latest_end, 4)
    assert_equal(task.fixed_duration, False)
    assert_equal(task.name, "TestTask")

    # Also test that default values are set correctly.
    task = Task()

    assert_equal(task.earliest_start, 0)
    assert_equal(task.latest_start, MAX_VALUE)
    assert_equal(task.earliest_end, 0)
    assert_equal(task.latest_end, MAX_VALUE)
    assert_equal(task.fixed_duration, True)
    assert_equal(task.name, "")


@pytest.mark.parametrize(
    "earliest_start, latest_start, earliest_end, latest_end",
    [
        (1, 0, 0, 0),  # earliest_start > latest_start
        (0, 0, 1, 0),  # earliest_end > latest_end
    ],
)
def test_task_attributes_raises_invalid_parameters(
    earliest_start: int,
    latest_start: int,
    earliest_end: int,
    latest_end: int,
):
    """
    Tests that an error is raised when invalid parameters are passed to the
    Task class.
    """
    with assert_raises(ValueError):
        Task(earliest_start, latest_start, earliest_end, latest_end)


def test_problem_data_input_parameter_attributes():
    """
    Tests that the input parameters of the ProblemData class are set correctly
    as attributes.
    """
    jobs = [Job(tasks=[idx]) for idx in range(5)]
    resources = [Machine() for _ in range(5)]
    tasks = [Task() for _ in range(5)]
    modes = [
        Mode(task=task, resources=[resource], duration=1)
        for task in range(5)
        for resource in range(5)
    ]
    constraints = {
        key: [Constraint.END_BEFORE_START] for key in ((0, 1), (2, 3), (4, 5))
    }
    setup_times = np.ones((5, 5, 5), dtype=int)
    horizon = 100
    objective = Objective.total_flow_time()

    data = ProblemData(
        jobs,
        resources,
        tasks,
        modes,
        constraints,
        setup_times,
        horizon,
        objective,
    )

    assert_equal(data.jobs, jobs)
    assert_equal(data.resources, resources)
    assert_equal(data.tasks, tasks)
    assert_equal(data.modes, modes)
    assert_equal(data.constraints, constraints)
    assert_equal(data.setup_times, setup_times)
    assert_equal(data.horizon, horizon)
    assert_equal(data.objective, objective)


def test_mode_attributes():
    """
    Tests that the attributes of the Mode class are set correctly.
    """
    mode = Mode(task=0, resources=[0], duration=1, demands=[1])

    assert_equal(mode.task, 0)
    assert_equal(mode.duration, 1)
    assert_equal(mode.resources, [0])
    assert_equal(mode.demands, [1])


@pytest.mark.parametrize(
    "resources, duration, demands",
    [
        ([0, 0], -1, [0, 0]),  # resources not unique
        ([0], -1, [0]),  # duration < 0
        ([0], 0, [-1]),  # demand < 0
        ([0], 0, [0, 0]),  # len(resources) != len(demands)
    ],
)
def test_mode_raises_invalid_parameters(resources, duration, demands):
    """
    Tests that a ValueError is raised when invalid parameters are passed to
    the Mode class.
    """
    with assert_raises(ValueError):
        Mode(task=0, resources=resources, duration=duration, demands=demands)


def test_problem_data_non_input_parameter_attributes():
    """
    Tests that attributes that are not input parameters of the ProblemData
    class are set correctly.
    """
    jobs = [Job(tasks=[0, 1, 2])]
    resources = [Resource(0) for _ in range(3)]
    tasks = [Task() for _ in range(3)]
    modes = [
        Mode(task=2, resources=[1], duration=1),
        Mode(task=1, resources=[2], duration=1),
        Mode(task=1, resources=[0], duration=1),
        Mode(task=0, resources=[2], duration=1),
    ]

    data = ProblemData(jobs, resources, tasks, modes)

    assert_equal(data.num_jobs, 1)
    assert_equal(data.num_resources, 3)
    assert_equal(data.num_tasks, 3)
    assert_equal(data.num_modes, 4)


def test_problem_data_default_values():
    """
    Tests that the default values of the ProblemData class are set correctly.
    """
    jobs = [Job(tasks=[0])]
    resources = [Resource(0)]
    tasks = [Task()]
    modes = [Mode(task=0, resources=[0], duration=1)]
    data = ProblemData(jobs, resources, tasks, modes)

    assert_equal(data.constraints, {})
    assert_equal(data.setup_times, None)
    assert_equal(data.horizon, MAX_VALUE)
    assert_equal(data.objective, Objective.makespan())


def test_problem_data_job_references_unknown_task():
    """
    Tests that an error is raised when a job references an unknown task.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job(tasks=[42])],
            [Resource(0)],
            [Task()],
            [Mode(0, [0], 1)],
        )


@pytest.mark.parametrize(
    "mode",
    [
        Mode(42, [0], 1),  # Task 42 does not exist.
        Mode(0, [42], 1),  # Resource 42 does not exist.
    ],
)
def test_problem_data_mode_references_unknown_data(mode):
    """
    Tests that an error is raised when a mode references unknown data.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job()],
            [Resource(0)],
            [Task()],
            [mode],
        )


def test_problem_data_task_without_modes():
    """
    Tests that an error is raised when a task has no processing modes.
    """
    with assert_raises(ValueError):
        ProblemData([Job()], [Resource(0)], [Task()], [])


def test_problem_data_all_modes_demand_infeasible():
    """
    Tests that an error is raised when all modes of a task have infeasible
    demands.
    """

    # This is OK: at least one mode is feasible.
    ProblemData(
        [Job()],
        [Resource(capacity=1)],
        [Task()],
        [
            Mode(0, [0], 2, demands=[1]),  # feasible
            Mode(0, [0], 2, demands=[2]),  # infeasible
        ],
    )

    with assert_raises(ValueError):
        # This is not OK: no mode is feasible.
        ProblemData(
            [Job()],
            [Resource(capacity=1)],
            [Task()],
            [
                Mode(0, [0], 2, demands=[2]),  # infeasible
                Mode(0, [0], 2, demands=[2]),  # infeasible
            ],
        )


@pytest.mark.parametrize(
    "setup_times, horizon",
    [
        # Negative setup times.
        (np.ones((1, 1, 1)) * -1, 1),
        # Invalid setup times shape.
        (np.ones((2, 2, 2)), 1),
        # Negative horizon.
        (np.ones((1, 1, 1)), -1),
    ],
)
def test_problem_data_raises_when_invalid_arguments(
    setup_times: np.ndarray, horizon: int
):
    """
    Tests that the ProblemData class raises an error when invalid arguments are
    passed.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job()],
            [Resource(0)],
            [Task()],
            modes=[Mode(0, [0], 1)],
            setup_times=setup_times.astype(int),
            horizon=horizon,
        )


def test_problem_data_raises_capacitated_resources_and_setup_times():
    """
    Tests that the ProblemData class raises an error when resources with
    nonzero capacities have setup times.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job()],
            [Resource(capacity=2)],
            [Task()],
            [Mode(0, [0], 0)],
            setup_times=np.array([[[1]]]),
        )


@pytest.mark.parametrize(
    "objective",
    [
        Objective.tardy_jobs(),
        Objective.total_tardiness(),
        Objective.total_earliness(),
    ],
)
def test_problem_data_tardy_objective_without_job_due_dates(
    objective: Objective,
):
    """
    Tests that an error is raised when jobs have no due dates and a
    tardiness-based objective is selected.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job()],
            [Resource(0)],
            [Task()],
            [Mode(0, [0], 0)],
            objective=objective,
        )


def describe_problem_data_replace():
    """
    Tests for the ProblemData.replace() method.
    """

    @pytest.fixture
    def data():
        jobs = [Job(due_date=1, deadline=1), Job(due_date=2, deadline=2)]
        resources = [
            Resource(capacity=0, name="resource"),
            Resource(capacity=0, name="resource"),
        ]
        tasks = [Task(earliest_start=1), Task(earliest_start=1)]
        modes = [
            Mode(task=0, resources=[0], duration=1),
            Mode(task=1, resources=[1], duration=2),
        ]
        constraints = {(0, 1): [Constraint.END_BEFORE_START]}
        setup_times = np.zeros((2, 2, 2))
        horizon = 1
        objective = Objective.makespan()

        return ProblemData(
            jobs,
            resources,
            tasks,
            modes,
            constraints,
            setup_times,
            horizon,
            objective,
        )

    def no_changes(data):
        """
        Tests that when using ``ProblemData.replace()`` without any arguments
        returns a new instance with different objects but with the same values.
        """

        new = data.replace()
        assert_(new is not data)

        for idx in range(data.num_jobs):
            assert_(new.jobs[idx] is not data.jobs[idx])
            assert_equal(new.jobs[idx].deadline, data.jobs[idx].deadline)
            assert_equal(new.jobs[idx].due_date, data.jobs[idx].due_date)

        for idx in range(data.num_resources):
            assert_(new.resources[idx] is not data.resources[idx])
            assert_equal(new.resources[idx].name, data.resources[idx].name)

        for idx in range(data.num_tasks):
            assert_(new.tasks[idx] is not data.tasks[idx])
            assert_equal(
                new.tasks[idx].earliest_start,
                data.tasks[idx].earliest_start,
            )

        for idx in range(data.num_modes):
            assert_(new.modes[idx] is not data.modes[idx])
            assert_equal(new.modes[idx].task, data.modes[idx].task)
            assert_equal(new.modes[idx].resources, data.modes[idx].resources)
            assert_equal(new.modes[idx].duration, data.modes[idx].duration)

        assert_equal(new.constraints, data.constraints)
        assert_equal(new.setup_times, data.setup_times)
        assert_equal(new.horizon, data.horizon)
        assert_equal(new.objective, data.objective)

    def with_changes(data):
        """
        Tests that when using ``ProblemData.replace()`` replaces the attributes
        with the new values when they are passed as arguments.
        """
        new = data.replace(
            jobs=[Job(due_date=2, deadline=2), Job(due_date=1, deadline=1)],
            resources=[Resource(capacity=0, name="new"), Machine(name="new")],
            tasks=[Task(earliest_start=2), Task(earliest_start=2)],
            modes=[
                Mode(task=0, resources=[0], duration=20),
                Mode(task=1, resources=[1], duration=10),
            ],
            constraints={(1, 0): [Constraint.END_BEFORE_START]},
            setup_times=np.array(
                [
                    np.zeros((2, 2)),  # resource without setup times
                    np.ones((2, 2)),  # resource with setup times
                ],
            ),
            horizon=2,
            objective=Objective.total_tardiness(),
        )
        assert_(new is not data)

        for idx in range(data.num_jobs):
            assert_(new.jobs[idx] is not data.jobs[idx])
            assert_(new.jobs[idx].deadline != data.jobs[idx].deadline)
            assert_(new.jobs[idx].due_date != data.jobs[idx].due_date)

        for idx in range(data.num_resources):
            assert_(new.resources[idx] is not data.resources[idx])
            assert_(new.resources[idx].name != data.resources[idx].name)

        for idx in range(data.num_tasks):
            assert_(new.tasks[idx] is not data.tasks[idx])
            assert_(
                new.tasks[idx].earliest_start != data.tasks[idx].earliest_start
            )

        for idx in range(data.num_modes):
            assert_(new.modes[idx] is not data.modes[idx])
            assert_(new.modes[idx].duration != data.modes[idx].duration)

        assert_(new.constraints != data.constraints)
        assert_(not np.array_equal(new.setup_times, data.setup_times))
        assert_(new.horizon != data.horizon)
        assert_(new.objective != data.objective)


# --- Tests that involve checking solver correctness of problem data. ---


def test_job_release_date(solver: str):
    """
    Tests that the tasks belonging to a job start no earlier than
    the job's release date.
    """
    model = Model()

    job = model.add_job(release_date=1)
    machine = model.add_machine()
    task = model.add_task(job=job)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Job's release date is one, so the task starts at one.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_job_deadline(solver: str):
    """
    Tests that the tasks beloning to a job end no later than the
    job's deadline.
    """
    model = Model()

    machine = model.add_machine()

    job1 = model.add_job()
    task1 = model.add_task(job=job1)

    job2 = model.add_job(deadline=2)
    task2 = model.add_task(job=job2)

    for task in [task1, task2]:
        model.add_mode(task, machine, duration=2)

    model.add_setup_time(machine, task2, task1, 10)

    result = model.solve(solver=solver)

    # Task 1 (processing time of 2) cannot start before task 2,
    # otherwise task 2 cannot start before time 1. So task 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and task 1 is processed from 12 to 14.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 14)


def test_job_deadline_infeasible(solver: str):
    """
    Tests that a too restrictive job deadline results in an infeasible model.
    """
    model = Model()

    job = model.add_job(deadline=1)
    machine = model.add_machine()
    task = model.add_task(job=job)

    model.add_mode(task, machine, duration=2)

    result = model.solve(solver=solver)

    # The processing time of the task is 2, but job deadline is 1.
    assert_equal(result.status.value, "Infeasible")


def test_task_earliest_start(solver: str):
    """
    Tests that an task starts no earlier than its earliest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job, earliest_start=1)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task starts at time 1 and takes 1 time unit, so the makespan is 2.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_task_latest_start(solver: str):
    """
    Tests that an task starts no later than its latest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [
        model.add_task(job=job),
        model.add_task(job=job, latest_start=1),
    ]

    for task in tasks:
        model.add_mode(task, machine, duration=2)

    model.add_setup_time(machine, tasks[1], tasks[0], 10)

    result = model.solve(solver=solver)

    # Task 1 (processing time of 2) cannot start before task 2,
    # otherwise task 2 cannot start before time 1. So task 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and task 1 is processed from 12 to 14.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 14)


def test_task_fixed_start(solver: str):
    """
    Tests that an task starts at its fixed start time when earliest
    and latest start times are equal.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job, earliest_start=42, latest_start=42)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task starts at time 42 and takes 1 time unit, so the makespan is 43.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 43)


def test_task_earliest_end(solver: str):
    """
    Tests that an task end no earlier than its earliest end time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job, earliest_end=2)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task cannot end before time 2, so it starts at time 1 with
    # duration 1, thus the makespan is 2.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_task_latest_end(solver: str):
    """
    Tests that an task ends no later than its latest end time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [
        model.add_task(job=job),
        model.add_task(job=job, latest_end=2),
    ]

    for task in tasks:
        model.add_mode(task, machine, duration=2)

    model.add_setup_time(machine, tasks[1], tasks[0], 10)

    result = model.solve(solver=solver)

    # Task 1 (processing time of 2) cannot start before task 2,
    # otherwise task 2 cannot end before time 2. So task 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and task 1 is processed from 12 to 14.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 14)


def test_task_fixed_end(solver: str):
    """
    Tests that an task ends at its fixed end time when earliest
    and latest end times are equal.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job, earliest_end=42, latest_end=42)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task ends at 42, so the makespan is 42.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 42)


def test_task_fixed_duration_infeasible_with_timing_constraints(
    solver: str,
):
    """
    Tests that an task with fixed duration cannot be feasibly scheduled
    in combination with tight timing constraints.
    """
    model = Model()

    machine = model.add_machine()
    task = model.add_task(latest_start=0, earliest_end=10)
    model.add_mode(task, machine, duration=1)

    # Because of the latest start and earliest end constraints, we cannot
    # schedule the task with fixed duration, since its processing time
    # is 1.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Infeasible")


def test_task_non_fixed_duration(solver: str):
    """
    Tests that an task with non-fixed duration is scheduled correctly.
    """
    model = Model()

    machine = model.add_machine()
    task = model.add_task(
        latest_start=0,
        earliest_end=10,
        fixed_duration=False,
    )
    model.add_mode(task, machine, duration=1)

    # Since the task's duration is not fixed, it can be scheduled in a
    # feasible way. In this case, it starts at 0 and ends at 10, which includes
    # the processing time (1) and respects the timing constraints.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 10)
    assert_equal(result.best.tasks, [TaskData(0, [0], 0, 10)])


def test_resource_processes_two_tasks_simultaneously(solver: str):
    """
    Tests that a resource can process two tasks simultaneously.
    """
    model = Model()
    resource = model.add_resource(capacity=2)
    task1 = model.add_task()
    task2 = model.add_task()
    model.add_mode(task1, [resource], duration=1, demands=[1])
    model.add_mode(task2, [resource], duration=1, demands=[1])

    # The resource has capacity 2, so both tasks can be scheduled at the same
    # time. This results in a makespan of 1 instead of 2 in the case where
    # resources can only process one task at a time.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 1)


def test_resource_renewable_capacity_is_respected(solver: str):
    """
    Tests that a resource with renewable capacity is respected.
    """
    model = Model()
    resource = model.add_resource(capacity=2)
    task1 = model.add_task()
    task2 = model.add_task()
    model.add_mode(task1, [resource], duration=1, demands=[2])
    model.add_mode(task2, [resource], duration=1, demands=[2])

    # The resource has capacity 2, and each task requires 2 units of
    # capacity, so only one task can be scheduled at a time. This results
    # in a makespan of 2.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_resource_zero_capacity_is_respected(solver: str):
    """
    Tests that a resource with zero capacity is respected.
    """
    model = Model()
    resource = model.add_resource(capacity=0)
    task = model.add_task()
    model.add_mode(task, [resource], duration=10, demands=[0])
    model.add_mode(task, [resource], duration=1, demands=[1])

    # The resource has zero capacity, so it can only be scheduled using the
    # first mode with much longer duration.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 10)


def test_resource_non_renewable_capacity(solver: str):
    """
    Tests that a resource with non-renewable capacity is respected.
    """
    model = Model()

    resource = model.add_resource(capacity=1, renewable=False)
    task1 = model.add_task()
    model.add_mode(task1, [resource], duration=1, demands=[1])

    # The resource has capacity 1 and the task requires 1 unit of
    # capacity, so the task can be scheduled.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 1)

    # Now we add a second task that requires 1 unit of capacity.
    task2 = model.add_task()
    model.add_mode(task2, [resource], duration=1, demands=[1])

    # Since the resource has non-renewable capacity, the second task
    # cannot be scheduled.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Infeasible")


@pytest.mark.parametrize(
    "prec_type,expected_makespan",
    [
        # start 0 == start 0
        (Constraint.START_AT_START, 2),
        # start 2 == end 2
        (Constraint.START_AT_END, 4),
        # start 0 <= start 0
        (Constraint.START_BEFORE_START, 2),
        # start 0 <= end 2
        (Constraint.START_BEFORE_END, 2),
        # end 2 == start 2
        (Constraint.END_AT_START, 4),
        # end 2 == end 2
        (Constraint.END_AT_END, 2),
        # end 2 <= start 2
        (Constraint.END_BEFORE_START, 4),
        # end 2 <= end 2
        (Constraint.END_BEFORE_END, 2),
        (Constraint.IDENTICAL_RESOURCES, 4),
        (Constraint.DIFFERENT_RESOURCES, 2),
    ],
)
def test_constraints(solver, prec_type: Constraint, expected_makespan: int):
    """
    Tests that constraints are respected. This example uses two tasks and two
    resources with processing times of 2.
    """
    model = Model()

    job = model.add_job()
    resources = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task(job=job) for _ in range(2)]
    modes = [
        Mode(task=task, resources=[resource], duration=2)
        for resource in range(len(resources))
        for task in range(len(tasks))
    ]

    data = ProblemData([job], resources, tasks, modes, {(0, 1): [prec_type]})
    result = solve(data, solver=solver)

    assert_equal(result.objective, expected_makespan)


def test_identical_resources_with_modes_and_multiple_resources(solver: str):
    """
    Tests that the identical resources constraint is respected when tasks have
    modes with multiple resources.
    """
    model = Model()

    machine1 = model.add_machine()
    machine2 = model.add_machine()
    task1 = model.add_task()
    task2 = model.add_task()

    model.add_mode(task1, [machine1], duration=1)  # mode 0
    model.add_mode(task2, [machine2], duration=1)  # mode 1
    model.add_mode(task1, [machine1, machine2], duration=10)  # mode 2
    model.add_mode(task2, [machine1, machine2], duration=10)  # mode 3

    # Selecting the single machine modes for both tasks is optimal, which
    # results in a makespan of 1.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 1)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[0].mode, 0)
    assert_equal(result.best.tasks[1].mode, 1)

    # Now we add the identical resources constraint...
    model.add_identical_resources(task1, task2)

    # ... which forces the tasks to be scheduled on identical resources:
    # this results in the double-resource mode to be selected, which results
    # in a makespan of 20.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 20)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[0].mode, 2)
    assert_equal(result.best.tasks[1].mode, 3)


def test_different_resources_with_modes_and_multiple_resources(solver: str):
    """
    Tests that the different resources constraint is respected when tasks have
    modes with multiple resources.
    """
    model = Model()

    machine1 = model.add_machine()
    machine2 = model.add_machine()
    machine3 = model.add_machine()
    task1 = model.add_task()
    task2 = model.add_task()

    model.add_mode(task1, [machine1, machine2], duration=1)  # mode 0
    model.add_mode(task1, [machine1, machine3], duration=2)  # mode 1
    model.add_mode(task1, [machine3], duration=100)  # mode 2
    model.add_mode(task2, [machine1, machine2], duration=1)  # mode 3

    # Selecting mode 0 and mode 3 is optimal.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 2)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[0].mode, 0)
    assert_equal(result.best.tasks[1].mode, 3)

    # Now we add the different resource constraint...
    model.add_different_resource(task1, task2)

    # ...so mode 0 and mode 3 can no longer be selected. The only option
    # is to select mode 2 for task 1 and mode 3 for task 2.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 100)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[0].mode, 2)
    assert_equal(result.best.tasks[1].mode, 3)


def test_previous_constraint(solver: str):
    """
    Tests that the previous constraint is respected.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task1 = model.add_task(job=job)
    task2 = model.add_task(job=job)

    model.add_mode(task1, machine, duration=1)
    model.add_mode(task2, machine, duration=1)

    model.add_setup_time(machine, task2, task1, duration=100)
    model.add_previous(task2, task1)

    result = model.solve(solver=solver)

    # Task 2 must be scheduled before task 1, but the setup time
    # between them is 100, so the makespan is 1 + 100 + 1 = 102.
    assert_equal(result.objective, 102)


def test_previous_multiple_machines(solver: str):
    """
    Test the previous constraint with tasks that have modes with multiple
    machines.
    """
    model = Model()

    machine1 = model.add_machine()
    machine2 = model.add_machine()
    task1 = model.add_task()
    task2 = model.add_task()

    model.add_mode(task1, [machine1, machine2], duration=1)
    model.add_mode(task2, [machine1, machine2], duration=1)

    model.add_setup_time(machine1, task2, task1, duration=10)
    model.add_setup_time(machine2, task2, task1, duration=10)

    result = model.solve(solver=solver)
    assert_equal(result.objective, 2)
    assert_equal(result.status.value, "Optimal")

    # Now we add the previous constraint...
    model.add_previous(task2, task1)

    # ...so task 2 must be scheduled before task 1, but the setup time
    # between them is 10, so the makespan is 1 + 10 + 1 = 2.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 12)
    assert_equal(result.status.value, "Optimal")


def test_before_constraint(solver: str):
    """
    Tests that the before constraint is respected.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task1 = model.add_task(job=job)
    task2 = model.add_task(job=job)
    task3 = model.add_task(job=job)

    for task in [task1, task2, task3]:
        model.add_mode(task, machine, duration=1)

    model.add_setup_time(machine, task1, task2, 100)
    model.add_setup_time(machine, task2, task3, 100)

    result = model.solve(solver=solver)

    # No constraints, so the makespan is 1 + 1 + 1 = 3.
    assert_equal(result.objective, 3)

    # Let's now add that task 1 must be scheduled before task 2 and task 2
    # before task 3.
    model.add_before(task1, task2)
    model.add_before(task2, task3)

    result = model.solve(solver=solver)

    # The setup times are 100, so the makespan is 1 + 100 + 1 + 100 + 1 = 203.
    assert_equal(result.objective, 203)


def test_tight_horizon_results_in_infeasiblity(solver: str):
    """
    Tests that a tight horizon results in an infeasible instance.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job)

    model.add_mode(task, machine, duration=2)
    model.set_horizon(1)

    result = model.solve(solver=solver)

    # Processing time is 2, but horizon is 1, so this is infeasible.
    assert_equal(result.status.value, "Infeasible")


@pytest.mark.parametrize(
    "objective, weights",
    [
        (Objective.makespan, (1, 0, 0, 0, 0)),
        (Objective.tardy_jobs, (0, 1, 0, 0, 0)),
        (Objective.total_tardiness, (0, 0, 1, 0, 0)),
        (Objective.total_flow_time, (0, 0, 0, 1, 0)),
        (Objective.total_earliness, (0, 0, 0, 0, 1)),
    ],
)
def test_objective_classmethods_set_attributes_correctly(objective, weights):
    """
    Checks that the classmethods of the Objective class set the attributes
    correctly.
    """
    obj = objective()
    assert_equal(obj.weight_makespan, weights[0])
    assert_equal(obj.weight_tardy_jobs, weights[1])
    assert_equal(obj.weight_total_tardiness, weights[2])
    assert_equal(obj.weight_total_flow_time, weights[3])
    assert_equal(obj.weight_total_earliness, weights[4])


def test_makespan_objective(solver: str):
    """
    Tests that the makespan objective is correctly optimized.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task in tasks:
        model.add_mode(task, machine, duration=2)

    result = model.solve(solver=solver)

    assert_equal(result.objective, 4)
    assert_equal(result.status.value, "Optimal")


def test_tardy_jobs(solver: str):
    """
    Tests that the number of tardy jobs objective is correctly optimized.
    """
    model = Model()
    machine = model.add_machine()

    for _ in range(3):
        job = model.add_job(due_date=3, weight=2)
        task = model.add_task(job=job)
        model.add_mode(task, machine, duration=3)

    model.set_objective(weight_tardy_jobs=1)

    # Only one job can be scheduled on time. The other two are tardy.
    # Both jobs have weight 2, so the objective value is 4.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 4)
    assert_equal(result.status.value, "Optimal")


def test_total_flow_time(solver: str):
    """
    Tests that the total flow time objective is correctly optimized.
    """
    model = Model()

    machine = model.add_machine()
    weights = [2, 10]

    for idx in range(2):
        job = model.add_job(weight=weights[idx], release_date=1)
        task = model.add_task(job=job)
        model.add_mode(task, machine, duration=idx + 1)

    model.set_objective(weight_total_flow_time=1)

    result = model.solve(solver=solver)

    # One resource and two jobs (A, B) with processing times (1, 2) and weights
    # (2, 10). Because of these weights, it's optimal to schedule B before A.
    # Release date is 1, so task B ends at time 3 and task A ends at time 4.
    # But the flow time is 2 and 3 for B and A, respectively, so we get an
    # objective of 2 * 1 + 3 * 2 = 26.
    assert_equal(result.objective, 26)
    assert_equal(result.status.value, "Optimal")


def test_total_tardiness(solver: str):
    """
    Tests that the total tardiness objective function is correctly optimized.
    """
    model = Model()

    machine = model.add_machine()
    durations = [2, 4]
    due_dates = [2, 2]
    weights = [2, 10]

    for idx in range(2):
        job = model.add_job(weight=weights[idx], due_date=due_dates[idx])
        task = model.add_task(job=job)
        model.add_mode(task, machine, durations[idx])

    model.set_objective(weight_total_tardiness=1)

    result = model.solve(solver=solver)

    # We have an instance with one resource and two jobs (A, B) with processing
    # times (2, 4), due dates (2, 2), and weights (2, 10). Because of the
    # weights, it's optimal to schedule B before A resulting in completion
    # times (6, 4) and thus a total tardiness of 2 * 4 + 10 * 2 = 28.
    assert_equal(result.objective, 28)
    assert_equal(result.status.value, "Optimal")


def test_total_earliness(solver: str):
    """
    Tests that the total earliness objective function is correctly optimized.
    """
    model = Model()
    machine = model.add_machine()
    job = model.add_job(weight=1, due_date=2)
    task = model.add_task(job=job)

    model.add_mode(task, machine, duration=1)
    model.set_objective(weight_total_earliness=1)

    result = model.solve(solver=solver)

    # Due date is 2, so we the task starts at 1 with duration 1 to incur
    # no earliness.
    assert_equal(result.objective, 0)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[0].start, 1)
    assert_equal(result.best.tasks[0].end, 2)

    # Now let's another job that cannot finish without earliness.
    job2 = model.add_job(weight=10, deadline=1, due_date=2)
    task2 = model.add_task(job=job2)
    model.add_mode(task2, machine, duration=1)

    result = model.solve(solver=solver)

    # The second job completes at time 1, which is 1 time unit too early.
    # Together with the job weight, this results in an objective value of 10.
    assert_equal(result.objective, 10)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[1].start, 0)
    assert_equal(result.best.tasks[1].end, 1)


def test_combined_objective(solver: str):
    """
    Tests that a combined objective function of makespan and tardy jobs is
    correctly optimized.
    """
    model = Model()

    machine = model.add_machine()
    durations = [2, 4]

    for idx in range(2):
        job = model.add_job(due_date=0)
        task = model.add_task(job=job)
        model.add_mode(task, machine, durations[idx])

    model.set_objective(weight_makespan=10, weight_tardy_jobs=2)
    result = model.solve(solver=solver)

    # Optimal solution has a makespan of 6 and both jobs are tardy.
    # The objective value is 10 * 6 + 2 * 2 = 64.
    assert_equal(result.objective, 64)
    assert_equal(result.status.value, "Optimal")
