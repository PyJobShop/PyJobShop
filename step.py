"""
Implements a step function using OR-Tools CP-SAT solver.
Snippet from ortools/sat/samples/step_function_sample_sat.py
"""

from ortools.sat.python.cp_model import (
    CHOOSE_FIRST,
    FIXED_SEARCH,
    SELECT_MIN_VALUE,
    CpModel,
    CpSolver,
    CpSolverSolutionCallback,
    Domain,
    IntVar,
)


class VarArraySolutionPrinter(CpSolverSolutionCallback):
    def __init__(self, variables: list[IntVar]):
        CpSolverSolutionCallback.__init__(self)
        self.__variables = variables

    def on_solution_callback(self) -> None:
        for v in self.__variables:
            print(f"{v}={self.value(v)}", end=" ")
        print()


def step_function_sample_sat():
    model = CpModel()

    # Declare our primary variable.
    x = model.new_int_var(0, 20, "x")
    y = model.new_int_var(0, 3, "y")

    # Create the expression variable and implement the step function
    # Note it is not defined for x == 2.
    #
    #        -               3
    # -- --      ---------   2
    #                        1
    #      -- ---            0
    # 0 ================ 20
    #

    # expr == 0 on [5, 6] U [8, 10]
    b0 = model.new_bool_var("b0")
    domain0 = Domain.from_intervals([(5, 6), (8, 10)])
    model.add_linear_expression_in_domain(x, domain0).only_enforce_if(b0)
    model.add(y == 0).only_enforce_if(b0)

    # expr == 2 on [0, 1] U [3, 4] U [11, 20]
    b2 = model.new_bool_var("b2")
    domain2 = Domain.from_intervals([(0, 1), (3, 4), (11, 20)])
    model.add_linear_expression_in_domain(x, domain2).only_enforce_if(b2)
    model.add(y == 2).only_enforce_if(b2)

    # expr == 3 when x == 7
    b3 = model.new_bool_var("b3")
    domain3 = Domain.from_intervals([(7, 7)])
    model.add_linear_expression_in_domain(x, domain3).only_enforce_if(b3)
    model.add(y == 3).only_enforce_if(b3)

    # At least one bi is true. (we could use an exactly one constraint).
    model.add_bool_or(b0, b2, b3)

    # Search for x values in increasing order.
    model.add_decision_strategy([x], CHOOSE_FIRST, SELECT_MIN_VALUE)

    solver = CpSolver()
    solver.parameters.search_branching = FIXED_SEARCH
    solver.parameters.enumerate_all_solutions = True

    printer = VarArraySolutionPrinter([x, y])
    solver.solve(model, printer)


step_function_sample_sat()
