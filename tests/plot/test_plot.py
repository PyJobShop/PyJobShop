from matplotlib.testing.decorators import image_comparison as img_comp

from pyjobshop.plot import (
    plot_machine_gantt,
    plot_resource_gantt,
    plot_resource_usage,
    plot_task_gantt,
)

IMG_KWARGS = {
    "remove_text": True,
    "tol": 8,
    "extensions": ["png"],
    "style": "mpl20",
}


@img_comp(["plot_machine_gantt"], **IMG_KWARGS)
def test_plot_machine_gantt():
    data = ...
    sol = ...

    plot_machine_gantt(sol, data)


@img_comp(["plot_resource_gantt"], **IMG_KWARGS)
def test_plot_resource_gantt():
    data = ...
    sol = ...

    plot_resource_gantt(sol, data)


@img_comp(["plot_resource_usage"], **IMG_KWARGS)
def test_plot_resource_usage():
    data = ...
    sol = ...

    plot_resource_usage(sol, data)


@img_comp(["plot_task_gantt"], **IMG_KWARGS)
def test_plot_task_gantt():
    data = ...
    sol = ...

    plot_task_gantt(sol, data)
