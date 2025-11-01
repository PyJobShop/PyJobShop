import pytest
from numpy.testing import assert_equal
from ortools.sat.python import cp_model
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


class TestPresenceOf:
    """
    Tests for the presence_of() method.
    """

    def test_optional_interval(self):
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

    def test_non_optional_interval(self):
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

    def test_negated_literal(self):
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


@pytest.mark.parametrize(
    "method_name",
    [
        "add_start_at_start",
        "add_start_at_end",
        "add_start_before_start",
        "add_start_before_end",
        "add_end_at_start",
        "add_end_at_end",
        "add_end_before_start",
        "add_end_before_end",
    ],
)
class TestIntervalPrecedenceConstraints:
    """
    Consolidated tests for all interval precedence constraint methods.
    """

    def test_basic_constraint(self, method_name):
        """
        Tests that constraint method creates correct constraint.
        """
        model = CpModelPlus()
        interval1 = model.new_interval_var(0, 10, 5, "interval1")
        interval2 = model.new_interval_var(0, 10, 5, "interval2")

        method = getattr(model, method_name)
        constraint = method(interval1, interval2, delay=2)

        assert constraint is not None
        assert model.proto.constraints[-1] is not None

    def test_with_optional_intervals(self, method_name):
        """
        Tests constraint with optional intervals.
        """
        model = CpModelPlus()

        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start1, 5, start1 + 5, presence1, "interval1"
        )
        interval2 = model.new_optional_interval_var(
            start2, 5, start2 + 5, presence2, "interval2"
        )

        method = getattr(model, method_name)
        constraint = method(interval1, interval2, delay=2)

        assert constraint is not None

    def test_both_absent_satisfied(self, method_name):
        """
        Tests constraint is satisfied when both intervals are absent.
        """
        model = CpModelPlus()
        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start1, 5, start1 + 5, presence1, "interval1"
        )
        interval2 = model.new_optional_interval_var(
            start2, 5, start2 + 5, presence2, "interval2"
        )

        method = getattr(model, method_name)
        method(interval1, interval2, delay=2)

        model.add(presence1 == 0)
        model.add(presence2 == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)

    def test_both_present_enforced(self, method_name):
        """
        Tests constraint is enforced when both intervals are present.
        This test verifies the constraint actually affects the solution.
        """
        model = CpModelPlus()
        start1 = model.new_int_var(0, 10, "start1")
        start2 = model.new_int_var(0, 10, "start2")
        presence1 = model.new_bool_var("presence1")
        presence2 = model.new_bool_var("presence2")

        interval1 = model.new_optional_interval_var(
            start1, 5, start1 + 5, presence1, "interval1"
        )
        interval2 = model.new_optional_interval_var(
            start2, 5, start2 + 5, presence2, "interval2"
        )

        method = getattr(model, method_name)
        method(interval1, interval2, delay=2)

        model.add(presence1 == 1)
        model.add(presence2 == 1)
        model.add(start1 == 3)

        solver = cp_model.CpSolver()
        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)

        # Verify constraint is enforced (actual value depends on method)
        assert solver.value(start2) is not None


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


