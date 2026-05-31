# PyJobShop API

::: pyjobshop.Model.Model

::: pyjobshop.ProblemData.ProblemData

::: pyjobshop.ProblemData.Job

::: pyjobshop.ProblemData.Machine

::: pyjobshop.ProblemData.Renewable

::: pyjobshop.ProblemData.Consumable

::: pyjobshop.ProblemData.Task

::: pyjobshop.ProblemData.Mode

## Constraint types

::: pyjobshop.ProblemData.StartBeforeStart

::: pyjobshop.ProblemData.StartBeforeEnd

::: pyjobshop.ProblemData.EndBeforeStart

::: pyjobshop.ProblemData.EndBeforeEnd

::: pyjobshop.ProblemData.StartAtStart

::: pyjobshop.ProblemData.StartAtEnd

::: pyjobshop.ProblemData.EndAtStart

::: pyjobshop.ProblemData.EndAtEnd

::: pyjobshop.ProblemData.IdenticalResources

::: pyjobshop.ProblemData.DifferentResources

::: pyjobshop.ProblemData.Consecutive

::: pyjobshop.ProblemData.SameSequence
    options:
      filters:
        - "!^tasks1$"
        - "!^tasks2$"

::: pyjobshop.ProblemData.SetupTime

::: pyjobshop.ProblemData.ModeDependency

::: pyjobshop.ProblemData.SelectAllOrNone
    options:
      filters:
        - "!^condition_task$"

::: pyjobshop.ProblemData.SelectAtLeastOne
    options:
      filters:
        - "!^condition_task$"

::: pyjobshop.ProblemData.SelectExactlyOne
    options:
      filters:
        - "!^condition_task$"

::: pyjobshop.ProblemData.Constraints
    options:
      filters:
        - "!^__len__$"

::: pyjobshop.ProblemData.Objective

::: pyjobshop.Solution.Solution

::: pyjobshop.Solution.ScheduledTask

::: pyjobshop.Solution.ScheduledJob

::: pyjobshop.Result.Result

::: pyjobshop.Result.SolveStatus

::: pyjobshop.solve.solve

::: pyjobshop.constants
