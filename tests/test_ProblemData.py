import pytest
from numpy.testing import assert_, assert_equal, assert_raises

from pyjobshop.constants import MAX_VALUE
from pyjobshop.Model import Model
from pyjobshop.ProblemData import (
    Consecutive,
    Constraints,
    DifferentResources,
    EndBeforeEnd,
    EndBeforeStart,
    IdenticalResources,
    Job,
    Machine,
    Mode,
    ModeDependency,
    NonRenewable,
    Objective,
    ProblemData,
    Renewable,
    SameSequence,
    SetupTime,
    StartBeforeEnd,
    StartBeforeStart,
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


def test_machine_attributes():
    """
    Tests that the attributes of the Machine class are set correctly.
    """
    machine = Machine(breaks=[], no_idle=True, name="Machine")
    assert_equal(machine.breaks, [])
    assert_equal(machine.no_idle, True)
    assert_equal(machine.name, "Machine")


def test_machine_default_attributes():
    """
    Tests that the default attributes of the Machine class are set correctly.
    """
    machine = Machine()
    assert_equal(machine.breaks, [])
    assert_equal(machine.no_idle, False)
    assert_equal(machine.name, "")


@pytest.mark.parametrize(
    "breaks, no_idle",
    [
        ([(-1, 0)], False),  # breaks start < 0
        ([(2, 1)], False),  # breaks start > end
        ([(1, 3), (2, 4)], False),  # breaks overlapping
        ([(1, 2)], True),  # breaks with no_idle
    ],
)
def test_machine_raises_invalid_parameters(breaks, no_idle):
    """
    Tests that a ValueError is raised when invalid parameters are passed
    to the Machine class.
    """
    with assert_raises(ValueError):
        Machine(breaks=breaks, no_idle=no_idle)


def test_renewable_attributes():
    """
    Tests that the attributes of the Renewable class are set correctly.
    """
    renewable = Renewable(capacity=1, breaks=[(1, 2)], name="TestRenewable")
    assert_equal(renewable.capacity, 1)
    assert_equal(renewable.breaks, [(1, 2)])
    assert_equal(renewable.name, "TestRenewable")


def test_renewable_default_attributes():
    """
    Tests that the default attributes of the Renewable class are set correctly.
    """
    renewable = Renewable(capacity=0)
    assert_equal(renewable.breaks, [])
    assert_equal(renewable.name, "")


@pytest.mark.parametrize(
    "capacity, breaks",
    [
        (-1, [(0, 1)]),  # capacity < 0
        (1, [(-1, 0)]),  # breaks start < 0
        (1, [(2, 1)]),  # breaks start > end
        (1, [(1, 3), (2, 4)]),  # breaks overlapping
    ],
)
def test_renewable_raises_invalid_parameters(capacity, breaks):
    """
    Tests that a ValueError is raised when invalid parameters are passed
    to the Renewable class.
    """
    with assert_raises(ValueError):
        Renewable(capacity=capacity, breaks=breaks)


def test_non_renewable_attributes():
    """
    Tests that the attributes of the NonRenewable class are set correctly.
    """
    # Let's first test the default values.
    non_renewable = NonRenewable(capacity=1)
    assert_equal(non_renewable.name, "")

    # Now test with some values.
    non_renewable = NonRenewable(capacity=1, name="TestNonRenewable")
    assert_equal(non_renewable.capacity, 1)
    assert_equal(non_renewable.name, "TestNonRenewable")


def test_non_renewable_default_attributes():
    """
    Tests that the default attributes of the NonRenewable class are set
    correctly.
    """
    non_renewable = NonRenewable(capacity=0)
    assert_equal(non_renewable.name, "")


def test_non_renewable_raises_invalid_capacity():
    """
    Tests that a ValueError is raised when an invalid capacity is passed
    to the Renewable class.
    """
    with assert_raises(ValueError):
        NonRenewable(capacity=-1)  # negative


def test_task_attributes():
    """
    Tests that the attributes of the Task class are set correctly.
    """
    task = Task(
        job=0,
        earliest_start=1,
        latest_start=2,
        earliest_end=3,
        latest_end=4,
        fixed_duration=False,
        name="TestTask",
    )

    assert_equal(task.job, 0)
    assert_equal(task.earliest_start, 1)
    assert_equal(task.latest_start, 2)
    assert_equal(task.earliest_end, 3)
    assert_equal(task.latest_end, 4)
    assert_equal(task.fixed_duration, False)
    assert_equal(task.name, "TestTask")


def test_task_default_attributes():
    """
    Tests that the default attributes of the Task class are set correctly.
    """
    task = Task()

    assert_equal(task.job, None)
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
        Task(
            earliest_start=earliest_start,
            latest_start=latest_start,
            earliest_end=earliest_end,
            latest_end=latest_end,
        )


def test_mode_attributes():
    """
    Tests that the attributes of the Mode class are set correctly.
    """
    mode = Mode(task=0, resources=[0], duration=1, demands=[1], name="mode")

    assert_equal(mode.task, 0)
    assert_equal(mode.duration, 1)
    assert_equal(mode.resources, [0])
    assert_equal(mode.demands, [1])
    assert_equal(mode.name, "mode")


def test_mode_default_attributes():
    """
    Tests that the default attributes of the Mode class are set correctly.
    """
    mode = Mode(task=0, resources=[0], duration=1, demands=[1])

    assert_equal(mode.name, "")


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


def test_mode_dependency_must_have_at_least_one_succesor_mode():
    """
    Tests that ModeDependency requires at least one successor mode.
    """
    with assert_raises(ValueError):
        ModeDependency(0, [])


@pytest.mark.parametrize(
    "tasks1, tasks2",
    [
        ([0], [1, 2]),  # not same length
        ([0, 0], [1, 2]),  # tasks1 duplicate values
        ([0, 1], [2, 2]),  # tasks2 duplicate values
    ],
)
def test_same_sequence_raises(tasks1: list[int], tasks2: list[int]):
    """
    Tests that SameSequence raises an error when the tasks are invalid.
    """
    with assert_raises(ValueError):
        SameSequence(0, 1, tasks1, tasks2)


def test_negative_setup_times_not_allowed():
    """
    Tests that SetupTime duration must be non-negative.
    """
    SetupTime(0, 0, 1, 0)  # OK

    with assert_raises(ValueError):
        SetupTime(0, 0, 1, -1)  # not OK


def test_constraints_str():
    """
    Tests the string representation of the Constraints class.
    """
    constraints = Constraints()
    assert_equal(str(constraints), "0 constraints")

    constraints.start_before_start.append(StartBeforeStart(0, 1))
    expected = "1 constraints\n└─ 1 start_before_start"
    assert_equal(str(constraints), expected)

    constraints.mode_dependencies.append(ModeDependency(0, [1, 2, 3]))
    expected = "2 constraints\n├─ 1 start_before_start\n└─ 1 mode_dependencies"
    assert_equal(str(constraints), expected)


@pytest.mark.parametrize(
    "weights",
    [
        [-1, 0, 0, 0, 0, 0, 0],  # weight_makespan < 0,
        [0, -1, 0, 0, 0, 0, 0],  # weight_tardy_jobs < 0
        [0, 0, -1, 0, 0, 0, 0],  # weight_total_flow_time < 0
        [0, 0, 0, -1, 0, 0, 0],  # weight_total_tardiness < 0
        [0, 0, 0, 0, -1, 0, 0],  # weight_total_earliness < 0
        [0, 0, 0, 0, 0, -1, 0],  # weight_max_tardiness < 0
        [0, 0, 0, 0, 0, 0, -1],  # weight_total_setup_time < 0
    ],
)
def test_objective_valid_values(weights: list[int]):
    """
    Tests that an error is raised when invalid weights are passed to the
    Objective class.
    """
    with assert_raises(ValueError):
        Objective(*weights)


def test_objective_str():
    """
    Tests the string representation of the Objective class.
    """
    objective = Objective()
    assert_equal(str(objective), "objective\n└─ no weights")

    objective = Objective(weight_makespan=1)
    assert_equal(str(objective), "objective\n└─ weight_makespan=1")

    objective = Objective(weight_makespan=1, weight_max_tardiness=10)

    expected = "objective\n├─ weight_makespan=1\n└─ weight_max_tardiness=10"
    assert_equal(str(objective), expected)


def test_problem_data_input_parameter_attributes():
    """
    Tests that the input parameters of the ProblemData class are set correctly
    as attributes.
    """
    jobs = [Job(tasks=[idx]) for idx in range(5)]
    resources = [Machine() for _ in range(5)]
    tasks = [Task(job=idx) for idx in range(5)]
    modes = [
        Mode(task=task, resources=[resource], duration=1)
        for task in range(5)
        for resource in range(5)
    ]
    constraints = Constraints(
        end_before_start=[
            EndBeforeStart(0, 1),
            EndBeforeStart(2, 3),
            EndBeforeStart(3, 4),
        ]
    )
    objective = Objective(weight_total_flow_time=1)

    data = ProblemData(
        jobs,
        resources,
        tasks,
        modes,
        constraints,
        objective,
    )

    assert_equal(data.jobs, jobs)
    assert_equal(data.resources, resources)
    assert_equal(data.tasks, tasks)
    assert_equal(data.modes, modes)
    assert_equal(data.constraints, constraints)
    assert_equal(data.objective, objective)


def test_problem_data_non_input_parameter_attributes():
    """
    Tests that attributes that are not input parameters of the ProblemData
    class are set correctly.
    """
    jobs = [Job(tasks=[0, 1, 2])]
    resources = [Machine(), Renewable(1), NonRenewable(2)]
    tasks = [Task(job=0) for _ in range(3)]
    modes = [
        Mode(task=2, resources=[1], duration=1),
        Mode(task=1, resources=[2], duration=1),
        Mode(task=1, resources=[0], duration=1),
        Mode(task=0, resources=[2], duration=1),
    ]
    constraints = Constraints(
        start_before_start=[StartBeforeStart(1, 1)],
        start_before_end=[StartBeforeEnd(1, 1)],
        end_before_end=[EndBeforeEnd(1, 1)],
        end_before_start=[EndBeforeStart(1, 1)],
    )

    data = ProblemData(jobs, resources, tasks, modes, constraints)

    assert_equal(data.num_jobs, 1)
    assert_equal(data.num_resources, 3)
    assert_equal(data.num_tasks, 3)
    assert_equal(data.num_modes, 4)
    assert_equal(data.num_constraints, 4)
    assert_equal(data.machine_idcs, [0])
    assert_equal(data.renewable_idcs, [1])
    assert_equal(data.non_renewable_idcs, [2])


def test_problem_data_default_values():
    """
    Tests that the default values of the ProblemData class are set correctly.
    """
    jobs = [Job(tasks=[0])]
    resources = [Renewable(0)]
    tasks = [Task(job=0)]
    modes = [Mode(task=0, resources=[0], duration=1)]
    data = ProblemData(jobs, resources, tasks, modes)

    assert_equal(data.constraints, Constraints())
    assert_equal(data.objective, Objective(weight_makespan=1))


def test_problem_data_str():
    """
    Tests the string representation of the ProblemData class.
    """
    jobs = [Job(tasks=[idx]) for idx in range(5)]
    resources = [Machine() for _ in range(5)] + [Renewable(1), NonRenewable(1)]
    tasks = [Task(job=idx) for idx in range(5)]
    modes = [
        Mode(task=task, resources=[resource], duration=1)
        for task in range(5)
        for resource in range(5)
    ]
    constraints = Constraints(
        end_before_start=[
            EndBeforeStart(0, 1),
            EndBeforeStart(2, 3),
            EndBeforeStart(3, 4),
        ]
    )
    objective = Objective(weight_makespan=10, weight_total_flow_time=1)
    data = ProblemData(jobs, resources, tasks, modes, constraints, objective)

    expected = (
        "5 jobs\n"
        "7 resources\n"
        "├─ 5 machines\n"
        "├─ 1 renewable\n"
        "└─ 1 non_renewable\n"
        "5 tasks\n"
        "25 modes\n"
        "3 constraints\n"
        "└─ 3 end_before_start\n"
        "objective\n"
        "├─ weight_makespan=10\n"
        "└─ weight_total_flow_time=1"
    )
    assert_equal(str(data), expected)


def test_problem_data_job_must_reference_at_least_one_task():
    """
    Tests that an error is raised when a job does not reference any tasks.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job(tasks=[])],
            [Renewable(0)],
            [Task()],
            [Mode(0, [0], 1)],
        )


def test_problem_data_job_references_unknown_task():
    """
    Tests that an error is raised when a job references an unknown task.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job(tasks=[42])],
            [Renewable(0)],
            [Task()],
            [Mode(0, [0], 1)],
        )


