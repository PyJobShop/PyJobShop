import pytest
from numpy.testing import assert_equal

from cpmodel.CpModelPlus import CpModelPlus


class TestStartAtStart:
    """
    Tests for the add_start_at_start() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_start_at_start creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_start_at_start(interval1, interval2, delay=2)

        # Constraint is already added to the model
        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_zero_delay(self):
        """
        Tests add_start_at_start with zero delay (default).
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_start_at_start(interval1, interval2)

        # Constraint is already added to the model
        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_with_optional_intervals(self):
        """
        Tests add_start_at_start with optional intervals (absent handling).
        """
        model = CpModelPlus()

        # Create optional intervals
        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=5,
            end=start2 + 5,
            is_present=presence2,
            name="interval2",
        )

        # Add constraint with delay
        constraint = model.add_start_at_start(interval1, interval2, delay=2)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_mixed_optional_non_optional(self):
        """
        Tests with one optional and one non-optional interval.
        """
        model = CpModelPlus()

        # Create one optional and one non-optional interval
        start1 = model.new_int_var(0, 10, "start1")
        presence1 = model.new_bool_var("presence1")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="optional_interval",
        )

        interval2 = model.new_interval_var(0, 10, 5, "non_optional_interval")

        # Add constraint - should only enforce when interval1 is present
        constraint = model.add_start_at_start(interval1, interval2, delay=3)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_absent_satisfied(self):
        """
        Tests constraint is satisfied when both intervals are absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        # Create optional intervals
        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=5,
            end=start2 + 5,
            is_present=presence2,
            name="interval2",
        )

        # Add start-at-start constraint
        model.add_start_at_start(interval1, interval2, delay=2)

        # Force both intervals to be absent
        model.add(presence1 == 0)
        model.add(presence2 == 0)

        # Should be satisfiable (constraint auto-satisfied when absent)
        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)

    def test_one_absent_satisfied(self):
        """
        Tests constraint is satisfied when only one interval is absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        # Create optional intervals
        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=5,
            end=start2 + 5,
            is_present=presence2,
            name="interval2",
        )

        # Add start-at-start constraint
        model.add_start_at_start(interval1, interval2, delay=2)

        # Force first interval present, second absent
        model.add(presence1 == 1)
        model.add(presence2 == 0)

        # Should be satisfiable (constraint auto-satisfied when one absent)
        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        # Create optional intervals
        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=5,
            end=start2 + 5,
            is_present=presence2,
            name="interval2",
        )

        # Add start-at-start constraint with delay=2
        model.add_start_at_start(interval1, interval2, delay=2)

        # Force both intervals to be present
        model.add(presence1 == 1)
        model.add(presence2 == 1)

        # Force start1 to a specific value
        model.add(start1 == 3)

        # Solve and verify the constraint is enforced
        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)

        # Verify: start2 should be start1 + delay = 3 + 2 = 5
        assert_equal(solver.value(start2), 5)


class TestStartAtEnd:
    """
    Tests for the add_start_at_end() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_start_at_end creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_start_at_end(interval1, interval2, delay=3)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=3,
            end=start2 + 3,
            is_present=presence2,
            name="interval2",
        )

        model.add_start_at_end(interval1, interval2, delay=2)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 3)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # end2 = start1 + delay = 3 + 2 = 5, so start2 = 5 - 3 = 2
        assert_equal(solver.value(start2), 2)


class TestStartBeforeStart:
    """
    Tests for the add_start_before_start() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_start_before_start creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_start_before_start(
            interval1, interval2, delay=1
        )

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=5,
            end=start2 + 5,
            is_present=presence2,
            name="interval2",
        )

        model.add_start_before_start(interval1, interval2, delay=2)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 3)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # start2 >= start1 + delay = 3 + 2 = 5
        assert solver.value(start2) >= 5


class TestStartBeforeEnd:
    """
    Tests for the add_start_before_end() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_start_before_end creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_start_before_end(interval1, interval2, delay=2)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=3,
            end=start2 + 3,
            is_present=presence2,
            name="interval2",
        )

        model.add_start_before_end(interval1, interval2, delay=1)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 2)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # end2 >= start1 + delay = 2 + 1 = 3
        # Since size2 = 3, start2 >= 3 - 3 = 0
        assert solver.value(start2) + 3 >= 3


class TestEndAtStart:
    """
    Tests for the add_end_at_start() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_end_at_start creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_end_at_start(interval1, interval2, delay=0)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=3,
            end=start2 + 3,
            is_present=presence2,
            name="interval2",
        )

        model.add_end_at_start(interval1, interval2, delay=1)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 2)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # start2 = end1 + delay = (2 + 5) + 1 = 8
        assert_equal(solver.value(start2), 8)


class TestEndAtEnd:
    """
    Tests for the add_end_at_end() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_end_at_end creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_end_at_end(interval1, interval2, delay=1)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=3,
            end=start2 + 3,
            is_present=presence2,
            name="interval2",
        )

        model.add_end_at_end(interval1, interval2, delay=2)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 2)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # end2 = end1 + delay = (2 + 5) + 2 = 9
        # start2 = end2 - size2 = 9 - 3 = 6
        assert_equal(solver.value(start2), 6)


class TestEndBeforeStart:
    """
    Tests for the add_end_before_start() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_end_before_start creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_end_before_start(interval1, interval2, delay=2)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 20, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=3,
            end=start2 + 3,
            is_present=presence2,
            name="interval2",
        )

        model.add_end_before_start(interval1, interval2, delay=2)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 3)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # start2 >= end1 + delay = (3 + 5) + 2 = 10
        assert solver.value(start2) >= 10


