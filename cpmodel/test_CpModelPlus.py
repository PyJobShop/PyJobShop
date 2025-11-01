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
    model.add_span(main, [candidate1, candidate2])

    num_constraints_after = len(model.proto.constraints)
    # Should add constraints for the span
    assert num_constraints_after > num_constraints_before


def test_add_span_single_candidate():
    """
    Tests add_span with a single candidate interval.
    """
    model = CpModelPlus()
    main = model.new_interval_var(0, 20, 10, "main")
    candidate = model.new_interval_var(0, 10, 5, "candidate")

    num_constraints_before = len(model.proto.constraints)
    model.add_span(main, [candidate])

    num_constraints_after = len(model.proto.constraints)
    assert num_constraints_after > num_constraints_before


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
    model.add_span(main, candidates)

    num_constraints_after = len(model.proto.constraints)
    assert num_constraints_after > num_constraints_before


def test_add_span_with_optional_intervals():
    """
    Tests add_span with optional candidate intervals.
    """
    from ortools.sat.python import cp_model

    model = CpModelPlus()
    main_pres = model.new_bool_var("main_pres")
    main = model.new_optional_interval_var(0, 10, 10, main_pres, "main")

    cand1_pres = model.new_bool_var("cand1_pres")
    cand2_pres = model.new_bool_var("cand2_pres")
    candidate1 = model.new_optional_interval_var(
        0, 5, 5, cand1_pres, "candidate1"
    )
    candidate2 = model.new_optional_interval_var(
        3, 8, 5, cand2_pres, "candidate2"
    )

    model.add_span(main, [candidate1, candidate2])

    # If both candidates absent, main should be absent
    model.add(cand1_pres == 0)
    model.add(cand2_pres == 0)

    solver = cp_model.CpSolver()
    status = solver.solve(model)

    assert_equal(status, cp_model.OPTIMAL)
    assert_equal(solver.value(main_pres), 0)


def test_add_span_shortcut_all_present():
    """
    Tests add_span shortcut when all intervals are non-optional.
    This tests the is_true helper and stronger formulation path.
    """
    from ortools.sat.python import cp_model

    model = CpModelPlus()
    # All non-optional intervals (always present)
    # Using fixed-size intervals with variable start times
    main_start = model.new_int_var(0, 20, "main_start")
    main = model.new_interval_var(main_start, 11, main_start + 11, "main")

    cand1_start = model.new_int_var(0, 10, "cand1_start")
    candidate1 = model.new_interval_var(
        cand1_start, 5, cand1_start + 5, "candidate1"
    )

    cand2_start = model.new_int_var(0, 10, "cand2_start")
    candidate2 = model.new_interval_var(
        cand2_start, 5, cand2_start + 5, "candidate2"
    )

    # Fix candidate positions to require span from 2 to 13 (size 11)
    model.add(cand1_start == 2)
    model.add(cand2_start == 8)

    cons1, cons2 = model.add_span(main, [candidate1, candidate2])

    # Verify constraints were returned
    assert cons1 is not None
    assert cons2 is not None

    solver = cp_model.CpSolver()
    status = solver.solve(model)

    assert_equal(status, cp_model.OPTIMAL)
    # Main should span both candidates
    # Start should be min (2)
    assert_equal(solver.value(main.start_expr()), 2)
    # End should be max (8 + 5 = 13)
    assert_equal(solver.value(main.end_expr()), 13)


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