def test_problem_data_job_task_reference_mismatch():
    """
    Tests that an error is raised when a job references a task that does
    not reference the job.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job(tasks=[0])],
            [Renewable(0)],
            [Task()],
            [Mode(0, [0], 1)],
        )


def test_problem_data_task_references_unknown_job():
    """
    Tests that an error is raised when a task references an unknown job.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job(tasks=[0])],
            [Renewable(0)],
            [Task(job=0), Task(job=42)],
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
            [],
            [Renewable(0)],
            [Task()],
            [mode],
        )


def test_problem_data_task_without_modes():
    """
    Tests that an error is raised when a task has no processing modes.
    """
    with assert_raises(ValueError):
        ProblemData([], [Renewable(0)], [Task()], [])


def test_problem_data_all_modes_demand_infeasible():
    """
    Tests that an error is raised when all modes of a task have infeasible
    demands.
    """

    # This is OK: at least one mode is feasible.
    ProblemData(
        [],
        [Renewable(capacity=1)],
        [Task()],
        [
            Mode(0, [0], 2, demands=[1]),  # feasible
            Mode(0, [0], 2, demands=[2]),  # infeasible
        ],
    )

    with assert_raises(ValueError):
        # This is not OK: no mode is feasible.
        ProblemData(
            [],
            [Renewable(capacity=1)],
            [Task()],
            [
                Mode(0, [0], 2, demands=[2]),  # infeasible
                Mode(0, [0], 2, demands=[2]),  # infeasible
            ],
        )


