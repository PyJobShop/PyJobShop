import pytest
from numpy.testing import assert_equal

from pyjobshop.Model import Model
from pyjobshop.ProblemData import (
    AssignmentPrecedence,
    Objective,
    TimingPrecedence,
)

# TODO refactor with Solution


def test_job_release_date():
    """
    Tests that the operations belonging to a job start no earlier than
    the job's release date.
    """
    model = Model()

    job = model.add_job(release_date=1)
    machine = model.add_machine()
    operation = model.add_operation()

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=1)

    result = model.solve()

    # Job's release date is one, so the operation starts at one.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 2)


def test_job_deadline():
    """
    Tests that the operations beloning to a job end no later than the
    job's deadline.
    """
    model = Model()

    machine = model.add_machine()

    job1 = model.add_job()
    operation1 = model.add_operation()
    model.assign_job_operations(job1, [operation1])

    job2 = model.add_job(deadline=2)
    operation2 = model.add_operation()
    model.assign_job_operations(job2, [operation2])

    for operation in [operation1, operation2]:
        model.add_processing_time(machine, operation, duration=2)

    model.add_setup_time(machine, operation2, operation1, 10)

    result = model.solve()

    # Operation 1 (processing time of 2) cannot start before operation 2,
    # otherwise operation 2 cannot start before time 1. So operation 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and operation 1 is processed from 12 to 14.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 14)


def test_job_deadline_infeasible():
    """
    Tests that a too restrictive job deadline results in an infeasible model.
    """
    model = Model()

    job = model.add_job(deadline=1)
    machine = model.add_machine()
    operation = model.add_operation()

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=2)

    result = model.solve()

    # Operation's processing time is 2, but job deadline is 1.
    assert_equal(result.get_solve_status(), "Infeasible")


def test_earliest_start():
    """
    Tests that an operation starts no earlier than its earliest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_start=1)

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=1)

    result = model.solve()

    # Operation starts at time 1 and takes 1 time unit, so the makespan is 2.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 2)


def test_latest_start():
    """
    Tests that an operation starts no later than its latest start time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [
        model.add_operation(),
        model.add_operation(latest_start=1),
    ]

    for operation in operations:
        model.add_processing_time(machine, operation, duration=2)

    model.assign_job_operations(job, operations)

    model.add_setup_time(machine, operations[1], operations[0], 10)

    result = model.solve()

    # Operation 1 (processing time of 2) cannot start before operation 2,
    # otherwise operation 2 cannot start before time 1. So operation 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and operation 1 is processed from 12 to 14.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 14)


def test_fixed_start():
    """
    Tests that an operation starts at its fixed start time when earliest
    and latest start times are equal.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_start=42, latest_start=42)

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=1)

    result = model.solve()

    # Operation starts at time 42 and takes 1 time unit, so the makespan is 43.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 43)


def test_earliest_end():
    """
    Tests that an operation end no earlier than its earliest end time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_end=2)

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=1)

    result = model.solve()

    # Operation cannot end before time 2, so it starts at time 1 with
    # duration 1, thus the makespan is 2.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 2)


def test_latest_end():
    """
    Tests that an operation ends no later than its latest end time.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [
        model.add_operation(),
        model.add_operation(latest_end=2),
    ]

    for operation in operations:
        model.add_processing_time(machine, operation, duration=2)

    model.assign_job_operations(job, operations)

    model.add_setup_time(machine, operations[1], operations[0], 10)

    result = model.solve()

    # Operation 1 (processing time of 2) cannot start before operation 2,
    # otherwise operation 2 cannot end before time 2. So operation 2 is
    # scheduled first and is processed from 0 to 2. Then a setup time of 10
    # is added and operation 1 is processed from 12 to 14.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 14)


def test_fixed_end():
    """
    Tests that an operation ends at its fixed end time when earliest
    and latest end times are equal.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation(earliest_end=42, latest_end=42)

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=1)

    result = model.solve()

    # Operation ends at 42, so the makespan is 42.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 42)


