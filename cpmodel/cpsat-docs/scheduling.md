[home](README.md) | [boolean logic](boolean_logic.md) | [integer arithmetic](integer_arithmetic.md) | [channeling constraints](channeling.md) | [scheduling](scheduling.md) | [Using the CP-SAT solver](solver.md) | [Model manipulation](model.md) | [Troubleshooting](troubleshooting.md) | [Python API](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)
----------------- | --------------------------------- | ------------------------------------------- | --------------------------------------- | --------------------------- | ------------------------------------ | ------------------------------ | ------------------------------------- | -----------------------------------------------------------------------------------
# Scheduling recipes for the CP-SAT solver.

https://developers.google.com/optimization/

## Introduction

Scheduling in Operations Research involves problems of tasks, resources and
times. In general, scheduling problems have the following features: fixed or
variable durations, alternate ways of performing the same task, mutual
exclusivity between tasks, and temporal relations between tasks.

## Interval variables

Intervals are constraints containing three constant of affine expressions
(start, size, and end). Creating an interval constraint will enforce that
`start + size == end`.

The more general API uses three expressions to define the interval. If the size
is fixed, a simpler API uses the start expression and the fixed size.

Creating these intervals is illustrated in the following code snippets.

### Python code

```python
# Snippet from ortools/sat/samples/interval_sample_sat.py
"""Code sample to demonstrates how to build an interval."""


from ortools.sat.python import cp_model


def interval_sample_sat():
  """Showcases how to build interval variables."""
  model = cp_model.CpModel()
  horizon = 100

  # An interval can be created from three affine expressions.
  start_var = model.new_int_var(0, horizon, 'start')
  duration = 10  # Python cp/sat code accept integer variables or constants.
  end_var = model.new_int_var(0, horizon, 'end')
  interval_var = model.new_interval_var(
      start_var, duration, end_var + 2, 'interval'
  )

  print(f'interval = {repr(interval_var)}')

  # If the size is fixed, a simpler version uses the start expression and the
  # size.
  fixed_size_interval_var = model.new_fixed_size_interval_var(
      start_var, 10, 'fixed_size_interval_var'
  )
  print(f'fixed_size_interval_var = {repr(fixed_size_interval_var)}')

  # A fixed interval can be created using the same API.
  fixed_interval = model.new_fixed_size_interval_var(5, 10, 'fixed_interval')
  print(f'fixed_interval = {repr(fixed_interval)}')


interval_sample_sat()
```

## Optional intervals

An interval can be marked as optional. The presence of this interval is
controlled by a literal. The **no overlap** and **cumulative** constraints
understand these presence literals, and correctly ignore inactive intervals.

### Python code

```python
# Snippet from ortools/sat/samples/optional_interval_sample_sat.py
"""Code sample to demonstrates how to build an optional interval."""

from ortools.sat.python import cp_model


def optional_interval_sample_sat():
  """Showcases how to build optional interval variables."""
  model = cp_model.CpModel()
  horizon = 100

  # An interval can be created from three affine expressions.
  start_var = model.new_int_var(0, horizon, 'start')
  duration = 10  # Python cp/sat code accept integer variables or constants.
  end_var = model.new_int_var(0, horizon, 'end')
  presence_var = model.new_bool_var('presence')
  interval_var = model.new_optional_interval_var(
      start_var, duration, end_var + 2, presence_var, 'interval'
  )

  print(f'interval = {repr(interval_var)}')

  # If the size is fixed, a simpler version uses the start expression and the
  # size.
  fixed_size_interval_var = model.new_optional_fixed_size_interval_var(
      start_var, 10, presence_var, 'fixed_size_interval_var'
  )
  print(f'fixed_size_interval_var = {repr(fixed_size_interval_var)}')

  # A fixed interval can be created using the same API.
  fixed_interval = model.new_optional_fixed_size_interval_var(
      5, 10, presence_var, 'fixed_interval'
  )
  print(f'fixed_interval = {repr(fixed_interval)}')


optional_interval_sample_sat()
```

## Time relations between intervals

Temporal relations between intervals can be expressions using linear
inequalities involving the start and end expressions of the intervals.

As seen above, the factory methods on the model used to build intervals accept
1-var affine expression (a * var + b, a, b integer constants) as arguments to
the start, size, and end parameters.

Once the interval is build, these same expressions can be queries using
`StartExpr(), SizeExpr() and EndExpr()` in C++ and C#, `start_expr(),
size_expr(), and end_expr()` in python, and `getStartExpr(), getSizeExpr(), and
getEndExpr()` in Java.

If one or both intervals are optional, then these inequalities must be reified
by the presence literals of the optional intervals used.

### Python code

```python
# Snippet from ortools/sat/samples/interval_relations_sample_sat.py
"""Builds temporal relations between intervals."""

from ortools.sat.python import cp_model


def interval_relations_sample_sat():
  """Showcases how to build temporal relations between intervals."""
  model = cp_model.CpModel()
  horizon = 100

  # An interval can be created from three 1-var affine expressions.
  start_var = model.new_int_var(0, horizon, 'start')
  duration = 10  # Python CP-SAT code accept integer variables or constants.
  end_var = model.new_int_var(0, horizon, 'end')
  interval_var = model.new_interval_var(
      start_var, duration, end_var, 'interval'
  )

  # If the size is fixed, a simpler version uses the start expression and the
  # size.
  fixed_size_start_var = model.new_int_var(0, horizon, 'fixed_start')
  fixed_size_duration = 10
  fixed_size_interval_var = model.new_fixed_size_interval_var(
      fixed_size_start_var,
      fixed_size_duration,
      'fixed_size_interval_var',
  )

  # An optional interval can be created from three 1-var affine expressions and
  # a literal.
  opt_start_var = model.new_int_var(0, horizon, 'opt_start')
  opt_duration = model.new_int_var(2, 6, 'opt_size')
  opt_end_var = model.new_int_var(0, horizon, 'opt_end')
  opt_presence_var = model.new_bool_var('opt_presence')
  opt_interval_var = model.new_optional_interval_var(
      opt_start_var, opt_duration, opt_end_var, opt_presence_var, 'opt_interval'
  )

  # If the size is fixed, a simpler version uses the start expression, the
  # size, and the presence literal.
  opt_fixed_size_start_var = model.new_int_var(0, horizon, 'opt_fixed_start')
  opt_fixed_size_duration = 10
  opt_fixed_size_presence_var = model.new_bool_var('opt_fixed_presence')
  opt_fixed_size_interval_var = model.new_optional_fixed_size_interval_var(
      opt_fixed_size_start_var,
      opt_fixed_size_duration,
      opt_fixed_size_presence_var,
      'opt_fixed_size_interval_var',
  )

  # Simple precedence between two non optional intervals.
  model.add(interval_var.start_expr() >= fixed_size_interval_var.end_expr())

  # Synchronize start between two intervals (one optional, one not)
  model.add(
      interval_var.start_expr() == opt_interval_var.start_expr()
  ).only_enforce_if(opt_presence_var)

  # Exact delay between two optional intervals.
  exact_delay: int = 5
  model.add(
      opt_interval_var.start_expr()
      == opt_fixed_size_interval_var.end_expr() + exact_delay
  ).only_enforce_if(opt_presence_var, opt_fixed_size_presence_var)