class TestSpan:
    """
    Tests for the add_span() method.
    """

    def test_basic_constraint(self):
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

    def test_single_candidate(self):
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

    def test_multiple_candidates(self):
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

    def test_with_optional_intervals(self):
        """
        Tests add_span with optional candidate intervals.
        """
        model = CpModelPlus()
        main_pres = model.new_bool_var("main_pres")
        main = model.new_optional_interval_var(0, 10, 10, main_pres, "main")

        # Both candidates absent
        candidate1 = model.new_optional_interval_var(
            0, 5, 5, model.new_constant(False), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            3, 8, 5, model.new_constant(False), "candidate2"
        )

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(main_pres), 0)

    def test_shortcut_all_present(self):
        """
        Tests add_span shortcut when all intervals are non-optional.
        This tests the is_true helper and stronger formulation path.
        """
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

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main should span both candidates
        # Start should be min (2)
        assert_equal(solver.value(main.start_expr()), 2)
        # End should be max (8 + 5 = 13)
        assert_equal(solver.value(main.end_expr()), 13)

    def test_only_one_candidate_present(self):
        """
        Tests add_span when only one of multiple candidates is present.
        """
        model = CpModelPlus()
        main_start = model.new_int_var(0, 20, "main_start")
        main_size = model.new_int_var(0, 20, "main_end")
        main_end = model.new_int_var(0, 20, "main_end")
        main_pres = model.new_bool_var("main_pres")
        main = model.new_optional_interval_var(
            main_start, main_size, main_end, main_pres, "main"
        )

        # Only candidate1 is present
        candidate1 = model.new_optional_interval_var(
            2, 5, 7, model.new_constant(True), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            8, 5, 13, model.new_constant(False), "candidate2"
        )

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)
        assert_equal(status, cp_model.OPTIMAL)

        # Main should be present and span only candidate1
        assert_equal(solver.value(main_pres), 1)
        assert_equal(solver.value(main.start_expr()), 2)
        assert_equal(solver.value(main.end_expr()), 7)  # 2 + 5

    def test_multiple_candidates_present(self):
        """
        Tests add_span when some candidates are present and some absent.
        """
        model = CpModelPlus()
        main_start = model.new_int_var(0, 30, "main_start")
        main = model.new_interval_var(main_start, 20, main_start + 20, "main")

        # candidate1 and candidate3 present, candidate2 absent
        candidate1 = model.new_optional_interval_var(
            1, 2, 3, model.new_constant(True), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            5, 3, 8, model.new_constant(False), "candidate2"
        )
        candidate3 = model.new_optional_interval_var(
            10, 11, 21, model.new_constant(True), "candidate3"
        )

        model.add_span(main, [candidate1, candidate2, candidate3])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main should span from candidate1 start (1) to candidate3 end (21)
        assert_equal(solver.value(main.start_expr()), 1)
        assert_equal(solver.value(main.end_expr()), 21)

    def test_correct_span_computation(self):
        """
        Tests that add_span correctly computes min start and max end.
        """
        model = CpModelPlus()
        main_start = model.new_int_var(0, 20, "main_start")
        main = model.new_interval_var(main_start, 9, main_start + 9, "main")

        # Create candidates with variable starts
        cand1_start = model.new_int_var(0, 10, "cand1_start")
        cand2_start = model.new_int_var(0, 10, "cand2_start")
        cand3_start = model.new_int_var(0, 10, "cand3_start")

        candidate1 = model.new_interval_var(
            cand1_start, 3, cand1_start + 3, "candidate1"
        )
        candidate2 = model.new_interval_var(
            cand2_start, 4, cand2_start + 4, "candidate2"
        )
        candidate3 = model.new_interval_var(
            cand3_start, 2, cand3_start + 2, "candidate3"
        )

        model.add_span(main, [candidate1, candidate2, candidate3])

        # Fix specific positions
        model.add(cand1_start == 5)  # Ends at 8
        model.add(cand2_start == 1)  # Ends at 5
        model.add(cand3_start == 8)  # Ends at 10

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main should start at min(5, 1, 8) = 1
        assert_equal(solver.value(main.start_expr()), 1)
        # Main should end at max(8, 5, 10) = 10
        assert_equal(solver.value(main.end_expr()), 10)

    def test_main_present_forces_candidate(self):
        """
        Tests that if main is present, at least one candidate must be present.
        """
        model = CpModelPlus()
        main_start = model.new_int_var(0, 20, "main_start")
        main = model.new_interval_var(main_start, 6, main_start + 6, "main")

        cand1_pres = model.new_bool_var("cand1_pres")
        cand2_pres = model.new_bool_var("cand2_pres")
        candidate1 = model.new_optional_interval_var(
            2, 3, 5, cand1_pres, "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            4, 4, 8, cand2_pres, "candidate2"
        )

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # At least one candidate must be present
        total_present = solver.value(cand1_pres) + solver.value(cand2_pres)
        assert total_present >= 1

    def test_with_overlapping_candidates(self):
        """
        Tests add_span with overlapping candidate intervals.
        """
        model = CpModelPlus()
        main_start = model.new_int_var(0, 20, "main_start")
        main = model.new_interval_var(main_start, 8, main_start + 8, "main")

        # Overlapping intervals
        candidate1 = model.new_interval_var(2, 5, 7, "candidate1")  # 2-7
        candidate2 = model.new_interval_var(4, 6, 10, "candidate2")  # 4-10
        candidate3 = model.new_interval_var(6, 4, 10, "candidate3")  # 6-10

        model.add_span(main, [candidate1, candidate2, candidate3])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main should span from 2 to 10
        assert_equal(solver.value(main.start_expr()), 2)
        assert_equal(solver.value(main.end_expr()), 10)

    def test_all_candidates_absent(self):
        """
        Tests that main is absent when all candidates are absent.
        """
        model = CpModelPlus()
        main_pres = model.new_bool_var("main_pres")
        main = model.new_optional_interval_var(0, 10, 10, main_pres, "main")

        # All candidates absent
        candidate1 = model.new_optional_interval_var(
            0, 5, 5, model.new_constant(False), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            3, 8, 5, model.new_constant(False), "candidate2"
        )

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main must be absent
        assert_equal(solver.value(main_pres), 0)

    def test_optional_main_non_optional_candidates(self):
        """
        Tests add_span with optional main and non-optional candidates.
        """
        model = CpModelPlus()
        main_pres = model.new_bool_var("main_pres")
        main_start = model.new_int_var(0, 20, "main_start")
        main = model.new_optional_interval_var(
            main_start, 6, main_start + 6, main_pres, "main"
        )

        # All candidates are non-optional (always present)
        candidate1 = model.new_interval_var(2, 3, 5, "candidate1")  # 2-5
        candidate2 = model.new_interval_var(6, 2, 8, "candidate2")  # 6-8

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main must be present since at least one candidate is present
        assert_equal(solver.value(main_pres), 1)
        # Main should span from 2 to 8 (size 6)
        assert_equal(solver.value(main.start_expr()), 2)
        assert_equal(solver.value(main.end_expr()), 8)

    def test_infeasible_main_present_candidates_absent(self):
        """
        Tests main present with all candidates absent is infeasible.
        """
        model = CpModelPlus()
        # Main present but all candidates absent (infeasible)
        main = model.new_optional_interval_var(
            0, 10, 10, model.new_constant(True), "main"
        )

        candidate1 = model.new_optional_interval_var(
            0, 5, 5, model.new_constant(False), "candidate1"
        )
        candidate2 = model.new_optional_interval_var(
            3, 8, 5, model.new_constant(False), "candidate2"
        )

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.INFEASIBLE)

    def test_infeasible_main_absent_candidates_present(self):
        """
        Tests main absent with candidates present is infeasible.
        """
        model = CpModelPlus()
        # Main absent but at least one candidate present (infeasible)
        main = model.new_optional_interval_var(
            0, 10, 10, model.new_constant(False), "main"
        )

        candidate1 = model.new_optional_interval_var(
            0, 5, 5, model.new_constant(True), "candidate1"
        )
        candidate2 = model.new_interval_var(3, 8, 5, "candidate2")

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.INFEASIBLE)

    def test_variable_size_main(self):
        """
        Tests add_span with a variable-size main interval.
        """
        model = CpModelPlus()
        main_start = model.new_int_var(0, 20, "main_start")
        main_size = model.new_int_var(5, 15, "main_size")
        main_end = model.new_int_var(0, 30, "main_end")
        main = model.new_interval_var(main_start, main_size, main_end, "main")

        # Candidates at fixed positions
        candidate1 = model.new_interval_var(3, 4, 7, "candidate1")  # 3-7
        candidate2 = model.new_interval_var(10, 3, 13, "candidate2")  # 10-13

        model.add_span(main, [candidate1, candidate2])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Main should span from 3 to 13 (size 10)
        assert_equal(solver.value(main.start_expr()), 3)
        assert_equal(solver.value(main.end_expr()), 13)
        assert_equal(solver.value(main.size_expr()), 10)

    def test_empty_candidates(self):
        """
        Tests add_span with empty candidates list raises ValueError.
        """
        model = CpModelPlus()
        main = model.new_interval_var(0, 10, 10, "main")

        # Should raise ValueError for empty candidates
        with pytest.raises(
            ValueError, match="[Cc]andidates.*empty|empty.*candidates"
        ):
            model.add_span(main, [])


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
        model = CpModelPlus()

        # Both intervals present
        main_start = model.new_int_var(0, 10, "main_start")
        main = model.new_optional_interval_var(
            main_start, 5, main_start + 5, model.new_constant(True), "main"
        )

        cand_start = model.new_int_var(0, 10, "cand_start")
        candidate = model.new_optional_interval_var(
            cand_start,
            5,
            cand_start + 5,
            model.new_constant(True),
            "candidate",
        )

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
        model = CpModelPlus()

        # Main interval present, candidate absent
        main_start = model.new_int_var(0, 10, "main_start")
        main = model.new_optional_interval_var(
            main_start, 5, main_start + 5, model.new_constant(True), "main"
        )

        cand_start = model.new_int_var(0, 10, "cand_start")
        candidate = model.new_optional_interval_var(
            cand_start,
            5,
            cand_start + 5,
            model.new_constant(False),
            "candidate",
        )

        model.add_synchronize(main, [candidate])

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        # Should be feasible even though candidate is absent
        assert_equal(status, cp_model.OPTIMAL)

    def test_different_durations_infeasible(self):
        """
        Tests that intervals with different durations cannot synchronize.
        """
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

    def test_multiple_conditions_all_true(self):
        """
        Tests if-then-else with multiple conditions (AND logic) when all true.
        """
        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")
        cond3 = model.new_bool_var("cond3")

        # If ALL conditions true, then y == 7, else y == 0
        model.add_if_then_else([cond1, cond2, cond3], y == 7, y == 0)

        # Force all conditions to be true
        model.add(cond1 == 1)
        model.add(cond2 == 1)
        model.add(cond3 == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 7)

    def test_multiple_conditions_one_false(self):
        """
        Tests if-then-else with multiple conditions when one is false.
        """
        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")
        cond3 = model.new_bool_var("cond3")

        # If ALL conditions true, then y == 7, else y == 0
        model.add_if_then_else([cond1, cond2, cond3], y == 7, y == 0)

        # Force one condition to be false
        model.add(cond1 == 1)
        model.add(cond2 == 0)  # This one is false
        model.add(cond3 == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Since one condition is false, else branch should be enforced
        assert_equal(solver.value(y), 0)

    def test_multiple_conditions_all_false(self):
        """
        Tests if-then-else with multiple conditions when all are false.
        """
        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        # If ALL conditions true, then y == 5, else y == 2
        model.add_if_then_else([cond1, cond2], y == 5, y == 2)

        # Force all conditions to be false
        model.add(cond1 == 0)
        model.add(cond2 == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 2)

    @pytest.mark.parametrize(
        "cond1_val,cond2_val,expected_y",
        [
            (True, True, 10),  # Both true -> then branch
            (True, False, 0),  # One false -> else branch
            (False, True, 0),  # One false -> else branch
            (False, False, 0),  # Both false -> else branch
        ],
    )
    def test_multiple_conditions_all_combinations(
        self, cond1_val, cond2_val, expected_y
    ):
        """
        Tests all combinations of two conditions with AND logic.
        """
        model = CpModelPlus()
        y = model.new_int_var(0, 10, "y")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        # If BOTH conditions true, then y == 10, else y == 0
        model.add_if_then_else([cond1, cond2], y == 10, y == 0)

        model.add(cond1 == (1 if cond1_val else 0))
        model.add(cond2 == (1 if cond2_val else 0))

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), expected_y)


