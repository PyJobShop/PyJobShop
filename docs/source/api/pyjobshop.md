# PyJobShop API

The public API is organized around a few core objects. Use the overview below
to jump to the high-level concepts, then use the detailed reference for
signatures, parameter tables, and return values.

<div class="api-overview-grid">

<a class="api-overview-card" href="#modeling-interface">
<strong>Modeling</strong>
<span>Build scheduling problems incrementally with <code>Model</code>, jobs,
resources, tasks, and modes.</span>
</a>

<a class="api-overview-card" href="#problem-data">
<strong>Problem data</strong>
<span>Inspect and serialize immutable scheduling instances with
<code>ProblemData</code>.</span>
</a>

<a class="api-overview-card" href="#constraint-types">
<strong>Constraints</strong>
<span>Represent timing, resource, sequencing, setup-time, and selection
rules.</span>
</a>

<a class="api-overview-card" href="#solutions-and-results">
<strong>Solutions</strong>
<span>Work with solver output, scheduled tasks, job metrics, and solve
status.</span>
</a>

</div>

## Modeling interface

::: pyjobshop.Model.Model

## Problem data

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

## Solutions and results

::: pyjobshop.Solution.Solution

::: pyjobshop.Solution.ScheduledTask

::: pyjobshop.Solution.ScheduledJob

::: pyjobshop.Result.Result

::: pyjobshop.Result.SolveStatus

## Helper functions and constants

::: pyjobshop.solve.solve

::: pyjobshop.constants
