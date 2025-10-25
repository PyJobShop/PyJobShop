# https://github.com/google/or-tools/blob/main/ortools/sat/docs/integer_arithmetic.md
# https://groups.google.com/g/or-tools-discuss/c/PYIIj1mEr9E
# Snippet from ortools/sat/samples/earliness_tardiness_cost_sample_sat.py
"""Encodes a convex piecewise linear function."""

from ortools.sat.python import cp_model


class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    """Print intermediate solutions."""

    def __init__(self, variables: list[cp_model.IntVar]):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables

    def on_solution_callback(self) -> None:
        for v in self.__variables:
            print(f"{v}={self.value(v)}", end=" ")
        print()


def main():
    early_date = 5
    early_cost = 8
    late_date = 15
    late_cost = 12
    MAX_VALUE = 2**32

    model = cp_model.CpModel()

    # Declare our primary variable - the completion date of a task.
    completion = model.new_int_var(0, 20, "x")

    # Create the expression variable and implement the piecewise linear
    # function as a function of the completion date. The function is:
    #
    #  \        /
    #   \______/
    #   ed    ld
    #
    cost = model.new_int_var(0, MAX_VALUE, "expr")

    # First segment - earliness cost.
    segment1 = model.new_int_var(-MAX_VALUE, MAX_VALUE, "s1")
    model.add(segment1 == early_cost * (early_date - completion))

    # Second segment - no cost.
    segment2 = 0

    # Third segment - lateness cost.
    segment3 = model.new_int_var(-MAX_VALUE, MAX_VALUE, "s3")
    model.add(segment3 == late_cost * (completion - late_date))

    # Link together the cost and the segments using a max equality.
    model.add_max_equality(cost, [segment1, segment2, segment3])

    # Search for x values in increasing order: this will show us nicely what
    # the cost is for each x.
    model.add_decision_strategy(
        [completion],
        cp_model.CHOOSE_FIRST,
        cp_model.SELECT_MIN_VALUE,
    )

    solver = cp_model.CpSolver()
    solver.parameters.search_branching = cp_model.FIXED_SEARCH
    solver.parameters.enumerate_all_solutions = True

    printer = VarArraySolutionPrinter([completion, cost])
    solver.solve(model, printer)


main()