def test_optional_operations():
    """
    Tests that optional operations are not scheduled.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [model.add_operation(), model.add_operation(optional=True)]

    model.assign_job_operations(job, operations)
    model.add_processing_time(machine, operations[0], duration=10)
    model.add_processing_time(machine, operations[1], duration=15)

    result = model.solve()

    # Operation 2 is not scheduled, so the makespan is 10, just the duration
    # of operation 1.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 10)


@pytest.mark.parametrize(
    "prec_type,expected_makespan",
    [
        # start 0 == start 0
        (TimingPrecedence.START_AT_START, 2),
        # start 2 == end 2
        (TimingPrecedence.START_AT_END, 4),
        # start 0 <= start 0
        (TimingPrecedence.START_BEFORE_START, 2),
        # start 0 <= end 2
        (TimingPrecedence.START_BEFORE_END, 2),
        # end 2 == start 2
        (TimingPrecedence.END_AT_START, 4),
        # end 2 == end 2
        (TimingPrecedence.END_AT_END, 2),
        # end 2 <= start 2
        (TimingPrecedence.END_BEFORE_START, 4),
        # end 2 <= end 2
        (TimingPrecedence.END_BEFORE_END, 2),
    ],
)
def test_timing_precedence(
    prec_type: TimingPrecedence, expected_makespan: int
):
    """
    Tests that timing precedence constraints are respected. This example
    uses two operations and two machines with processing times of 2.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine(), model.add_machine()]
    operations = [model.add_operation(), model.add_operation()]

    model.assign_job_operations(job, operations)

    for machine in machines:
        for operation in operations:
            model.add_processing_time(machine, operation, duration=2)

    model.add_timing_precedence(operations[0], operations[1], prec_type)

    result = model.solve()

    assert_equal(result.get_objective_value(), expected_makespan)


@pytest.mark.parametrize(
    "prec_type,expected_makespan",
    [
        # start 0 + delay 1 == start 1
        (TimingPrecedence.START_AT_START, 3),
        # start 1 + delay 1 == end 3
        (TimingPrecedence.START_AT_END, 3),
        # start 0 + delay 1 <= start 1
        (TimingPrecedence.START_BEFORE_START, 3),
        # start 0 + delay 1 <= end 2
        (TimingPrecedence.START_BEFORE_END, 2),
        # end 2 + delay 1 == start 0
        (TimingPrecedence.END_AT_START, 5),
        # end 2 + delay 1 == end 2
        (TimingPrecedence.END_AT_END, 3),
        # end 2 + delay 1 <= start 3
        (TimingPrecedence.END_BEFORE_START, 5),
        # end 2 + delay 1 <= end 3
        (TimingPrecedence.END_BEFORE_END, 3),
    ],
)
def test_timing_precedence_with_one_delay(
    prec_type: TimingPrecedence, expected_makespan: int
):
    """
    Tests that timing precedence constraints with delays are respected. This
    example is similar to `test_timing_precedence`, but with a delay of 1.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine(), model.add_machine()]
    operations = [model.add_operation(), model.add_operation()]

    model.assign_job_operations(job, operations)

    for machine in machines:
        for operation in operations:
            model.add_processing_time(machine, operation, duration=2)

    model.add_timing_precedence(
        operations[0], operations[1], prec_type, delay=1
    )

    result = model.solve()

    assert_equal(result.get_objective_value(), expected_makespan)


@pytest.mark.parametrize(
    "prec_type,expected_makespan",
    [
        (AssignmentPrecedence.PREVIOUS, 2),  # TODO needs better test
        (AssignmentPrecedence.SAME_UNIT, 4),
        (AssignmentPrecedence.DIFFERENT_UNIT, 2),
    ],
)
def test_assignment_precedence(
    prec_type: AssignmentPrecedence, expected_makespan: int
):
    """
    Tests that assignment precedence constraints are respected. This example
    uses two operations and two machines with processing times of 2.
    """
    model = Model()

    job = model.add_job()
    machines = [model.add_machine(), model.add_machine()]
    operations = [model.add_operation(), model.add_operation()]

    model.assign_job_operations(job, operations)

    for machine in machines:
        for operation in operations:
            model.add_processing_time(machine, operation, duration=2)

    model.add_assignment_precedence(operations[0], operations[1], prec_type)

    result = model.solve()

    assert_equal(result.get_objective_value(), expected_makespan)


def test_process_plans():
    """
    Tests that setting optional plans works correctly.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [model.add_operation(optional=True) for _ in range(4)]

    model.assign_job_operations(job, operations)

    for operation, duration in zip(operations, [1, 2, 3, 4]):
        model.add_processing_time(machine, operation, duration)

    plan1 = [operations[0], operations[1]]
    plan2 = [operations[2], operations[3]]
    model.add_process_plan(plan1, plan2)

    result = model.solve()

    # Schedule plan 1, so the makespan is 1 + 2 = 3.
    assert_equal(result.get_objective_value(), 3)


