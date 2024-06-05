import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_equal, assert_raises

from pyjobshop.constants import MAX_VALUE
from pyjobshop.Model import Model
from pyjobshop.ProblemData import (
    Constraint,
    Job,
    Machine,
    Objective,
    ProblemData,
    Task,
)
from pyjobshop.Solution import Task as Task_


def test_job_attributes():
    """
    Tests that the attributes of the Job class are set correctly.
    """
    job = Job(weight=0, release_date=1, due_date=2, deadline=3, name="test")

    assert_equal(job.weight, 0)
    assert_equal(job.release_date, 1)
    assert_equal(job.due_date, 2)
    assert_equal(job.deadline, 3)
    assert_equal(job.name, "test")


def test_job_default_attributes():
    """
    Tests that the default attributes of the Job class are set correctly.
    """
    job = Job()

    assert_equal(job.weight, 1)
    assert_equal(job.release_date, 0)
    assert_equal(job.due_date, None)
    assert_equal(job.deadline, None)
    assert_equal(job.name, "")


@pytest.mark.parametrize(
    "weight, release_date, due_date, deadline, name",
    [
        (-1, 0, 0, 0, ""),  # weight < 0
        (0, -1, 0, 0, ""),  # release_date < 0
        (0, 0, -1, 0, ""),  # due_date < 0
        (0, 0, 0, -1, ""),  # deadline < 0
        (0, 10, 0, 0, ""),  # release_date > deadline
    ],
)
def test_job_attributes_raises_invalid_parameters(
    weight: int, release_date: int, due_date: int, deadline: int, name: str
):
    """
    Tests that a ValueError is raised when invalid parameters are passed to
    Job.
    """
    with assert_raises(ValueError):
        Job(
            weight=weight,
            release_date=release_date,
            due_date=due_date,
            deadline=deadline,
            name=name,
        )


def test_machine_attributes():
    """
    Tests that the attributes of the Machine class are set correctly.
    """
    # Let's first test the default values.
    machine = Machine()

    assert_equal(machine.allow_overlap, False)
    assert_equal(machine.name, "")

    # Now test with some values.
    machine = Machine(allow_overlap=True, name="TestMachine")

    assert_equal(machine.allow_overlap, True)
    assert_equal(machine.name, "TestMachine")


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
    jobs = [Job() for _ in range(5)]
    machines = [Machine() for _ in range(5)]
    tasks = [Task() for _ in range(5)]
    job2tasks = [[0], [1], [2], [3], [4]]
    processing_times = {(i, j): 1 for i in range(5) for j in range(5)}
    constraints = {
        key: [Constraint.END_BEFORE_START] for key in ((0, 1), (2, 3), (4, 5))
    }
    setup_times = np.ones((5, 5, 5), dtype=int)
    planning_horizon = 100
    objective = Objective.TOTAL_COMPLETION_TIME

    data = ProblemData(
        jobs,
        machines,
        tasks,
        job2tasks,
        processing_times,
        constraints,
        setup_times,
        planning_horizon,
        objective,
    )

    assert_equal(data.jobs, jobs)
    assert_equal(data.machines, machines)
    assert_equal(data.tasks, tasks)
    assert_equal(data.job2tasks, job2tasks)
    assert_equal(data.processing_times, processing_times)
    assert_equal(data.constraints, constraints)
    assert_allclose(data.setup_times, setup_times)
    assert_equal(data.planning_horizon, planning_horizon)
    assert_equal(data.objective, objective)


def test_problem_data_non_input_parameter_attributes():
    """
    Tests that attributes that are not input parameters of the ProblemData
    class are set correctly.
    """
    jobs = [Job() for _ in range(1)]
    machines = [Machine() for _ in range(3)]
    tasks = [Task() for _ in range(3)]
    job2tasks = [[0, 1, 2]]
    processing_times = {(1, 2): 1, (2, 1): 1, (0, 1): 1, (2, 0): 1}

    data = ProblemData(jobs, machines, tasks, job2tasks, processing_times, {})

    # The lists in machine2tasks and task2machines are sorted.
    machine2tasks = [[1], [2], [0, 1]]
    task2machines = [[2], [0, 2], [1]]
    assert_equal(data.machine2tasks, machine2tasks)
    assert_equal(data.task2machines, task2machines)

    assert_equal(data.num_jobs, 1)
    assert_equal(data.num_machines, 3)
    assert_equal(data.num_tasks, 3)


