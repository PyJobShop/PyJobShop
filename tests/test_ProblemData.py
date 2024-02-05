import random
from typing import Optional

import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_equal, assert_raises

from pyjobshop.Model import Model
from pyjobshop.ProblemData import (
    AssignmentPrecedence,
    Job,
    Machine,
    Objective,
    Operation,
    ProblemData,
    TimingPrecedence,
)


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

    assert_equal(machine.downtimes, ())
    assert_equal(machine.allow_overlap, False)
    assert_equal(machine.name, "")

    # Now test with some values.
    machine = Machine([(1, 2)], True, name="TestMachine")

    assert_equal(machine.downtimes, [(1, 2)])
    assert_equal(machine.allow_overlap, True)
    assert_equal(machine.name, "TestMachine")


@pytest.mark.parametrize(
    "downtimes",
    [
        [(1, 0)],  # start > end
    ],
)
def test_machine_attributes_raises_invalid_parameters(
    downtimes: list[tuple[int, int]],
):
    """
    Tests that a ValueError is raised when invalid parameters are passed to
    Machine.
    """
    with assert_raises(ValueError):
        Machine(downtimes)


def test_operation_attributes():
    """
    Tests that the attributes of the Operation class are set correctly.
    """
    operation = Operation(1, 2, 3, 4, False, True, name="TestOperation")

    assert_equal(operation.earliest_start, 1)
    assert_equal(operation.latest_start, 2)
    assert_equal(operation.earliest_end, 3)
    assert_equal(operation.latest_end, 4)
    assert_equal(operation.fixed_duration, False)
    assert_equal(operation.optional, True)
    assert_equal(operation.name, "TestOperation")

    # Also test that default values are set correctly.
    operation = Operation()

    assert_equal(operation.earliest_start, None)
    assert_equal(operation.latest_start, None)
    assert_equal(operation.earliest_end, None)
    assert_equal(operation.latest_end, None)
    assert_equal(operation.fixed_duration, True)
    assert_equal(operation.optional, False)
    assert_equal(operation.name, "")


@pytest.mark.parametrize(
    "earliest_start, latest_start, earliest_end, latest_end",
    [
        (1, 0, None, None),  # earliest_start > latest_start
        (None, None, 1, 0),  # earliest_end > latest_end
    ],
)
def test_operation_attributes_raises_invalid_parameters(
    earliest_start: Optional[int],
    latest_start: Optional[int],
    earliest_end: Optional[int],
    latest_end: Optional[int],
):
    """
    Tests that an error is raised when invalid parameters are passed to the
    Operation class.
    """
    with assert_raises(ValueError):
        Operation(earliest_start, latest_start, earliest_end, latest_end)


def test_problem_data_input_parameter_attributes():
    """
    Tests that the input parameters of the ProblemData class are set correctly
    as attributes.
    """
    jobs = [Job() for _ in range(5)]
    machines = [Machine() for _ in range(5)]
    operations = [Operation() for _ in range(5)]
    job2ops = [[0], [1], [2], [3], [4]]
    processing_times = {(i, j): 1 for i in range(5) for j in range(5)}
    timing_precedences = {
        key: [TimingPrecedence.END_BEFORE_START]
        for key in ((0, 1), (2, 3), (4, 5))
    }
    assignment_precedences = {(0, 1): [AssignmentPrecedence.PREVIOUS]}
    setup_times = np.ones((5, 5, 5), dtype=int)
    process_plans = [[[0, 1, 2, 3, 4]]]
    planning_horizon = 100
    objective = Objective.TOTAL_COMPLETION_TIME

    data = ProblemData(
        jobs,
        machines,
        operations,
        job2ops,
        processing_times,
        timing_precedences,
        assignment_precedences,
        setup_times,
        process_plans,
        planning_horizon,
        objective,
    )

    assert_equal(data.jobs, jobs)
    assert_equal(data.machines, machines)
    assert_equal(data.operations, operations)
    assert_equal(data.job2ops, job2ops)
    assert_equal(data.processing_times, processing_times)
    assert_equal(data.timing_precedences, timing_precedences)
    assert_equal(data.assignment_precedences, assignment_precedences)
    assert_allclose(data.setup_times, setup_times)
    assert_equal(data.process_plans, process_plans)
    assert_equal(data.planning_horizon, planning_horizon)
    assert_equal(data.objective, objective)


def test_problem_data_non_input_parameter_attributes():
    """
    Tests that attributes that are not input parameters of the ProblemData
    class are set correctly.
    """
    jobs = [Job() for _ in range(1)]
    machines = [Machine() for _ in range(3)]
    operations = [Operation() for _ in range(3)]
    job2ops = [[0, 1, 2]]
    processing_times = {(1, 2): 1, (2, 1): 1, (0, 1): 1, (2, 0): 1}

    data = ProblemData(
        jobs, machines, operations, job2ops, processing_times, {}
    )

    # The lists in machine2ops and op2machines are sorted.
    machine2ops = [[1], [2], [0, 1]]
    op2machines = [[2], [0, 2], [1]]
    assert_equal(data.machine2ops, machine2ops)
    assert_equal(data.op2machines, op2machines)

    assert_equal(data.num_jobs, 1)
    assert_equal(data.num_machines, 3)
    assert_equal(data.num_operations, 3)


