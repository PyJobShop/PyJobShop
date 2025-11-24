from itertools import pairwise

from ortools.sat.python.cp_model import (
    BoolVarT,
    Constraint,
    CpModel,
    Domain,
    IntervalVar,
    IntVar,
    LinearExprT,
)

MAX_VALUE = 2**53


class CpModelPlus(CpModel):
    """
    Extended CP Model with scheduling constraint methods from various sources.

    - https://xiang.es/posts/cp-sat/
    - https://github.com/d-krupke/cpsat-primer
    - https://www.hakank.org/or_tools/cp_sat_utils.py
    - https://ibmdecisionoptimization.github.io/docplex-doc/cp/docplex.cp.modeler.py.html
    - https://github.com/jiayi9/cp/tree/main/scheduling

    Helpers
    -------
    - [x] add_all_equal(): Enforce identical values across variables
    - [x] presence_of(): Extract presence literal from optional intervals

    CP Optimizer's API
    ------------------
    - [x] add_start_at_start(): Delay between starts of two intervals
    - [x] add_start_at_end(): Delay between start of one and end of another
    - [x] add_start_before_start(): Minimum delay between starts
    - [x] add_start_before_end(): Minimum delay between start and end
    - [x] add_end_at_start(): Delay between end of one and start of another
    - [x] add_end_at_end(): Delay between ends of two intervals
    - [x] add_end_before_start(): Minimum delay between end and start
    - [x] add_end_before_end(): Minimum delay between ends
    - [ ] add_forbid_start(): Forbid interval starts in specified regions
    - [ ] add_forbid_end(): Forbid interval ends in specified regions
    - [ ] add_forbid_extent(): Forbid interval overlap with regions
    - [ ] add_start_eval(): Evaluate function at interval start
    - [ ] add_end_eval(): Evaluate function at interval end
    - [ ] add_size_eval(): Evaluate function on interval size
    - [ ] add_length_eval(): Evaluate function on interval length
    - [x] add_span(): Span constraint
    - [x] add_alternative(): Alternative constraint with cardinality
    - [x] add_synchronize(): Synchronization constraint between intervals
    - [ ] add_isomorphism(): Isomorphism constraint between interval sets

    Other
    -----
    - [x] new_product_var(): Create new variable for product of two int vars
    - [x] new_max_var(): Create new variable for maximum of int vars
    - [x] new_min_var(): Create new variable for minimum of int vars
    - [x] new_step_var(): Create piecewise constant (step) function var
    - [x] new_convex_pwl_var(): Create convex piecewise linear function var
    - [x] new_overlap_var(): Create overlap length variable
    - [x] new_has_overlap_var(): Create Boolean for interval overlap
    - [x] new_conditional_var(): Create conditionally equal variable
    - [x] new_count_var(): Create count variable for value occurrences
    - [x] add_if_then_else(): If-then-else constraint for expressions

    Inherited OR-Tools Methods
    --------------------------
    All methods from OR-Tools CpModel are available, including:

    Constraint methods:
    - add(): Add BoundedLinearExpression to model
    - add_linear_constraint(): Add constraint lb <= expr <= ub
    - add_linear_expression_in_domain(): Add expr in domain constraint
    - add_all_different(): Force all expressions to have different values
    - add_element(): Add element constraint expressions[index] == target
    - add_allowed_assignments(): Constrain expressions to allowed tuples
    - add_forbidden_assignments(): Forbid specified tuple assignments
    - add_automaton(): Add automaton constraint
    - add_inverse(): Add inverse constraint
    - add_circuit(): Add circuit constraint from sparse list of arcs
    - add_multiple_circuit(): Add VRP constraint (multiple circuits)
    - add_reservoir_constraint(): Add reservoir/cumulative constraint
    - add_reservoir_constraint_with_active(): Reservoir with active variables
    - add_map_domain(): Map domain values

    Boolean constraints:
    - add_implication(): Add implication constraint
    - add_bool_or(): Add disjunction constraint
    - add_bool_and(): Add conjunction constraint
    - add_bool_xor(): Add XOR constraint
    - add_at_least_one(): At least one expression must be true
    - add_at_most_one(): At most one expression can be true
    - add_exactly_one(): Exactly one expression must be true

    Arithmetic constraints:
    - add_min_equality(): Target equals minimum of expressions
    - add_max_equality(): Target equals maximum of expressions
    - add_division_equality(): Add division equality constraint
    - add_abs_equality(): Add absolute value equality constraint
    - add_modulo_equality(): Add modulo equality constraint
    - add_multiplication_equality(): Add multiplication equality constraint

    Scheduling constraints:
    - add_no_overlap(): Add no-overlap constraint for intervals
    - add_no_overlap_2d(): Add 2D no-overlap constraint
    - add_cumulative(): Add cumulative constraint

    Other resources
    ---------------
    - Scheduling documentation
      https://github.com/google/or-tools/blob/main/ortools/sat/docs/scheduling.md
    - Integer arithmetic documentation
      https://github.com/google/or-tools/blob/main/ortools/sat/docs/integer_arithmetic.md
    """

    def __init__(self):
        super().__init__()

    def add_all_equal(self, variables: list[IntVar | LinearExprT]):
        """
        Enforces that all variables in the list have identical values.

        Creates pairwise equality constraints between consecutive variables,
        ensuring all variables must take the same value in any solution.

        Parameters
        ----------
        variables
            List of integer variables to be set equal.
        """
        for var1, var2 in pairwise(variables):
            self.add(var1 == var2)

    def presence_of(self, interval: IntervalVar):
        """
        Extracts the presence literal from an optional interval variable. This
        is a helper method that will be superseded by ``presence_lterals()``
        when CP-SAT v10 is released.

        Parameters
        ----------
        interval
            The interval variable (optional or non-optional).

        Returns
        -------
        BoolVar
            Boolean variable representing presence, or constant True if not
            optional.
        """
        literals = interval.proto.enforcement_literal
        if len(literals) == 0:  # not an optional
            return self.new_constant(True)

        if len(literals) > 1:  # don't support intervals with multiple literals
            raise NotImplementedError(
                "Intervals with multiple enforcement literals are not "
                "supported."
            )

        # Get the index of the presence literal (first enforcement literal)
        idcs = literals[0]
        if idcs >= 0:
            return self.get_bool_var_from_proto_index(idcs)

        pos_index = -idcs - 1
        return self.get_bool_var_from_proto_index(pos_index).negated()

    # -------------------------------------------------------------------------
    # CP Optimizer scheduling constraints
    # -------------------------------------------------------------------------
    def add_start_at_start(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains the delay between the starts of two interval variables.

        When both intervals are present, the second interval must start exactly
        at start_of(first) + delay. If either interval is absent, the
        constraint is automatically satisfied. Negative delays are permitted.

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.
        delay
            Exact delay between starts (default 0).

        Returns
        -------
        Constraint
            The start-at-start constraint.
        """
        expr = first.start_expr() + delay == second.start_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_start_at_end(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains delay between start of one interval and end of another.

        When both intervals are present, the second interval must end exactly
        at start_of(first) + delay. If either interval is absent, the
        constraint is automatically satisfied. Negative delays are permitted.

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.
        delay
            Exact delay between start of first and end of second (default 0).

        Returns
        -------
        Constraint
            The start-at-end constraint.
        """
        expr = first.start_expr() + delay == second.end_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_start_before_start(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains the minimum delay between starts of two intervals.

        When both intervals are present, the second interval cannot start
        before start_of(first) + delay. This establishes a minimum (rather than
        exact) constraint. If either interval is absent, the constraint is
        automatically satisfied. Negative delays allow the second interval to
        start before the first within the specified bound.

        Parameters
        ----------
        first
            Interval variable starting first.
        second
            Interval variable starting after.
        delay
            Minimal delay between starts (default 0).

        Returns
        -------
        Constraint
            The start-before-start constraint.
        """
        expr = first.start_expr() + delay <= second.start_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_start_before_end(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains minimum delay between start of one and end of another.

        When both intervals are present, the second interval cannot end before
        start_of(first) + delay. This is a minimum constraint allowing
        flexibility in scheduling. If either interval is absent, the constraint
        is automatically satisfied. Negative delays are permitted.

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.
        delay
            Minimal delay (default 0).

        Returns
        -------
        Constraint
            The start-before-end constraint.
        """
        expr = first.start_expr() + delay <= second.end_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_end_at_start(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains delay between end of one interval and start of another.

        When both intervals are present, the second interval must start
        exactly at end_of(first) + delay. This creates a precise sequencing
        constraint. If either interval is absent, the constraint is
        automatically satisfied. Negative delays are permitted.

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.
        delay
            Exact delay between end of first and start of second (default 0).

        Returns
        -------
        Constraint
            The end-at-start constraint.
        """
        expr = first.end_expr() + delay == second.start_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_end_at_end(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains the delay between the ends of two interval variables.

        When both intervals are present, the second interval must end exactly
        at end_of(first) + delay. This provides precise synchronization of
        endpoints. If either interval is absent, the constraint is
        automatically satisfied. Negative delays are permitted.

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.
        delay
            Exact delay between ends (default 0).

        Returns
        -------
        Constraint
            The end-at-end constraint.
        """
        expr = first.end_expr() + delay == second.end_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_end_before_start(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains minimum delay between end of one and start of another.

        When both intervals are present, the second interval cannot start
        before end_of(first) + delay. This establishes a minimum spacing
        requirement. If either interval is absent, the constraint is
        automatically satisfied. Negative delays allow earlier starts within
        bounds.

        Parameters
        ----------
        first
            Interval variable ending first.
        second
            Interval variable starting after.
        delay
            Minimal delay between end and start (default 0).

        Returns
        -------
        Constraint
            The end-before-start constraint.
        """
        expr = first.end_expr() + delay <= second.start_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_end_before_end(
        self, first: IntervalVar, second: IntervalVar, delay: int = 0
    ) -> Constraint:
        """
        Constrains the minimum delay between the ends of two intervals.

        When both intervals are present, the second interval cannot end before
        end_of(first) + delay. This enforces minimum temporal separation of
        endpoints. If either interval is absent, the constraint is
        automatically satisfied. Negative delays are permitted.

        Parameters
        ----------
        first
            Interval variable ending first.
        second
            Interval variable ending after.
        delay
            Minimal delay between ends (default 0).

        Returns
        -------
        Constraint
            The end-before-end constraint.
        """
        expr = first.end_expr() + delay <= second.end_expr()
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.add(expr).only_enforce_if(both_present)

    def add_forbid_start(self, interval: IntervalVar, function):
        """
        Forbids an interval variable to start during specified regions.

        Behavior:
        - [ ] Interval cannot start in regions where step function is non-zero

        - [ ] Step function defines forbidden time windows

        Parameters
        ----------
        interval
            The interval variable.
        function
            Step function defining forbidden regions.
        """
        raise NotImplementedError

    def add_forbid_end(self, interval: IntervalVar, function):
        """
        Forbids an interval variable to end during specified regions.

        Behavior:
        - [ ] Interval cannot end in regions where step function is non-zero

        - [ ] Step function defines forbidden time windows

        Parameters
        ----------
        interval
            The interval variable.
        function
            Step function defining forbidden regions.
        """
        raise NotImplementedError

    def add_forbid_extent(self, interval: IntervalVar, function):
        """
        Forbids an interval variable to overlap with specified regions.

        Behavior:
        - [ ] Interval cannot overlap with regions where step function is
              non-zero
        - [ ] Step function defines forbidden time windows

        Parameters
        ----------
        interval
            The interval variable.
        function
            Step function defining forbidden regions.
        """
        raise NotImplementedError

    def add_start_eval(
        self, interval: IntervalVar, function, absent_value=None
    ):
        """
        Evaluates a segmented function at the start of an interval.

        Behavior:
        - [ ] Evaluates segmented function at interval start time

        - [ ] Returns absent_value if interval is absent
        - [ ] Function is piecewise-defined over time

        Parameters
        ----------
        interval
            The interval variable.
        function
            Segmented function to evaluate.
        absent_value
            Value when interval is absent (default None).

        Returns
        -------
        float
            Float expression representing the evaluated value.
        """
        raise NotImplementedError

    def add_end_eval(self, interval: IntervalVar, function, absent_value=None):
        """
        Evaluates a segmented function at the end of an interval.

        Behavior:
        - [ ] Evaluates segmented function at interval end time

        - [ ] Returns absent_value if interval is absent
        - [ ] Function is piecewise-defined over time

        Parameters
        ----------
        interval
            The interval variable.
        function
            Segmented function to evaluate.
        absent_value
            Value when interval is absent (default None).

        Returns
        -------
        float
            Float expression representing the evaluated value.
        """
        raise NotImplementedError

    def add_size_eval(
        self, interval: IntervalVar, function, absent_value=None
    ):
        """
        Evaluates a segmented function on the size of an interval.

        Behavior:
        - [ ] Evaluates segmented function based on interval size

        - [ ] Returns absent_value if interval is absent
        - [ ] Function maps size values to outputs

        Parameters
        ----------
        interval
            The interval variable.
        function
            Segmented function to evaluate.
        absent_value
            Value when interval is absent (default None).

        Returns
        -------
        float
            Float expression representing the evaluated value.
        """
        raise NotImplementedError

    def add_length_eval(
        self, interval: IntervalVar, function, absent_value=None
    ):
        """
        Evaluates segmented function on the length of an interval.

        Behavior:
        - [ ] Evaluates segmented function based on interval length

        - [ ] Returns absent_value if interval is absent
        - [ ] Function maps length values to outputs

        Parameters
        ----------
        interval
            The interval variable.
        function
            Segmented function to evaluate.
        absent_value
            Value when interval is absent (default None).

        Returns
        -------
        float
            Float expression representing the evaluated value.
        """
        raise NotImplementedError

    def add_span(
        self,
        main: IntervalVar,
        candidates: list[IntervalVar],
        assume_present: bool = False,
    ):
        """
        Creates a span constraint over interval variables.

        The span constraint ensures that when the main interval is present,
        it spans exactly from the earliest start to the latest end of all
        present candidate intervals. The main interval is present if and
        only if at least one candidate interval is present.

        Parameters
        ----------
        main
            Spanning interval variable that covers all present candidates.
        candidates
            List of interval variables to be spanned.
        assume_present
            Assumes that all intervals are present, which uses a more efficient
            formulation.

        Raises
        ------
        ValueError
            If candidates list is empty.
        """
        if not candidates:
            raise ValueError("Candidates list cannot be empty")

        def is_true(var: IntVar) -> bool:
            return list(var.proto.domain) == [1, 1]

        main_pres = self.presence_of(main)
        cand_pres = [self.presence_of(cand) for cand in candidates]
        starts = [cand.start_expr() for cand in candidates]
        ends = [cand.end_expr() for cand in candidates]

        if assume_present or all(is_true(x) for x in [main_pres, *cand_pres]):
            # Shortcut when all intervals are always present. This uses a
            # more efficient formulation.
            self.add_min_equality(main.start_expr(), starts)
            self.add_max_equality(main.end_expr(), ends)
            return

        # Main present <=> at least one candidate present.
        self.add(main_pres <= sum(cand_pres))
        self.add(len(candidates) * main_pres >= sum(cand_pres))

        # Use conditional variables to handle absence in min/max constraints.
        start_var = self.new_conditional_var(main.start_expr(), main_pres)
        start_vars = [
            self.new_conditional_var(
                cand.start_expr(),
                self.presence_of(cand),
                absent_value=MAX_VALUE,
            )
            for cand in candidates
        ]
        self.add_min_equality(start_var, start_vars)

        end_var = self.new_conditional_var(main.end_expr(), main_pres)
        end_vars = [
            self.new_conditional_var(
                cand.end_expr(),
                self.presence_of(cand),
                absent_value=-MAX_VALUE,
            )
            for cand in candidates
        ]
        self.add_max_equality(end_var, end_vars)

    def add_alternative(
        self,
        main: IntervalVar,
        candidates: list[IntervalVar],
        cardinality: int = 1,
    ):
        """
        Creates an alternative constraint between interval variables.

        When the main interval is present, exactly cardinality candidate
        intervals must be selected (made present), and all selected intervals
        must have identical start, size, and end times as the main interval.
        The main interval is absent if and only if all candidate intervals are
        absent. If cardinality is not specified, it defaults to 1, meaning
        exactly one candidate is selected when the main interval is present.

        Parameters
        ----------
        main
            Master interval variable.
        candidates
            List of candidate interval variables to choose from.
        cardinality
            Number of candidates to select (default 1).
        """
        # Select ``cardinality`` intervals from candidates if main is present,
        # otherwise zero.
        presences = [self.presence_of(interval) for interval in candidates]
        self.add(cardinality * self.presence_of(main) == sum(presences))

        # Enforce start/end equality between main and selected candidates.
        for candidate in candidates:
            equal_start = main.start_expr() == candidate.start_expr()
            equal_size = main.size_expr() == candidate.size_expr()
            equal_end = main.end_expr() == candidate.end_expr()

            for expr in [equal_start, equal_size, equal_end]:
                self.add(expr).only_enforce_if(self.presence_of(candidate))

    def add_synchronize(
        self, main: IntervalVar, candidates: list[IntervalVar]
    ):
        """
        Creates a synchronization constraint between interval variables.

        When both the main interval and a candidate interval are present, they
        must start and end at exactly the same times. This creates perfect
        temporal alignment between synchronized intervals. If either interval
        is absent, the synchronization constraint is not enforced.

        Parameters
        ----------
        main
            Main interval variable to synchronize with.
        candidates
            List of candidate interval variables to synchronize.
        """
        for candidate in candidates:
            both_present = [
                self.presence_of(main),
                self.presence_of(candidate),
            ]

            equal_start = main.start_expr() == candidate.start_expr()
            equal_size = main.size_expr() == candidate.size_expr()
            equal_end = main.end_expr() == candidate.end_expr()

            for expr in [equal_start, equal_size, equal_end]:
                self.add(expr).only_enforce_if(both_present)

    def add_isomorphism(
        self,
        array1: list[IntervalVar],
        array2: list[IntervalVar],
        map=None,
        absent_value=None,
    ):
        """
        Creates an isomorphism constraint between two interval sets.

        Behavior:
        - [ ] Ensures ordering and presence patterns match between arrays

        - [ ] Optional mapping defines correspondence between intervals

        - [ ] Absent intervals correspond between structures


        Parameters
        ----------
        array1
            First array of interval variables.
        array2
            Second array of interval variables.
        map
            Optional mapping between arrays (default None).
        absent_value
            Value when interval is absent (default None).
        """
        raise NotImplementedError

    def new_interval_var(
        self,
        start: IntVar | tuple[int, int] = (),
        size: IntVar | tuple[int, int] = (),
        end: IntVar | tuple[int, int] = (),
        optional: BoolVarT | bool = False,
        name: str = "",
    ) -> IntervalVar:
        """
        Creates a new optional interval variable. This helper method simplifies
        the creation of optional interval variables by handling the creation of
        helper variables.

        Parameters
        ----------
        start
            Start variable or (lb, ub) tuple.
        size
            Size variable or (lb, ub) tuple.
        end
            End variable or (lb, ub) tuple.
        optional
            Boolean variable or constant indicating if interval is optional.
            If a Boolean variable is provided, then its interpretation is the
            same as `is_present`.
        name
            Name of the interval variable.
        """
        if not isinstance(start, IntVar):
            start = self.new_int_var(start[0], start[1], f"{name}_start")

        if not isinstance(size, IntVar):
            size = self.new_int_var(size[0], size[1], f"{name}_size")

        if not isinstance(end, IntVar):
            end = self.new_int_var(end[0], end[1], f"{name}_end")

        is_present = optional
        if not isinstance(is_present, BoolVarT):  # then we create var
            if is_present:
                is_present = self.new_bool_var(f"{name}_is_present")
            else:
                is_present = self.new_constant(True)

        return self.new_optional_interval_var(
            start, size, end, is_present, name
        )

    def new_product_var(self, var1: IntVar, var2: IntVar) -> IntVar:
        """
        Creates a new integer variable representing the product of two integer
        variables. Uses optimized implementations for Boolean variables.

        Parameters
        ----------
        var1
            First integer variable.
        var2
            Second integer variable.

        Returns
        -------
        IntVar
            New integer variable representing the product.
        """

        def is_bool_var(var) -> bool:
            return list(var.proto.domain) == [0, 1]

        if is_bool_var(var1) and is_bool_var(var2):
            product_var = self.new_bool_var("")
            self.add_bool_or(~var1, ~var2, product_var)
            self.add_implication(product_var, var1)
            self.add_implication(product_var, var2)
            return product_var

        if not is_bool_var(var1) and not is_bool_var(var2):  # int x int
            domain1, domain2 = var1.proto.domain, var2.proto.domain
            min1, max1 = domain1[0], domain1[-1]
            min2, max2 = domain2[0], domain2[-1]
            corners = [min1 * min2, min1 * max2, max1 * min2, max1 * max2]
            product_var = self.new_int_var(
                # This protects against overflows.
                max(min(corners), -MAX_VALUE),
                min(max(corners), MAX_VALUE),
                "",
            )
            self.add_multiplication_equality(product_var, [var1, var2])
            return product_var

        # One integer variable and one boolean variable.
        # See https://github.com/google/or-tools/blob/main/ortools/sat/docs/integer_arithmetic.md#product-of-a-boolean-variable-and-an-integer-variable # noqa: E501
        int_var, bool_var = (var2, var1) if is_bool_var(var1) else (var1, var2)
        domain = Domain.from_flat_intervals(int_var.proto.domain)
        domain = domain.union_with(Domain(0, 0))  # if bool is false
        product_var = self.new_int_var_from_domain(domain, "")
        self.add(product_var == int_var).only_enforce_if(bool_var)
        self.add(product_var == 0).only_enforce_if(~bool_var)
        return product_var

    def new_max_var(self, *exprs: LinearExprT) -> IntVar:
        """
        Creates a new integer variable representing the maximum of given
        expressions.
        """
        max_var = self.new_int_var(-MAX_VALUE, MAX_VALUE, "")
        self.add_max_equality(max_var, list(exprs))
        return max_var

    def new_min_var(self, *exprs: LinearExprT) -> IntVar:
        """
        Creates a new integer variable representing the minimum of given
        expressions.
        """
        min_var = self.new_int_var(-MAX_VALUE, MAX_VALUE, "")
        self.add_min_equality(min_var, list(exprs))
        return min_var

    def new_step_var(
        self, x: IntVar, domains: list[Domain], values: list[int]
    ) -> IntVar:
        """
        Creates a new integer variable representing a step function of x, i.e.,
        a piecewise constant function.

        A step function maps ranges of input values to specific output values.
        This method creates a variable y such that:
        - When x is in domains[0], then y = values[0]
        - When x is in domains[1], then y = values[1]
        - And so on...

        Parameters
        ----------
        x
            Integer variable to evaluate.
        domains
            List of domains defining the step function.
        values
            List of values corresponding to each domain.

        Returns
        -------
        IntVar
            New integer variable representing the step function value.
        """
        if len(domains) != len(values):
            raise ValueError("domains and values must have the same length")

        y = self.new_int_var_from_domain(Domain.from_values(values), "")
        selected = [self.new_bool_var("") for _ in range(len(domains))]

        for var, domain, value in zip(selected, domains, values):
            cons = self.add_linear_expression_in_domain(x, domain)
            cons.only_enforce_if(var)
            self.add(y == value).only_enforce_if(var)

        self.add_bool_or(selected)
        return y

    def new_convex_pwl_var(
        self,
        x: IntVar,
        breakpoints: list[int],
        rates: list[int],
        initial_value: int = 0,
    ) -> IntVar:
        """
        Creates a new integer variable representing a convex piecewise linear
        function.

        This method creates a convex PWL function by specifying breakpoints
        (where the rate changes) and the rate (slope) in each segment.
        The function is continuous across all breakpoints.

        A convex piecewise linear function can be expressed as:
        ``f(x) = max{a₁*x + b₁, a₂*x + b₂, ..., aₘ*x + bₘ}``
        where ``a₁ ≤ a₂ ≤ ... ≤ aₘ`` (non-decreasing rates).

        For non-convex piecewise functions, use new_step_var() instead.

        Parameters
        ----------
        x
            The input variable for the piecewise linear function.
        breakpoints
            List of x-values where the rate changes. Must have the same
            length as rates. The function starts at breakpoints[0].
        rates
            List of rates (slopes) for each segment. rates[i] is the rate
            from breakpoints[i] onwards. Must be non-decreasing for convexity.
        initial_value
            The value of the function at breakpoints[0]. Defaults to 0.

        Returns
        -------
        IntVar
            New integer variable representing the convex PWL function value.

        Raises
        ------
        ValueError
            If rates are not non-decreasing (non-convex function).
        ValueError
            If lengths of breakpoints and rates don't match.

        Examples
        --------
        Earliness-tardiness cost function with due date window [5, 15],
        earliness cost 8 and tardiness cost 12.

        >>> x = model.new_int_var(0, 20, "completion")
        >>> cost = model.new_convex_pwl_var(
        ...     x,
        ...     breakpoints=[0, 5, 15],
        ...     rates=[-8, 0, 12]
        ... )

        Absolute value function |x|:

        >>> x = model.new_int_var(-10, 10, "x")
        >>> abs_x = model.new_convex_pwl_var(
        ...     x,
        ...     breakpoints=[-10, 0],
        ...     rates=[-1, 1],
        ...     initial_value=10
        ... )
        """
        if len(breakpoints) != len(rates):
            msg = "breakpoints and rates must have the same length"
            raise ValueError(msg)

        for rate1, rate2 in pairwise(rates):
            if rate1 > rate2:
                raise ValueError("Rates must be non-decreasing to be convex.")

        # Compute intercepts to ensure continuity at each breakpoint.
        intercepts = [initial_value - rates[0] * breakpoints[0]]
        for idx in range(len(rates) - 1):
            bp = breakpoints[idx + 1]
            intercept = (rates[idx] - rates[idx + 1]) * bp + intercepts[idx]
            intercepts.append(intercept)

        # Each segment variable represent the value of a linear function f(x)
        # as defined by the rates and intercepts.
        segment_vars = [
            self.new_conditional_var(rate * x + intercept)
            for rate, intercept in zip(rates, intercepts)
        ]

        # The piecewise linear function is convex by design, so at any point x,
        # the maximum value across all segments gives the correct PWL value.
        return self.new_max_var(*segment_vars)

    def new_overlap_var(
        self, first: IntervalVar, second: IntervalVar
    ) -> IntVar:
        """
        Creates a new integer variable representing the overlap length
        between two intervals.

        The overlap length is the duration during which both intervals are
        active simultaneously. It is computed as:
        ``max(0, min(end_first, end_second) - max(start_first, start_second))``

        If either interval is absent, the overlap is 0.

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.

        Returns
        -------
        IntVar
            New integer variable representing the overlap length (>= 0).
        """
        min_end = self.new_min_var(first.end_expr(), second.end_expr())
        max_start = self.new_max_var(first.start_expr(), second.start_expr())

        # both present => overlap = raw_overlap | otherwise overlap = 0.
        overlap = self.new_max_var(0, min_end - max_start)
        both_present = [self.presence_of(first), self.presence_of(second)]
        return self.new_conditional_var(overlap, both_present, absent_value=0)

    def new_has_overlap_var(
        self, first: IntervalVar, second: IntervalVar
    ) -> BoolVarT:
        """
        Creates a new Boolean variable indicating whether two intervals
        overlap.

        Two intervals overlap if they are both active at the same time,
        meaning neither starts after the other ends. The overlap Boolean
        is true when: ``start_first < end_second AND start_second < end_first``

        This implements the pattern from OR-Tools documentation using three
        Boolean variables linked by clauses and implications for efficient
        propagation.

        If either interval is absent, the result is False (no overlap).

        Parameters
        ----------
        first
            First interval variable.
        second
            Second interval variable.

        Returns
        -------
        BoolVarT
            Boolean variable that is True if intervals overlap, False
            otherwise.
        """
        after = self.new_bool_var("")  # first after second
        true_expr = first.start_expr() >= second.end_expr()
        false_expr = first.start_expr() < second.end_expr()
        self.add_if_then_else(after, true_expr, false_expr)

        before = self.new_bool_var("")  # first before second
        true_expr = first.end_expr() <= second.start_expr()
        false_expr = first.end_expr() > second.start_expr()
        self.add_if_then_else(before, true_expr, false_expr)

        # Define ``has_overlap`` by linking with ``after`` and ``before``,
        # but only if both intervals are present.
        has_overlap = self.new_bool_var("")
        both_present = [self.presence_of(first), self.presence_of(second)]

        for constraint in [
            self.add_bool_or(after, before, has_overlap),
            self.add_implication(after, ~has_overlap),
            self.add_implication(before, ~has_overlap),
        ]:
            constraint.only_enforce_if(both_present)

        # Otherwise, ``has_overlap`` should just be false.
        self.add(has_overlap <= self.presence_of(first))
        self.add(has_overlap <= self.presence_of(second))

        return has_overlap

    def new_conditional_var(
        self,
        expr: LinearExprT,
        condition: BoolVarT | list[BoolVarT] = True,
        absent_value: int | None = None,
    ) -> IntVar:
        """
        Creates a new variable that conditionally equals an expression.

        When all conditions are true, the new variable equals the expression.
        When any condition is false, the new variable is unconstrained within
        its domain.

        Parameters
        ----------
        expr
            The source variable or linear expression to conditionally sync
            with.
        condition
            Boolean variable or list of Boolean variables. The new variable
            equals x if and only if all conditions are true (AND logic).
        absent_value
            Value to assign when condition is false. If None, the new variable
            is unconstrained within the domain of x.

        Returns
        -------
        IntVar
            A new integer variable constrained to equal x when all conditions
            are true.
        """
        y = self.new_int_var(-MAX_VALUE, MAX_VALUE, "")

        if absent_value is not None:
            self.add_if_then_else(condition, y == expr, y == absent_value)
        else:
            if isinstance(condition, BoolVarT):
                condition = [condition]
            self.add(y == expr).only_enforce_if(condition)

        return y

    def new_count_var(self, array: list[IntVar], val: int | IntVar) -> IntVar:
        """
        Creates a new integer variable representing the number of occurrences
        of a value in an array.

        Parameters
        ----------
        array
            Array of variables to search.
        val
            Value to count (can be constant or variable).

        Returns
        -------
        IntVar
            Integer variable equal to the count of val in array.
        """
        size = len(array)
        count = self.new_int_var(0, size, "")
        is_equal = [self.new_bool_var("") for _ in range(size)]

        for idx in range(size):
            self.add(array[idx] == val).only_enforce_if(is_equal[idx])
            self.add(array[idx] != val).only_enforce_if(~is_equal[idx])

        self.add(count == sum(is_equal))
        return count

    def add_if_then_else(
        self,
        condition: BoolVarT | list[BoolVarT],
        then_expr: LinearExprT,
        else_expr: LinearExprT,
    ):
        """
        Adds an if-then-else constraint to the model.

        Parameters
        ----------
        condition
            One or more Boolean variables. If multiple, then it evaluates
            True iff all variables are True (using AND logic).
        then_expr
            Expression enforced if condition is true.
        else_expr
            Expression enforced if condition is false.
        """
        if isinstance(condition, BoolVarT):
            condition = [condition]

        self.add(then_expr).only_enforce_if(condition)

        for var in condition:  # enforce else branch if one var is False
            self.add(else_expr).only_enforce_if(~var)

    def add_cumulative_profiles(
        self,
        intervals: list[IntervalVar],
        demands: list[IntVar],
        max_profile: list[tuple[int, int]],
        min_profile: list[tuple[int, int]] | None = None,
    ):
        """
        Adds a cumulative constraint with capacity profiles.

        Parameters
        ----------
        intervals
            List of interval variables.
        demands
            List of demand variables corresponding to intervals.
        max_profile
            List of (time, capacity) tuples defining the maximum capacity
            profile over time. Assumes that time points are sorted in
            increasing order, and that capacity applies from the given time
            until the next time point (``MAX_VALUE`` if last point).
        min_profile
            List of (time, capacity) tuples defining the minimum capacity
            profile over time. Assumes that time points are sorted in
            increasing order, and that capacity applies from the given time
            until the next time point (``MAX_VALUE`` if last point).
        """
        times, capacities = zip(*max_profile)
        for t1, t2 in pairwise(times):
            if t1 >= t2:
                raise ValueError("Time points in profile must be increasing.")

        # To model the max profile, we introduce fixed, dummy intervals that
        # consume load equal to the difference between the maximum capacity
        # and the desired profile level.
        dummy = []
        occupied = []
        max_capacity = max(capacities)

        for idx in range(len(times)):
            load = max_capacity - capacities[idx]
            if load == 0:
                # If this is zero, then the maximum capacity is allowed in this
                # segment, so no need to add a dummy interval.
                continue

            start = times[idx]
            end = times[idx + 1] if idx + 1 < len(times) else MAX_VALUE
            interval = self.new_interval_var(start, end - start, end, "")
            dummy.append(interval)
            occupied.append(load)

        self.add_cumulative(
            [*intervals, *dummy],
            [*demands, *occupied],
            max_capacity,
        )

        if min_profile is None:
            return

        # TODO check that min load cannot be larger than max load. This hangs.
        # TODO understand if min load can be added without max load

        # Now we start modelling min load profiles using "complement capacity".
        # Present intervals contribute to this capacity over the entire domain.
        complement_capacity = self.new_int_var(0, sum(demands), "")
        selected_demands = [
            demand * self.presence_of(interval)
            for interval, demand in zip(intervals, demands)
        ]
        self.add(complement_capacity == sum(selected_demands))

        # We introduce prefix and suffix intervals for each interval.
        prefixes = [
            self.new_optional_interval_var(
                start=0,
                size=interval.start_expr(),
                end=interval.start_expr(),
                is_present=self.presence_of(interval),
                name=f"prefix_{interval.name}",
            )
            for interval in intervals
        ]
        suffixes = [
            self.new_optional_interval_var(
                start=interval.end_expr(),
                size=MAX_VALUE - interval.end_expr(),
                end=MAX_VALUE,
                is_present=self.presence_of(interval),
                name=f"suffix_{interval.name}",
            )
            for interval in intervals
        ]

        times, min_loads = zip(*min_profile)
        for t1, t2 in pairwise(times):
            if t1 >= t2:
                raise ValueError("Time points in profile must be increasing.")

        # We also introduce fixed, dummy intervals that consume load equal to
        # the minimum load in this segment.
        dummy = []
        occupied = []

        for idx in range(len(times)):
            if min_loads[idx] == 0:
                continue  # nothing to do

            start = times[idx]
            end = times[idx + 1] if idx + 1 < len(times) else MAX_VALUE
            interval = self.new_interval_var(start, end - start, end, "")
            dummy.append(interval)
            occupied.append(min_loads[idx])

        # The prefix and suffix intervals directly consume the demand, so
        # effectively there is only capacity available on the domain
        # [start, end). The dummy intervals force that enough effective
        # capacity is created to satisfy the minimum load profile.
        self.add_cumulative(
            [*prefixes, *suffixes, *dummy],
            [*demands, *demands, *occupied],
            complement_capacity,
        )