interval_relations_sample_sat()
```

## NoOverlap constraint

A no_overlap constraint simply states that all intervals are disjoint. It is
built with a list of interval variables. Fixed intervals are useful for
excluding part of the timeline.

In the following examples, you want to schedule 3 tasks on 3 weeks excluding
weekends, making the final day as early as possible.

### Python code

```python
# Snippet from ortools/sat/samples/no_overlap_sample_sat.py
"""Code sample to demonstrate how to build a NoOverlap constraint."""

from ortools.sat.python import cp_model


def no_overlap_sample_sat():
  """No overlap sample with fixed activities."""
  model = cp_model.CpModel()
  horizon = 21  # 3 weeks.

  # Task 0, duration 2.
  start_0 = model.new_int_var(0, horizon, 'start_0')
  duration_0 = 2  # Python cp/sat code accepts integer variables or constants.
  end_0 = model.new_int_var(0, horizon, 'end_0')
  task_0 = model.new_interval_var(start_0, duration_0, end_0, 'task_0')
  # Task 1, duration 4.
  start_1 = model.new_int_var(0, horizon, 'start_1')
  duration_1 = 4  # Python cp/sat code accepts integer variables or constants.
  end_1 = model.new_int_var(0, horizon, 'end_1')
  task_1 = model.new_interval_var(start_1, duration_1, end_1, 'task_1')

  # Task 2, duration 3.
  start_2 = model.new_int_var(0, horizon, 'start_2')
  duration_2 = 3  # Python cp/sat code accepts integer variables or constants.
  end_2 = model.new_int_var(0, horizon, 'end_2')
  task_2 = model.new_interval_var(start_2, duration_2, end_2, 'task_2')

  # Weekends.
  weekend_0 = model.new_interval_var(5, 2, 7, 'weekend_0')
  weekend_1 = model.new_interval_var(12, 2, 14, 'weekend_1')
  weekend_2 = model.new_interval_var(19, 2, 21, 'weekend_2')

  # No Overlap constraint.
  model.add_no_overlap(
      [task_0, task_1, task_2, weekend_0, weekend_1, weekend_2]
  )

  # Makespan objective.
  obj = model.new_int_var(0, horizon, 'makespan')
  model.add_max_equality(obj, [end_0, end_1, end_2])
  model.minimize(obj)

  # Solve model.
  solver = cp_model.CpSolver()
  status = solver.solve(model)

  if status == cp_model.OPTIMAL:
    # Print out makespan and the start times for all tasks.
    print(f'Optimal Schedule Length: {solver.objective_value}')
    print(f'Task 0 starts at {solver.value(start_0)}')
    print(f'Task 1 starts at {solver.value(start_1)}')
    print(f'Task 2 starts at {solver.value(start_2)}')
  else:
    print(f'Solver exited with nonoptimal status: {status}')


no_overlap_sample_sat()
```

## Cumulative constraint with min and max capacity profile.

A cumulative constraint takes a list of intervals, and a list of demands, and a
capacity. It enforces that at any time point, the sum of demands of tasks active
at that time point is less than a given capacity.

Modeling a non constant max profile can be done using fixed (interval, demand)
to occupy the capacity between the actual profile and it max capacity.

Modeling a non zero min profile can be done using fixed (interval, demand) on
the complementary cumulative constraint.

### Python code

```python
# Snippet from ortools/sat/samples/cumulative_variable_profile_sample_sat.py
"""Solves a scheduling problem with a min and max profile for the work load."""

import io

from absl import app
import pandas as pd

from ortools.sat.python import cp_model


def create_data_model() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
  """Creates the dataframes that describes the model."""

  max_load_str: str = """
  start_hour  max_load
     0            0
     2            0
     4            3
     6            6
     8            8
    10           12
    12            8
    14           12
    16           10
    18            6
    20            4
    22            0
  """

  min_load_str: str = """
  start_hour  min_load
     0            0
     2            0
     4            0
     6            0
     8            3
    10            3
    12            1
    14            3
    16            3
    18            1
    20            1
    22            0
  """

  tasks_str: str = """
  name  duration load  priority
   t1      60      3      2
   t2     180      2      1
   t3     240      5      3
   t4      90      4      2
   t5     120      3      1
   t6     300      3      3
   t7     120      1      2
   t8     100      5      2
   t9     110      2      1
   t10    300      5      3
   t11     90      4      2
   t12    120      3      1
   t13    250      3      3
   t14    120      1      2
   t15     40      5      3
   t16     70      4      2
   t17     90      8      1
   t18     40      3      3
   t19    120      5      2
   t20     60      3      2
   t21    180      2      1
   t22    240      5      3
   t23     90      4      2
   t24    120      3      1
   t25    300      3      3
   t26    120      1      2
   t27    100      5      2
   t28    110      2      1
   t29    300      5      3
   t30     90      4      2
  """

  max_load_df = pd.read_table(io.StringIO(max_load_str), sep=r'\s+')
  min_load_df = pd.read_table(io.StringIO(min_load_str), sep=r'\s+')
  tasks_df = pd.read_table(io.StringIO(tasks_str), index_col=0, sep=r'\s+')
  return max_load_df, min_load_df, tasks_df


def check_solution(
    tasks: list[tuple[int, int, int]],
    min_load_df: pd.DataFrame,
    max_load_df: pd.DataFrame,
    period_length: int,
    horizon: int,
) -> bool:
  """Checks the solution validity against the min and max load constraints."""
  minutes_per_hour = 60
  actual_load_profile = [0 for _ in range(horizon)]
  min_load_profile = [0 for _ in range(horizon)]
  max_load_profile = [0 for _ in range(horizon)]

  # The complexity of the checker is linear in the number of time points, and
  # should be improved.
  for task in tasks:
    for t in range(task[1]):
      actual_load_profile[task[0] + t] += task[2]
  for row in max_load_df.itertuples():
    for t in range(period_length):
      max_load_profile[row.start_hour * minutes_per_hour + t] = row.max_load
  for row in min_load_df.itertuples():
    for t in range(period_length):
      min_load_profile[row.start_hour * minutes_per_hour + t] = row.min_load

  for time in range(horizon):
    if actual_load_profile[time] > max_load_profile[time]:
      print(
          f'actual load {actual_load_profile[time]} at time {time} is greater'
          f' than max load {max_load_profile[time]}'
      )
      return False
    if actual_load_profile[time] < min_load_profile[time]:
      print(
          f'actual load {actual_load_profile[time]} at time {time} is'
          f' less than min load {min_load_profile[time]}'
      )
      return False
  return True


