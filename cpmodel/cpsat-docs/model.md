[home](README.md) | [boolean logic](boolean_logic.md) | [integer arithmetic](integer_arithmetic.md) | [channeling constraints](channeling.md) | [scheduling](scheduling.md) | [Using the CP-SAT solver](solver.md) | [Model manipulation](model.md) | [Troubleshooting](troubleshooting.md) | [Python API](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)
----------------- | --------------------------------- | ------------------------------------------- | --------------------------------------- | --------------------------- | ------------------------------------ | ------------------------------ | ------------------------------------- | -----------------------------------------------------------------------------------
# Model manipulation

https://developers.google.com/optimization/

## Introduction

In all languages, the CpModel class is a thin wrapper around a
[protocol buffer](http://developers.google.com/protocol-buffers/) object
[cp_model.proto](../cp_model.proto).

Some functionalities require using the cp_model protobuf directly. To write code
that manipulates this protobuf, one must understand how modeling objects
(variables, constraints) are mapped onto the protobuf.

The fundamental idea is that the cp_model protobuf object contains a list of
variables and a list of constraints. Constraints are built with variables and
reference them using their indices in the list of variables.

In all languages, the `IntVar` class has a method to query their index in the
model list of variables:

-   **C++**: `var.index()`
-   **Python**: `var.Index()`
-   **Java**: `var.getIndex()`
-   **C#**: `var.Index` or `var.GetIndex()`
-   **Go**: `var.Index()`

The implementation of Boolean literals differs across languages.

-   **C++**: The `BoolVar` class is a separate class from the `IntVar` class. A
    `BoolVar` object can implicitly be cast to an `IntVar` object. A `BoolVar`
    object has two important methods: `index()` and `Not()`. `Not()` returns
    another `BoolVar` with a different index: `b.Not().index() = -b.index() -
    1`.
-   **Python**: There is no `BoolVar` class. A Boolean variable is defined as an
    `IntVar` with a Boolean domain (0 or 1). The `Not()` method returns a
    different class. Both the `IntVar` class and the negation class implement
    `Index()` and `Not()`.
-   **Java**: There is no `BoolVar` class. A Boolean variable is defined as an
    `IntVar` with a Boolean domain (0 or 1). Boolean variables and their
    negation implement the `Literal` interface. This interface defines
    `getIndex()` and `not()` methods.
-   **C#**: Boolean variables are defined as an `IntVar` with a Boolean domain
    (0 or 1). Boolean variables and their negations implement the `ILiteral`
    interface. This interface defines `GetIndex()` and `Not()` methods.
-   **Go**: The `BoolVar` class is a separate class from the `IntVar` class. A
    `BoolVar` object has two important methods: `Not()` and `Index()`. `Not()`
    returned another `BoolVar` with a different index: `b.Not.Index() =
    -b.Index() - 1`

## Solution hinting

A solution is a partial assignment of variables to values that the search will
try to stick to. It is meant to guide the search with external knowledge towards
good solutions.

The `CpModelProto` message has a `solution_hint` field. This field is a
`PartialVariableAssignment` message that contains two parallel vectors (variable
indices and hint values).

Adding solution hinting to a model implies filling these two fields. This is
done by the `addHint`, `AddHint`, or `SetHint` methods.

Some remarks:

-   A solution hint is not a hard constraint. The solver will try to use it in
    search for a while, and then gradually revert to its default search
    technique.
-   It's OK to have an infeasible solution hint. It can still be helpful in some
    repair procedures, where one wants to identify a solution close to a
    previously violated state.
-   Solution hints don't need to use all variables: partial solution hints are
    fine.

### Python code

```python
# Snippet from ortools/sat/samples/solution_hinting_sample_sat.py
from ortools.sat.python import cp_model


def solution_hinting_sample_sat():
  """Showcases solution hinting."""
  # Creates the model.
  model = cp_model.CpModel()

  # Creates the variables.
  num_vals = 3
  x = model.new_int_var(0, num_vals - 1, 'x')
  y = model.new_int_var(0, num_vals - 1, 'y')
  z = model.new_int_var(0, num_vals - 1, 'z')

  # Creates the constraints.
  model.add(x != y)

  model.maximize(x + 2 * y + 3 * z)

  # Solution hinting: x <- 1, y <- 2
  model.add_hint(x, 1)
  model.add_hint(y, 2)

  # Creates a solver and solves.
  solver = cp_model.CpSolver()
  solution_printer = cp_model.VarArrayAndObjectiveSolutionPrinter([x, y, z])
  status = solver.solve(model, solution_printer)

  print(f'Status = {solver.status_name(status)}')
  print(f'Number of solutions found: {solution_printer.solution_count}')


solution_hinting_sample_sat()
```

## Model copy

The `CpModel` classes supports deep copy from a previous model. This is useful
to solve variations of a base model. The trick is to recover the copies of the
variables in the original model to be able to manipulate the new model. This is
illustrated in the following examples.

### Python code

The deep copy python mechanism relies on the
[`copy` Python Standard Library](https://docs.python.org/3/library/copy.html).

```python
# Snippet from ortools/sat/samples/clone_model_sample_sat.py
import copy

from ortools.sat.python import cp_model


def clone_model_sample_sat():
  """Showcases cloning a model."""
  # Creates the model.
  model = cp_model.CpModel()

  # Creates the variables.
  num_vals = 3
  x = model.new_int_var(0, num_vals - 1, 'x')
  y = model.new_int_var(0, num_vals - 1, 'y')
  z = model.new_int_var(0, num_vals - 1, 'z')

  # Creates the constraints.
  model.add(x != y)

  model.maximize(x + 2 * y + 3 * z)

  # Creates a solver and solves.
  solver = cp_model.CpSolver()
  status = solver.solve(model)

  if status == cp_model.OPTIMAL:
    print(
        'Optimal value of the original model: {}'.format(solver.objective_value)
    )

  # Creates a dictionary holding the model and the variables you want to use.
  to_clone = {
      'model': model,
      'x': x,
      'y': y,
      'z': z,
  }

  # Deep copy the dictionary.
  clone = copy.deepcopy(to_clone)

  # Retrieve the cloned model and variables.
  cloned_model: cp_model.CpModel = clone['model']
  cloned_x = clone['x']
  cloned_y = clone['y']
  cloned_model.add(cloned_x + cloned_y <= 1)

  status = solver.solve(cloned_model)

  if status == cp_model.OPTIMAL:
    print(
        'Optimal value of the modified model: {}'.format(solver.objective_value)
    )


clone_model_sample_sat()
```