def test_problem_data_default_values():
    """
    Tests that the default values of the ProblemData class are set correctly.
    """
    jobs = [Job() for _ in range(1)]
    machines = [Machine() for _ in range(1)]
    tasks = [Task() for _ in range(1)]
    job2tasks = [[0]]
    constraints = {(0, 1): [Constraint.END_BEFORE_START]}
    processing_times = {(0, 0): 1}
    data = ProblemData(
        jobs, machines, tasks, job2tasks, processing_times, constraints
    )

    assert_allclose(data.setup_times, np.zeros((1, 1, 1), dtype=int))
    assert_equal(data.planning_horizon, MAX_VALUE)
    assert_equal(data.objective, Objective.MAKESPAN)


@pytest.mark.parametrize(
    "processing_times,  setup_times, planning_horizon",
    [
        # Negative processing times.
        ({(0, 0): -1}, np.ones((1, 1, 1)), 1),
        # Negative setup times.
        ({(0, 0): 1}, np.ones((1, 1, 1)) * -1, 1),
        # Invalid setup times shape.
        ({(0, 0): 1}, np.ones((2, 2, 2)), 1),
        # Negative planning horizon.
        ({(0, 0): 1}, np.ones((2, 2, 2)), -1),
    ],
)
def test_problem_data_raises_when_invalid_arguments(
    processing_times: dict[tuple[int, int], int],
    setup_times: np.ndarray,
    planning_horizon: int,
):
    """
    Tests that the ProblemData class raises an error when invalid arguments are
    passed.
    """
    with assert_raises(ValueError):
        ProblemData(
            [Job()],
            [Machine()],
            [Task()],
            [[0]],
            processing_times,
            {},
            setup_times.astype(int),
            planning_horizon=planning_horizon,
        )


@pytest.mark.parametrize(
    "objective", [Objective.TARDY_JOBS, Objective.TOTAL_TARDINESS]
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
            [Machine()],
            [Task()],
            [[0]],
            {},
            {},
            objective=objective,
        )


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

    model.add_processing_time(machine, task, duration=1)

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
        model.add_processing_time(machine, task, duration=2)

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

    model.add_processing_time(machine, task, duration=2)

    result = model.solve(solver=solver)

    # Task's processing time is 2, but job deadline is 1.
    assert_equal(result.status.value, "Infeasible")


def test_machine_allow_overlap(solver: str):
    """
    Tests that allowing overlap results in a shorter makespan.
    """
    model = Model()
    job = model.add_job()
    machine = model.add_machine(allow_overlap=False)  # no overlap
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task in tasks:
        model.add_processing_time(machine, task, duration=2)

    result = model.solve(solver=solver)

    # No overlap, so we schedule the two tasks consecutively with
    # final makespan of four.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 4)

    # Let's now allow for overlap.
    model = Model()
    job = model.add_job()
    machine = model.add_machine(allow_overlap=True)
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task in tasks:
        model.add_processing_time(machine, task, duration=2)

    result = model.solve(solver=solver)

    # With overlap we can schedule both tasks simultaneously on the
    # machine, resulting in a makespan of two.
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 2)


def test_task_earliest_start(solver: str):
    """
    Tests that an task starts no earlier than its earliest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job, earliest_start=1)

    model.add_processing_time(machine, task, duration=1)

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
        model.add_processing_time(machine, task, duration=2)

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

    model.add_processing_time(machine, task, duration=1)

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

    model.add_processing_time(machine, task, duration=1)

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
        model.add_processing_time(machine, task, duration=2)

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

    model.add_processing_time(machine, task, duration=1)

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
    model.add_processing_time(machine, task, duration=1)

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
    model.add_processing_time(machine, task, duration=1)

    # Since the task's duration is not fixed, it can be scheduled in a
    # feasible way. In this case, it starts at 0 and ends at 10, which includes
    # the processing time (1) and respects the timing constraints.
    result = model.solve(solver=solver)
    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 10)
    assert_equal(result.best.schedule, [Task_(0, 0, 0, 10)])


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
    ],
)
def test_timing_precedence(
    solver, prec_type: Constraint, expected_makespan: int
):
    """
    Tests that timing precedence constraints are respected. This example
    uses two tasks and two machines with processing times of 2.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine(), model.add_machine()]
    tasks = [model.add_task(job=job) for _ in range(2)]

    for machine in machines:
        for task in tasks:
            model.add_processing_time(machine, task, duration=2)

    model.add_constraint(tasks[0], tasks[1], prec_type)

    result = model.solve(solver=solver)

    assert_equal(result.objective, expected_makespan)


