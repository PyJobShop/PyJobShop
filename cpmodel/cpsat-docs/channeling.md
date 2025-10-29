[home](README.md) | [boolean logic](boolean_logic.md) | [integer arithmetic](integer_arithmetic.md) | [channeling constraints](channeling.md) | [scheduling](scheduling.md) | [Using the CP-SAT solver](solver.md) | [Model manipulation](model.md) | [Troubleshooting](troubleshooting.md) | [Python API](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)
----------------- | --------------------------------- | ------------------------------------------- | --------------------------------------- | --------------------------- | ------------------------------------ | ------------------------------ | ------------------------------------- | -----------------------------------------------------------------------------------
# Channeling constraints

https://developers.google.com/optimization/

A *channeling constraint* links variables inside a model. They're used when you
want to express a complicated relationship between variables, such as "if this
variable satisfies a condition, force another variable to a particular value".

Channeling is usually implemented using *half-reified* linear constraints: one
constraint implies another (a &rarr; b), but not necessarily the other way
around (a &larr; b).

## If-Then-Else expressions

Let's say you want to implement the following: "If *x* is less than 5, set *y*
to 0. Otherwise, set *y* to 10-*x*". You can do this creating an intermediate
boolean variable *b* that is true if *x* is greater than or equal to 5, and
false otherwise:

*b* implies *y* == 10 - *x*

not(*b*) implies *y* == 0

These are implemented using the `OnlyEnforceIf` method as shown below.

### Python code

```python
# Snippet from ortools/sat/samples/channeling_sample_sat.py
"""Link integer constraints together."""


from ortools.sat.python import cp_model


class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
  """Print intermediate solutions."""

  def __init__(self, variables: list[cp_model.IntVar]):
    cp_model.CpSolverSolutionCallback.__init__(self)
    self.__variables = variables

  def on_solution_callback(self) -> None:
    for v in self.__variables:
      print(f'{v}={self.value(v)}', end=' ')
    print()


def channeling_sample_sat():
  """Demonstrates how to link integer constraints together."""

  # Create the CP-SAT model.
  model = cp_model.CpModel()

  # Declare our two primary variables.
  x = model.new_int_var(0, 10, 'x')
  y = model.new_int_var(0, 10, 'y')

  # Declare our intermediate boolean variable.
  b = model.new_bool_var('b')

  # Implement b == (x >= 5).
  model.add(x >= 5).only_enforce_if(b)
  model.add(x < 5).only_enforce_if(~b)

  # Create our two half-reified constraints.
  # First, b implies (y == 10 - x).
  model.add(y == 10 - x).only_enforce_if(b)
  # Second, not(b) implies y == 0.
  model.add(y == 0).only_enforce_if(~b)

  # Search for x values in increasing order.
  model.add_decision_strategy(
      [x], cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
  )

  # Create a solver and solve with a fixed search.
  solver = cp_model.CpSolver()

  # Force the solver to follow the decision strategy exactly.
  solver.parameters.search_branching = cp_model.FIXED_SEARCH
  # Enumerate all solutions.
  solver.parameters.enumerate_all_solutions = True

  # Search and print out all solutions.
  solution_printer = VarArraySolutionPrinter([x, y, b])
  solver.solve(model, solution_printer)


channeling_sample_sat()
```

## Computing the index of the first Boolean variable set to true

A common request is to compute the index of the first Boolean variable set to
true. It can be encoded using a min_equality constraint. The index will be set
to the number of Boolean variables if they are all false.

### Python code

```python
# Snippet from ortools/sat/samples/index_first_boolvar_true_sample_sat.py
"""Compute the index of the first Boolean variable set to true."""

from ortools.sat.python import cp_model


class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
  """Print intermediate solutions."""

  def __init__(self, index: cp_model.IntVar, boolvars: list[cp_model.IntVar]):
    cp_model.CpSolverSolutionCallback.__init__(self)
    self.__index = index
    self.__boolvars = boolvars

  def on_solution_callback(self) -> None:
    line = ''
    for v in self.__boolvars:
      line += f'{self.value(v)}'
    line += f' -> {self.value(self.__index)}'
    print(line)


def index_of_first_bool_at_true_sample_sat():
  """Compute the index of the first Boolean variable set to true."""

  # Model.
  model = cp_model.CpModel()

  # Variables
  num_bool_vars = 5
  bool_vars = [model.new_bool_var(f'{i}') for i in range(num_bool_vars)]
  index = model.new_int_var(0, num_bool_vars, 'index')

  # Channeling between the index and the Boolean variables.
  model.add_min_equality(
      index,
      [
          num_bool_vars - bool_vars[i] * (num_bool_vars - i)
          for i in range(num_bool_vars)
      ],
  )

  # Flip bool_vars in increasing order.
  model.add_decision_strategy(
      bool_vars, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
  )

  # Create a solver and solve with a fixed search.
  solver = cp_model.CpSolver()

  # Force the solver to follow the decision strategy exactly.
  solver.parameters.search_branching = cp_model.FIXED_SEARCH

  # Search and print out all solutions.
  solver.parameters.enumerate_all_solutions = True
  solution_printer = VarArraySolutionPrinter(index, bool_vars)
  solver.solve(model, solution_printer)


index_of_first_bool_at_true_sample_sat()
```

