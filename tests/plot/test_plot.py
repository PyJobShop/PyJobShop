from matplotlib.testing.decorators import image_comparison as img_comp

from pyjobshop import Model
from pyjobshop import solve as _solve
from pyjobshop.plot import (
    plot_machine_gantt,
    plot_resource_usage,
    plot_task_gantt,
)
from tests.utils import read

IMG_KWARGS = {
    "remove_text": True,
    "tol": 8,
    "extensions": ["png"],
    "style": "mpl20",
}


@img_comp(["plot_machine_gantt"], **IMG_KWARGS)
def test_plot_machine_gantt():
    data = read("data/small.fjs")
    result = solve(data)
    sol = result.best

    plot_machine_gantt(sol, data)


@img_comp(["plot_resource_usage"], **IMG_KWARGS)
def test_plot_resource_usage():
    model = Model()
    resources = [
        model.add_machine(name="Machine"),
        model.add_renewable(capacity=5, name="Renewable"),
        model.add_non_renewable(capacity=2, name="Non-renewable"),
    ]

    for idx in [1, 2]:
        task = model.add_task()
        model.add_mode(task, resources, duration=idx * 10, demands=[0, idx, 1])

    data = model.data()
    result = solve(data)
    sol = result.best

    plot_resource_usage(sol, data)


@img_comp(["plot_task_gantt"], **IMG_KWARGS)
def test_plot_task_gantt():
    data = read("data/small.mm", instance_format="psplib")
    result = solve(data)
    sol = result.best

    plot_task_gantt(sol, data)


def solve(data):
    """
    Wrapper around ``solve`` to provide deterministic results with
    OR-Tools, because parallel solves are non-deterministic.
    """
    return _solve(data, num_workers=1)