@pytest.mark.parametrize(
    "name, cls, idcs_list",
    [
        ("start_before_start", StartBeforeStart, [(2, 0), (0, 2)]),
        ("start_before_end", StartBeforeEnd, [(2, 0), (0, 2)]),
        ("end_before_start", EndBeforeStart, [(2, 0), (0, 2)]),
        ("end_before_end", EndBeforeEnd, [(2, 0), (0, 2)]),
        ("identical_resources", IdenticalResources, [(2, 0), (0, 2)]),
        ("different_resources", DifferentResources, [(2, 0), (0, 2)]),
        ("consecutive", Consecutive, [(2, 0), (0, 2)]),
        (
            "same_sequence",
            SameSequence,
            [
                (0, 2, [0], [0]),  # invalid resource idx
                (2, 0, [0], [0]),  # invalid resource idx
                (0, 1, [0], [0]),  # not a machine idx
                (1, 0, [0], [0]),  # not a machine idx
                (0, 0, [2], [0]),  # invalid task idx
                (0, 0, [0], [2]),  # invalid task idx
            ],
        ),
        (
            "setup_times",
            SetupTime,
            [
                (1, 0, 0, 1),  # invalid resource idx
                (2, 0, 0, 1),  # not a machine idx
                (0, 2, 0, 1),  # invalid task idx1
                (0, 0, 2, 1),  # invalid task idx2
            ],
        ),
        ("mode_dependencies", ModeDependency, [(2, [0]), (0, [2])]),
    ],
)
def test_problem_data_raises_invalid_indices(name, cls, idcs_list):
    """
    Tests that the ProblemData class raises an error when the indices of
    constraints are invalid.
    """
    for idcs in idcs_list:
        constraints = Constraints()
        getattr(constraints, name).append(cls(*idcs))

        with assert_raises(ValueError):
            ProblemData(
                [],
                [Machine(), Renewable(0)],
                [Task(), Task()],
                [Mode(0, [0], 1), Mode(1, [0], 2)],
                constraints,
            )


