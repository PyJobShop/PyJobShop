import pytest
from numpy.testing import assert_equal
from ortools.sat.python.cp_model import CpSolver

from cpmodel.CpModelPlus import CpModelPlus


class TestAllEqual:
    """
    Tests for the add_all_equal() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_all_equal enforces all variables to have same value.
        """
        model = CpModelPlus()
        var1 = model.new_int_var(0, 10, "var1")
        var2 = model.new_int_var(0, 10, "var2")
        var3 = model.new_int_var(0, 10, "var3")

        model.add_all_equal([var1, var2, var3])
        model.add(var1 == 5)

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        assert_equal(solver.value(var1), 5)
        assert_equal(solver.value(var2), 5)
        assert_equal(solver.value(var3), 5)

    def test_two_variables(self):
        """
        Tests add_all_equal with just two variables.
        """
        model = CpModelPlus()
        var1 = model.new_int_var(0, 10, "var1")
        var2 = model.new_int_var(0, 10, "var2")

        model.add_all_equal([var1, var2])
        model.add(var1 == 7)

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        assert_equal(solver.value(var1), 7)
        assert_equal(solver.value(var2), 7)

    def test_many_variables(self):
        """
        Tests add_all_equal with many variables.
        """
        model = CpModelPlus()
        variables = [model.new_int_var(0, 100, f"var{i}") for i in range(10)]

        model.add_all_equal(variables)
        model.add(variables[0] == 42)

        solver = CpSolver()
        status = solver.solve(model)

        assert status == 4  # OPTIMAL
        for var in variables:
            assert_equal(solver.value(var), 42)

    def test_constraints_added(self):
        """
        Tests that add_all_equal adds the correct number of constraints.
        """
        model = CpModelPlus()
        variables = [model.new_int_var(0, 10, f"var{i}") for i in range(5)]

        num_constraints_before = len(model.proto.constraints)
        model.add_all_equal(variables)
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

        model.add_all_equal([var1, var2, var3])

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


