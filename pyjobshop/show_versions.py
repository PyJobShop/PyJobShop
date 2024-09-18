import sys
from importlib.metadata import PackageNotFoundError, version


def _version(name: str) -> str:
    """
    Lightweight wrapper around ``importlib.metadata.version()`` to deal with
    optional dependencies.
    """
    try:
        return version(name)
    except PackageNotFoundError:
        return "not installed"


def show_versions():
    """
    This function prints version information that is useful when filing bug
    reports.

    Examples
    --------
    Calling this function should print information like the following
    (dependency versions in your local installation will likely differ):

    >>> import pyjobshop
    >>> pyjobshop.show_versions()
    INSTALLED VERSIONS
    ------------------
     pyjobshop: 0.0.2b0
    matplotlib: 3.9.2
       ortools: 9.10.4067
    enum-tools: 0.12.0
       docplex: 2.28.240
         cplex: not installed
          tqdm: 4.66.5
         tomli: 2.0.1
        Python: 3.10.10
    """
    python_version = ".".join(map(str, sys.version_info[:3]))

    print("INSTALLED VERSIONS")
    print("------------------")
    print(f" pyjobshop: {_version('pyjobshop')}")
    print(f"matplotlib: {_version('matplotlib')}")
    print(f"   ortools: {_version('ortools')}")
    print(f"enum-tools: {_version('enum_tools')}")
    print(f"   docplex: {_version('docplex')}")
    print(f"     cplex: {_version('cplex')}")
    print(f"      tqdm: {_version('tqdm')}")
    print(f"     tomli: {_version('tomli')}")
    print(f"    Python: {python_version}")