def test_problem_data_raises_same_sequence_invalid_machine_assigned_tasks():
    """
    Tests that the ProblemData class raises an error when the number of tasks
    assigned to the machines is not the same.
    """
    with pytest.raises(ValueError):
        # Machine 1 can process two tasks, but Machine 2 can only process one.
        ProblemData(
            [],
            [Machine(), Machine()],
            [Task(), Task(), Task()],
            [Mode(0, [0], 1), Mode(1, [0], 1), Mode(2, [1], 1)],
            Constraints(same_sequence=[SameSequence(0, 1)]),
        )


@pytest.mark.parametrize(
    "same_sequence",
    [
        SameSequence(0, 1, [0, 2], [2, 3]),  # tasks1 invalid
        SameSequence(0, 1, [0, 1], [0, 3]),  # tasks2 invalid
        SameSequence(0, 1, [0], [2]),  # incomplete
        SameSequence(0, 1, [0, 1, 4], [2, 3, 4]),  # incomplete
    ],
)
def test_problem_data_raises_same_sequence_invalid_tasks(same_sequence):
    """
    Tests that the ProblemData class raises an error when the tasks in a
    SameSequence constraint are not valid.
    """
    with pytest.raises(ValueError, match="tasks"):
        ProblemData(
            [],
            [Machine(), Machine(), Machine()],
            [Task(), Task(), Task(), Task(), Task()],
            [
                Mode(0, [0], 1),
                Mode(1, [0], 1),
                Mode(2, [1], 1),
                Mode(3, [1], 1),
                Mode(4, [2], 1),
            ],
            Constraints(same_sequence=[same_sequence]),
        )


@pytest.mark.parametrize(
    "resource",
    [
        Renewable(capacity=1),
        NonRenewable(capacity=1),
    ],
)
def test_problem_data_raises_capacitated_resources_and_setup_times(resource):
    """
    Tests that the ProblemData class raises an error when invalid resources
    have setup times.
    """
    with assert_raises(ValueError):
        ProblemData(
            [],
            [resource],
            [Task(), Task()],
            [Mode(0, [0], 0), Mode(1, [0], 0)],
            Constraints(setup_times=[SetupTime(0, 0, 1, 1)]),
        )


def test_problem_data_raises_mode_dependency_same_task():
    """
    Tests that the ProblemData class raises an error when a mode dependency
    constraint refers to modes of all the same task.
    """
    with assert_raises(ValueError):
        ProblemData(
            [],
            [Renewable(0)],
            [Task()],
            [Mode(0, [0], 1), Mode(0, [0], 2), Mode(0, [0], 3)],
            Constraints(mode_dependencies=[ModeDependency(0, [1])]),
        )