def test_previous_constraint(solver: str):
    """
    Tests that the previous constraint is respected.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    model.add_processing_time(machine, tasks[0], duration=1)
    model.add_processing_time(machine, tasks[1], duration=1)

    model.add_setup_time(machine, tasks[1], tasks[0], duration=100)
    model.add_constraint(tasks[1], tasks[0], Constraint.PREVIOUS)

    result = model.solve(solver=solver)

    # Task 1 must be scheduled before task 0, but the setup time
    # between them is 100, so the makespan is 1 + 100 + 1 = 102.
    assert_equal(result.objective, 102)


@pytest.mark.parametrize(
    "prec_type,expected_makespan",
    [
        (Constraint.SAME_UNIT, 4),
        (Constraint.DIFFERENT_UNIT, 2),
    ],
)
def test_assignment_constraint(
    solver, prec_type: Constraint, expected_makespan: int
):
    """
    Tests that assignment constraints are respected. This example
    uses two tasks and two machines with processing times of 2.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine(), model.add_machine()]
    tasks = [model.add_task(job=job) for _ in range(2)]

    for machine in machines:
        for task in tasks:
            model.add_processing_time(machine, task, duration=2)

    model.add_constraint(tasks[0], tasks[1], prec_type)

    result = model.solve(solver=solver)

    assert_equal(result.objective, expected_makespan)


def test_tight_planning_horizon_results_in_infeasiblity(solver: str):
    """
    Tests that a tight planning horizon results in an infeasible instance.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    task = model.add_task(job=job)

    model.add_processing_time(machine, task, duration=2)
    model.set_planning_horizon(1)

    result = model.solve(solver=solver)

    # Processing time is 2, but planning horizon is 1, so this is infeasible.
    assert_equal(result.status.value, "Infeasible")


def test_makespan_objective(solver: str):
    """
    Tests that the makespan objective is correctly optimized.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    tasks = [model.add_task(job=job) for _ in range(2)]

    for task in tasks:
        model.add_processing_time(machine, task, duration=2)

    result = model.solve(solver=solver)

    assert_equal(result.objective, 4)
    assert_equal(result.status.value, "Optimal")


def test_tardy_jobs(solver: str):
    """
    Tests that the (number of) tardy jobs objective is correctly optimized.
    """
    model = Model()

    machine = model.add_machine()

    for idx in range(3):
        job = model.add_job(due_date=idx + 1)
        task = model.add_task(job=job)
        model.add_processing_time(machine, task, duration=3)

    model.set_objective(Objective.TARDY_JOBS)

    result = model.solve(solver=solver)

    # Only the last job/task can be scheduled on time. The other two
    # are tardy.
    assert_equal(result.objective, 2)
    assert_equal(result.status.value, "Optimal")


def test_total_completion_time(solver: str):
    """
    Tests that the total completion time objective is correctly optimized.
    """
    model = Model()

    machines = [model.add_machine() for _ in range(2)]

    for idx in range(3):
        job = model.add_job()
        task = model.add_task(job=job)

        for machine in machines:
            model.add_processing_time(machine, task, duration=idx + 1)

    model.set_objective(Objective.TOTAL_COMPLETION_TIME)

    result = model.solve(solver=solver)

    # We have three jobs (A, B, C) with processing times of 1, 2, 3 on either
    # machine. The optimal schedule is [A, C] and [B] with total completion
    # time of: 1 (A) + 4 (C) + 2 (B) = 7. Note how this leads a suboptimal
    # makespan of 4, while it could have been 3 (with schedule [A, B] and [C]).
    assert_equal(result.objective, 7)
    assert_equal(result.status.value, "Optimal")