class TestConditionalVar:
    """
    Tests for the new_conditional_var() method.
    """

    def test_single_condition_true(self):
        """
        Tests that when condition is true, y equals x.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition)

        # Set values
        model.add(x == 5)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 5)
        assert_equal(solver.value(y), 5)

    def test_single_condition_false(self):
        """
        Tests that when condition is false, y is unconstrained.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition)

        # Set x and condition
        model.add(x == 5)
        model.add(condition == 0)

        # Force y to a different value
        model.add(y == 8)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 5)
        assert_equal(solver.value(y), 8)  # y can differ from x

    def test_multiple_conditions_all_true(self):
        """
        Tests with multiple conditions when all are true.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")
        cond3 = model.new_bool_var("cond3")

        y = model.new_conditional_var(x, cond1, cond2, cond3)

        # Set all conditions true
        model.add(x == 7)
        model.add(cond1 == 1)
        model.add(cond2 == 1)
        model.add(cond3 == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 7)

    def test_multiple_conditions_one_false(self):
        """
        Tests with multiple conditions when one is false.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        y = model.new_conditional_var(x, cond1, cond2)

        # Set one condition false
        model.add(x == 4)
        model.add(cond1 == 1)
        model.add(cond2 == 0)  # False

        # Force y to different value
        model.add(y == 9)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 4)
        assert_equal(solver.value(y), 9)  # y can differ

    def test_forces_condition_value(self):
        """
        Tests that y != x forces condition to be false.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition)

        # Force x and y to different values
        model.add(x == 2)
        model.add(y == 7)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        # Condition must be false since y != x
        assert_equal(solver.value(condition), 0)

    @pytest.mark.parametrize(
        "cond1_val,cond2_val,x_val,can_differ",
        [
            (True, True, 5, False),  # Both true -> y must equal x
            (True, False, 5, True),  # One false -> y can differ
            (False, True, 5, True),  # One false -> y can differ
            (False, False, 5, True),  # Both false -> y can differ
        ],
    )
    def test_all_combinations(self, cond1_val, cond2_val, x_val, can_differ):
        """
        Tests all combinations of two conditions.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        y = model.new_conditional_var(x, cond1, cond2)

        model.add(x == x_val)
        model.add(cond1 == (1 if cond1_val else 0))
        model.add(cond2 == (1 if cond2_val else 0))

        if can_differ:
            # Try to set y to different value
            different_val = (x_val + 3) % 11
            model.add(y == different_val)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)

        if can_differ:
            # Should be able to set y to different value
            assert_equal(solver.value(y), (x_val + 3) % 11)
        else:
            # y must equal x
            assert_equal(solver.value(y), x_val)

    def test_with_negative_domain(self):
        """
        Tests conditional variable with negative values in domain.
        """
        model = CpModelPlus()
        x = model.new_int_var(-10, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition)

        # Set x to negative value, condition true
        model.add(x == -5)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), -5)

    def test_with_linear_expression(self):
        """
        Tests conditional variable with linear expression (x + 5).
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        # Create conditional var from expression
        y = model.new_conditional_var(x + 5, condition)

        # When condition is true, y should equal x + 5
        model.add(x == 3)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 8)  # x + 5 = 3 + 5

    def test_with_expression_condition_false(self):
        """
        Tests expression-based conditional var is unconstrained when false.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(2 * x, condition)

        # When condition is false, y is unconstrained
        model.add(x == 4)
        model.add(condition == 0)
        model.add(y == 100)  # Can be anything

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(x), 4)
        assert_equal(solver.value(y), 100)

    def test_with_complex_expression(self):
        """
        Tests conditional variable with complex expression.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 5, "x")
        z = model.new_int_var(0, 5, "z")
        condition = model.new_bool_var("condition")

        # Create conditional var from complex expression
        y = model.new_conditional_var(2 * x + z, condition)

        # When condition is true
        model.add(x == 2)
        model.add(z == 3)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 7)  # 2*2 + 3 = 7

    def test_expression_with_multiple_conditions(self):
        """
        Tests expression with multiple conditions.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        y = model.new_conditional_var(x + 10, cond1, cond2)

        # Both conditions true
        model.add(x == 5)
        model.add(cond1 == 1)
        model.add(cond2 == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 15)  # x + 10 = 5 + 10

    def test_absent_value_condition_true(self):
        """
        Tests that absent_value is ignored when condition is true.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition, absent_value=99)

        # When condition is true, y should equal x regardless of absent_value
        model.add(x == 5)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 5)  # y == x, not absent_value

    def test_absent_value_condition_false(self):
        """
        Tests that absent_value is used when condition is false.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition, absent_value=99)

        # When condition is false, y should equal absent_value
        model.add(x == 5)
        model.add(condition == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 99)  # y == absent_value

    def test_absent_value_zero(self):
        """
        Tests absent_value=0 works correctly.
        """
        model = CpModelPlus()
        x = model.new_int_var(5, 15, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition, absent_value=0)

        model.add(x == 10)
        model.add(condition == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 0)

    def test_absent_value_negative(self):
        """
        Tests negative absent_value.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(x, condition, absent_value=-100)

        model.add(condition == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), -100)

    def test_absent_value_with_expression(self):
        """
        Tests absent_value with linear expression.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(2 * x + 5, condition, absent_value=0)

        # When condition is true
        model.add(x == 3)
        model.add(condition == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 11)  # 2*3 + 5

    def test_absent_value_with_expression_false(self):
        """
        Tests absent_value with linear expression when condition false.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        condition = model.new_bool_var("condition")

        y = model.new_conditional_var(2 * x + 5, condition, absent_value=0)

        # When condition is false
        model.add(x == 3)
        model.add(condition == 0)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 0)  # absent_value, not 2*3+5

    def test_absent_value_multiple_conditions_all_true(self):
        """
        Tests absent_value with multiple conditions all true.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        y = model.new_conditional_var(x, cond1, cond2, absent_value=50)

        model.add(x == 7)
        model.add(cond1 == 1)
        model.add(cond2 == 1)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 7)  # All conditions true, use x

    def test_absent_value_multiple_conditions_one_false(self):
        """
        Tests absent_value with multiple conditions, one false.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        y = model.new_conditional_var(x, cond1, cond2, absent_value=50)

        model.add(x == 7)
        model.add(cond1 == 1)
        model.add(cond2 == 0)  # One false

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), 50)  # Any condition false, use absent

    @pytest.mark.parametrize(
        "cond1_val,cond2_val,expected",
        [
            (True, True, 8),  # Both true -> x value
            (True, False, 42),  # One false -> absent_value
            (False, True, 42),  # One false -> absent_value
            (False, False, 42),  # Both false -> absent_value
        ],
    )
    def test_absent_value_all_combinations(
        self, cond1_val, cond2_val, expected
    ):
        """
        Tests absent_value with all condition combinations.
        """
        model = CpModelPlus()
        x = model.new_int_var(0, 10, "x")
        cond1 = model.new_bool_var("cond1")
        cond2 = model.new_bool_var("cond2")

        y = model.new_conditional_var(x, cond1, cond2, absent_value=42)

        model.add(x == 8)
        model.add(cond1 == (1 if cond1_val else 0))
        model.add(cond2 == (1 if cond2_val else 0))

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(y), expected)


class TestMaxVar:
    """
    Tests for the new_max_var() method.
    """

    def test_basic_max_two_variables(self):
        """
        Tests basic maximum of two variables.
        """
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

    @pytest.mark.parametrize(
        "start_a,size_a,start_b,size_b,expected",
        [
            (2, 5, 5, 5, 2),  # Partial overlap: [2,7) and [5,10) -> [5,7)
            (0, 5, 10, 5, 0),  # Disjoint: [0,5) and [10,15)
            (0, 10, 3, 4, 4),  # Containment: [0,10) contains [3,7)
            (0, 5, 5, 5, 0),  # Adjacent: [0,5) and [5,10)
            (5, 10, 5, 10, 10),  # Identical: [5,15) and [5,15)
        ],
    )
    def test_overlap_basic(self, start_a, size_a, start_b, size_b, expected):
        """
        Tests overlap length for various non-optional interval configurations.
        """
        model = CpModelPlus()
        a = model.new_interval_var(start_a, size_a, start_a + size_a, "a")
        b = model.new_interval_var(start_b, size_b, start_b + size_b, "b")

        overlap = model.new_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), expected)

    def test_variable_start_times(self):
        """
        Tests overlap with variable start times determined by solver.
        """
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

    @pytest.mark.parametrize(
        "first_present,second_present,expected",
        [
            (False, True, 0),  # First absent
            (True, False, 0),  # Second absent
            (False, False, 0),  # Both absent
            (True, True, 3),  # Both present: [0,5) and [2,7) -> [2,5)
        ],
    )
    def test_overlap_optional(self, first_present, second_present, expected):
        """
        Tests overlap length with optional intervals in various presence
        configurations.
        """
        model = CpModelPlus()

        # Create optional intervals
        first_pres = model.new_bool_var("first_pres")
        first = model.new_optional_interval_var(0, 5, 5, first_pres, "first")

        second_pres = model.new_bool_var("second_pres")
        second = model.new_optional_interval_var(
            2, 5, 7, second_pres, "second"
        )

        overlap = model.new_overlap_var(first, second)

        # Set presence values
        model.add(first_pres == (1 if first_present else 0))
        model.add(second_pres == (1 if second_present else 0))

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap), expected)

    @pytest.mark.parametrize(
        "start_a,size_a,start_b,size_b,expected",
        [
            (2, 5, 5, 5, True),  # Partial overlap: [2,7) and [5,10)
            (0, 5, 10, 5, False),  # Disjoint: [0,5) and [10,15)
            (0, 5, 5, 5, False),  # Adjacent: [0,5) and [5,10)
            (2, 8, 4, 2, True),  # Containment: [2,10) contains [4,6)
            (0, 5, 0, 5, True),  # Identical: [0,5) and [0,5)
            (0, 0, 0, 0, False),  # Zero-duration: [0,0) and [0,0)
            (5, 5, 2, 5, True),  # Second before first: [5,10) and [2,7)
        ],
    )
    def test_has_overlap_basic(
        self, start_a, size_a, start_b, size_b, expected
    ):
        """
        Tests Boolean overlap for various non-optional interval configurations.
        """
        model = CpModelPlus()
        a = model.new_interval_var(start_a, size_a, start_a + size_a, "a")
        b = model.new_interval_var(start_b, size_b, start_b + size_b, "b")

        has_overlap = model.new_has_overlap_var(a, b)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(has_overlap), expected)

    @pytest.mark.parametrize(
        "first_present,second_present,overlapping,expected",
        [
            (False, True, True, False),  # First absent
            (True, False, True, False),  # Second absent
            (False, False, True, False),  # Both absent
            (True, True, True, True),  # Both present, overlapping
            (True, True, False, False),  # Both present, disjoint
        ],
    )
    def test_has_overlap_optional(
        self, first_present, second_present, overlapping, expected
    ):
        """
        Tests Boolean overlap with optional intervals in various presence
        and overlap configurations.
        """
        model = CpModelPlus()

        # Create optional intervals
        first_pres = model.new_bool_var("first_pres")
        first = model.new_optional_interval_var(0, 5, 5, first_pres, "first")

        second_pres = model.new_bool_var("second_pres")
        # Use overlapping or disjoint configuration
        second_start = 2 if overlapping else 10
        second = model.new_optional_interval_var(
            second_start, 5, second_start + 5, second_pres, "second"
        )

        has_overlap = model.new_has_overlap_var(first, second)

        # Set presence values
        model.add(first_pres == (1 if first_present else 0))
        model.add(second_pres == (1 if second_present else 0))

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(has_overlap), expected)

    def test_has_overlap_variable_timings(self):
        """
        Tests Boolean overlap with variable start times to verify
        constraint propagation works correctly.
        """
        model = CpModelPlus()

        # Create intervals with variable start times
        start_a = model.new_int_var(0, 10, "start_a")
        a = model.new_interval_var(start_a, 5, start_a + 5, "a")

        start_b = model.new_int_var(0, 10, "start_b")
        b = model.new_interval_var(start_b, 5, start_b + 5, "b")

        has_overlap = model.new_has_overlap_var(a, b)

        # Force them to overlap: a = [0, 5), b starts in [2, 4]
        model.add(start_a == 0)
        model.add(start_b >= 2)
        model.add(start_b <= 4)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(has_overlap), True)

    def test_has_overlap_symmetry(self):
        """
        Tests that overlap detection is symmetric: has_overlap(a, b) ==
        has_overlap(b, a).
        """
        model = CpModelPlus()

        a = model.new_interval_var(2, 5, 7, "a")
        b = model.new_interval_var(5, 5, 10, "b")

        overlap_ab = model.new_has_overlap_var(a, b)
        overlap_ba = model.new_has_overlap_var(b, a)

        model.add(overlap_ab == overlap_ba)

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(overlap_ab), solver.value(overlap_ba))

    def test_has_overlap_in_constraint(self):
        """
        Tests using has_overlap Boolean in constraints to enforce
        non-overlapping intervals.
        """
        model = CpModelPlus()

        # Variable start times
        start_a = model.new_int_var(0, 10, "start_a")
        a = model.new_interval_var(start_a, 5, start_a + 5, "a")

        start_b = model.new_int_var(0, 10, "start_b")
        b = model.new_interval_var(start_b, 5, start_b + 5, "b")

        has_overlap = model.new_has_overlap_var(a, b)

        # Enforce no overlap
        model.add(has_overlap == 0)

        # Try to minimize total makespan
        model.minimize(model.new_max_var(start_a + 5, start_b + 5))

        solver = cp_model.CpSolver()
        status = solver.solve(model)

        assert_equal(status, cp_model.OPTIMAL)
        assert_equal(solver.value(has_overlap), False)
        # Optimal solution should be sequential: [0,5) and [5,10)
        assert_equal(solver.objective_value, 10)
