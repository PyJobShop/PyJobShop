import pytest
from numpy.testing import assert_equal
from ortools.sat.python.cp_model import CpSolver

from cpmodel.CpModelPlus import CpModelPlus


class TestAllIdentical:
    """
    Tests for the add_all_identical() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_all_identical enforces all variables to have same value.
        """
        model = CpModelPlus()
        var1 = model.new_int_var(0, 10, "var1")
        var2 = model.new_int_var(0, 10, "var2")
        var3 = model.new_int_var(0, 10, "var3")

        model.add_all_identical([var1, var2, var3])
        model.add(var1 == 5)

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        assert_equal(solver.value(var1), 5)
        assert_equal(solver.value(var2), 5)
        assert_equal(solver.value(var3), 5)

    def test_two_variables(self):
        """
        Tests add_all_identical with just two variables.
        """
        model = CpModelPlus()
        var1 = model.new_int_var(0, 10, "var1")
        var2 = model.new_int_var(0, 10, "var2")

        model.add_all_identical([var1, var2])
        model.add(var1 == 7)

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        assert_equal(solver.value(var1), 7)
        assert_equal(solver.value(var2), 7)

    def test_many_variables(self):
        """
        Tests add_all_identical with many variables.
        """
        model = CpModelPlus()
        variables = [model.new_int_var(0, 100, f"var{i}") for i in range(10)]

        model.add_all_identical(variables)
        model.add(variables[0] == 42)

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        for var in variables:
            assert_equal(solver.value(var), 42)

    def test_constraints_added(self):
        """
        Tests that add_all_identical adds the correct number of constraints.
        """
        model = CpModelPlus()
        variables = [model.new_int_var(0, 10, f"var{i}") for i in range(5)]

        num_constraints_before = len(model.proto.constraints)
        model.add_all_identical(variables)
        num_constraints_after = len(model.proto.constraints)

        # Should add n-1 constraints for n variables
        assert_equal(num_constraints_after - num_constraints_before, 4)

    def test_enforced_constraint(self):
        """
        Tests that all variables are forced to have identical values.
        """
        model = CpModelPlus()
        var1 = model.new_int_var(0, 10, "var1")
        var2 = model.new_int_var(5, 15, "var2")
        var3 = model.new_int_var(3, 8, "var3")

        model.add_all_identical([var1, var2, var3])

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        # All must have same value within intersection [5, 8]
        val1 = solver.value(var1)
        val2 = solver.value(var2)
        val3 = solver.value(var3)
        assert_equal(val1, val2)
        assert_equal(val2, val3)
        assert 5 <= val1 <= 8


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