def main(_) -> None:
  """Create the model and solves it."""
  max_load_df, min_load_df, tasks_df = create_data_model()

  # Create the model.
  model = cp_model.CpModel()

  # Get the max capacity from the capacity dataframe.
  max_load = max_load_df.max_load.max()
  print(f'Max capacity = {max_load}')
  print(f'#tasks = {len(tasks_df)}')

  minutes_per_hour: int = 60
  horizon: int = 24 * 60

  # Variables
  starts = model.new_int_var_series(
      name='starts',
      lower_bounds=0,
      upper_bounds=horizon - tasks_df.duration,
      index=tasks_df.index,
  )
  performed = model.new_bool_var_series(name='performed', index=tasks_df.index)

  intervals = model.new_optional_fixed_size_interval_var_series(
      name='intervals',
      index=tasks_df.index,
      starts=starts,
      sizes=tasks_df.duration,
      are_present=performed,
  )

  # Set up the max profile. We use fixed (intervals, demands) to fill in the
  # space between the actual max load profile and the max capacity.
  time_period_max_intervals = model.new_fixed_size_interval_var_series(
      name='time_period_max_intervals',
      index=max_load_df.index,
      starts=max_load_df.start_hour * minutes_per_hour,
      sizes=minutes_per_hour * 2,
  )
  time_period_max_heights = max_load - max_load_df.max_load

  # Cumulative constraint for the max profile.
  model.add_cumulative(
      intervals.to_list() + time_period_max_intervals.to_list(),
      tasks_df.load.to_list() + time_period_max_heights.to_list(),
      max_load,
  )

  # Set up complemented intervals (from 0 to start, and from start + size to
  # horizon).
  prefix_intervals = model.new_optional_interval_var_series(
      name='prefix_intervals',
      index=tasks_df.index,
      starts=0,
      sizes=starts,
      ends=starts,
      are_present=performed,
  )

  suffix_intervals = model.new_optional_interval_var_series(
      name='suffix_intervals',
      index=tasks_df.index,
      starts=starts + tasks_df.duration,
      sizes=horizon - starts - tasks_df.duration,
      ends=horizon,
      are_present=performed,
  )

  # Set up the min profile. We use complemented intervals to maintain the
  # complement of the work load, and fixed intervals to enforce the min
  # number of active workers per time period.
  #
  # Note that this works only if the max load cumulative is also added to the
  # model.
  time_period_min_intervals = model.new_fixed_size_interval_var_series(
      name='time_period_min_intervals',
      index=min_load_df.index,
      starts=min_load_df.start_hour * minutes_per_hour,
      sizes=minutes_per_hour * 2,
  )
  time_period_min_heights = min_load_df.min_load

  # We take into account optional intervals. The actual capacity of the min load
  # cumulative is the sum of all the active demands.
  sum_of_demands = sum(tasks_df.load)
  complement_capacity = model.new_int_var(
      0, sum_of_demands, 'complement_capacity'
  )
  model.add(complement_capacity == performed.dot(tasks_df.load))

  # Cumulative constraint for the min profile.
  model.add_cumulative(
      prefix_intervals.to_list()
      + suffix_intervals.to_list()
      + time_period_min_intervals.to_list(),
      tasks_df.load.to_list()
      + tasks_df.load.to_list()
      + time_period_min_heights.to_list(),
      complement_capacity,
  )

  # Objective: maximize the value of performed intervals.
  # 1 is the max priority.
  max_priority = max(tasks_df.priority)
  model.maximize(sum(performed * (max_priority + 1 - tasks_df.priority)))

  # Create the solver and solve the model.
  solver = cp_model.CpSolver()
  # solver.parameters.log_search_progress = True  # Uncomment to see the logs.
  solver.parameters.num_workers = 16
  solver.parameters.max_time_in_seconds = 30.0
  status = solver.solve(model)

  if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    start_values = solver.values(starts)
    performed_values = solver.boolean_values(performed)
    tasks: list[tuple[int, int, int]] = []
    for task in tasks_df.index:
      if performed_values[task]:
        print(
            f'task {task} duration={tasks_df["duration"][task]} '
            f'load={tasks_df["load"][task]} starts at {start_values[task]}'
        )
        tasks.append(
            (start_values[task], tasks_df.duration[task], tasks_df.load[task])
        )
      else:
        print(f'task {task} is not performed')
    assert check_solution(
        tasks=tasks,
        min_load_df=min_load_df,
        max_load_df=max_load_df,
        period_length=2 * minutes_per_hour,
        horizon=horizon,
    )
  elif status == cp_model.INFEASIBLE:
    print('No solution found')
  else:
    print('Something is wrong, check the status and the log of the solve')


if __name__ == '__main__':
  app.run(main)
```

## Alternative resources for one interval

## Ranking tasks in a disjunctive resource

To rank intervals in a no_overlap constraint, you will count the number of
performed intervals that precede each interval.

This is slightly complicated if some interval variables are optional. To
implement it, you will create a matrix of `precedences` boolean variables.
`precedences[i][j]` is set to true if and only if interval `i` is performed,
interval `j` is performed, and if the start of `i` is before the start of `j`.

Furthermore, `precedences[i][i]` is set to be equal to `presences[i]`. This way,
you can define the rank of an interval `i` as `sum over j(precedences[j][i]) -
1`. If the interval is not performed, the rank computed as -1, if the interval
is performed, its presence variable negates the -1, and the formula counts the
number of other intervals that precede it.

### Python code

```python
# Snippet from ortools/sat/samples/ranking_sample_sat.py
"""Code sample to demonstrates how to rank intervals."""

from ortools.sat.python import cp_model


