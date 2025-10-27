from ortools.sat.python.cp_model import Constraint, CpModel, IntervalVar


class CpModelPlus(CpModel):
    """
    Extended CP Model with scheduling constraint methods from docplex.

    This class extends OR-Tools' CpModel with additional scheduling methods
    similar to those available in IBM's docplex CP Modeler, see below:
    https://ibmdecisionoptimization.github.io/docplex-doc/cp/docplex.cp.modeler.py.html

    Implementation Status
    ---------------------
    - [x] presence_of(): Extract presence literal from optional intervals
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
    - [ ] add_overlap_length(): Compute overlap length between intervals
    - [ ] add_start_eval(): Evaluate function at interval start
    - [ ] add_end_eval(): Evaluate function at interval end
    - [ ] add_size_eval(): Evaluate function on interval size
    - [ ] add_length_eval(): Evaluate function on interval length
    - [-] add_span(): Span constraint (missing absent interval handling)
    - [x] add_alternative(): Alternative constraint with cardinality
    - [ ] add_synchronize(): Synchronization constraint between intervals
    - [ ] add_isomorphism(): Isomorphism constraint between interval sets
    """

    def __init__(self):
        super().__init__()

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

        # Get the index of the presence literal (first enforcement literal)
        idcs = literals[0]
        if idcs >= 0:
            return self.get_bool_var_from_proto_index(idcs)

        pos_index = -idcs - 1
        return self.get_bool_var_from_proto_index(pos_index).negated()

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

    def add_overlap_length(self, a: IntervalVar, b: IntervalVar):
        """
        Computes the length of overlap between two interval variables.

        Behavior:
        - [ ] Returns length of time during which both intervals are active

        - [ ] Returns zero if intervals do not overlap
        - [ ] Handles absent intervals appropriately

        Parameters
        ----------
        a
            First interval variable.
        b
            Second interval variable.

        Returns
        -------
        int
            Integer expression representing overlap length.
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
        self, main: IntervalVar, candidates: list[IntervalVar]
    ) -> tuple[Constraint, Constraint]:
        """
        Creates a span constraint over interval variables.

        Behavior:
        - [x] When main interval is present: its start equals the minimum
              start of all present candidate intervals
        - [x] When main interval is present: its end equals the maximum end
              of all present candidate intervals
        - [ ] Handling of absent main and candidate intervals.

        Parameters
        ----------
        main
            Spanning interval variable.
        candidates
            List of interval variables to be spanned.

        Returns
        -------
        tuple[Constraint, Constraint]
            The start and end span constraints.
        """
        starts = [candidate.start_expr() for candidate in candidates]
        ends = [candidate.end_expr() for candidate in candidates]
        cons1 = self.add_min_equality(main.start_expr(), starts)
        cons2 = self.add_max_equality(main.end_expr(), ends)
        return cons1, cons2

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

        Behavior:
        - [ ] All present intervals in candidates start together with main
        - [ ] All present intervals in candidates end together with main
        - [ ] Creates tight synchronization with identical start/end times
              when present

        Parameters
        ----------
        main
            Main interval variable to synchronize with.
        candidates
            List of candidate interval variables to synchronize.
        """
        raise NotImplementedError

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
