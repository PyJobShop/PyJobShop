# Copyright (c) 2019 Hakan Kjellerstrand
#
# Utilities for OR-Tools CP-SAT solver.
#
# This package was created by Hakan Kjellerstrand (hakank@gmail.com)
# See my other Google OR-tools models: http://www.hakank.org/or_tools/
#
from ortools.sat.python.cp_model import (
    CpModel,
    IntVar,
)


def new_count_var(
    model: CpModel, array: list[IntVar], val: int | IntVar
) -> IntVar:
    """
    # NOTE: keep this!
    Creates a new integer variable representing the number of occurrences of
    a value in an array.

    Parameters
    ----------
    model
        The CP model.
    array
        Array of variables to search.
    value
        Value to count (can be constant or variable).
    """
    size = len(array)
    count_var = model.new_int_var(0, size, "count")
    is_equal = [model.new_bool_var(f"b[{i}]") for i in range(size)]

    for idx in range(size):
        model.add(array[idx] == val).only_enforce_if(is_equal[idx])
        model.add(array[idx] != val).only_enforce_if(~is_equal[idx])

    model.add(count_var == sum(is_equal))
    return count_var


def at_most(model: CpModel, val: int | IntVar, x: list[IntVar], n: int):
    """
    Constrain at most n occurrences of value val in array x.

    Parameters
    ----------
    model
        The CP model.
    val
        Value to count.
    x
        Array of variables.
    n
        Maximum number of occurrences.
    """
    count_var = new_count_var(model, x, val)
    model.add(count_var <= n)


def at_least(model: CpModel, val: int | IntVar, x: list[IntVar], n: int):
    """
    Constrain at least n occurrences of value val in array x.

    Parameters
    ----------
    model
        The CP model.
    val
        Value to count.
    x
        Array of variables.
    n
        Minimum number of occurrences.
    """
    count_var = new_count_var(model, x, val)
    model.add(count_var >= n)


def exactly(model: CpModel, val: int | IntVar, x: list[IntVar], n: int):
    """
    Constrain exactly n occurrences of value val in array x.

    Parameters
    ----------
    model
        The CP model.
    val
        Value to count.
    x
        Array of variables.
    n
        Exact number of occurrences.
    """
    count_var = new_count_var(model, x, val)
    model.add(count_var == n)


def all_different_except_0(model: CpModel, a: list[IntVar]):
    """
    Ensure all non-zero values are distinct.

    All values in array a that are not equal to 0 must be different
    from each other. Values equal to 0 can repeat.

    Parameters
    ----------
    model
        The CP model.
    a
        Array of variables.
    """
    n = len(a)
    # ba[i] <=> a[i] != 0
    ba = [model.new_bool_var(f"ba[{i}]") for i in range(n)]
    for i in range(n):
        model.add(a[i] != 0).only_enforce_if(ba[i])
        model.add(a[i] == 0).only_enforce_if(~ba[i])

    for i in range(n):
        for j in range(i):
            # ba[i] && ba[j] -> a[i] != a[j]
            b = model.new_bool_var(f"b[{i},{j}]")
            model.add_bool_and([ba[i], ba[j]]).only_enforce_if(b)
            model.add_bool_or([~ba[i], ~ba[j]]).only_enforce_if(~b)
            model.add(a[i] != a[j]).only_enforce_if(b)


def scalar_product(
    model: CpModel, x: list[IntVar], y: list[IntVar], s: IntVar
):
    """
    Constrain s to equal the scalar product of x and y.

    Implements s = sum(x[i] * y[i] for i in range(n)).
    Both x and y can be decision variables.

    Parameters
    ----------
    model
        The CP model.
    x
        First array of variables.
    y
        Second array of variables.
    s
        Variable that will equal the scalar product.
    """
    n = len(x)
    slb, sub = s.proto.domain
    t = [model.new_int_var(slb, sub, "") for _ in range(n)]
    for i in range(n):
        model.add_multiplication_equality(t[i], [x[i], y[i]])
    model.add(s == sum(t))


def my_cumulative(
    model: CpModel,
    s: list[IntVar],
    d: list[int],
    r: list[int],
    b: IntVar | int,
):
    """
    Decomposition of cumulative constraint.

    Enforces that for each job i:
    - s[i] is the start time
    - d[i] is the duration
    - r[i] is the resource requirement

    b is the resource limit. The constraint ensures that at no point in time
    the total resource usage exceeds b.

    Inspired by the MiniZinc implementation. See:
    - http://www.cs.mu.oz.au/~pjs/rcpsp/papers/cp09-cu.pdf
    - http://www.cs.mu.oz.au/~pjs/rcpsp/cumu_lazyfd.pdf

    Parameters
    ----------
    model
        The CP model.
    s
        Start time variables.
    d
        Durations (array of integers).
    r
        Resource requirements (array of integers).
    b
        Resource limit (variable or constant).
    """
    max_r = max(r)

    tasks = [i for i in range(len(s)) if r[i] > 0 and d[i] > 0]

    # CP-SAT uses var.proto.domain for lower/upper bounds
    lb = [s[i].proto.domain[0] for i in tasks]
    ub = [s[i].proto.domain[1] for i in tasks]

    times_min = min(lb)
    times_max = max(ub)

    for t in range(times_min, times_max + 1):
        bb = []
        for i in tasks:
            # s[i] <= t
            b1 = model.new_bool_var("")
            model.add(s[i] <= t).only_enforce_if(b1)
            model.add(s[i] > t).only_enforce_if(~b1)

            # t < s[i] + d[i]
            b2 = model.new_bool_var("")
            model.add(t < s[i] + d[i]).only_enforce_if(b2)
            model.add(t >= s[i] + d[i]).only_enforce_if(~b2)

            # b1 and b2
            b3 = model.new_bool_var("")
            model.add_bool_and([b1, b2]).only_enforce_if(b3)
            model.add_bool_or([~b1, ~b2]).only_enforce_if(~b3)

            # b3 * r[i]
            b4 = model.new_int_var(0, max_r, "b4")
            model.add_multiplication_equality(b4, [b3, r[i]])
            bb.append(b4)

        model.add(sum(bb) <= b)

    # Constrain upper limit of b if it's a variable
    if not isinstance(b, int):
        model.add(b <= sum(r))


def global_cardinality(
    model: CpModel, x: list[IntVar], domain: list[int], gcc: list[IntVar]
):
    """
    Global cardinality constraint.

    For each value in domain, gcc counts the number of occurrences in x.
    The length of domain must equal the length of gcc.

    Parameters
    ----------
    model
        The CP model.
    x
        Array of variables.
    domain
        Array of values to count.
    gcc
        Array of count variables.
    """
    assert len(gcc) == len(domain)
    for i in range(len(domain)):
        count_var = new_count_var(model, x, domain[i])
        model.add(gcc[i] == count_var)