def test_total_weighted_completion_time(solver: str):
    """
    Tests that the weights are taken into account when using the total
    completion time objective function.
    """
    model = Model()

    machine = model.add_machine()
    weights = [2, 10]

    for idx in range(2):
        job = model.add_job(weight=weights[idx])
        task = model.add_task(job=job)
        model.add_processing_time(machine, task, duration=idx + 1)

    model.set_objective(Objective.TOTAL_COMPLETION_TIME)

    result = model.solve(solver=solver)

    # One machine and two jobs (A, B) with processing times (1, 2) and weights
    # (2, 10). Because of these weights, it's optimal to schedule B for A with
    # completion times (3, 2) and objective 2 * 3 + 10 * 2 = 26.
    assert_equal(result.objective, 26)
    assert_equal(result.status.value, "Optimal")


def test_total_tardiness(solver: str):
    """
    Tests that the total tardiness objective function is correctly optimized.
    """
    model = Model()

    machines = [model.add_machine() for _ in range(2)]
    due_dates = [1, 2, 3]

    for idx in range(3):
        job = model.add_job(due_date=due_dates[idx])
        task = model.add_task(job=job)

        for machine in machines:
            model.add_processing_time(machine, task, duration=idx + 1)

    model.set_objective(Objective.TOTAL_TARDINESS)

    result = model.solve(solver=solver)

    # We have three jobs (A, B, C) with processing times of 1, 2, 3 on either
    # machine and due dates 1, 2, 3. We schedule A and B first on both machines
    # and C is scheduled after A on machine 1. Jobs A and B are on time
    # while C is one time unit late, resulting in 1 total tardiness.
    assert_equal(result.objective, 1)
    assert_equal(result.status.value, "Optimal")


def test_total_weighted_tardiness(solver: str):
    """
    Tests that the weights are taken into account when using the total
    tardiness objective function.
    """
    model = Model()

    machine = model.add_machine()
    processing_times = [2, 4]
    due_dates = [2, 2]
    weights = [2, 10]

    for idx in range(2):
        job = model.add_job(weight=weights[idx], due_date=due_dates[idx])
        task = model.add_task(job=job)
        model.add_processing_time(machine, task, processing_times[idx])

    model.set_objective(Objective.TOTAL_TARDINESS)

    result = model.solve(solver=solver)

    # We have an instance with one machine and two jobs (A, B) with processing
    # times (2, 4), due dates (2, 2), and weights (2, 10). Because of the
    # weights, it's optimal to schedule B before A resulting in completion
    # times (6, 4) and thus a total tardiness of 2 * 4 + 10 * 2 = 28.
    assert_equal(result.objective, 28)
    assert_equal(result.status.value, "Optimal")


# --- Small classical examples. ---


def test_jobshop(solver: str):
    """
    Tests a simple job shop problem with 3 machines and 6 jobs.

    Example from https://developers.google.com/optimization/scheduling/job_shop
    """

    # A job consists of tasks, which is a tuple (machine_id, processing_time).
    jobs_data = [
        [(0, 3), (1, 2), (2, 2)],  # Job0
        [(0, 2), (2, 1), (1, 4)],  # Job1
        [(1, 4), (2, 3)],  # Job2
        [(2, 3), (1, 4), (0, 8)],  # Job3
        [(1, 3), (0, 4), (2, 2)],  # Job4
        [(1, 3)],  # Job5
    ]
    num_jobs = len(jobs_data)

    model = Model()
    jobs = [model.add_job() for _ in range(num_jobs)]
    machines = [model.add_machine() for _ in range(3)]

    for job_idx, tasks_ in enumerate(jobs_data):
        tasks = [model.add_task(job=jobs[job_idx]) for _ in tasks_]

        # Add processing times.
        for idx, (machine_idx, duration) in enumerate(tasks_):
            model.add_processing_time(
                machines[machine_idx], tasks[idx], duration
            )

        # Impose linear routing precedence constraints.
        for task_idx in range(1, len(tasks)):
            task1, task2 = tasks[task_idx - 1], tasks[task_idx]
            model.add_constraint(task1, task2, Constraint.END_BEFORE_START)

    result = model.solve(solver=solver)

    assert_equal(result.status.value, "Optimal")
    assert_equal(result.objective, 20)
