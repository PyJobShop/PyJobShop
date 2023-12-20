from dataclasses import dataclass
from typing import Union

from pyjobshop.Model import Model
from pyjobshop.ProblemData import Job


@dataclass
class Completion:
    job: Job


@dataclass
class FlowTime:
    job: Job


@dataclass
class Tardiness:
    job: Job


@dataclass
class Lateness:
    job: Job


@dataclass
class Earliness:
    job: Job


Primitive = Union[float, Completion, Earliness, Tardiness, Lateness, FlowTime]


# Expressions
class Expression:
    items: list[Union["Expression", Primitive]]


@dataclass
class Max(Expression):
    items: list[Union[Expression, Primitive]]


@dataclass
class Min(Expression):
    items: list[Union[Expression, Primitive]]


@dataclass
class Sum(Expression):
    items: list[Union[Expression, Primitive]]


# Expressions
class Makespan(Expression):
    def __init__(self, jobs: list[Job]):
        self.items = [Max([Completion(job) for job in jobs])]


class TotalTardiness(Sum):
    def __init__(self, jobs: list[Job]):
        self.items = [Tardiness(job) for job in jobs]


class TotalEarliness(Sum):
    def __init__(self, jobs: list[Job]):
        self.items = [Earliness(job) for job in jobs]


class TotalLateness(Sum):
    def __init__(self, jobs: list[Job]):
        self.items = [Lateness(job) for job in jobs]


class TotalFlowTime(Sum):
    def __init__(self, jobs: list[Job]):
        self.items = [FlowTime(job) for job in jobs]


class TotalCompletionTime(Sum):
    def __init__(self, jobs: list[Job]):
        self.items = [Completion(job) for job in jobs]


def traverse_expr(expr):
    if isinstance(expr, Expression):
        if isinstance(expr, Max):
            print("Max")
        elif isinstance(expr, Min):
            print("Min")
        elif isinstance(expr, Sum):
            print("Sum")

        for arg in expr.items:
            traverse_expr(arg)

    elif isinstance(expr, (float, Completion, Earliness, Tardiness, Lateness)):
        # These are "leaves", we do something useful with them here.
        handle_primitive(expr)
    else:
        raise ValueError(f"Unexpected type: {type(expr)}")


def handle_primitive(prim):
    print(type(prim).__name__, prim.job)


model = Model()

jobs = [model.add_job() for _ in range(10)]

model.add_objective("makespan")


job1 = model.add_job()
job2 = model.add_job()
job3 = model.add_job()

traverse_expr(TotalTardiness(jobs))
