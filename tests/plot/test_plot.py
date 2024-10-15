from matplotlib.testing.decorators import image_comparison as img_comp

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
    data = read("data/c154_3.mm", instance_format="psplib")
    result = solve(data)
    sol = result.best

    plot_resource_usage(sol, data)


@img_comp(["plot_task_gantt"], **IMG_KWARGS)
def test_plot_task_gantt():
    data = read("data/c154_3.mm", instance_format="psplib")
    result = solve(data)
    sol = result.best

    plot_task_gantt(sol, data)


def solve(data):
    """
    Wrapper around ``solve`` to provide deterministic results with
    OR-Tools.
    """
    return _solve(data, num_workers=1)  # parallel is non-deterministic