def test_problem_data_default_values():
    """
    Tests that the default values of the ProblemData class are set correctly.
    """
    jobs = [Job() for _ in range(1)]
    machines = [Machine() for _ in range(1)]
    operations = [Operation() for _ in range(1)]
    job2ops = [[0]]
    timing_precedences = {(0, 1): [TimingPrecedence.END_BEFORE_START]}
    processing_times = {(0, 0): 1}
    data = ProblemData(
        jobs,
        machines,
        operations,
        job2ops,
        processing_times,
        timing_precedences,
    )

    assert_equal(data.assignment_precedences, {})
    assert_allclose(data.setup_times, np.zeros((1, 1, 1), dtype=int))
    assert_equal(data.process_plans, [])
    assert_equal(data.planning_horizon, None)
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
            [Operation()],
            [[0]],
            processing_times,
            {},
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
            [Operation()],
            [[0]],
            {},
            {},
            objective=objective,
        )


# --- Tests that involve checking solver correctness of problem data. ---


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


def test_machine_downtime_single_interval():
    """
    Tests that operations are scheduled around machine downtimes.
    """
    model = Model()
    job = model.add_job()
    machine = model.add_machine([(0, 2)])
    operation = model.add_operation()

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=2)

    result = model.solve()

    # Machine is down between (0, 2) onwards, so the makespan is be 4.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 4)


def test_restrictive_machine_downtime_and_horizon():
    """
    Tests that a restrictive machine downtime and planning horizon results
    in an infeasible model.
    """
    model = Model()
    job = model.add_job()
    machine = model.add_machine([(0, 2)])
    operation = model.add_operation()

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=2)
    model.set_planning_horizon(3)

    result = model.solve()

    # Machine is down between (0, 2) onwards, but the planning horizon is
    # only 3, so the operation cannot be scheduled.
    assert_equal(result.get_solve_status(), "Infeasible")


def test_machine_allow_overlap():
    """
    Tests that allowing overlap results in a shorter makespan.
    """
    model = Model()
    job = model.add_job()
    machine = model.add_machine()  # no overlap
    operations = [model.add_operation(), model.add_operation()]

    model.assign_job_operations(job, operations)
    for operation in operations:
        model.add_processing_time(machine, operation, duration=2)

    result = model.solve()

    # No overlap, so we schedule the two operations consecutively with
    # final makespan of four.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 4)

    # Let's now allow for overlap.
    model = Model()
    job = model.add_job()
    machine = model.add_machine(allow_overlap=True)
    operations = [model.add_operation(), model.add_operation()]

    model.assign_job_operations(job, operations)
    for operation in operations:
        model.add_processing_time(machine, operation, duration=2)

    result = model.solve()

    # With overlap we can schedule both operations simultaneously on the
    # machine, resulting in a makespan of two.
    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 2)


def test_operation_earliest_start():
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


def test_operation_latest_start():
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


def test_operation_fixed_start():
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


def test_operation_earliest_end():
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


def test_operation_latest_end():
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


def test_operation_fixed_end():
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


def test_operation_no_fixed_duration_blocking():
    """
    Tests that operations with no fixed duration are scheduled correctly
    in a blocking environment.
    """
    pass


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


def test_tight_planning_horizon_results_in_infeasiblity():
    """
    Tests that a tight planning horizon results in an infeasible instance.
    """
    model = Model()

    job = model.add_job()
    machine = model.add_machine()
    operation = model.add_operation()

    model.assign_job_operations(job, [operation])
    model.add_processing_time(machine, operation, duration=2)
    model.set_planning_horizon(1)

    result = model.solve()

    # Processing time is 2, but planning horizon is 1, so this is infeasible.
    assert_equal(result.get_solve_status(), "Infeasible")


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


def test_tardy_jobs():
    """
    Tests that the (number of) tardy jobs objective is correctly optimized.
    """
    model = Model()

    machine = model.add_machine()

    for idx in range(3):
        job = model.add_job(due_date=idx + 1)
        operation = model.add_operation()

        model.assign_job_operations(job, [operation])
        model.add_processing_time(machine, operation, duration=3)

    model.set_objective(Objective.TARDY_JOBS)

    result = model.solve()

    # Only the last job/operation can be scheduled on time. The other two
    # are tardy.
    assert_equal(result.get_objective_value(), 2)
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
    """
    Tests that the weights are taken into account when using the total
    completion time objective function.
    """
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
    """
    Tests that the total tardiness objective function is correctly optimized.
    """
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


# --- Small classical examples. ---
def test_flowshop():
    """
    Blocking flowshop example.
    """
    random.seed(42)

    NUM_JOBS = 5
    NUM_MACHINES = 5

    model = Model()
    jobs = [model.add_job() for _ in range(NUM_JOBS)]
    machines = [model.add_machine() for _ in range(NUM_MACHINES)]

    for job in jobs:
        # One operation per job and machine pair.
        operations = [model.add_operation() for _ in range(NUM_MACHINES)]
        model.assign_job_operations(job, operations)

        for machine, op in zip(machines, operations):
            model.add_processing_time(machine, op, random.randint(1, 10))

        # Create precedence constraints between operations.
        for idx in range(len(operations) - 1):
            model.add_timing_precedence(
                operations[idx],
                operations[idx + 1],
                TimingPrecedence.END_AT_START,
            )

    result = model.solve()

    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 51)


def test_jobshop():
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

    for job_idx, tasks in enumerate(jobs_data):
        operations = [model.add_operation() for _ in tasks]
        model.assign_job_operations(jobs[job_idx], operations)

        # Add processing times.
        for idx, (machine_idx, duration) in enumerate(tasks):
            model.add_processing_time(
                machines[machine_idx], operations[idx], duration
            )

        # Impose linear routing precedence constraints.
        for op_idx in range(1, len(operations)):
            op1, op2 = operations[op_idx - 1], operations[op_idx]
            model.add_timing_precedence(
                op1, op2, TimingPrecedence.END_BEFORE_START
            )

    result = model.solve()

    assert_equal(result.get_solve_status(), "Optimal")
    assert_equal(result.get_objective_value(), 20)