def rank_tasks(
    model: cp_model.CpModel,
    starts: list[cp_model.IntVar],
    presences: list[cp_model.BoolVarT],
    ranks: list[cp_model.IntVar],
) -> None:
  """This method adds constraints and variables to links tasks and ranks.

  This method assumes that all starts are disjoint, meaning that all tasks have
  a strictly positive duration, and they appear in the same NoOverlap
  constraint.

  Args:
    model: The CpModel to add the constraints to.
    starts: The array of starts variables of all tasks.
    presences: The array of presence variables or constants of all tasks.
    ranks: The array of rank variables of all tasks.
  """

  num_tasks = len(starts)
  all_tasks = range(num_tasks)

  # Creates precedence variables between pairs of intervals.
  precedences: dict[tuple[int, int], cp_model.BoolVarT] = {}
  for i in all_tasks:
    for j in all_tasks:
      if i == j:
        precedences[(i, j)] = presences[i]
      else:
        prec = model.new_bool_var(f'{i} before {j}')
        precedences[(i, j)] = prec
        model.add(starts[i] < starts[j]).only_enforce_if(prec)

  # Treats optional intervals.
  for i in range(num_tasks - 1):
    for j in range(i + 1, num_tasks):
      tmp_array: list[cp_model.BoolVarT] = [
          precedences[(i, j)],
          precedences[(j, i)],
      ]
      if not cp_model.object_is_a_true_literal(presences[i]):
        tmp_array.append(~presences[i])
        # Makes sure that if i is not performed, all precedences are false.
        model.add_implication(~presences[i], ~precedences[(i, j)])
        model.add_implication(~presences[i], ~precedences[(j, i)])
      if not cp_model.object_is_a_true_literal(presences[j]):
        tmp_array.append(~presences[j])
        # Makes sure that if j is not performed, all precedences are false.
        model.add_implication(~presences[j], ~precedences[(i, j)])
        model.add_implication(~presences[j], ~precedences[(j, i)])
      # The following bool_or will enforce that for any two intervals:
      #    i precedes j or j precedes i or at least one interval is not
      #        performed.
      model.add_bool_or(tmp_array)
      # Redundant constraint: it propagates early that at most one precedence
      # is true.
      model.add_implication(precedences[(i, j)], ~precedences[(j, i)])
      model.add_implication(precedences[(j, i)], ~precedences[(i, j)])

  # Links precedences and ranks.
  for i in all_tasks:
    model.add(ranks[i] == sum(precedences[(j, i)] for j in all_tasks) - 1)


def ranking_sample_sat() -> None:
  """Ranks tasks in a NoOverlap constraint."""

  model = cp_model.CpModel()
  horizon = 100
  num_tasks = 4
  all_tasks = range(num_tasks)

  starts = []
  ends = []
  intervals = []
  presences: list[cp_model.BoolVarT] = []
  ranks = []

  # Creates intervals, half of them are optional.
  for t in all_tasks:
    start = model.new_int_var(0, horizon, f'start[{t}]')
    duration = t + 1
    end = model.new_int_var(0, horizon, f'end[{t}]')
    if t < num_tasks // 2:
      interval = model.new_interval_var(start, duration, end, f'interval[{t}]')
      presence = model.new_constant(1)
    else:
      presence = model.new_bool_var(f'presence[{t}]')
      interval = model.new_optional_interval_var(
          start, duration, end, presence, f'o_interval[{t}]'
      )
    starts.append(start)
    ends.append(end)
    intervals.append(interval)
    presences.append(presence)

    # Ranks = -1 if and only if the tasks is not performed.
    ranks.append(model.new_int_var(-1, num_tasks - 1, f'rank[{t}]'))

  # Adds NoOverlap constraint.
  model.add_no_overlap(intervals)

  # Adds ranking constraint.
  rank_tasks(model, starts, presences, ranks)

  # Adds a constraint on ranks.
  model.add(ranks[0] < ranks[1])

  # Creates makespan variable.
  makespan = model.new_int_var(0, horizon, 'makespan')
  for t in all_tasks:
    model.add(ends[t] <= makespan).only_enforce_if(presences[t])

  # Minimizes makespan - fixed gain per tasks performed.
  # As the fixed cost is less that the duration of the last interval,
  # the solver will not perform the last interval.
  model.minimize(2 * makespan - 7 * sum(presences[t] for t in all_tasks))

  # Solves the model model.
  solver = cp_model.CpSolver()
  status = solver.solve(model)

  if status == cp_model.OPTIMAL:
    # Prints out the makespan and the start times and ranks of all tasks.
    print(f'Optimal cost: {solver.objective_value}')
    print(f'Makespan: {solver.value(makespan)}')
    for t in all_tasks:
      if solver.value(presences[t]):
        print(
            f'Task {t} starts at {solver.value(starts[t])} '
            f'with rank {solver.value(ranks[t])}'
        )
      else:
        print(
            f'Task {t} in not performed and ranked at {solver.value(ranks[t])}'
        )
  else:
    print(f'Solver exited with nonoptimal status: {status}')


ranking_sample_sat()
```

## Ranking tasks in a disjunctive resource with a circuit constraint.

To rank intervals in a no_overlap constraint, you will use a circuit constraint
to perform the transitive reduction from precedences to successors.

This is slightly complicated if some interval variables are optional, and you
need to take into account the case where no task is performed.

### Python code

```python
# Snippet from ortools/sat/samples/ranking_circuit_sample_sat.py
"""Code sample to demonstrates how to rank intervals using a circuit."""


from collections.abc import Sequence

from ortools.sat.python import cp_model


def rank_tasks_with_circuit(
    model: cp_model.CpModel,
    starts: Sequence[cp_model.IntVar],
    durations: Sequence[int],
    presences: Sequence[cp_model.IntVar],
    ranks: Sequence[cp_model.IntVar],
) -> None:
  """This method uses a circuit constraint to rank tasks.

  This method assumes that all starts are disjoint, meaning that all tasks have
  a strictly positive duration, and they appear in the same NoOverlap
  constraint.

  To implement this ranking, we will create a dense graph with num_tasks + 1
  nodes.
  The extra node (with id 0) will be used to decide which task is first with
  its only outgoing arc, and which task is last with its only incoming arc.
  Each task i will be associated with id i + 1, and an arc between i + 1 and j +
  1 indicates that j is the immediate successor of i.

  The circuit constraint ensures there is at most 1 hamiltonian cycle of
  length > 1. If no such path exists, then no tasks are active.
  We also need to enforce that any hamiltonian cycle of size > 1 must contain
  the node 0. And thus, there is a self loop on node 0 iff the circuit is empty.

  Args:
    model: The CpModel to add the constraints to.
    starts: The array of starts variables of all tasks.
    durations: the durations of all tasks.
    presences: The array of presence variables of all tasks.
    ranks: The array of rank variables of all tasks.
  """

  num_tasks = len(starts)
  all_tasks = range(num_tasks)

  arcs: list[cp_model.ArcT] = []
  for i in all_tasks:
    # if node i is first.
    start_lit = model.new_bool_var(f'start_{i}')
    arcs.append((0, i + 1, start_lit))
    model.add(ranks[i] == 0).only_enforce_if(start_lit)

    # As there are no other constraints on the problem, we can add this
    # redundant constraint.
    model.add(starts[i] == 0).only_enforce_if(start_lit)

    # if node i is last.
    end_lit = model.new_bool_var(f'end_{i}')
    arcs.append((i + 1, 0, end_lit))

    for j in all_tasks:
      if i == j:
        arcs.append((i + 1, i + 1, ~presences[i]))
        model.add(ranks[i] == -1).only_enforce_if(~presences[i])
      else:
        literal = model.new_bool_var(f'arc_{i}_to_{j}')
        arcs.append((i + 1, j + 1, literal))
        model.add(ranks[j] == ranks[i] + 1).only_enforce_if(literal)

        # To perform the transitive reduction from precedences to successors,
        # we need to tie the starts of the tasks with 'literal'.
        # In a pure problem, the following inequality could be an equality.
        # It is not true in general.
        #
        # Note that we could use this literal to penalize the transition, add an
        # extra delay to the precedence.
        model.add(starts[j] >= starts[i] + durations[i]).only_enforce_if(
            literal
        )

  # Manage the empty circuit
  empty = model.new_bool_var('empty')
  arcs.append((0, 0, empty))

  for i in all_tasks:
    model.add_implication(empty, ~presences[i])

  # Add the circuit constraint.
  model.add_circuit(arcs)