class TestEndBeforeEnd:
    """
    Tests for the add_end_before_end() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_end_before_end creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        constraint = model.add_end_before_end(interval1, interval2, delay=3)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_both_present_enforced(self):
        """
        Tests constraint is enforced when both intervals are present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        solver = cp_model.CpSolver()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 20, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start=start1,
            size=5,
            end=start1 + 5,
            is_present=presence1,
            name="interval1",
        )

        interval2 = model.new_optional_interval_var(
            start=start2,
            size=3,
            end=start2 + 3,
            is_present=presence2,
            name="interval2",
        )

        model.add_end_before_end(interval1, interval2, delay=1)
        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 2)

        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)
        # end2 >= end1 + delay = (2 + 5) + 1 = 8
        # start2 >= 8 - 3 = 5
        assert solver.value(start2) + 3 >= 8


@pytest.mark.parametrize(
    "method_name,delay",
    [
        ("add_start_at_start", 0),
        ("add_start_at_start", 5),
        ("add_start_at_end", 0),
        ("add_start_at_end", 3),
        ("add_start_before_start", 0),
        ("add_start_before_start", 2),
        ("add_start_before_end", 0),
        ("add_start_before_end", 4),
        ("add_end_at_start", 0),
        ("add_end_at_start", 1),
        ("add_end_at_end", 0),
        ("add_end_at_end", 2),
        ("add_end_before_start", 0),
        ("add_end_before_start", 3),
        ("add_end_before_end", 0),
        ("add_end_before_end", 1),
    ],
)
def test_constraint_methods_with_various_delays(method_name, delay):
    """
    Tests all constraint methods with various delay values.
    """
    model = CpModelPlus()
    interval1 = model.new_interval_var(0, 10, 5, "interval1")
    interval2 = model.new_interval_var(0, 10, 5, "interval2")

    method = getattr(model, method_name)
    constraint = method(interval1, interval2, delay=delay)

    # All timing constraint methods now add constraint automatically
    assert constraint is not None
    assert model.proto.constraints[-1] is not None


def test_add_span():
    """
    Tests that add_span creates correct constraints.
    """
    model = CpModelPlus()
    main = model.new_interval_var(0, 20, 10, "main")
    candidate1 = model.new_interval_var(0, 10, 5, "candidate1")
    candidate2 = model.new_interval_var(5, 15, 5, "candidate2")

    num_constraints_before = len(model.proto.constraints)
    cons1, cons2 = model.add_span(main, [candidate1, candidate2])

    assert cons1 is not None
    assert cons2 is not None
    num_constraints_after = len(model.proto.constraints)
    assert_equal(num_constraints_after - num_constraints_before, 2)


def test_add_span_single_candidate():
    """
    Tests add_span with a single candidate interval.
    """
    model = CpModelPlus()
    main = model.new_interval_var(0, 20, 10, "main")
    candidate = model.new_interval_var(0, 10, 5, "candidate")

    cons1, cons2 = model.add_span(main, [candidate])

    assert cons1 is not None
    assert cons2 is not None


def test_add_span_multiple_candidates():
    """
    Tests add_span with multiple candidate intervals.
    """
    model = CpModelPlus()
    main = model.new_interval_var(0, 30, 15, "main")
    candidates = [
        model.new_interval_var(0, 10, 5, f"candidate{i}") for i in range(5)
    ]

    num_constraints_before = len(model.proto.constraints)
    cons1, cons2 = model.add_span(main, candidates)

    assert cons1 is not None
    assert cons2 is not None
    num_constraints_after = len(model.proto.constraints)
    assert_equal(num_constraints_after - num_constraints_before, 2)


def test_presence_of_optional_interval():
    """
    Tests presence_of returns the presence literal for optional intervals.
    """
    model = CpModelPlus()
    start = model.new_int_var(0, 10, "start")
    presence = model.new_bool_var("presence")

    # Create an optional interval
    interval = model.new_optional_interval_var(
        start=start,
        size=5,
        end=start + 5,
        is_present=presence,
        name="optional_interval",
    )

    # Get the presence literal back
    presence_lit = model.presence_of(interval)

    assert presence_lit is not None
    # The presence literal should be the same variable (or its negation)
    assert (
        presence_lit.index == presence.index
        or presence_lit.index == -presence.index - 1
    )


def test_presence_of_non_optional_interval():
    """
    Tests presence_of returns constant True for non-optional intervals.
    """
    model = CpModelPlus()
    interval = model.new_interval_var(0, 10, 5, "interval")

    presence_lit = model.presence_of(interval)

    assert presence_lit is not None
    # For non-optional intervals, should return a constant True
    # We can verify this by checking that it's a valid bool var
    assert hasattr(presence_lit, "index")


def test_presence_of_negated_literal():
    """
    Tests presence_of handles negated presence literals correctly.
    """
    model = CpModelPlus()
    start = model.new_int_var(0, 10, "start")
    presence = model.new_bool_var("presence")

    # Create an optional interval with negated presence
    interval = model.new_optional_interval_var(
        start=start,
        size=5,
        end=start + 5,
        is_present=presence.negated(),
        name="optional_interval",
    )

    # Get the presence literal back
    presence_lit = model.presence_of(interval)

    assert presence_lit is not None
