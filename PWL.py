"""
https://github.com/google/or-tools/blob/main/ortools/sat/docs/integer_arithmetic.md
Example demonstrating how to encode a convex piecewise linear function.

References
----------
- https://groups.google.com/g/or-tools-discuss/c/PYIIj1mEr9E
- ortools/sat/samples/earliness_tardiness_cost_sample_sat.py
"""

from ortools.sat.python import cp_model
from ortools.sat.python.cp_model import IntVar

MAX_VALUE = 2**32


class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables: list[IntVar]):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.__variables = variables

    def on_solution_callback(self):
        for v in self.__variables:
            print(f"{v}={self.value(v)}", end=" ")
        print()


def segment_var(model: cp_model.CpModel, a: int, b: int, x: IntVar) -> IntVar:
    var = model.new_int_var(-MAX_VALUE, MAX_VALUE, "")
    model.add(var == a * x + b)
    return var


def pwl_var(
    model: cp_model.CpModel, segment_vars: list[IntVar], name: str
) -> IntVar:
    var = model.new_int_var(-MAX_VALUE, MAX_VALUE, name)
    model.add_max_equality(var, segment_vars)
    return var


def main():
    early_date = 5
    early_cost = 8
    late_date = 15
    late_cost = 12

    model = cp_model.CpModel()

    # Declare our primary variable - the completion date of a task.
    completion = model.new_int_var(0, 40, "x")

    # Create the expression variable and implement the piecewise linear
    # function as a function of the completion date. The function is:
    #
    #  \        /
    #   \______/
    #   ed    ld
    #

    # First segment - earliness cost.
    a = -early_cost
    b = early_cost * early_date
    segment1 = segment_var(model, a, b, completion)

    # Second segment - no cost.
    segment2 = segment_var(model, 0, 0, completion)

    # Third segment - lateness cost.
    a = late_cost
    b = -late_cost * late_date
    segment3 = segment_var(model, a, b, completion)

    # Link together the cost and the segments using a max equality. Because of
    # convexity, the cost takes on the right value of each segment.
    segments = [segment1, segment2, segment3]
    cost = pwl_var(model, segments, name="cost")

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