def ranking_sample_sat() -> None:
  """Ranks tasks in a NoOverlap constraint."""

  model = cp_model.CpModel()
  horizon = 100
  num_tasks = 4
  all_tasks = range(num_tasks)

  starts = []
  durations = []
  intervals = []
  presences = []
  ranks = []

  # Creates intervals, half of them are optional.
  for t in all_tasks:
    start = model.new_int_var(0, horizon, f'start[{t}]')
    duration = t + 1
    presence = model.new_bool_var(f'presence[{t}]')
    interval = model.new_optional_fixed_size_interval_var(
        start, duration, presence, f'opt_interval[{t}]'
    )
    if t < num_tasks // 2:
      model.add(presence == 1)

    starts.append(start)
    durations.append(duration)
    intervals.append(interval)
    presences.append(presence)

    # Ranks = -1 if and only if the tasks is not performed.
    ranks.append(model.new_int_var(-1, num_tasks - 1, f'rank[{t}]'))

  # Adds NoOverlap constraint.
  model.add_no_overlap(intervals)

  # Adds ranking constraint.
  rank_tasks_with_circuit(model, starts, durations, presences, ranks)

  # Adds a constraint on ranks.
  model.add(ranks[0] < ranks[1])

  # Creates makespan variable.
  makespan = model.new_int_var(0, horizon, 'makespan')
  for t in all_tasks:
    model.add(starts[t] + durations[t] <= makespan).only_enforce_if(
        presences[t]
    )

  # Minimizes makespan - fixed gain per tasks performed.
  # As the fixed cost is less that the duration of the last interval,
  # the solver will not perform the last interval.
  model.minimize(2 * makespan - 7 * sum(presences[t] for t in all_tasks))

  # Solves the model model.
  solver = cp_model.CpSolver()
  status = solver.solve(model)

  if status == cp_model.OPTIMAL:
    # Prints out the makespan and the start times and ranks of all tasks.
    print(f'Optimal cost: {solver.objective_value}')
    print(f'Makespan: {solver.value(makespan)}')
    for t in all_tasks:
      if solver.value(presences[t]):
        print(
            f'Task {t} starts at {solver.value(starts[t])} '
            f'with rank {solver.value(ranks[t])}'
        )
      else:
        print(
            f'Task {t} in not performed and ranked at {solver.value(ranks[t])}'
        )
  else:
    print(f'Solver exited with nonoptimal status: {status}')


ranking_sample_sat()
```

## Intervals spanning over breaks in the calendar

Sometimes, a task can be interrupted by a break (overnight, lunch break). In
that context, although the processing time of the task is the same, the duration
can vary.

To implement this feature, you will have the duration of the task be a function
of the start of the task. This is implemented using channeling constraints.

The following code displays:

    start=8 duration=3 across=0
    start=9 duration=3 across=0
    start=10 duration=3 across=0
    start=11 duration=4 across=1
    start=12 duration=4 across=1
    start=14 duration=3 across=0
    start=15 duration=3 across=0

### Python code

```python
# Snippet from ortools/sat/samples/scheduling_with_calendar_sample_sat.py
"""Code sample to demonstrate how an interval can span across a break."""

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


def scheduling_with_calendar_sample_sat():
  """Interval spanning across a lunch break."""
  model = cp_model.CpModel()

  # The data is the following:
  #   Work starts at 8h, ends at 18h, with a lunch break between 13h and 14h.
  #   We need to schedule a task that needs 3 hours of processing time.
  #   Total duration can be 3 or 4 (if it spans the lunch break).
  #
  # Because the duration is at least 3 hours, work cannot start after 15h.
  # Because of the break, work cannot start at 13h.

  start = model.new_int_var_from_domain(
      cp_model.Domain.from_intervals([(8, 12), (14, 15)]), 'start'
  )
  duration = model.new_int_var(3, 4, 'duration')
  end = model.new_int_var(8, 18, 'end')
  unused_interval = model.new_interval_var(start, duration, end, 'interval')

  # We have 2 states (spanning across lunch or not)
  across = model.new_bool_var('across')
  non_spanning_hours = cp_model.Domain.from_values([8, 9, 10, 14, 15])
  model.add_linear_expression_in_domain(
      start, non_spanning_hours
  ).only_enforce_if(~across)
  model.add_linear_constraint(start, 11, 12).only_enforce_if(across)
  model.add(duration == 3).only_enforce_if(~across)
  model.add(duration == 4).only_enforce_if(across)

  # Search for x values in increasing order.
  model.add_decision_strategy(
      [start], cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE
  )

  # Create a solver and solve with a fixed search.
  solver = cp_model.CpSolver()

  # Force the solver to follow the decision strategy exactly.
  solver.parameters.search_branching = cp_model.FIXED_SEARCH
  # Enumerate all solutions.
  solver.parameters.enumerate_all_solutions = True

  # Search and print all solutions.
  solution_printer = VarArraySolutionPrinter([start, duration, across])
  solver.solve(model, solution_printer)


scheduling_with_calendar_sample_sat()
```

## Detecting if two intervals overlap.

You want a Boolean variable to be true if and only if two intervals overlap. To
enforce this, you will create 3 Boolean variables, link two of them to the
relative positions of the two intervals, and define the third one using the
other two Boolean variables.

There are two ways of linking the three Boolean variables. The first version
uses one clause and two implications. Propagation will be faster using this
version. The second version uses a `sum(..) == 1` equation. It is more compact,
but assumes the length of the two intervals is > 0.

Note that you need to create the intervals to enforce `start + size == end`, but
you do not actually use them in this code sample.

The following code displays

```
start_a=0 start_b=0 a_overlaps_b=1
start_a=0 start_b=1 a_overlaps_b=1
start_a=0 start_b=2 a_overlaps_b=1
start_a=0 start_b=3 a_overlaps_b=0
start_a=0 start_b=4 a_overlaps_b=0
start_a=0 start_b=5 a_overlaps_b=0
start_a=1 start_b=0 a_overlaps_b=1
start_a=1 start_b=1 a_overlaps_b=1
start_a=1 start_b=2 a_overlaps_b=1
start_a=1 start_b=3 a_overlaps_b=1
start_a=1 start_b=4 a_overlaps_b=0
start_a=1 start_b=5 a_overlaps_b=0
...
```

### Python code

```python
# Snippet from ortools/sat/samples/overlapping_intervals_sample_sat.py
"""Code sample to demonstrates how to detect if two intervals overlap."""

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