@pytest.mark.parametrize(
    "objective",
    [
        Objective(weight_tardy_jobs=1),
        Objective(weight_total_tardiness=1),
        Objective(weight_total_earliness=1),
        Objective(weight_max_tardiness=1),
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
            [Job(tasks=[0])],
            [Renewable(0)],
            [Task()],
            [Mode(0, [0], 0)],
            objective=objective,
        )


def test_problem_data_setup_times_objective_without_setup_times_constraints():
    """
    Tests that an error is raised when setup times are not defined in the
    constraints and the total setup times objective is selected.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job(tasks=[0])],
            [Renewable(0)],
            [Task()],
            [Mode(0, [0], 0)],
            objective=Objective(weight_total_setup_time=1),
        )


def make_replace_data():
    jobs = [
        Job(tasks=[0], due_date=1, deadline=1),
        Job(tasks=[1], due_date=2, deadline=2),
    ]
    resources = [
        Renewable(capacity=0, name="resource"),
        NonRenewable(capacity=0, name="resource"),
    ]
    tasks = [Task(job=0, earliest_start=1), Task(job=1, earliest_start=1)]
    modes = [
        Mode(task=0, resources=[0], duration=1),
        Mode(task=1, resources=[1], duration=2),
    ]
    constraints = Constraints(end_before_start=[EndBeforeStart(0, 1)])
    objective = Objective(weight_makespan=1)

    return ProblemData(
        jobs,
        resources,
        tasks,
        modes,
        constraints,
        objective,
    )


def test_problem_data_replace_no_changes():
    """
    Tests that when using ``ProblemData.replace()`` without any arguments
    returns a new instance with different objects but with the same values.
    """

    data = make_replace_data()
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
    assert_equal(new.objective, data.objective)


def test_problem_data_replace_with_changes():
    """
    Tests that when using ``ProblemData.replace()`` replaces the attributes
    with the new values when they are passed as arguments.
    """
    data = make_replace_data()
    new = data.replace(
        jobs=[
            Job(tasks=[1], due_date=2, deadline=2),
            Job(tasks=[0], due_date=1, deadline=1),
        ],
        resources=[Renewable(capacity=0, name="new"), Machine(name="new")],
        tasks=[Task(job=1, earliest_start=2), Task(job=0, earliest_start=2)],
        modes=[
            Mode(task=0, resources=[0], duration=20),
            Mode(task=1, resources=[1], duration=10),
        ],
        constraints=Constraints(
            end_before_start=[EndBeforeStart(1, 0)],
            setup_times=[SetupTime(1, 0, 1, 0), SetupTime(1, 1, 0, 10)],
        ),
        objective=Objective(weight_total_tardiness=1),
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
    assert_(new.objective != data.objective)


def test_problem_data_resource2modes():
    """
    Tests that the mode indices corresponding to each resource are correctly
    computed.
    """
    data = ProblemData(
        [],
        [Renewable(0), Renewable(0)],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
    )

    assert_equal(data.resource2modes(0), [0])
    assert_equal(data.resource2modes(1), [1, 2])

    # Check that the task2modes method raises an error when an resource
    # index is passed.
    with pytest.raises(ValueError):
        data.resource2modes(-1)

    with pytest.raises(ValueError):
        data.resource2modes(2)


def test_problem_data_task2modes():
    """
    Tests that the mode indices corresponding to each task are correctly
    computed.
    """
    data = ProblemData(
        [],
        [Renewable(0), Renewable(0)],
        [Task(), Task()],
        modes=[Mode(0, [0], 1), Mode(0, [1], 10), Mode(1, [1], 0)],
    )

    assert_equal(data.task2modes(0), [0, 1])
    assert_equal(data.task2modes(1), [2])

    # Check that the task2modes method raises an error when an invalid task
    # index is passed.
    with pytest.raises(ValueError):
        data.task2modes(-1)

    with pytest.raises(ValueError):
        data.task2modes(2)


# --- Tests that involve checking solver correctness of problem data. ---


def test_empty_problem_instance(solver: str):
    """
    Tests that an empty problem data instance can be solved.
    """
    data = ProblemData([], [], [], [])
    result = solve(data, solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 0)


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
    Tests that the tasks belonging to a job end no later than the
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
    Tests that a task starts no earlier than its earliest start time.
    """
    model = Model()

    machine = model.add_machine()
    task = model.add_task(earliest_start=1)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task starts at time 1 and takes 1 time unit, so the makespan is 2.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_task_latest_start(solver: str):
    """
    Tests that a task starts no later than its latest start time.
    """
    model = Model()

    machine = model.add_machine()
    tasks = [
        model.add_task(),
        model.add_task(latest_start=1),
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
    Tests that a task starts at its fixed start time when earliest
    and latest start times are equal.
    """
    model = Model()

    machine = model.add_machine()
    task = model.add_task(earliest_start=42, latest_start=42)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task starts at time 42 and takes 1 time unit, so the makespan is 43.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 43)


def test_task_earliest_end(solver: str):
    """
    Tests that a task end no earlier than its earliest end time.
    """
    model = Model()

    machine = model.add_machine()
    task = model.add_task(earliest_end=2)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task cannot end before time 2, so it starts at time 1 with
    # duration 1, thus the makespan is 2.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_task_latest_end(solver: str):
    """
    Tests that a task ends no later than its latest end time.
    """
    model = Model()

    machine = model.add_machine()
    tasks = [model.add_task(), model.add_task(latest_end=2)]

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
    Tests that a task ends at its fixed end time when earliest
    and latest end times are equal.
    """
    model = Model()

    machine = model.add_machine()
    task = model.add_task(earliest_end=42, latest_end=42)

    model.add_mode(task, machine, duration=1)

    result = model.solve(solver=solver)

    # Task ends at 42, so the makespan is 42.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 42)


def test_task_fixed_duration_infeasible_with_timing_constraints(
    solver: str,
):
    """
    Tests that a task with fixed duration cannot be feasibly scheduled
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
    Tests that a task with non-fixed duration is scheduled correctly.
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


def test_machine_breaks(solver: str):
    """
    Tests that a machine resource respects breaks.
    """
    model = Model()
    machine1 = model.add_machine(breaks=[(1, 2), (3, 4)])
    machine2 = model.add_machine(breaks=[(0, 10)])
    task = model.add_task()
    model.add_mode(task, machine1, duration=2)
    model.add_mode(task, machine2, duration=2)

    # It's best to use machine 1, and the earliest that the task can start is
    # at time 4, so the makespan is 6.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 6)


def test_machine_no_idle(solver: str):
    """
    Tests that a machine with no idle time is respected.
    """
    model = Model()
    machine = model.add_machine(no_idle=True)
    task1 = model.add_task(earliest_start=10)
    task2 = model.add_task()
    model.add_mode(task1, machine, 1)
    model.add_mode(task2, machine, 2)

    # Add a few dummy modes to check if multiple modes are handled correctly.
    model.add_mode(task1, machine, 20)
    model.add_mode(task2, machine, 20)

    # Task 1 can start earliest at time 10. Because the machine does not allow
    # idle times, task 2 will be scheduled at time 8.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 11)

    sol_tasks = result.best.tasks
    assert_equal(sol_tasks[0].start, 10)
    assert_equal(sol_tasks[0].end, 11)
    assert_equal(sol_tasks[1].start, 8)
    assert_equal(sol_tasks[1].end, 10)


def test_machine_no_idle_setup_times(solver: str):
    """
    Tests that a machine with no idle time and setup times is respected.
    Setup times are allowed on machines with idle times.
    """
    model = Model()
    machine = model.add_machine(no_idle=True)
    task1 = model.add_task(earliest_start=10)
    task2 = model.add_task()
    model.add_mode(task1, machine, 1)
    model.add_mode(task2, machine, 2)

    # Add a few dummy modes to check if multiple modes are handled correctly.
    model.add_mode(task1, machine, 20)
    model.add_mode(task2, machine, 20)

    model.add_setup_time(machine, task2, task1, 3)
    model.add_setup_time(machine, task1, task2, 3)

    # Task 1 can start earliest at time 10. Because the machine does not allow
    # idle times, task 2 will be scheduled at time 5 and complete at 7. The
    # setup time of 3 is added, so task 2 starts at 10 and ends at 11.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 11)

    sol_tasks = result.best.tasks
    assert_equal(sol_tasks[0].start, 10)
    assert_equal(sol_tasks[0].end, 11)
    assert_equal(sol_tasks[1].start, 5)
    assert_equal(sol_tasks[1].end, 7)


def test_resource_processes_two_tasks_simultaneously(solver: str):
    """
    Tests that a resource can process two tasks simultaneously.
    """
    model = Model()
    resource = model.add_renewable(capacity=2)
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
    resource = model.add_renewable(capacity=2)
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
    resource = model.add_renewable(capacity=0)
    task = model.add_task()
    model.add_mode(task, [resource], duration=10, demands=[0])
    model.add_mode(task, [resource], duration=1, demands=[1])

    # The resource has zero capacity, so it can only be scheduled using the
    # first mode with much longer duration.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 10)


def test_renewable_breaks(solver: str):
    """
    Tests that a renewable resource respects breaks.
    """
    model = Model()
    resource1 = model.add_renewable(capacity=1, breaks=[(1, 2), (3, 4)])
    resource2 = model.add_renewable(capacity=1, breaks=[(0, 100)])
    task = model.add_task()
    model.add_mode(task, resource1, duration=2)
    model.add_mode(task, resource2, duration=2)

    # It's best to use resource 1, and the earliest that the task can start is
    # at time 4, so the makespan is 6.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 6)


def test_renewable_breaks_respected_by_zero_demand(solver: str):
    """
    Tests that a renewable resource break is respected even if the mode has
    zero demand.
    """
    model = Model()
    resource = model.add_renewable(capacity=1, breaks=[(1, 2), (3, 4)])
    task = model.add_task()
    model.add_mode(task, resource, duration=2, demands=[0])

    # The earliest that the task can start is as time 4, so the makespan is 6.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 6)


def test_resource_non_renewable_capacity(solver: str):
    """
    Tests that a resource with non-renewable capacity is respected.
    """
    model = Model()

    resource = model.add_non_renewable(capacity=1)
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


@pytest.fixture(scope="function")
def timing_constraints_model():
    """
    Sets up a simple model with 2 machines, 2 tasks and unit processing times.
    """
    model = Model()

    machines = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task() for _ in range(2)]
    [
        model.add_mode(task, machine, duration=1)
        for task in tasks
        for machine in machines
    ]

    return model


def test_start_before_start(timing_constraints_model: Model, solver: str):
    """
    Tests that the start before start constraint is respected.
    """
    model = timing_constraints_model
    model.add_start_before_start(model.tasks[0], model.tasks[1], delay=2)

    # Task 1 starts at 0, task 2 can start earliest at 0 + 2 (delay).
    result = model.solve(solver=solver)
    assert_equal(result.objective, 3)
    assert_equal(result.best.tasks[0].start, 0)
    assert_equal(result.best.tasks[1].start, 2)


def test_start_before_end(timing_constraints_model: Model, solver: str):
    """
    Tests that the start before end constraint is respected.
    """
    model = timing_constraints_model
    model.add_start_before_end(model.tasks[0], model.tasks[1], delay=2)

    # Task 1 starts at 0, task 2 must end after 0 + 2 (delay).
    result = model.solve(solver=solver)
    assert_equal(result.objective, 2)
    assert_equal(result.best.tasks[0].start, 0)
    assert_equal(result.best.tasks[1].end, 2)


def test_end_before_start(timing_constraints_model: Model, solver: str):
    """
    Tests that the end before start constraint is respected.
    """
    model = timing_constraints_model
    model.add_end_before_start(model.tasks[0], model.tasks[1], delay=2)

    # Task 1 ends at 1 earliest, task 2 must start after 1 + 2 (delay).
    result = model.solve(solver=solver)
    assert_equal(result.objective, 4)
    assert_equal(result.best.tasks[0].end, 1)
    assert_equal(result.best.tasks[1].start, 3)


def test_end_before_end(timing_constraints_model: Model, solver: str):
    """
    Tests that the end before end constraint is respected.
    """
    model = timing_constraints_model
    model.add_end_before_end(model.tasks[0], model.tasks[1], delay=2)

    # Task 1 ends at 1 earliest, task 2 must end after 1 + 2 (delay).
    result = model.solve(solver=solver)
    assert_equal(result.objective, 3)
    assert_equal(result.best.tasks[0].end, 1)
    assert_equal(result.best.tasks[1].end, 3)


def test_identical_resources(solver: str):
    """
    Tests that the identical resources constraint is respected.
    """
    model = Model()

    resources = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task() for _ in range(2)]
    [
        model.add_mode(task=task, resources=resource, duration=2)
        for resource in resources
        for task in tasks
    ]
    model.add_identical_resources(tasks[0], tasks[1])

    result = model.solve(solver=solver)

    # The identical resources constraint forces the tasks to be scheduled on
    # the same resource (instead of using two different resources), so the
    # makespan is 4.
    assert_equal(result.objective, 4)


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


def test_different_resources(solver: str):
    """
    Tests that the different resources constraint is respected.
    """
    model = Model()

    resources = [model.add_machine() for _ in range(2)]
    tasks = [model.add_task() for _ in range(2)]

    # Processing duration 1 on first resource, 5 on second resource.
    modes = [model.add_mode(task, resources[0], duration=1) for task in tasks]
    modes += [model.add_mode(task, resources[1], duration=5) for task in tasks]
    model.add_different_resources(tasks[0], tasks[1])

    result = model.solve(solver=solver)

    # The different resources constraint forces the tasks to be scheduled on
    # different resources, so the makespan is 5.
    assert_equal(result.objective, 5)


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
    model.add_different_resources(task1, task2)

    # ...so mode 0 and mode 3 can no longer be selected. The only option
    # is to select mode 2 for task 1 and mode 3 for task 2.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 100)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.best.tasks[0].mode, 2)
    assert_equal(result.best.tasks[1].mode, 3)


def test_consecutive_constraint(solver: str):
    """
    Tests that the consecutive constraint is respected.
    """
    model = Model()

    machine = model.add_machine()
    task1 = model.add_task()
    task2 = model.add_task()

    model.add_mode(task1, machine, duration=1)
    model.add_mode(task2, machine, duration=1)

    model.add_setup_time(machine, task2, task1, duration=100)
    model.add_consecutive(task2, task1)

    result = model.solve(solver=solver)

    # Task 2 must be scheduled directly before task 1, but the setup time
    # between them is 100, so the makespan is 1 + 100 + 1 = 102.
    assert_equal(result.objective, 102)


def test_consecutive_multiple_machines(solver: str):
    """
    Test the consecutive constraint with tasks that have modes with multiple
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

    # Now we add the consecutive constraint...
    model.add_consecutive(task2, task1)

    # ...so task 2 must be scheduled directly before task 1, but the setup time
    # between them is 10, so the makespan is 1 + 10 + 1 = 2.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 12)
    assert_equal(result.status.value, "Optimal")


def test_same_sequence(solver: str):
    """
    Tests that the same sequence constraint is respected for a simple
    permutation flow shop problem.
    """
    model = Model()

    machine1 = model.add_machine()
    machine2 = model.add_machine()

    tasks1 = [model.add_task() for _ in range(2)]
    tasks2 = [model.add_task() for _ in range(2)]

    for task in tasks1:
        model.add_mode(task, machine1, duration=1)

    for task in tasks2:
        model.add_mode(task, machine2, duration=1)

    for task1, task2 in zip(tasks1, tasks2):
        model.add_end_before_start(task1, task2)

    model.add_consecutive(tasks1[0], tasks1[1])
    model.add_setup_time(machine2, tasks2[0], tasks2[1], 10)
    model.add_same_sequence(machine1, machine2)

    # Tasks1 and tasks2 must be scheduled in the same sequence on both
    # machines. Because of the consecutive constraint, the first task
    # must be scheduled before the second task on both machines. This
    # incurs a setup time of 10.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 13)


def test_same_sequence_custom_ordering(solver: str):
    """
    Tests that the same sequence constraint with custom ordering of tasks is
    respected. Same example as above, but with tasks2 reversed at places.
    """
    model = Model()

    machine1 = model.add_machine()
    machine2 = model.add_machine()

    tasks1 = [model.add_task() for _ in range(2)]
    tasks2 = [model.add_task() for _ in range(2)]

    for task in tasks1:
        model.add_mode(task, machine1, duration=1)

    for task in tasks2:
        model.add_mode(task, machine2, duration=1)

    for task1, task2 in zip(tasks1, tasks2[::-1]):
        model.add_end_before_start(task1, task2)

    model.add_same_sequence(machine1, machine2, tasks1, tasks2[::-1])
    model.add_consecutive(tasks1[0], tasks1[1])
    model.add_setup_time(machine2, tasks2[1], tasks2[0], 10)

    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 13)


def test_same_sequence_invalid_multiple_modes_cpoptimizer():
    """
    Tests that a ValueError is raised when the same sequence constraint is
    imposed on tasks that have multiple modes using the same resource, and
    CP Optimizer is used as solver.
    """
    model = Model()

    machine1 = model.add_machine()
    machine2 = model.add_machine()

    tasks1 = [model.add_task() for _ in range(2)]
    tasks2 = [model.add_task() for _ in range(2)]

    for task in tasks1:
        model.add_mode(task, machine1, duration=1)
        model.add_mode(task, machine1, duration=1)

    for task in tasks2:
        model.add_mode(task, machine2, duration=1)

    model.add_same_sequence(machine1, machine2, tasks1, tasks2)

    with assert_raises(ValueError):
        model.solve(solver="cpoptimizer")


def test_setup_time_bug(solver: str):
    """
    Tests that a bug identified in #307 is correctly fixed. This bug caused
    setup times to be ignored because dummy assignment variables were not
    properly deactivated for absent (task, machine) pairs.
    """
    model = Model()

    job = model.add_job()
    task1 = model.add_task(job)
    machine1 = model.add_machine()
    model.add_mode(task1, machine1, 1)

    machine2 = model.add_machine()
    task2 = model.add_task(job)
    task3 = model.add_task(job)
    model.add_mode(task2, machine2, 1)
    model.add_mode(task3, machine2, 1)

    for task_from in model.tasks:
        for task_to in model.tasks:
            model.add_setup_time(machine2, task_from, task_to, 1)

    # Before fixing this bug, the solver would incorrecty ignore the setup
    # time between task 2 and task 3 (due to a dummy assignment variable).
    result = model.solve(solver=solver)
    assert_equal(result.objective, 3)
    assert_equal(result.status.value, "Optimal")


def test_mode_dependencies(solver: str):
    """
    Test that the mode dependency constraint works correctly. We test with
    a simple model that is solved with and without the mode dependency
    constraint and check the objectives of the two different variants of
    the model.
    """
    model = Model()

    machines = [model.add_machine() for _ in range(4)]
    task1 = model.add_task()
    task2 = model.add_task()

    mode1 = model.add_mode(task=task1, resources=machines[0], duration=5)
    model.add_mode(task=task2, resources=machines[1], duration=2)
    mode3 = model.add_mode(task=task2, resources=machines[2], duration=10)
    mode4 = model.add_mode(task=task2, resources=machines[3], duration=10)
    model.add_end_before_start(task1, task2)

    # First we solve the model without the mode dependency constraint, we
    # expect to get an optimal solution with a makespan of 7.
    result = model.solve(solver=solver)
    assert_equal(result.objective, 7)

    # Now we add the mode dependency, and we see that enforce that if mode1
    # gets selected for task 1 (only option in this test case) then we need
    # to enforce that mode3 or mode 4 gets selected for task 2. Since these
    # modes have both duration 10 instead of 2, the makespan now equals 15.
    model.add_mode_dependency(mode1, [mode3, mode4])
    result = model.solve()
    assert_equal(result.objective, 15)


def test_empty_objective(solver: str):
    """
    Tests that the empty objective is correctly optimized.
    """
    data = ProblemData([], [], [], [], objective=Objective())
    result = solve(data, solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 0)


def test_makespan_objective(solver: str):
    """
    Tests that the makespan objective is correctly optimized.
    """
    model = Model()

    machine = model.add_machine()
    tasks = [model.add_task() for _ in range(2)]

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


def test_max_tardiness(solver: str):
    """
    Tests that the maximum tardiness objective function is correctly optimized.
    """
    model = Model()

    for idx in range(2):
        machine = model.add_machine()
        job = model.add_job(weight=idx + 1, due_date=0)
        task = model.add_task(job=job)
        model.add_mode(task, machine, duration=2)

    model.set_objective(weight_max_tardiness=2)

    result = model.solve(solver=solver)

    # Both jobs are tardy by 2 time units, but job 1 has weight 2 and job 2
    # has weight 1. So the maximum tardiness is 2 * 2 = 4. Multiplied with the
    # ``weight_max_tardiness`` of 2, the objective value is 8.
    assert_equal(result.objective, 8)
    assert_equal(result.best.tasks[0].end, 2)
    assert_equal(result.best.tasks[1].end, 2)


def test_total_setup_time(solver: str):
    """
    Tests that the total setup time objective function is correctly optimized.
    """
    model = Model()

    machine = model.add_machine()
    tasks = [model.add_task() for _ in range(3)]

    for task in tasks:
        model.add_mode(task, machine, duration=1)

    setups = [
        [100, 1, 100],
        [100, 100, 3],
        [100, 100, 100],
    ]
    for idx1, task1 in enumerate(tasks):
        for idx2, task2 in enumerate(tasks):
            model.add_setup_time(machine, task1, task2, setups[idx1][idx2])

    model.set_objective(weight_total_setup_time=2)
    result = model.solve(solver=solver)

    # Tasks 0, 1 and 2 are scheduled consecutively on a single machine with
    # setup times 1 and 3, respectively. Combined with an objective weight of
    # two, the objective value is 2 * (1 + 3) = 8.
    assert_equal(result.objective, 8)
    assert_equal(result.status.value, "Optimal")


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