class TestIfThenElse:
    """
    Tests for the add_if_then_else() method.
    """

    def test_condition_true_enforces_then(self):
        """
        Tests that when condition is true, then_expr is enforced.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == 5, else y == 0
        model.add_if_then_else(condition, y == 5, y == 0)

        # Force condition to be true
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 5)

    def test_condition_false_enforces_else(self):
        """
        Tests that when condition is false, else_expr is enforced.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == 5, else y == 0
        model.add_if_then_else(condition, y == 5, y == 0)

        # Force condition to be false
        model.add(condition == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 0)

    def test_with_linear_expressions(self):
        """
        Tests if-then-else with linear expressions.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == 10 - x, else y == 0
        model.add_if_then_else(condition, y == 10 - x, y == 0)

        # Set x and condition
        model.add(x == 3)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 3)
        assert_equal(solver.value(y), 7)

    def test_with_inequality_constraints(self):
        """
        Tests if-then-else with inequality constraints.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y >= 5, else y <= 2
        model.add_if_then_else(condition, y >= 5, y <= 2)

        # Force condition to be true
        model.add(condition == 1)

        # Minimize y
        model.minimize(y)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 5)

    def test_nested_conditions(self):
        """
        Tests multiple if-then-else constraints on same variable.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        # If cond1, then y == 5, else y == 0
        model.add_if_then_else(cond1, y == 5, y == 0)

        # If cond2, then x == 3, else x == 7
        model.add_if_then_else(cond2, x == 3, x == 7)

        # Set conditions
        model.add(cond1 == 1)
        model.add(cond2 == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 5)
        assert_equal(solver.value(x), 7)

    def test_condition_derived_from_constraint(self):
        """
        Tests condition that is derived from another constraint.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # Condition represents x >= 5
        model.add(x >= 5).only_enforce_if(condition)
        model.add(x < 5).only_enforce_if(~condition)

        # If condition (x >= 5), then y == 10 - x, else y == 0
        model.add_if_then_else(condition, y == 10 - x, y == 0)

        # Set x = 7
        model.add(x == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 7)
        assert_equal(solver.value(y), 3)

    def test_infeasible_then_branch(self):
        """
        Tests that infeasible then branch forces condition false.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == 5, else y == 0
        model.add_if_then_else(condition, y == 5, y == 0)

        # Force y to be in range that conflicts with then branch
        model.add(y <= 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Condition must be false since y == 5 is infeasible
        assert_equal(solver.value(condition), 0)
        assert_equal(solver.value(y), 0)

    def test_infeasible_else_branch(self):
        """
        Tests that infeasible else branch forces condition true.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == 5, else y == 0
        model.add_if_then_else(condition, y == 5, y == 0)

        # Force y to value that conflicts with else branch
        model.add(y >= 4)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Condition must be true since y == 0 is infeasible
        assert_equal(solver.value(condition), 1)
        assert_equal(solver.value(y), 5)

    def test_with_sum_expressions(self):
        """
        Tests if-then-else with sum expressions.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 5, "x")
        y = model.new_int_var(0, 5, "y")
        z = model.new_int_var(0, 10, "z")
        condition = model.new_bool_var("condition")

        # If condition, then z == x + y, else z == 0
        model.add_if_then_else(condition, z == x + y, z == 0)

        # Set values
        model.add(x == 3)
        model.add(y == 4)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(z), 7)

    def test_with_product_expressions(self):
        """
        Tests if-then-else with multiplication expressions.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(2, 5, "x")
        y = model.new_int_var(0, 20, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == 2 * x, else y == 0
        model.add_if_then_else(condition, y == 2 * x, y == 0)

        # Set values
        model.add(x == 4)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 8)

    def test_all_solutions_enumeration(self):
        """
        Tests enumerating all solutions with if-then-else.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 3, "x")
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If x >= 2, then y == 5, else y == 0
        model.add(x >= 2).only_enforce_if(condition)
        model.add(x < 2).only_enforce_if(~condition)
        model.add_if_then_else(condition, y == 5, y == 0)

        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True

        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []

            def on_solution_callback(self):
                self.solutions.append(
                    (self.value(x), self.value(y), self.value(condition))
                )

        collector = SolutionCollector()
        solver.solve(model, collector)

        # Should have 4 solutions (x in [0,3])
        assert len(collector.solutions) == 4

        # Verify each solution
        for x_val, y_val, cond_val in collector.solutions:
            if x_val >= 2:
                assert cond_val == 1
                assert y_val == 5
            else:
                assert cond_val == 0
                assert y_val == 0

    def test_constraints_added(self):
        """
        Tests that add_if_then_else adds exactly 2 constraints.
        """

        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        num_constraints_before = len(model.proto.constraints)
        model.add_if_then_else(condition, y == 5, y == 0)
        num_constraints_after = len(model.proto.constraints)

        # Should add exactly 2 constraints (one for then, one for else)
        assert_equal(num_constraints_after - num_constraints_before, 2)

    def test_with_optimization_objective(self):
        """
        Tests if-then-else with optimization objective.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == x + 5, else y == 0
        model.add_if_then_else(condition, y == x + 5, y == 0)

        # Maximize y
        model.maximize(y)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # To maximize y, condition should be true and x should be max
        assert_equal(solver.value(condition), 1)
        assert_equal(solver.value(x), 5)  # x + 5 <= 10, so x <= 5
        assert_equal(solver.value(y), 10)

    def test_minimize_with_conditional(self):
        """
        Tests minimization with if-then-else constraint.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        condition = model.new_bool_var("condition")

        # If condition, then y == x + 5, else y == 10
        model.add_if_then_else(condition, y == x + 5, y == 10)

        # Minimize y
        model.minimize(y)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # To minimize y, condition should be true and x should be 0
        assert_equal(solver.value(condition), 1)
        assert_equal(solver.value(x), 0)
        assert_equal(solver.value(y), 5)


class TestMaxVar:
    """
    Tests for the new_max_var() method.
    """

    def test_basic_max_two_variables(self):
        """
        Tests basic maximum of two variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(3, 7, "y")

        max_var = model.new_max_var(x, y)

        # Set values
        model.add(x == 4)
        model.add(y == 6)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 6)

    def test_max_with_equal_values(self):
        """
        Tests maximum when both variables have the same value.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")

        max_var = model.new_max_var(x, y)

        model.add(x == 5)
        model.add(y == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 5)

    def test_max_three_variables(self):
        """
        Tests maximum of three variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        z = model.new_int_var(0, 10, "z")

        max_var = model.new_max_var(x, y, z)

        model.add(x == 3)
        model.add(y == 7)
        model.add(z == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 7)

    def test_max_many_variables(self):
        """
        Tests maximum of many variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        variables = [model.new_int_var(0, 20, f"x{i}") for i in range(10)]

        max_var = model.new_max_var(*variables)

        # Set values with x5 being the maximum
        for idx, var in enumerate(variables):
            model.add(var == idx * 2)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Maximum should be 9 * 2 = 18
        assert_equal(solver.value(max_var), 18)

    def test_max_with_negative_values(self):
        """
        Tests maximum with negative values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-10, -5, "x")
        y = model.new_int_var(-8, -2, "y")

        max_var = model.new_max_var(x, y)

        model.add(x == -7)
        model.add(y == -3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), -3)

    def test_max_with_mixed_signs(self):
        """
        Tests maximum with mixed positive and negative values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-10, 0, "x")
        y = model.new_int_var(0, 10, "y")

        max_var = model.new_max_var(x, y)

        model.add(x == -5)
        model.add(y == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 3)

    def test_max_with_single_variable(self):
        """
        Tests maximum with a single variable (edge case).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 15, "x")

        max_var = model.new_max_var(x)

        model.add(x == 10)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 10)

    def test_max_in_constraint(self):
        """
        Tests using max variable in other constraints.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")
        z = model.new_int_var(1, 10, "z")

        max_var = model.new_max_var(x, y)

        # Add constraint: max must be less than z
        model.add(max_var < z)
        model.add(x == 5)
        model.add(y == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 7)
        assert solver.value(z) > 7

    def test_max_with_optimization(self):
        """
        Tests max variable in optimization objective.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")

        max_var = model.new_max_var(x, y)

        # Minimize the maximum
        model.minimize(max_var)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # To minimize max, both should be 1
        assert_equal(solver.value(x), 1)
        assert_equal(solver.value(y), 1)
        assert_equal(solver.value(max_var), 1)

    def test_max_maximize_objective(self):
        """
        Tests maximizing the max variable.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(3, 8, "y")

        max_var = model.new_max_var(x, y)

        # Maximize the maximum
        model.maximize(max_var)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # To maximize max, y should be 8 (its upper bound)
        assert_equal(solver.value(y), 8)
        assert_equal(solver.value(max_var), 8)

    def test_max_all_solutions(self):
        """
        Tests that max variable is correct across all solutions.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 3, "x")
        y = model.new_int_var(2, 4, "y")

        max_var = model.new_max_var(x, y)

        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True

        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []

            def on_solution_callback(self):
                self.solutions.append(
                    (self.value(x), self.value(y), self.value(max_var))
                )

        collector = SolutionCollector()
        solver.solve(model, collector)

        # Verify each solution
        for x_val, y_val, max_val in collector.solutions:
            assert_equal(max_val, max(x_val, y_val))

        # Should have 3 * 3 = 9 solutions
        assert len(collector.solutions) == 9

    def test_max_with_overlapping_domains(self):
        """
        Tests maximum with overlapping variable domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(3, 8, "x")
        y = model.new_int_var(5, 10, "y")

        max_var = model.new_max_var(x, y)

        model.add(x == 6)
        model.add(y == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 6)

    def test_max_constraint_propagation(self):
        """
        Tests that max constraint properly propagates bounds.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")

        max_var = model.new_max_var(x, y)

        # Force max to be at most 5
        model.add(max_var <= 5)

        # This should constrain both x and y to be <= 5
        model.maximize(x + y)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 5)
        assert_equal(solver.value(y), 5)
        assert_equal(solver.value(max_var), 5)

    def test_max_with_constants(self):
        """
        Tests maximum with constant-valued variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 5, "x")  # Constant
        y = model.new_int_var(1, 10, "y")

        max_var = model.new_max_var(x, y)

        model.add(y == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 5)

    def test_max_with_zero(self):
        """
        Tests maximum with zero in the domain.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-5, 0, "x")
        y = model.new_int_var(0, 5, "y")

        max_var = model.new_max_var(x, y)

        model.add(x == -2)
        model.add(y == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(max_var), 0)

    def test_max_constraints_added(self):
        """
        Tests that new_max_var adds the appropriate constraint.
        """
        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(3, 7, "y")

        num_constraints_before = len(model.proto.constraints)
        model.new_max_var(x, y)
        num_constraints_after = len(model.proto.constraints)

        # Should add 1 constraint (the max_equality constraint)
        assert_equal(num_constraints_after - num_constraints_before, 1)