def test_makespan_objective():
    """
    Tests that the makespan objective is correctly optimized.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operations = [model.add_operation() for _ in range(2)]

    model.assign_job_operations(job, operations)

    for operation in operations:
        model.add_processing_time(machine, operation, duration=2)

    result = model.solve()

    assert_equal(result.get_objective_value(), 4)
    assert_equal(result.get_solve_status(), "Optimal")


def test_total_completion_time():
    """
    Tests that the total completion time objective is correctly optimized.
    """
    model = Model()

    machines = [model.add_machine() for _ in range(2)]

    for idx in range(3):
        job = model.add_job()
        operation = model.add_operation()

        model.assign_job_operations(job, [operation])

        for machine in machines:
            model.add_processing_time(machine, operation, duration=idx + 1)

    model.set_objective(Objective.TOTAL_COMPLETION_TIME)

    result = model.solve()

    # We have three jobs (A, B, C) with processing times of 1, 2, 3 on either
    # machine. The optimal schedule is [A, C] and [B] with total completion
    # time of: 1 (A) + 4 (C) + 2 (B) = 7. Note how this leads a suboptimal
    # makespan of 4, while it could have been 3 (with schedule [A, B] and [C]).
    assert_equal(result.get_objective_value(), 7)
    assert_equal(result.get_solve_status(), "Optimal")


def test_total_weighted_completion_time():
    model = Model()

    machine = model.add_machine()
    weights = [2, 10]

    for idx in range(2):
        job = model.add_job(weight=weights[idx])
        operation = model.add_operation()

        model.assign_job_operations(job, [operation])
        model.add_processing_time(machine, operation, duration=idx + 1)

    model.set_objective(Objective.TOTAL_COMPLETION_TIME)

    result = model.solve()

    # One machine and two jobs (A, B) with processing times (1, 2) and weights
    # (2, 10). Because of these weights, it's optimal to schedule B for A with
    # completion times (3, 2) and objective 2 * 3 + 10 * 2 = 26.
    assert_equal(result.get_objective_value(), 26)
    assert_equal(result.get_solve_status(), "Optimal")


def test_total_tardiness():
    model = Model()

    machines = [model.add_machine() for _ in range(2)]
    due_dates = [1, 2, 3]

    for idx in range(3):
        job = model.add_job(due_date=due_dates[idx])
        operation = model.add_operation()

        model.assign_job_operations(job, [operation])

        for machine in machines:
            model.add_processing_time(machine, operation, duration=idx + 1)

    model.set_objective(Objective.TOTAL_TARDINESS)

    result = model.solve()

    # We have three jobs (A, B, C) with processing times of 1, 2, 3 on either
    # machine and due dates 1, 2, 3. We schedule A and B first on both machines
    # and C is scheduled after A on machine 1. Jobs A and B are on time
    # while C is one time unit late, resulting in 1 total tardiness.
    assert_equal(result.get_objective_value(), 1)
    assert_equal(result.get_solve_status(), "Optimal")


def test_total_weighted_tardiness():
    model = Model()

    machine = model.add_machine()
    processing_times = [2, 4]
    due_dates = [2, 2]
    weights = [2, 10]

    for idx in range(2):
        job = model.add_job(weight=weights[idx], due_date=due_dates[idx])
        operation = model.add_operation()

        model.assign_job_operations(job, [operation])
        model.add_processing_time(
            machine, operation, duration=processing_times[idx]
        )

    model.set_objective(Objective.TOTAL_TARDINESS)

    result = model.solve()

    # We have an instance with one machine and two jobs (A, B) with processing
    # times (2, 4), due dates (2, 2), and weights (2, 10). Because of the
    # weights, it's optimal to schedule B before A resulting in completion
    # times (6, 4) and thus a total tardiness of 2 * 4 + 10 * 2 = 28.
    assert_equal(result.get_objective_value(), 28)
    assert_equal(result.get_solve_status(), "Optimal")
