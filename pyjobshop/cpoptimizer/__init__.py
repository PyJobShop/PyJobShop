try:
    from .Solver import Solver as Solver
except ModuleNotFoundError:
    msg = (
        "Using CP Optimizer requires the relevant dependencies to be "
        "installed. You can install those using `pip install "
        "pyjobshop[cpoptimizer]`."
    )
    raise ModuleNotFoundError(msg) from None
