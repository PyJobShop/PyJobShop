[home](README.md) | [boolean logic](boolean_logic.md) | [integer arithmetic](integer_arithmetic.md) | [channeling constraints](channeling.md) | [scheduling](scheduling.md) | [Using the CP-SAT solver](solver.md) | [Model manipulation](model.md) | [Troubleshooting](troubleshooting.md) | [Python API](https://or-tools.github.io/docs/pdoc/ortools/sat/python/cp_model.html)
----------------- | --------------------------------- | ------------------------------------------- | --------------------------------------- | --------------------------- | ------------------------------------ | ------------------------------ | ------------------------------------- | -----------------------------------------------------------------------------------
# Solving a CP-SAT model

https://developers.google.com/optimization/

## Changing the parameters of the solver

The SatParameters protobuf encapsulates the set of parameters of a CP-SAT
solver. The most useful one is the time limit.

### Specifying the time limit in Python

```python
# Snippet from ortools/sat/samples/solve_with_time_limit_sample_sat.py
"""Solves a problem with a time limit."""

from ortools.sat.python import cp_model


def solve_with_time_limit_sample_sat():
  """Minimal CP-SAT example to showcase calling the solver."""
  # Creates the model.
  model = cp_model.CpModel()
  # Creates the variables.
  num_vals = 3
  x = model.new_int_var(0, num_vals - 1, 'x')
  y = model.new_int_var(0, num_vals - 1, 'y')
  z = model.new_int_var(0, num_vals - 1, 'z')
  # Adds an all-different constraint.
  model.add(x != y)

  # Creates a solver and solves the model.
  solver = cp_model.CpSolver()

  # Sets a time limit of 10 seconds.
  solver.parameters.max_time_in_seconds = 10.0

  status = solver.solve(model)

  if status == cp_model.OPTIMAL:
    print(f'x = {solver.value(x)}')
    print(f'y = {solver.value(y)}')
    print(f'z = {solver.value(z)}')


solve_with_time_limit_sample_sat()
```

### Specifying the time limit in C++

```cpp
// Snippet from ortools/sat/samples/solve_with_time_limit_sample_sat.cc
#include <stdlib.h>

#include "ortools/base/init_google.h"
#include "ortools/base/logging.h"
#include "absl/base/log_severity.h"
#include "absl/log/globals.h"
#include "ortools/sat/cp_model.h"
#include "ortools/sat/cp_model.pb.h"
#include "ortools/sat/cp_model_solver.h"
#include "ortools/sat/model.h"
#include "ortools/sat/sat_parameters.pb.h"
#include "ortools/util/sorted_interval_list.h"

namespace operations_research {
namespace sat {

void SolveWithTimeLimitSampleSat() {
  CpModelBuilder cp_model;

  const Domain domain(0, 2);
  const IntVar x = cp_model.NewIntVar(domain).WithName("x");
  const IntVar y = cp_model.NewIntVar(domain).WithName("y");
  const IntVar z = cp_model.NewIntVar(domain).WithName("z");

  cp_model.AddNotEqual(x, y);

  // Solving part.
  Model model;

  // Sets a time limit of 10 seconds.
  SatParameters parameters;
  parameters.set_max_time_in_seconds(10.0);
  model.Add(NewSatParameters(parameters));

  // Solve.
  const CpSolverResponse response = SolveCpModel(cp_model.Build(), &model);
  LOG(INFO) << CpSolverResponseStats(response);

  if (response.status() == CpSolverStatus::OPTIMAL) {
    LOG(INFO) << "  x = " << SolutionIntegerValue(response, x);
    LOG(INFO) << "  y = " << SolutionIntegerValue(response, y);
    LOG(INFO) << "  z = " << SolutionIntegerValue(response, z);
  }
}

}  // namespace sat
}  // namespace operations_research

int main(int argc, char* argv[]) {
  InitGoogle(argv[0], &argc, &argv, true);
  absl::SetStderrThreshold(absl::LogSeverityAtLeast::kInfo);
  operations_research::sat::SolveWithTimeLimitSampleSat();
  return EXIT_SUCCESS;
}
```

### Specifying the time limit in Java

```java
// Snippet from ortools/sat/samples/SolveWithTimeLimitSampleSat.java
package com.google.ortools.sat.samples;

import com.google.ortools.Loader;
import com.google.ortools.sat.CpSolverStatus;
import com.google.ortools.sat.CpModel;
import com.google.ortools.sat.CpSolver;
import com.google.ortools.sat.IntVar;

/** Solves a problem with a time limit. */
public final class SolveWithTimeLimitSampleSat {
  public static void main(String[] args) {
    Loader.loadNativeLibraries();
    // Create the model.
    CpModel model = new CpModel();
    // Create the variables.
    int numVals = 3;

    IntVar x = model.newIntVar(0, numVals - 1, "x");
    IntVar y = model.newIntVar(0, numVals - 1, "y");
    IntVar z = model.newIntVar(0, numVals - 1, "z");
    // Create the constraint.
    model.addDifferent(x, y);

    // Create a solver and solve the model.
    CpSolver solver = new CpSolver();
    solver.getParameters().setMaxTimeInSeconds(10.0);
    CpSolverStatus status = solver.solve(model);

    if (status == CpSolverStatus.OPTIMAL) {
      System.out.println("x = " + solver.value(x));
      System.out.println("y = " + solver.value(y));
      System.out.println("z = " + solver.value(z));
    }
  }

  private SolveWithTimeLimitSampleSat() {}
}
```

### Specifying the time limit in C\#.

Parameters must be passed as string to the solver.

```csharp
// Snippet from ortools/sat/samples/SolveWithTimeLimitSampleSat.cs
using System;
using Google.OrTools.Sat;

public class SolveWithTimeLimitSampleSat
{
    static void Main()
    {
        // Creates the model.
        CpModel model = new CpModel();
        // Creates the variables.
        int num_vals = 3;

        IntVar x = model.NewIntVar(0, num_vals - 1, "x");
        IntVar y = model.NewIntVar(0, num_vals - 1, "y");
        IntVar z = model.NewIntVar(0, num_vals - 1, "z");
        // Adds a different constraint.
        model.Add(x != y);

        // Creates a solver and solves the model.
        CpSolver solver = new CpSolver();

        // Adds a time limit. Parameters are stored as strings in the solver.
        solver.StringParameters = "max_time_in_seconds:10.0";

        CpSolverStatus status = solver.Solve(model);

        if (status == CpSolverStatus.Optimal)
        {
            Console.WriteLine("x = " + solver.Value(x));
            Console.WriteLine("y = " + solver.Value(y));
            Console.WriteLine("z = " + solver.Value(z));
        }
    }
}
```

### Specifying the time limit in Go

```go
// Snippet from ortools/sat/samples/solve_with_time_limit_sample_sat.go
// The solve_with_time_limit_sample_sat command is an example of setting a time limit on the model.
package main

import (
	"fmt"

	log "github.com/golang/glog"
	"google.golang.org/protobuf/proto"
	"github.com/google/or-tools/ortools/sat/go/cpmodel"

	cmpb "github.com/google/or-tools/ortools/sat/proto/cpmodel"
	sppb "github.com/google/or-tools/ortools/sat/proto/satparameters"
)

func solveWithTimeLimitSampleSat() error {
	model := cpmodel.NewCpModelBuilder()

	domain := cpmodel.NewDomain(0, 2)
	x := model.NewIntVarFromDomain(domain).WithName("x")
	y := model.NewIntVarFromDomain(domain).WithName("y")
	z := model.NewIntVarFromDomain(domain).WithName("z")

	model.AddNotEqual(x, y)

	m, err := model.Model()
	if err != nil {
		return fmt.Errorf("failed to instantiate the CP model: %w", err)
	}

	// Sets a time limit of 10 seconds.
		params := &sppb.SatParameters{
		MaxTimeInSeconds: proto.Float64(10.0),
	}

	// Solve.
	response, err := cpmodel.SolveCpModelWithParameters(m, params)
	if err != nil {
		return fmt.Errorf("failed to solve the model: %w", err)
	}

	fmt.Printf("Status: %v\n", response.GetStatus())

	if response.GetStatus() == cmpb.CpSolverStatus_OPTIMAL {
		fmt.Printf(" x = %v\n", cpmodel.SolutionIntegerValue(response, x))
		fmt.Printf(" y = %v\n", cpmodel.SolutionIntegerValue(response, y))
		fmt.Printf(" z = %v\n", cpmodel.SolutionIntegerValue(response, z))
	}

	return nil
}

func main() {
	if err := solveWithTimeLimitSampleSat(); err != nil {
		log.Exitf("solveWithTimeLimitSampleSat returned with error: %v", err)
	}
}

```

## Printing intermediate solutions

In an optimization model, you can print intermediate solutions. For all
languages except Go, you need to register a callback on the solver that will be
called at each solution. For Go, callbacks are not implemented, but you can
still get the intermediate solutions in the response.

The exact implementation depends on the target language.

### Python code

```python
# Snippet from ortools/sat/samples/solve_and_print_intermediate_solutions_sample_sat.py
from ortools.sat.python import cp_model


# You need to subclass the cp_model.CpSolverSolutionCallback class.
class VarArrayAndObjectiveSolutionPrinter(cp_model.CpSolverSolutionCallback):
  """Print intermediate solutions."""

  def __init__(self, variables: list[cp_model.IntVar]):
    cp_model.CpSolverSolutionCallback.__init__(self)
    self.__variables = variables
    self.__solution_count = 0

  def on_solution_callback(self) -> None:
    print(f'Solution {self.__solution_count}')
    print(f'  objective value = {self.objective_value}')
    for v in self.__variables:
      print(f'  {v}={self.value(v)}', end=' ')
    print()
    self.__solution_count += 1

  @property
  def solution_count(self) -> int:
    return self.__solution_count


def solve_and_print_intermediate_solutions_sample_sat():
  """Showcases printing intermediate solutions found during search."""
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
  solution_printer = VarArrayAndObjectiveSolutionPrinter([x, y, z])
  status = solver.solve(model, solution_printer)

  print(f'Status = {solver.status_name(status)}')
  print(f'Number of solutions found: {solution_printer.solution_count}')


solve_and_print_intermediate_solutions_sample_sat()
```

## Searching for all solutions in a satisfiability model

In an non-optimization model, you can search for all solutions. For all
languages except Go, you need to register a callback on the solver that will be
called at each solution. For Go, callbacks are not implemented, but you can
still get the intermediate solutions in the response.

Note that it does not work in parallel (i. e. parameter `num_workers` > 1).

It also does not work if the model contains an objective.

The method will return the following:

*   *FEASIBLE* if some solutions have been found
*   *INFEASIBLE* if the solver has proved there are no solution
*   *OPTIMAL* if all solutions have been found

The exact implementation depends on the target language.

### Python code

To search for all solutions, use the Solve() method after setting the correct
parameter.

```python
# Snippet from ortools/sat/samples/search_for_all_solutions_sample_sat.py
from ortools.sat.python import cp_model


class VarArraySolutionPrinter(cp_model.CpSolverSolutionCallback):
  """Print intermediate solutions."""

  def __init__(self, variables: list[cp_model.IntVar]):
    cp_model.CpSolverSolutionCallback.__init__(self)
    self.__variables = variables
    self.__solution_count = 0

  def on_solution_callback(self) -> None:
    self.__solution_count += 1
    for v in self.__variables:
      print(f'{v}={self.value(v)}', end=' ')
    print()

  @property
  def solution_count(self) -> int:
    return self.__solution_count


def search_for_all_solutions_sample_sat():
  """Showcases calling the solver to search for all solutions."""
  # Creates the model.
  model = cp_model.CpModel()

  # Creates the variables.
  num_vals = 3
  x = model.new_int_var(0, num_vals - 1, 'x')
  y = model.new_int_var(0, num_vals - 1, 'y')
  z = model.new_int_var(0, num_vals - 1, 'z')

  # Create the constraints.
  model.add(x != y)

  # Create a solver and solve.
  solver = cp_model.CpSolver()
  solution_printer = VarArraySolutionPrinter([x, y, z])
  # Enumerate all solutions.
  solver.parameters.enumerate_all_solutions = True
  # Solve.
  status = solver.solve(model, solution_printer)

  print(f'Status = {solver.status_name(status)}')
  print(f'Number of solutions found: {solution_printer.solution_count}')


search_for_all_solutions_sample_sat()
```

## Stopping search early

Sometimes, you might decide that the current solution is good enough. In this
section, we will enumerate all possible combinations of three variables, and
stop after the fifth combination found.

### Python code

You can stop the search by calling StopSearch() inside of
CpSolverSolutionCallback.OnSolutionCallback().

```python
# Snippet from ortools/sat/samples/stop_after_n_solutions_sample_sat.py
"""Code sample that solves a model and displays a small number of solutions."""

from ortools.sat.python import cp_model


class VarArraySolutionPrinterWithLimit(cp_model.CpSolverSolutionCallback):
  """Print intermediate solutions."""

  def __init__(self, variables: list[cp_model.IntVar], limit: int):
    cp_model.CpSolverSolutionCallback.__init__(self)
    self.__variables = variables
    self.__solution_count = 0
    self.__solution_limit = limit

  def on_solution_callback(self) -> None:
    self.__solution_count += 1
    for v in self.__variables:
      print(f'{v}={self.value(v)}', end=' ')
    print()
    if self.__solution_count >= self.__solution_limit:
      print(f'Stop search after {self.__solution_limit} solutions')
      self.stop_search()

  @property
  def solution_count(self) -> int:
    return self.__solution_count


def stop_after_n_solutions_sample_sat():
  """Showcases calling the solver to search for small number of solutions."""
  # Creates the model.
  model = cp_model.CpModel()
  # Creates the variables.
  num_vals = 3
  x = model.new_int_var(0, num_vals - 1, 'x')
  y = model.new_int_var(0, num_vals - 1, 'y')
  z = model.new_int_var(0, num_vals - 1, 'z')

  # Create a solver and solve.
  solver = cp_model.CpSolver()
  solution_printer = VarArraySolutionPrinterWithLimit([x, y, z], 5)
  # Enumerate all solutions.
  solver.parameters.enumerate_all_solutions = True
  # Solve.
  status = solver.solve(model, solution_printer)
  print(f'Status = {solver.status_name(status)}')
  print(f'Number of solutions found: {solution_printer.solution_count}')
  assert solution_printer.solution_count == 5


stop_after_n_solutions_sample_sat()
```