def overlapping_interval_sample_sat():
  """Create the overlapping Boolean variables and enumerate all states."""
  model = cp_model.CpModel()

  horizon = 7

  # First interval.
  start_var_a = model.new_int_var(0, horizon, 'start_a')
  duration_a = 3
  end_var_a = model.new_int_var(0, horizon, 'end_a')
  unused_interval_var_a = model.new_interval_var(
      start_var_a, duration_a, end_var_a, 'interval_a'
  )

  # Second interval.
  start_var_b = model.new_int_var(0, horizon, 'start_b')
  duration_b = 2
  end_var_b = model.new_int_var(0, horizon, 'end_b')
  unused_interval_var_b = model.new_interval_var(
      start_var_b, duration_b, end_var_b, 'interval_b'
  )

  # a_after_b Boolean variable.
  a_after_b = model.new_bool_var('a_after_b')
  model.add(start_var_a >= end_var_b).only_enforce_if(a_after_b)
  model.add(start_var_a < end_var_b).only_enforce_if(~a_after_b)

  # b_after_a Boolean variable.
  b_after_a = model.new_bool_var('b_after_a')
  model.add(start_var_b >= end_var_a).only_enforce_if(b_after_a)
  model.add(start_var_b < end_var_a).only_enforce_if(~b_after_a)

  # Result Boolean variable.
  a_overlaps_b = model.new_bool_var('a_overlaps_b')

  # Option a: using only clauses
  model.add_bool_or(a_after_b, b_after_a, a_overlaps_b)
  model.add_implication(a_after_b, ~a_overlaps_b)
  model.add_implication(b_after_a, ~a_overlaps_b)

  # Option b: using an exactly one constraint.
  # model.add_exactly_one(a_after_b, b_after_a, a_overlaps_b)

  # Search for start values in increasing order for the two intervals.
  model.add_decision_strategy(
      [start_var_a, start_var_b],
      cp_model.CHOOSE_FIRST,
      cp_model.SELECT_MIN_VALUE,
  )

  # Create a solver and solve with a fixed search.
  solver = cp_model.CpSolver()

  # Force the solver to follow the decision strategy exactly.
  solver.parameters.search_branching = cp_model.FIXED_SEARCH
  # Enumerate all solutions.
  solver.parameters.enumerate_all_solutions = True

  # Search and print out all solutions.
  solution_printer = VarArraySolutionPrinter(
      [start_var_a, start_var_b, a_overlaps_b])
  solver.solve(model, solution_printer)


overlapping_interval_sample_sat()
```

## Transitions in a no_overlap constraint

In some scheduling problems, switching between certain type of tasks on a
machine implies some penalty, and/or some delay. Implementing these
functionalities implies knowing which are the direct successors of each task.

The circuit constraint is used to perform the transitive reduction from
precedences to successors. Once this is done, it is straightforward to use the
successor literals to implement the penalties or the delays.

### Python code

```python
# Snippet from ortools/sat/samples/transitions_in_no_overlap_sample_sat.py
"""Implements transition times and costs in a no_overlap constraint."""

from collections.abc import Sequence
from typing import Union

from ortools.sat.python import cp_model


def transitive_reduction_with_circuit_delays_and_penalties(
    model: cp_model.CpModel,
    starts: Sequence[cp_model.IntVar],
    durations: Sequence[int],
    presences: Sequence[Union[cp_model.IntVar, bool]],
    penalties: dict[tuple[int, int], int],
    delays: dict[tuple[int, int], int],
) -> Sequence[tuple[cp_model.IntVar, int]]:
  """This method uses a circuit constraint to rank tasks.

  This method assumes that all starts are disjoint, meaning that all tasks have
  a strictly positive duration, and they appear in the same NoOverlap
  constraint.

  The extra node (with id 0) will be used to decide which task is first with
  its only outgoing arc, and which task is last with its only incoming arc.
  Each task i will be associated with id i + 1, and an arc between i + 1 and j +
  1 indicates that j is the immediate successor of i.

  The circuit constraint ensures there is at most 1 hamiltonian cycle of
  length > 1. If no such path exists, then no tasks are active.
  We also need to enforce that any hamiltonian cycle of size > 1 must contain
  the node 0. And thus, there is a self loop on node 0 iff the circuit is empty.

  Args:
    model: The CpModel to add the constraints to.
    starts: The array of starts variables of all tasks.
    durations: the durations of all tasks.
    presences: The array of presence variables of all tasks.
    penalties: the array of tuple (`tail_index`, `head_index`, `penalty`) that
      specifies that if task `tail_index` is the successor of the task
      `head_index`, then `penalty` must be added to the cost.
    delays: the array of tuple (`tail_index`, `head_index`, `delay`) that
      specifies that if task `tail_index` is the successor of the task
      `head_index`, then an extra `delay` must be added between the end of the
      first task and the start of the second task.

  Returns:
    The list of pairs (Boolean variables, penalty) to be added to the objective.
  """

  num_tasks = len(starts)
  all_tasks = range(num_tasks)

  arcs: list[cp_model.ArcT] = []
  penalty_terms = []
  for i in all_tasks:
    # if node i is first.
    start_lit = model.new_bool_var(f'start_{i}')
    arcs.append((0, i + 1, start_lit))

    # As there are no other constraints on the problem, we can add this
    # redundant constraint.
    model.add(starts[i] == 0).only_enforce_if(start_lit)

    # if node i is last.
    end_lit = model.new_bool_var(f'end_{i}')
    arcs.append((i + 1, 0, end_lit))

    for j in all_tasks:
      if i == j:
        arcs.append((i + 1, i + 1, ~presences[i]))
      else:
        literal = model.new_bool_var(f'arc_{i}_to_{j}')
        arcs.append((i + 1, j + 1, literal))

        # To perform the transitive reduction from precedences to successors,
        # we need to tie the starts of the tasks with 'literal'.
        # In a pure problem, the following inequality could be an equality.
        # It is not true in general.
        #
        # Note that we could use this literal to penalize the transition, add an
        # extra delay to the precedence.
        min_delay = 0
        key = (i, j)
        if key in delays:
          min_delay = delays[key]
        model.add(
            starts[j] >= starts[i] + durations[i] + min_delay
        ).only_enforce_if(literal)

        # Create the penalties.
        if key in penalties:
          penalty_terms.append((literal, penalties[key]))

  # Manage the empty circuit
  empty = model.new_bool_var('empty')
  arcs.append((0, 0, empty))

  for i in all_tasks:
    model.add_implication(empty, ~presences[i])

  # Add the circuit constraint.
  model.add_circuit(arcs)

  return penalty_terms