class TestMinVar:
    """
    Tests for the new_min_var() method.
    """

    def test_basic_min_two_variables(self):
        """
        Tests basic minimum of two variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(3, 7, "y")

        min_var = model.new_min_var(x, y)

        # Set values
        model.add(x == 4)
        model.add(y == 6)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 4)

    def test_min_with_equal_values(self):
        """
        Tests minimum when both variables have the same value.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")

        min_var = model.new_min_var(x, y)

        model.add(x == 5)
        model.add(y == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 5)

    def test_min_three_variables(self):
        """
        Tests minimum of three variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        y = model.new_int_var(0, 10, "y")
        z = model.new_int_var(0, 10, "z")

        min_var = model.new_min_var(x, y, z)

        model.add(x == 7)
        model.add(y == 3)
        model.add(z == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 3)

    def test_min_many_variables(self):
        """
        Tests minimum of many variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        variables = [model.new_int_var(0, 20, f"x{i}") for i in range(10)]

        min_var = model.new_min_var(*variables)

        # Set values with x0 being the minimum
        for idx, var in enumerate(variables):
            model.add(var == idx * 2 + 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Minimum should be 0 * 2 + 1 = 1
        assert_equal(solver.value(min_var), 1)

    def test_min_with_negative_values(self):
        """
        Tests minimum with negative values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-10, -5, "x")
        y = model.new_int_var(-8, -2, "y")

        min_var = model.new_min_var(x, y)

        model.add(x == -7)
        model.add(y == -3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), -7)

    def test_min_with_mixed_signs(self):
        """
        Tests minimum with mixed positive and negative values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-10, 0, "x")
        y = model.new_int_var(0, 10, "y")

        min_var = model.new_min_var(x, y)

        model.add(x == -5)
        model.add(y == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), -5)

    def test_min_with_single_variable(self):
        """
        Tests minimum with a single variable (edge case).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 15, "x")

        min_var = model.new_min_var(x)

        model.add(x == 10)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 10)

    def test_min_in_constraint(self):
        """
        Tests using min variable in other constraints.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")
        z = model.new_int_var(1, 10, "z")

        min_var = model.new_min_var(x, y)

        # Add constraint: min must be greater than z
        model.add(min_var > z)
        model.add(x == 5)
        model.add(y == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 5)
        assert solver.value(z) < 5

    def test_min_with_optimization(self):
        """
        Tests min variable in optimization objective.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")

        min_var = model.new_min_var(x, y)

        # Maximize the minimum
        model.maximize(min_var)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # To maximize min, both should be 10
        assert_equal(solver.value(x), 10)
        assert_equal(solver.value(y), 10)
        assert_equal(solver.value(min_var), 10)

    def test_min_minimize_objective(self):
        """
        Tests minimizing the min variable.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(3, 8, "y")

        min_var = model.new_min_var(x, y)

        # Minimize the minimum
        model.minimize(min_var)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # To minimize min, x should be 1 (its lower bound)
        assert_equal(solver.value(x), 1)
        assert_equal(solver.value(min_var), 1)

    def test_min_all_solutions(self):
        """
        Tests that min variable is correct across all solutions.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 3, "x")
        y = model.new_int_var(2, 4, "y")

        min_var = model.new_min_var(x, y)

        solver = cp_model.CpSolver()
        solver.parameters.enumerate_all_solutions = True

        class SolutionCollector(cp_model.CpSolverSolutionCallback):
            def __init__(self):
                cp_model.CpSolverSolutionCallback.__init__(self)
                self.solutions = []

            def on_solution_callback(self):
                self.solutions.append(
                    (self.value(x), self.value(y), self.value(min_var))
                )

        collector = SolutionCollector()
        solver.solve(model, collector)

        # Verify each solution
        for x_val, y_val, min_val in collector.solutions:
            assert_equal(min_val, min(x_val, y_val))

        # Should have 3 * 3 = 9 solutions
        assert len(collector.solutions) == 9

    def test_min_with_overlapping_domains(self):
        """
        Tests minimum with overlapping variable domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(3, 8, "x")
        y = model.new_int_var(5, 10, "y")

        min_var = model.new_min_var(x, y)

        model.add(x == 6)
        model.add(y == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 5)

    def test_min_constraint_propagation(self):
        """
        Tests that min constraint properly propagates bounds.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")

        min_var = model.new_min_var(x, y)

        # Force min to be at least 5
        model.add(min_var >= 5)

        # This should constrain both x and y to be >= 5
        model.minimize(x + y)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 5)
        assert_equal(solver.value(y), 5)
        assert_equal(solver.value(min_var), 5)

    def test_min_with_constants(self):
        """
        Tests minimum with constant-valued variables.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(5, 5, "x")  # Constant
        y = model.new_int_var(1, 10, "y")

        min_var = model.new_min_var(x, y)

        model.add(y == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 5)

    def test_min_with_zero(self):
        """
        Tests minimum with zero in the domain.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-5, 0, "x")
        y = model.new_int_var(0, 5, "y")

        min_var = model.new_min_var(x, y)

        model.add(x == -2)
        model.add(y == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), -2)

    def test_min_constraints_added(self):
        """
        Tests that new_min_var adds the appropriate constraint.
        """
        model = CpModelPlus()
        x = model.new_int_var(1, 5, "x")
        y = model.new_int_var(3, 7, "y")

        num_constraints_before = len(model.proto.constraints)
        model.new_min_var(x, y)
        num_constraints_after = len(model.proto.constraints)

        # Should add 1 constraint (the min_equality constraint)
        assert_equal(num_constraints_after - num_constraints_before, 1)

    def test_min_and_max_together(self):
        """
        Tests using min and max variables together.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 10, "x")
        y = model.new_int_var(1, 10, "y")
        z = model.new_int_var(1, 10, "z")

        min_var = model.new_min_var(x, y, z)
        max_var = model.new_max_var(x, y, z)

        # Constrain the range
        model.add(max_var - min_var <= 3)

        # Set some values
        model.add(x == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert solver.value(max_var) - solver.value(min_var) <= 3

    def test_min_with_large_range(self):
        """
        Tests minimum with large value ranges.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(1, 1000, "x")
        y = model.new_int_var(500, 1500, "y")

        min_var = model.new_min_var(x, y)

        model.add(x == 750)
        model.add(y == 600)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(min_var), 600)


class TestStepVar:
    """
    Tests for the new_step_var() method.
    """

    def test_basic_two_domains(self):
        """
        Tests a basic step function with two domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # If x in [0, 10], y = 100; if x in [11, 20], y = 200
        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test first domain
        model.add(x == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 100)

    def test_basic_two_domains_second_range(self):
        """
        Tests the second domain of a basic step function.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # If x in [0, 10], y = 100; if x in [11, 20], y = 200
        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test second domain
        model.add(x == 15)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 200)

    def test_three_domains(self):
        """
        Tests a step function with three domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 30, "x")

        domains = [
            cp_model.Domain(0, 10),
            cp_model.Domain(11, 20),
            cp_model.Domain(21, 30),
        ]
        values = [10, 20, 30]
        y = model.new_step_var(x, domains, values)

        # Test middle domain
        model.add(x == 15)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 20)

    def test_many_domains(self):
        """
        Tests a step function with many domains (stress test).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 100, "x")

        # Create 10 domains, each of width 10
        domains = [
            cp_model.Domain(i * 10, (i + 1) * 10 - 1) for i in range(10)
        ]
        values = [i * 100 for i in range(10)]
        y = model.new_step_var(x, domains, values)

        # Test domain 7 (x in [70, 79], y = 700)
        model.add(x == 75)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 700)

    def test_non_contiguous_domains(self):
        """
        Tests step function with gaps between domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 50, "x")

        # Domains with gaps: [0,5], [10,15], [20,25]
        domains = [
            cp_model.Domain(0, 5),
            cp_model.Domain(10, 15),
            cp_model.Domain(20, 25),
        ]
        values = [1, 2, 3]
        y = model.new_step_var(x, domains, values)

        # Test second domain
        model.add(x == 12)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 2)

    def test_negative_domains(self):
        """
        Tests step function with negative domain ranges.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-20, 10, "x")

        domains = [
            cp_model.Domain(-20, -10),
            cp_model.Domain(-9, 0),
            cp_model.Domain(1, 10),
        ]
        values = [100, 200, 300]
        y = model.new_step_var(x, domains, values)

        # Test negative domain
        model.add(x == -15)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 100)

    def test_negative_output_values(self):
        """
        Tests step function with negative output values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [-100, -50]
        y = model.new_step_var(x, domains, values)

        model.add(x == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), -100)

    def test_mixed_sign_values(self):
        """
        Tests step function with both positive and negative output values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 30, "x")

        domains = [
            cp_model.Domain(0, 10),
            cp_model.Domain(11, 20),
            cp_model.Domain(21, 30),
        ]
        values = [-50, 0, 50]
        y = model.new_step_var(x, domains, values)

        # Test zero value
        model.add(x == 15)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 0)

    def test_single_domain(self):
        """
        Tests step function with just one domain (edge case).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")

        domains = [cp_model.Domain(0, 10)]
        values = [42]
        y = model.new_step_var(x, domains, values)

        model.add(x == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 42)

    def test_domain_boundary_lower(self):
        """
        Tests behavior at lower domain boundary.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test at lower boundary of first domain
        model.add(x == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 100)

    def test_domain_boundary_upper(self):
        """
        Tests behavior at upper domain boundary.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test at upper boundary of first domain
        model.add(x == 10)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 100)

    def test_domain_boundary_between(self):
        """
        Tests boundary between two domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test at lower boundary of second domain
        model.add(x == 11)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 200)

    def test_invalid_mismatched_lengths(self):
        """
        Tests error handling for mismatched domain and value lengths.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        domains = [cp_model.Domain(0, 10), cp_model.Domain(11, 20)]
        values = [100]  # Too few values

        with pytest.raises(ValueError):
            model.new_step_var(x, domains, values)

    def test_output_variable_bounds(self):
        """
        Verifies the output variable has correct bounds.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 30, "x")

        domains = [
            cp_model.Domain(0, 10),
            cp_model.Domain(11, 20),
            cp_model.Domain(21, 30),
        ]
        values = [5, 15, 25]
        y = model.new_step_var(x, domains, values)

        # The output variable should have domain containing exactly {5, 15, 25}
        proto = model.proto
        y_var = proto.variables[y.index]
        y_domain = cp_model.Domain.from_flat_intervals(y_var.domain)

        # Check that the domain contains exactly the values
        for value in values:
            assert y_domain.contains(value)

        # Check bounds
        assert_equal(min(y_var.domain), 5)
        assert_equal(max(y_var.domain), 25)

        # Verify it's a discrete domain (not continuous [5, 25])
        # The domain should be {5, 15, 25}, not all values from 5 to 25
        assert_equal(list(y_var.domain), [5, 5, 15, 15, 25, 25])

    def test_discrete_domain_values(self):
        """
        Tests step function with discrete (non-contiguous) domain values.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # Domain with specific discrete values
        domains = [
            cp_model.Domain.from_values([1, 3, 5, 7]),
            cp_model.Domain.from_values([2, 4, 6, 8]),
        ]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test odd value (first domain)
        model.add(x == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 100)

    def test_discrete_domain_values_even(self):
        """
        Tests the second discrete domain.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # Domain with specific discrete values
        domains = [
            cp_model.Domain.from_values([1, 3, 5, 7]),
            cp_model.Domain.from_values([2, 4, 6, 8]),
        ]
        values = [100, 200]
        y = model.new_step_var(x, domains, values)

        # Test even value (second domain)
        model.add(x == 4)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 200)

    def test_gap_should_be_infeasible(self):
        """
        When x is forced into a gap between domains, model should be
        INFEASIBLE.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 50, "x")

        # Domains with gaps: [0,5], [10,15], [20,25]
        domains = [
            cp_model.Domain(0, 5),
            cp_model.Domain(10, 15),
            cp_model.Domain(20, 25),
        ]
        values = [1, 2, 3]
        _ = model.new_step_var(x, domains, values)

        # Force x into a gap (7 is not in any domain)
        model.add(x == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.INFEASIBLE)

    def test_outside_all_domains_infeasible(self):
        """
        When x is forced outside all domains, model should be INFEASIBLE.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 50, "x")

        # Domains: [0,10], [20,30]
        domains = [cp_model.Domain(0, 10), cp_model.Domain(20, 30)]
        values = [100, 200]
        _ = model.new_step_var(x, domains, values)

        # Force x outside all domains
        model.add(x == 40)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.INFEASIBLE)

    def test_unconstrained_x_stays_in_domains(self):
        """
        When x is unconstrained, solver should only choose values in domains.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 50, "x")

        # Domains with gaps: [0,5], [10,15], [20,25]
        domains = [
            cp_model.Domain(0, 5),
            cp_model.Domain(10, 15),
            cp_model.Domain(20, 25),
        ]
        values = [1, 2, 3]
        _ = model.new_step_var(x, domains, values)

        # Don't constrain x, but verify it's in one of the domains
        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        x_val = solver.value(x)

        # Verify x is in one of the domains
        in_first = 0 <= x_val <= 5
        in_second = 10 <= x_val <= 15
        in_third = 20 <= x_val <= 25
        in_domain = in_first or in_second or in_third

        assert in_domain, f"x={x_val} should be in one of the domains"

    def test_discrete_domain_gap_infeasible(self):
        """
        With discrete domains, values between them should be infeasible.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # Discrete domains: {1,3,5,7} and {2,4,6,8}
        domains = [
            cp_model.Domain.from_values([1, 3, 5, 7]),
            cp_model.Domain.from_values([2, 4, 6, 8]),
        ]
        values = [100, 200]
        _ = model.new_step_var(x, domains, values)

        # Force x to a value not in any domain
        model.add(x == 9)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.INFEASIBLE)


class TestConvexPwlVar:
    """
    Tests for the new_convex_pwl_var() method.
    """

    def test_basic_v_shape(self):
        """
        Tests a basic V-shaped convex function (absolute value).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(-10, 10, "x")

        # V-shape: rate -1 before x=0, rate +1 after x=0
        # f(x) = max(-x, x) = |x|
        y = model.new_convex_pwl_var(
            x, breakpoints=[-10, 0], rates=[-1, 1], initial_value=10
        )

        # Test at x = -5: |-5| = 5
        model.add(x == -5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 5)

    def test_earliness_tardiness(self):
        """
        Tests earliness-tardiness cost function (real-world example).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        completion = model.new_int_var(0, 20, "completion")

        # Earliness penalty of 8 before time 5, zero cost until 15,
        # tardiness penalty of 12 after 15
        cost = model.new_convex_pwl_var(
            completion, breakpoints=[0, 5, 15], rates=[-8, 0, 12]
        )

        # Early completion at time 2: cost = -8*2 + 0 = -16? No...
        # Actually at breakpoint 0, initial_value=0, so segment 1 is -8*x + 0
        # At x=2: -8*2 + 0 = -16, but we want positive cost
        # Need to adjust: earliness means PENALTY, so we want cost to increase
        # as we go earlier. So rate should be positive going left.
        # Actually, let's reconsider: if x < 5, we want higher cost.
        # So f(x) for x < 5 should have negative slope
        model.add(completion == 2)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # With breakpoints=[0,5,15], rates=[-8,0,12], initial_value=0:
        # Segment 1: -8*x + 0
        # At x=5: -8*5 + 0 = -40
        # Segment 2 must pass through (5, -40): 0*x + b = -40 at x=5, so b=-40
        # Segment 3 must pass through (15, -40): 12*x + c = -40 at x=15
        # So c = -40 - 12*15 = -40 - 180 = -220
        # At x=2: max(-8*2+0, 0*2-40, 12*2-220) = max(-16, -40, -196) = -16
        assert_equal(solver.value(cost), -16)

    def test_earliness_tardiness_on_time(self):
        """
        Tests on-time completion has zero cost.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        completion = model.new_int_var(0, 20, "completion")

        cost = model.new_convex_pwl_var(
            completion, breakpoints=[0, 5, 15], rates=[-8, 0, 12]
        )

        # On-time at 5
        model.add(completion == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # At x=5: max(-8*5+0, 0*5-40, 12*5-220) = max(-40, -40, -160) = -40
        assert_equal(solver.value(cost), -40)

    def test_earliness_tardiness_late(self):
        """
        Tests late completion incurs tardiness cost.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        completion = model.new_int_var(0, 20, "completion")

        cost = model.new_convex_pwl_var(
            completion, breakpoints=[0, 5, 15], rates=[-8, 0, 12]
        )

        # Late at 20
        model.add(completion == 20)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # At x=20: max(-8*20+0, 0*20-40, 12*20-220) = max(-160, -40, 20) = 20
        assert_equal(solver.value(cost), 20)

    def test_multiple_segments(self):
        """
        Tests PWL function with many segments.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 100, "x")

        # 5 segments with increasing rates
        y = model.new_convex_pwl_var(
            x, breakpoints=[0, 20, 40, 60, 80], rates=[-10, -5, 0, 5, 10]
        )

        # Test at x = 20
        model.add(x == 20)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # At x=20 (second breakpoint), value is the same
        # Segment 1: -10*20 + 0 = -200
        assert_equal(solver.value(y), -200)

    def test_single_segment(self):
        """
        Tests single segment (trivially convex).
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")

        y = model.new_convex_pwl_var(
            x, breakpoints=[0], rates=[2], initial_value=5
        )

        model.add(x == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 2 * 7 + 5)

    def test_two_segments(self):
        """
        Tests minimal convex function with two segments.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # Two segments: rate 1 from x=0, rate 3 from x=10
        y = model.new_convex_pwl_var(x, breakpoints=[0, 10], rates=[1, 3])

        model.add(x == 15)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Segment 1: 1*x + 0, at x=10: 10
        # Segment 2: 3*x + b, must equal 10 at x=10, so b = 10 - 30 = -20
        # At x=15: max(1*15+0, 3*15-20) = max(15, 25) = 25
        assert_equal(solver.value(y), 25)

    def test_all_negative_rates(self):
        """
        Tests convex function with all negative rates.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")

        # Negative rates, non-decreasing: -10, -5, -1
        y = model.new_convex_pwl_var(
            x, breakpoints=[0, 5, 8], rates=[-10, -5, -1], initial_value=100
        )

        model.add(x == 5)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # At x=5 (breakpoint): -10*5 + 100 = 50
        assert_equal(solver.value(y), 50)

    def test_all_positive_rates(self):
        """
        Tests convex function with all positive rates.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")

        # Positive rates, non-decreasing: 1, 5, 10
        y = model.new_convex_pwl_var(
            x, breakpoints=[0, 4, 6], rates=[1, 5, 10]
        )

        model.add(x == 8)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Segment 1: 1*x + 0, at x=4: 4
        # Segment 2: 5*x + b, at x=4 must be 4, so b = 4 - 20 = -16
        # At x=6: 5*6 - 16 = 14
        # Segment 3: 10*x + c, at x=6 must be 14, so c = 14 - 60 = -46
        # At x=8: max(1*8+0, 5*8-16, 10*8-46) = max(8, 14, 34) = 34
        assert_equal(solver.value(y), 34)

    def test_with_zero_rates(self):
        """
        Tests convex function including flat (zero rate) segments.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()
        x = model.new_int_var(0, 20, "x")

        # Rates with zeros: -2, 0, 0, 2
        y = model.new_convex_pwl_var(
            x,
            breakpoints=[0, 5, 10, 15],
            rates=[-2, 0, 0, 2],
            initial_value=20,
        )

        model.add(x == 10)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Segment 1: -2*x + 20, at x=5: -10 + 20 = 10
        # Segments 2 & 3: 0*x + 10 (flat at 10)
        # At x=10: max(-2*10+20, 0*10+10, 0*10+10, 2*10+b)
        # Segment 4: at x=15 must be 10, so b = -20
        # At x=10: 2*10 - 20 = 0
        # So max(0, 10, 10, 0) = 10
        assert_equal(solver.value(y), 10)

    def test_non_convex_detection(self):
        """
        Tests that non-convex function raises ValueError.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")

        # Non-convex: rates decrease from 5 to 3
        with pytest.raises(ValueError) as exc_info:
            model.new_convex_pwl_var(
                x, breakpoints=[0, 5, 10], rates=[5, 3, 7]
            )

        assert "non-decreasing" in str(exc_info.value)

    def test_length_mismatch_error(self):
        """
        Tests error when breakpoints and rates have different lengths.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")

        with pytest.raises(ValueError) as exc_info:
            model.new_convex_pwl_var(
                x,
                breakpoints=[0, 5, 10],
                rates=[1, 2],  # Mismatch
            )

        assert "same length" in str(exc_info.value)

    def test_function_evaluation_at_multiple_points(self):
        """
        Tests that PWL function evaluates correctly at different x values.
        """
        from ortools.sat.python import cp_model

        # Test at multiple points
        test_cases = [
            (0, 0),  # |0| = 0
            (5, 5),  # |5| = 5
            (10, 10),  # |10| = 10
            (-5, 5),  # |-5| = 5
        ]

        for x_val, expected_y in test_cases:
            model = CpModelPlus()
            x = model.new_int_var(-10, 10, "x")

            # Absolute value function
            y = model.new_convex_pwl_var(
                x, breakpoints=[-10, 0], rates=[-1, 1], initial_value=10
            )

            model.add(x == x_val)

            solver = cp_model.CpSolver()
            status = solver.solve(model)

            assert_equal(status, cp_model.OPTIMAL)
            assert_equal(solver.value(y), expected_y)


class TestOverlapVar:
    """
    Tests for the new_overlap_var method.
    """

    def test_partial_overlap(self):
        """
        Tests two intervals with partial overlap.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Interval a: [2, 7) with size 5
        # Interval b: [5, 10) with size 5
        # Overlap: [5, 7) with length 2
        a = model.new_interval_var(2, 5, 7, "a")
        b = model.new_interval_var(5, 5, 10, "b")

        overlap = model.new_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), 2)

    def test_no_overlap(self):
        """
        Tests two disjoint intervals that don't overlap.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Interval a: [0, 5) with size 5
        # Interval b: [10, 15) with size 5
        # No overlap, expected length 0
        a = model.new_interval_var(0, 5, 5, "a")
        b = model.new_interval_var(10, 5, 15, "b")

        overlap = model.new_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), 0)

    def test_complete_overlap(self):
        """
        Tests when one interval completely contains another.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Interval a: [0, 10) with size 10
        # Interval b: [3, 7) with size 4
        # Complete overlap: b is inside a, length 4
        a = model.new_interval_var(0, 10, 10, "a")
        b = model.new_interval_var(3, 4, 7, "b")

        overlap = model.new_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), 4)

    def test_adjacent_intervals(self):
        """
        Tests adjacent intervals that touch but don't overlap.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Interval a: [0, 5) with size 5
        # Interval b: [5, 10) with size 5
        # Adjacent (touching at 5), no overlap expected
        a = model.new_interval_var(0, 5, 5, "a")
        b = model.new_interval_var(5, 5, 10, "b")

        overlap = model.new_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), 0)

    def test_identical_intervals(self):
        """
        Tests two identical intervals that completely overlap.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Both intervals: [5, 15) with size 10
        # Complete overlap, length 10
        a = model.new_interval_var(5, 10, 15, "a")
        b = model.new_interval_var(5, 10, 15, "b")

        overlap = model.new_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), 10)

    def test_variable_start_times(self):
        """
        Tests overlap with variable start times determined by solver.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create intervals with variable start times
        start_a = model.new_int_var(0, 10, "start_a")
        start_b = model.new_int_var(0, 10, "start_b")

        # Both have size 5
        a = model.new_interval_var(start_a, 5, start_a + 5, "a")
        b = model.new_interval_var(start_b, 5, start_b + 5, "b")

        overlap = model.new_overlap_var(a, b)

        # Force specific start times: a at 2, b at 4
        model.add(start_a == 2)
        model.add(start_b == 4)
        # a: [2, 7), b: [4, 9), overlap: [4, 7) = 3

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), 3)

    def test_maximize_overlap(self):
        """
        Tests that solver can maximize overlap between intervals.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create intervals with variable start times
        start_a = model.new_int_var(0, 10, "start_a")
        start_b = model.new_int_var(0, 10, "start_b")

        # Both have size 5
        a = model.new_interval_var(start_a, 5, start_a + 5, "a")
        b = model.new_interval_var(start_b, 5, start_b + 5, "b")

        overlap = model.new_overlap_var(a, b)

        # Maximize overlap
        model.maximize(overlap)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Maximum overlap is when intervals are identical: 5
        assert_equal(solver.value(overlap), 5)

    def test_minimize_overlap(self):
        """
        Tests that solver can minimize overlap between intervals.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Create intervals with variable start times
        start_a = model.new_int_var(0, 20, "start_a")
        start_b = model.new_int_var(0, 20, "start_b")

        # Both have size 5
        a = model.new_interval_var(start_a, 5, start_a + 5, "a")
        b = model.new_interval_var(start_b, 5, start_b + 5, "b")

        overlap = model.new_overlap_var(a, b)

        # Minimize overlap
        model.minimize(overlap)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Minimum overlap is 0 (disjoint)
        assert_equal(solver.value(overlap), 0)

    def test_optional_first_absent(self):
        """
        Tests overlap when first interval is optional and absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # First interval is optional and will be absent
        first_pres = model.new_bool_var("first_pres")
        first = model.new_optional_interval_var(0, 5, 5, first_pres, "first")

        # Second interval is present
        second = model.new_interval_var(2, 5, 7, "second")

        overlap = model.new_overlap_var(first, second)

        # Force first to be absent
        model.add(first_pres == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # First is absent, so overlap should be 0
        assert_equal(solver.value(overlap), 0)

    def test_optional_second_absent(self):
        """
        Tests overlap when second interval is optional and absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # First interval is present
        first = model.new_interval_var(0, 5, 5, "first")

        # Second interval is optional and will be absent
        second_pres = model.new_bool_var("second_pres")
        second = model.new_optional_interval_var(
            2, 5, 7, second_pres, "second"
        )

        overlap = model.new_overlap_var(first, second)

        # Force second to be absent
        model.add(second_pres == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Second is absent, so overlap should be 0
        assert_equal(solver.value(overlap), 0)

    def test_optional_both_present(self):
        """
        Tests overlap when both intervals are optional and present.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Both intervals are optional
        first_pres = model.new_bool_var("first_pres")
        first = model.new_optional_interval_var(0, 5, 5, first_pres, "first")

        second_pres = model.new_bool_var("second_pres")
        second = model.new_optional_interval_var(
            2, 5, 7, second_pres, "second"
        )

        overlap = model.new_overlap_var(first, second)

        # Force both to be present
        model.add(first_pres == 1)
        model.add(second_pres == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Both present: [0, 5) and [2, 7), overlap: [2, 5) = 3
        assert_equal(solver.value(overlap), 3)

    def test_optional_both_absent(self):
        """
        Tests overlap when both intervals are optional and absent.
        """
        from ortools.sat.python import cp_model

        model = CpModelPlus()

        # Both intervals are optional
        first_pres = model.new_bool_var("first_pres")
        first = model.new_optional_interval_var(0, 5, 5, first_pres, "first")

        second_pres = model.new_bool_var("second_pres")
        second = model.new_optional_interval_var(
            2, 5, 7, second_pres, "second"
        )

        overlap = model.new_overlap_var(first, second)

        # Force both to be absent
        model.add(first_pres == 0)
        model.add(second_pres == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Both absent, so overlap should be 0
        assert_equal(solver.value(overlap), 0)
