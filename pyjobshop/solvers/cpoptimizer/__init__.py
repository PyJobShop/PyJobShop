try:
    from .Solver import Solver as Solver
except ModuleNotFoundError:
    msg = (
        "CP Optimizer solver requires the 'docplex' package. "
        "Install it with: pip install pyjobshop[docplex]"
    )
    raise ModuleNotFoundError(msg) from None