def transitions_in_no_overlap_sample_sat():
  """Implement transitions in a NoOverlap constraint."""

  model = cp_model.CpModel()
  horizon = 40
  num_tasks = 4

  # Breaking the natural sequence induces a fixed penalty.
  penalties = {
      (1, 0): 10,
      (2, 0): 10,
      (3, 0): 10,
      (2, 1): 10,
      (3, 1): 10,
      (3, 2): 10,
  }

  # Switching from an odd to even or even to odd task indices induces a delay.
  delays = {
      (1, 0): 10,
      (0, 1): 10,
      (3, 0): 10,
      (0, 3): 10,
      (1, 2): 10,
      (2, 1): 10,
      (3, 2): 10,
      (2, 3): 10,
  }

  all_tasks = range(num_tasks)

  starts = []
  durations = []
  intervals = []
  presences = []

  # Creates intervals, all present. But the cost is robust w.r.t. optional
  # intervals.
  for t in all_tasks:
    start = model.new_int_var(0, horizon, f'start[{t}]')
    duration = 5
    presence = True
    interval = model.new_optional_fixed_size_interval_var(
        start, duration, presence, f'opt_interval[{t}]'
    )

    starts.append(start)
    durations.append(duration)
    intervals.append(interval)
    presences.append(presence)

  # Adds NoOverlap constraint.
  model.add_no_overlap(intervals)

  # Adds ranking constraint.
  penalty_terms = transitive_reduction_with_circuit_delays_and_penalties(
      model, starts, durations, presences, penalties, delays
  )

  # Minimize the sum of penalties,
  model.minimize(sum(var * penalty for var, penalty in penalty_terms))

  # In practise, only one penalty can happen. Thus the two even tasks are
  # together, same for the two odd tasks.
  # Because of the penalties, the optimal sequence is 0 -> 2 -> 1 -> 3
  # which induces one penalty and one delay.

  # Solves the model model.
  solver = cp_model.CpSolver()
  status = solver.solve(model)

  if status == cp_model.OPTIMAL:
    # Prints out the makespan and the start times and ranks of all tasks.
    print(f'Optimal cost: {solver.objective_value}')
    for t in all_tasks:
      if solver.value(presences[t]):
        print(f'Task {t} starts at {solver.value(starts[t])} ')
      else:
        print(f'Task {t} in not performed')
  else:
    print(f'Solver exited with nonoptimal status: {status}')


transitions_in_no_overlap_sample_sat()
```

## Managing sequences in a no_overlap constraint

In some scheduling problems, there can be constraints on sequence of tasks. For
instance, tasks of a given type may have limit on the min or max number of
contiguous tasks of the same type.

The circuit constraint is used to constraint the length of any sequence of tasks
of the same type. It uses counters attached to each task, and transition
literals to maintain these counters.

### Python code

```python
# Snippet from ortools/sat/samples/sequences_in_no_overlap_sample_sat.py
"""Implements sequence constraints in a no_overlap constraint."""

from collections.abc import Sequence

from ortools.sat.python import cp_model


def sequence_constraints_with_circuit(
    model: cp_model.CpModel,
    starts: Sequence[cp_model.IntVar],
    durations: Sequence[int],
    task_types: Sequence[str],
    lengths: Sequence[cp_model.IntVar],
    cumuls: Sequence[cp_model.IntVar],
    sequence_length_constraints: dict[str, tuple[int, int]],
    sequence_cumul_constraints: dict[str, tuple[int, int, int]],
) -> Sequence[tuple[cp_model.IntVar, int]]:
  """This method enforces constraints on sequences of tasks of the same type.

  This method assumes that all durations are strictly positive.

  The extra node (with id 0) will be used to decide which task is first with
  its only outgoing arc, and which task is last with its only incoming arc.
  Each task i will be associated with id i + 1, and an arc between i + 1 and j +
  1 indicates that j is the immediate successor of i.

  The circuit constraint ensures there is at most 1 hamiltonian cycle of
  length > 1. If no such path exists, then no tasks are active.
  In this simplified model, all tasks must be performed.

  Args:
    model: The CpModel to add the constraints to.
    starts: The array of starts variables of all tasks.
    durations: the durations of all tasks.
    task_types: The type of all tasks.
    lengths: the number of tasks of the same type in the current sequence.
    cumuls: The computed cumul of the current sequence for each task.
    sequence_length_constraints: the array of tuple (`task_type`, (`length_min`,
      `length_max`)) that specifies the minimum and maximum length of the
      sequence of tasks of type `task_type`.
    sequence_cumul_constraints: the array of tuple (`task_type`, (`soft_max`,
      `linear_penalty`, `hard_max`)) that specifies that if the cumul of the
      sequence of tasks of type `task_type` is greater than `soft_max`, then
      `linear_penalty * (cumul - soft_max)` is added to the cost

  Returns:
    The list of pairs (integer variables, penalty) to be added to the objective.
  """

  num_tasks = len(starts)
  all_tasks = range(num_tasks)

  arcs: list[cp_model.ArcT] = []
  for i in all_tasks:
    # if node i is first.
    start_lit = model.new_bool_var(f'start_{i}')
    arcs.append((0, i + 1, start_lit))
    model.add(lengths[i] == 1).only_enforce_if(start_lit)
    model.add(cumuls[i] == durations[i]).only_enforce_if(start_lit)

    # As there are no other constraints on the problem, we can add this
    # redundant constraint. This is not valid in general.
    model.add(starts[i] == 0).only_enforce_if(start_lit)

    # if node i is last.
    end_lit = model.new_bool_var(f'end_{i}')
    arcs.append((i + 1, 0, end_lit))

    # Make sure the previous length is within bounds.
    type_length_min = sequence_length_constraints[task_types[i]][0]
    model.add(lengths[i] >= type_length_min).only_enforce_if(end_lit)

    for j in all_tasks:
      if i == j:
        continue
      lit = model.new_bool_var(f'arc_{i}_to_{j}')
      arcs.append((i + 1, j + 1, lit))

      # The circuit constraint is use to enforce the consistency between the
      # precedences relations and the successor arcs. This is implemented by
      # adding the constraint that force the implication task j is the next of
      # task i implies that start(j) is greater or equal than the end(i).
      #
      # In the majority of problems, the following equality must be an
      # inequality. In that particular case, as there are no extra constraints,
      # we can keep the equality between start(j) and end(i).
      model.add(starts[j] == starts[i] + durations[i]).only_enforce_if(lit)

      # We add the constraints to incrementally maintain the length and the
      # cumul variables of the sequence.
      if task_types[i] == task_types[j]:  # Same task type.
        # Increase the length of the sequence by 1.
        model.add(lengths[j] == lengths[i] + 1).only_enforce_if(lit)

        # Increase the cumul of the sequence by the duration of the task.
        model.add(cumuls[j] == cumuls[i] + durations[j]).only_enforce_if(lit)

      else:
        # Switching task type. task[i] is the last task of the previous
        # sequence, task[j] is the first task of the new sequence.
        #
        # Reset the length to 1.
        model.add(lengths[j] == 1).only_enforce_if(lit)

        # Make sure the previous length is within bounds.
        type_length_min = sequence_length_constraints[task_types[i]][0]
        model.add(lengths[i] >= type_length_min).only_enforce_if(lit)

        # Reset the cumul to the duration of the task.
        model.add(cumuls[j] == durations[j]).only_enforce_if(lit)

  # Add the circuit constraint.
  model.add_circuit(arcs)

  # Create the penalty terms. We can penalize each cumul locally.
  penalty_terms = []
  for i in all_tasks:
    # Penalize the cumul of the last task w.r.t. the soft max
    soft_max, linear_penalty, hard_max = sequence_cumul_constraints[
        task_types[i]
    ]

    # To make it separable per task, and avoid double counting, we use the
    # following trick:
    #     reduced_excess = min(durations[i], max(0, cumul[i] - soft_max))
    if soft_max < hard_max:
      excess = model.new_int_var(0, hard_max - soft_max, f'excess+_{i}')
      model.add_max_equality(excess, [0, cumuls[i] - soft_max])
      reduced_excess = model.new_int_var(0, durations[i], f'reduced_excess_{i}')
      model.add_min_equality(reduced_excess, [durations[i], excess])
      penalty_terms.append((reduced_excess, linear_penalty))

  return penalty_terms