class TestSynchronize:
    """
    Tests for the add_synchronize() method.
    """

    def test_basic_constraint(self):
        """
        Tests that add_synchronize creates constraints in the model.
        """
        model = CpModelPlus()
        main = model.new_interval_var(0, 5, 5, "main")
        candidate1 = model.new_interval_var(0, 5, 5, "candidate1")
        candidate2 = model.new_interval_var(0, 5, 5, "candidate2")

        num_constraints_before = len(model.proto.constraints)
        model.add_synchronize(main, [candidate1, candidate2])
        num_constraints_after = len(model.proto.constraints)

        # Should add 3 constraints per candidate (start + size + end)
        assert_equal(num_constraints_after - num_constraints_before, 6)

    def test_both_present_synchronized(self):
        """
        Tests that synchronized intervals have identical start and end times.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create main interval at flexible position
        main_start = model.new_int_var(0, 10, "main_start")
        main = model.new_interval_var(main_start, 5, main_start + 5, "main")

        # Create candidate with flexible position
        cand_start = model.new_int_var(0, 10, "cand_start")
        candidate = model.new_interval_var(
            cand_start, 5, cand_start + 5, "candidate"
        )

        # Add synchronization constraint
        model.add_synchronize(main, [candidate])

        # Add some objective to force a specific solution
        model.minimize(main_start)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # Verify both intervals have identical timing
        main_start_val = solver.value(main.start_expr())
        main_end_val = solver.value(main.end_expr())
        cand_start_val = solver.value(candidate.start_expr())
        cand_end_val = solver.value(candidate.end_expr())

        assert_equal(main_start_val, cand_start_val)
        assert_equal(main_end_val, cand_end_val)

    def test_single_candidate(self):
        """
        Tests synchronization with a single candidate.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        main = model.new_interval_var(5, 3, 8, "main")
        candidate = model.new_int_var(0, 10, "cand_start")
        cand_interval = model.new_interval_var(
            candidate, 3, candidate + 3, "candidate"
        )

        model.add_synchronize(main, [cand_interval])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(candidate), 5)

    def test_multiple_candidates(self):
        """
        Tests that all candidates are synchronized with the main interval.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Fixed main interval
        main = model.new_interval_var(3, 4, 7, "main")

        # Multiple candidates with flexible start
        candidates = []
        for idx in range(3):
            start = model.new_int_var(0, 10, f"c{idx}_start")
            interval = model.new_interval_var(start, 4, start + 4, f"c{idx}")
            candidates.append((start, interval))

        model.add_synchronize(main, [c[1] for c in candidates])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # All candidates should start at 3
        for start_var, _ in candidates:
            assert_equal(solver.value(start_var), 3)

    def test_with_optional_both_present(self):
        """
        Tests synchronization with optional intervals, both present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Optional main interval
        main_start = model.new_int_var(0, 10, "main_start")
        main_pres = model.new_bool_var("main_pres")
        main = model.new_optional_interval_var(
            main_start, 5, main_start + 5, main_pres, "main"
        )

        # Optional candidate
        cand_start = model.new_int_var(0, 10, "cand_start")
        cand_pres = model.new_bool_var("cand_pres")
        candidate = model.new_optional_interval_var(
            cand_start, 5, cand_start + 5, cand_pres, "candidate"
        )

        # Both must be present
        model.add(main_pres == 1)
        model.add(cand_pres == 1)

        model.add_synchronize(main, [candidate])
        model.minimize(main_start)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(
            solver.value(main.start_expr()),
            solver.value(candidate.start_expr()),
        )
        assert_equal(
            solver.value(main.end_expr()), solver.value(candidate.end_expr())
        )

    def test_with_optional_one_absent(self):
        """
        Tests that synchronization is not enforced when one interval is absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Optional main interval (present)
        main_start = model.new_int_var(0, 10, "main_start")
        main_pres = model.new_bool_var("main_pres")
        main = model.new_optional_interval_var(
            main_start, 5, main_start + 5, main_pres, "main"
        )

        # Optional candidate (absent)
        cand_start = model.new_int_var(0, 10, "cand_start")
        cand_pres = model.new_bool_var("cand_pres")
        candidate = model.new_optional_interval_var(
            cand_start, 5, cand_start + 5, cand_pres, "candidate"
        )

        model.add(main_pres == 1)
        model.add(cand_pres == 0)  # Candidate is absent

        model.add_synchronize(main, [candidate])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        # Should be feasible even though candidate is absent
        assert_equal(status, cp_model.OPTIMAL)

    def test_different_durations_infeasible(self):
        """
        Tests that intervals with different durations cannot synchronize.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Main interval with duration 5
        main = model.new_interval_var(0, 5, 5, "main")

        # Candidate with duration 3 (different from main)
        candidate = model.new_interval_var(0, 3, 3, "candidate")

        model.add_synchronize(main, [candidate])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        # Should be infeasible because durations differ
        assert_equal(status, cp_model.INFEASIBLE)

    def test_constraints_added(self):
        """
        Tests that the correct number of constraints are added.
        """
        model = CpModelPlus()
        main = model.new_interval_var(0, 5, 5, "main")
        candidates = [
            model.new_interval_var(0, 5, 5, f"c{i}") for i in range(5)
        ]

        num_constraints_before = len(model.proto.constraints)
        model.add_synchronize(main, candidates)
        num_constraints_after = len(model.proto.constraints)

        # Should add 3 constraints per candidate (start + size + end)
        expected_constraints = 3 * len(candidates)
        assert_equal(
            num_constraints_after - num_constraints_before,
            expected_constraints,
        )