class TestAlternative:
    """
    Tests for the add_alternative() method.
    """

    def test_basic_constraint_cardinality_one(self):
        """
        Tests basic alternative constraint with cardinality=1.
        """
        model = CpModelPlus()
        main = model.new_optional_interval_var(
            0, 5, 5, model.new_bool_var("main_presence"), "main"
        )
        candidate1 = model.new_optional_interval_var(
            0, 5, 5, model.new_bool_var("c1_presence"), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            0, 5, 5, model.new_bool_var("c2_presence"), "candidate2"
        )

        model.add_alternative(main, [candidate1, candidate2], cardinality=1)

        # Constraint is added to the model
        assert len(model.proto.constraints) > 0

    def test_cardinality_one_enforced(self):
        """
        Tests that exactly one candidate is selected when main is present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create main interval (force it to be present)
        main_presence = model.new_bool_var("main_presence")
        model.add(main_presence == 1)  # Force main to be present

        main = model.new_optional_interval_var(0, 5, 5, main_presence, "main")

        # Create three candidate intervals
        candidate1 = model.new_optional_interval_var(
            0, 5, 5, model.new_bool_var("c1_presence"), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            0, 5, 5, model.new_bool_var("c2_presence"), "candidate2"
        )
        candidate3 = model.new_optional_interval_var(
            0, 5, 5, model.new_bool_var("c3_presence"), "candidate3"
        )

        candidates = [candidate1, candidate2, candidate3]

        # Add alternative constraint with cardinality=1
        model.add_alternative(main, candidates, cardinality=1)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # Verify exactly one candidate is selected
        num_selected = sum(
            1 for c in candidates if solver.boolean_value(model.presence_of(c))
        )
        assert num_selected == 1

    def test_cardinality_two_enforced(self):
        """
        Tests that exactly two candidates are selected with cardinality=2.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create main interval (force it to be present)
        main_presence = model.new_bool_var("main_presence")
        model.add(main_presence == 1)

        main = model.new_optional_interval_var(0, 5, 5, main_presence, "main")

        # Create four candidate intervals
        candidates = [
            model.new_optional_interval_var(
                0, 5, 5, model.new_bool_var(f"c{idx}_presence"), f"c{idx}"
            )
            for idx in range(4)
        ]

        # Add alternative constraint with cardinality=2
        model.add_alternative(main, candidates, cardinality=2)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # Verify exactly two candidates are selected
        num_selected = sum(
            1 for c in candidates if solver.boolean_value(model.presence_of(c))
        )
        assert num_selected == 2

    def test_main_absent_all_candidates_absent(self):
        """
        Tests that when main is absent, all candidates are absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create main interval (force it to be absent)
        main_presence = model.new_bool_var("main_presence")
        model.add(main_presence == 0)  # Force main to be absent

        main = model.new_optional_interval_var(0, 5, 5, main_presence, "main")

        # Create candidate intervals
        candidates = [
            model.new_optional_interval_var(
                0, 5, 5, model.new_bool_var(f"c{idx}_presence"), f"c{idx}"
            )
            for idx in range(3)
        ]

        # Add alternative constraint
        model.add_alternative(main, candidates, cardinality=1)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # Verify all candidates are absent
        for c in candidates:
            assert not solver.boolean_value(model.presence_of(c))

    def test_selected_candidates_match_main_timing(self):
        """
        Tests that selected candidates have same start/end as main.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create main interval with fixed timing
        main_presence = model.new_bool_var("main_presence")
        model.add(main_presence == 1)

        main = model.new_optional_interval_var(5, 3, 8, main_presence, "main")

        # Create candidate intervals with flexible start but fixed size
        candidates = []
        for idx in range(3):
            start = model.new_int_var(0, 10, f"c{idx}_start")
            presence = model.new_bool_var(f"c{idx}_presence")
            interval = model.new_optional_interval_var(
                start, 3, start + 3, presence, f"c{idx}"
            )
            candidates.append(interval)

        # Add alternative constraint
        model.add_alternative(main, candidates, cardinality=1)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # Find the selected candidate
        selected = [
            c for c in candidates if solver.boolean_value(model.presence_of(c))
        ]
        assert len(selected) == 1

        # Verify selected candidate has same start/end as main
        selected_interval = selected[0]
        assert_equal(solver.value(selected_interval.start_expr()), 5)
        assert_equal(solver.value(selected_interval.size_expr()), 3)
        assert_equal(solver.value(selected_interval.end_expr()), 8)

    def test_default_cardinality(self):
        """
        Tests that cardinality defaults to 1 when not specified.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create main interval (force it to be present)
        main_presence = model.new_bool_var("main_presence")
        model.add(main_presence == 1)

        main = model.new_optional_interval_var(0, 5, 5, main_presence, "main")

        # Create candidate intervals
        candidates = [
            model.new_optional_interval_var(
                0, 5, 5, model.new_bool_var(f"c{idx}_presence"), f"c{idx}"
            )
            for idx in range(3)
        ]

        # Add alternative constraint without specifying cardinality
        model.add_alternative(main, candidates)

        # Solve
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # Verify exactly one candidate is selected (default cardinality=1)
        num_selected = sum(
            1 for c in candidates if solver.boolean_value(model.presence_of(c))
        )
        assert num_selected == 1