This displays the following:

```
00000 -> 5
00001 -> 4
00010 -> 3
00011 -> 3
00100 -> 2
00101 -> 2
00110 -> 2
00111 -> 2
01000 -> 1
01001 -> 1
01010 -> 1
01011 -> 1
01100 -> 1
01101 -> 1
01110 -> 1
01111 -> 1
10000 -> 0
10001 -> 0
10010 -> 0
10011 -> 0
10100 -> 0
10101 -> 0
10110 -> 0
10111 -> 0
11000 -> 0
11001 -> 0
11010 -> 0
11011 -> 0
11100 -> 0
11101 -> 0
11110 -> 0
11111 -> 0
```

## A bin-packing problem

As another example of a channeling constraint, consider a bin packing problem in
which one part of the model computes the load of each bin, while another
maximizes the number of bins under a given threshold. To implement this, you can
*channel* the load of each bin into a set of boolean variables, each indicating
whether it's under the threshold.

To make this more concrete, let's say you have 10 bins of capacity 100, and
items to pack into the bins. You would like to maximize the number of bins that
can accept one emergency load of size 20.

To do this, you need to maximize the number of bins that have a load less
than 80. In the code below, channeling is used to link the *load* and *slack*
variables together:

### Python code

```python
# Snippet from ortools/sat/samples/binpacking_problem_sat.py
"""Solves a binpacking problem using the CP-SAT solver."""


from ortools.sat.python import cp_model


def binpacking_problem_sat():
  """Solves a bin-packing problem using the CP-SAT solver."""
  # Data.
  bin_capacity = 100
  slack_capacity = 20
  num_bins = 5
  all_bins = range(num_bins)

  items = [(20, 6), (15, 6), (30, 4), (45, 3)]
  num_items = len(items)
  all_items = range(num_items)

  # Model.
  model = cp_model.CpModel()

  # Main variables.
  x = {}
  for i in all_items:
    num_copies = items[i][1]
    for b in all_bins:
      x[(i, b)] = model.new_int_var(0, num_copies, f'x[{i},{b}]')

  # Load variables.
  load = [model.new_int_var(0, bin_capacity, f'load[{b}]') for b in all_bins]

  # Slack variables.
  slacks = [model.new_bool_var(f'slack[{b}]') for b in all_bins]

  # Links load and x.
  for b in all_bins:
    model.add(load[b] == sum(x[(i, b)] * items[i][0] for i in all_items))

  # Place all items.
  for i in all_items:
    model.add(sum(x[(i, b)] for b in all_bins) == items[i][1])

  # Links load and slack through an equivalence relation.
  safe_capacity = bin_capacity - slack_capacity
  for b in all_bins:
    # slack[b] => load[b] <= safe_capacity.
    model.add(load[b] <= safe_capacity).only_enforce_if(slacks[b])
    # not(slack[b]) => load[b] > safe_capacity.
    model.add(load[b] > safe_capacity).only_enforce_if(~slacks[b])

  # Maximize sum of slacks.
  model.maximize(sum(slacks))

  # Solves and prints out the solution.
  solver = cp_model.CpSolver()
  status = solver.solve(model)
  print(f'solve status: {solver.status_name(status)}')
  if status == cp_model.OPTIMAL:
    print(f'Optimal objective value: {solver.objective_value}')
  print('Statistics')
  print(f'  - conflicts : {solver.num_conflicts}')
  print(f'  - branches  : {solver.num_branches}')
  print(f'  - wall time : {solver.wall_time}s')


binpacking_problem_sat()
```