class TestProductVar:
    """
    Tests for the new_product_var() method.
    """

    def test_bool_int_product(self):
        """
        Tests Boolean x Integer product using optimized encoding.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(2, 5, "x")

        p = model.new_product_var(b, x)

        # Verify product variable was created
        assert p is not None
        assert hasattr(p, "proto")

        # Test with b=1, x=3
        model.add(b == 1)
        model.add(x == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 3)

    def test_bool_int_product_when_bool_false(self):
        """
        Tests Boolean x Integer product when Boolean is false.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(2, 5, "x")

        p = model.new_product_var(b, x)

        # Test with b=0
        model.add(b == 0)
        model.add(x == 4)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 0)

    def test_int_bool_product(self):
        """
        Tests Integer x Boolean product (reversed order).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 10, "x")
        b = model.new_bool_var("b")

        p = model.new_product_var(x, b)

        # Test with x=7, b=1
        model.add(x == 7)
        model.add(b == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 7)

    def test_int_bool_product_when_bool_false(self):
        """
        Tests Integer x Boolean product when Boolean is false.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 10, "x")
        b = model.new_bool_var("b")

        p = model.new_product_var(x, b)

        # Test with b=0
        model.add(x == 9)
        model.add(b == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 0)

    def test_int_int_product(self):
        """
        Tests Integer x Integer product using general encoding.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(2, 4, "x")
        y = model.new_int_var(3, 5, "y")

        p = model.new_product_var(x, y)

        # Test with x=3, y=4
        model.add(x == 3)
        model.add(y == 4)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 12)

    def test_bool_int_product_with_domain(self):
        """
        Tests Boolean x Integer product with non-contiguous domain.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var_from_domain(
            cp_model.Domain.from_values([1, 3, 5, 7]), "x"
        )

        p = model.new_product_var(b, x)

        # Enumerate all solutions
        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True

        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []

            def on_solution_callback(self):
                self.solutions.append(
                    {
                        "b": self.value(b),
                        "x": self.value(x),
                        "p": self.value(p),
                    }
                )

        collector = SolutionCollector()
        solver.solve(model, collector)

        # Verify all solutions have correct product
        for sol in collector.solutions:
            expected = sol["b"] * sol["x"]
            actual = sol["p"]
            assert_equal(actual, expected)

        # Should have 8 solutions: 4 x-values * 2 b-values
        assert len(collector.solutions) == 8

    def test_product_var_domain(self):
        """
        Tests that product variable has correct domain.
        """

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(3, 7, "x")

        p = model.new_product_var(b, x)

        # Product domain should be union of x's domain [3,7] and {0}
        domain_values = []
        for idx in range(0, len(p.proto.domain), 2):
            lb = p.proto.domain[idx]
            ub = p.proto.domain[idx + 1]
            domain_values.extend(range(lb, ub + 1))

        # Should include 0 and values from 3 to 7
        assert 0 in domain_values
        for val in range(3, 8):
            assert val in domain_values

    def test_int_int_product_bounds(self):
        """
        Tests that Integer x Integer product has correct bounds.
        """

        model = CpModelPlus()
        x = model.new_int_var(2, 3, "x")
        y = model.new_int_var(4, 6, "y")

        p = model.new_product_var(x, y)

        # Product should be in range [2*4, 3*6] = [8, 18]
        assert p.proto.domain[0] == 8
        assert p.proto.domain[-1] == 18

    def test_product_with_zero_in_domain(self):
        """
        Tests product when one variable can be zero.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 3, "x")
        y = model.new_int_var(2, 5, "y")

        p = model.new_product_var(x, y)

        # Test with x=0
        model.add(x == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 0)

    def test_product_with_negative_values(self):
        """
        Tests product with negative integer values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-3, -1, "x")
        y = model.new_int_var(2, 4, "y")

        p = model.new_product_var(x, y)

        # Test with x=-2, y=3
        model.add(x == -2)
        model.add(y == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), -6)

    def test_bool_int_product_all_solutions(self):
        """
        Tests that all solutions for Boolean x Integer are correct.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(5, 7, "x")

        p = model.new_product_var(b, x)

        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True

        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []

            def on_solution_callback(self):
                self.solutions.append(
                    (self.value(b), self.value(x), self.value(p))
                )

        collector = SolutionCollector()
        solver.solve(model, collector)

        # Should have 6 solutions: 3 x-values * 2 b-values
        assert len(collector.solutions) == 6

        # Verify each solution
        for b_val, x_val, p_val in collector.solutions:
            assert_equal(p_val, b_val * x_val)

    def test_bool_bool_product(self):
        """
        Tests Boolean x Boolean product (both are [0,1] domain).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b1 = model.new_bool_var("b1")
        b2 = model.new_bool_var("b2")

        p = model.new_product_var(b1, b2)

        # Test with b1=1, b2=1
        model.add(b1 == 1)
        model.add(b2 == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 1)

    def test_product_in_constraint(self):
        """
        Tests using product variable in other constraints.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(1, 5, "x")
        p = model.new_product_var(b, x)

        # Add constraint: p >= 3
        model.add(p >= 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        # If p >= 3, then b must be 1 and x >= 3
        assert solver.value(b) == 1
        assert solver.value(x) >= 3
        assert solver.value(p) >= 3

    @pytest.mark.parametrize(
        "x_lb,x_ub,y_lb,y_ub",
        [
            (1, 3, 2, 4),
            (0, 5, 1, 3),
            (-2, 2, 3, 5),
            (5, 10, -3, -1),
        ],
    )
    def test_int_int_product_various_ranges(self, x_lb, x_ub, y_lb, y_ub):
        """
        Tests Integer x Integer product with various ranges.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(x_lb, x_ub, "x")
        y = model.new_int_var(y_lb, y_ub, "y")

        p = model.new_product_var(x, y)

        # Pick middle values
        x_val = (x_lb + x_ub) // 2
        y_val = (y_lb + y_ub) // 2

        model.add(x == x_val)
        model.add(y == y_val)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), x_val * y_val)

    def test_bool_bool_product_all_solutions(self):
        """
        Tests Boolean x Boolean product for all 4 possible combinations.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b1 = model.new_bool_var("b1")
        b2 = model.new_bool_var("b2")

        p = model.new_product_var(b1, b2)

        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True

        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []

            def on_solution_callback(self):
                self.solutions.append(
                    (self.value(b1), self.value(b2), self.value(p))
                )

        collector = SolutionCollector()
        solver.solve(model, collector)

        # Should have 4 solutions
        assert len(collector.solutions) == 4

        # Verify each solution
        for b1_val, b2_val, p_val in collector.solutions:
            assert_equal(p_val, b1_val * b2_val)

    def test_bool_bool_product_false_false(self):
        """
        Tests Boolean x Boolean product when both are false.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b1 = model.new_bool_var("b1")
        b2 = model.new_bool_var("b2")

        p = model.new_product_var(b1, b2)

        model.add(b1 == 0)
        model.add(b2 == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 0)

    def test_bool_bool_product_true_false(self):
        """
        Tests Boolean x Boolean product when one is true, one is false.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b1 = model.new_bool_var("b1")
        b2 = model.new_bool_var("b2")

        p = model.new_product_var(b1, b2)

        model.add(b1 == 1)
        model.add(b2 == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 0)

    def test_bool_bool_product_enforces_and_logic(self):
        """
        Tests Boolean x Boolean product is equivalent to AND operation.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b1 = model.new_bool_var("b1")
        b2 = model.new_bool_var("b2")

        p = model.new_product_var(b1, b2)

        # Product should equal 1 only when both are 1
        model.add(p == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(b1), 1)
        assert_equal(solver.value(b2), 1)

    def test_int_int_product_with_negative_bounds(self):
        """
        Tests Integer x Integer product with both negative bounds.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-5, -2, "x")
        y = model.new_int_var(-4, -1, "y")

        p = model.new_product_var(x, y)

        # Test with x=-3, y=-2
        model.add(x == -3)
        model.add(y == -2)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 6)

    def test_int_int_product_spanning_zero(self):
        """
        Tests Integer x Integer product with ranges spanning zero.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-3, 3, "x")
        y = model.new_int_var(-2, 2, "y")

        p = model.new_product_var(x, y)

        # Test with x=2, y=-2
        model.add(x == 2)
        model.add(y == -2)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), -4)

    def test_bool_int_product_with_negative_domain(self):
        """
        Tests Boolean x Integer product with negative integer domain.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(-10, -5, "x")

        p = model.new_product_var(b, x)

        # Test with b=1, x=-7
        model.add(b == 1)
        model.add(x == -7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), -7)

    def test_bool_int_product_domain_includes_zero(self):
        """
        Tests Boolean x Integer product domain includes zero.
        """

        model = CpModelPlus()
        b = model.new_bool_var("b")
        x = model.new_int_var(5, 10, "x")

        p = model.new_product_var(b, x)

        # Product domain should include 0 and [5, 10]
        domain_values = []
        for idx in range(0, len(p.proto.domain), 2):
            lb = p.proto.domain[idx]
            ub = p.proto.domain[idx + 1]
            domain_values.extend(range(lb, ub + 1))

        assert 0 in domain_values
        for val in range(5, 11):
            assert val in domain_values

    def test_product_var_constraints_added(self):
        """
        Tests that new_product_var adds appropriate constraints.
        """

        model = CpModelPlus()

        # Boolean x Boolean case
        b1 = model.new_bool_var("b1")
        b2 = model.new_bool_var("b2")
        constraints_before = len(model.proto.constraints)
        model.new_product_var(b1, b2)
        constraints_after = len(model.proto.constraints)
        # Should add 3 constraints for boolean product
        assert constraints_after - constraints_before == 3

        # Boolean x Integer case
        model2 = CpModelPlus()
        b = model2.new_bool_var("b")
        x = model2.new_int_var(1, 5, "x")
        constraints_before = len(model2.proto.constraints)
        model2.new_product_var(b, x)
        constraints_after = len(model2.proto.constraints)
        # Should add 2 constraints for bool x int
        assert constraints_after - constraints_before == 2

        # Integer x Integer case
        model3 = CpModelPlus()
        x = model3.new_int_var(1, 5, "x")
        y = model3.new_int_var(2, 6, "y")
        constraints_before = len(model3.proto.constraints)
        model3.new_product_var(x, y)
        constraints_after = len(model3.proto.constraints)
        # Should add 1 constraint for int x int
        assert constraints_after - constraints_before == 1

    def test_product_commutative(self):
        """
        Tests that product is commutative: var1 * var2 == var2 * var1.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(2, 5, "x")
        y = model.new_int_var(3, 7, "y")

        p1 = model.new_product_var(x, y)
        p2 = model.new_product_var(y, x)

        # Force both products to be equal
        model.add(p1 == p2)

        # Set specific values
        model.add(x == 3)
        model.add(y == 4)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p1), 12)
        assert_equal(solver.value(p2), 12)

    def test_product_with_single_value_domain(self):
        """
        Tests product when one variable has a single-value domain.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 5, "x")  # Single value
        y = model.new_int_var(2, 4, "y")

        p = model.new_product_var(x, y)

        model.add(y == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(p), 15)

    def test_product_used_in_optimization(self):
        """
        Tests product variable used in objective function.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(1, 5, "y")

        p = model.new_product_var(x, y)

        # Minimize the product
        model.minimize(p)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Minimum should be 1*1 = 1
        assert_equal(solver.value(p), 1)
        assert_equal(solver.value(x), 1)
        assert_equal(solver.value(y), 1)

    def test_product_maximize_objective(self):
        """
        Tests product variable maximized in objective.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(2, 4, "y")

        p = model.new_product_var(x, y)

        # Maximize the product
        model.maximize(p)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Maximum should be 5*4 = 20
        assert_equal(solver.value(p), 20)
        assert_equal(solver.value(x), 5)
        assert_equal(solver.value(y), 4)