def sequences_in_no_overlap_sample_sat():
  """Implement cumul and length constraints in a NoOverlap constraint."""

  # Tasks (duration, type).
  tasks = [
      (5, 'A'),
      (6, 'A'),
      (7, 'A'),
      (2, 'A'),
      (3, 'A'),
      (5, 'B'),
      (2, 'B'),
      (3, 'B'),
      (1, 'B'),
      (4, 'B'),
      (3, 'B'),
      (6, 'B'),
      (2, 'B'),
  ]

  # Sequence length constraints per task_types: (hard_min, hard_max)
  #
  # Note that this constraint is very tight for task type B and will fail with
  # an odd number of tasks of type B.
  sequence_length_constraints = {
      'A': (1, 3),
      'B': (2, 2),
  }

  # Sequence accumulated durations constraints per task_types:
  #     (soft_max, linear_penalty, hard_max)
  sequence_cumul_constraints = {
      'A': (6, 1, 10),
      'B': (7, 0, 7),
  }

  model: cp_model.CpModel = cp_model.CpModel()
  horizon: int = sum(t[0] for t in tasks)

  num_tasks = len(tasks)
  all_tasks = range(num_tasks)

  starts = []
  durations = []
  intervals = []
  task_types = []

  # Creates intervals for each task.
  for duration, task_type in tasks:
    index = len(starts)
    start = model.new_int_var(0, horizon - duration, f'start[{index}]')
    interval = model.new_fixed_size_interval_var(
        start, duration, f'interval[{index}]'
    )

    starts.append(start)
    durations.append(duration)
    intervals.append(interval)
    task_types.append(task_type)

  # Create length variables for each task.
  lengths = []
  for i in all_tasks:
    max_hard_length = sequence_length_constraints[task_types[i]][1]
    lengths.append(model.new_int_var(1, max_hard_length, f'length_{i}'))

  # Create cumul variables for each task.
  cumuls = []
  for i in all_tasks:
    max_hard_cumul = sequence_cumul_constraints[task_types[i]][2]
    cumuls.append(model.new_int_var(durations[i], max_hard_cumul, f'cumul_{i}'))

  # Adds NoOverlap constraint.
  model.add_no_overlap(intervals)

  # Adds the constraints on the lengths and cumuls of maximal sequences of
  # tasks of the same type.
  penalty_terms = sequence_constraints_with_circuit(
      model,
      starts,
      durations,
      task_types,
      lengths,
      cumuls,
      sequence_length_constraints,
      sequence_cumul_constraints,
  )

  # Minimize the sum of penalties,
  model.minimize(sum(var * penalty for var, penalty in penalty_terms))

  # Solves the model model.
  solver = cp_model.CpSolver()
  status = solver.solve(model)

  if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    # Prints out the makespan and the start times and lengths, cumuls at each
    # step.
    if status == cp_model.OPTIMAL:
      print(f'Optimal cost: {solver.objective_value}')
    else:
      print(f'Feasible cost: {solver.objective_value}')

    to_sort = []
    for t in all_tasks:
      to_sort.append((solver.value(starts[t]), t))
    to_sort.sort()

    sum_of_penalties = 0
    for i, (start, t) in enumerate(to_sort):
      # Check length constraints.
      length: int = solver.value(lengths[t])
      hard_min_length, hard_max_length = sequence_length_constraints[
          task_types[t]
      ]
      assert length >= 0
      assert length <= hard_max_length
      if (
          i + 1 == len(to_sort)
          or task_types[t] != task_types[to_sort[i + 1][1]]
      ):  # End of sequence.
        assert length >= hard_min_length

      # Check cumul constraints.
      cumul: int = solver.value(cumuls[t])
      soft_max_cumul, penalty, hard_max_cumul = sequence_cumul_constraints[
          task_types[t]
      ]
      assert cumul >= 0
      assert cumul <= hard_max_cumul

      if cumul > soft_max_cumul:
        penalty = penalty * (cumul - soft_max_cumul)
        sum_of_penalties += penalty
        print(
            f'Task {t} of type {task_types[t]} with'
            f' duration={durations[t]} starts at {start}, length={length},'
            f' cumul={cumul} penalty={penalty}'
        )
      else:
        print(
            f'Task {t} of type {task_types[t]} with duration'
            f' {durations[t]} starts at {start}, length ='
            f' {length}, cumul = {cumul} '
        )

    assert int(solver.objective_value) == sum_of_penalties
  else:
    print(f'Solver exited with the following status: {status}')


sequences_in_no_overlap_sample_sat()
```

## Convex hull of a set of intervals
