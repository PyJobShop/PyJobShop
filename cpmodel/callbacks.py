from threading import Timer

from ortools.sat.python.cp_model import (
    CpSolverSolutionCallback,
    IntVar,
)


class SimpleSolutionPrinter(CpSolverSolutionCallback):
    """
    Prints solution in one line.
    """

    def __init__(self, variables: list[IntVar]):
        super().__init__()
        self.__variables = variables
        self.__solution_count = 0

    def on_solution_callback(self):
        self.__solution_count += 1
        for var in self.__variables:
            print(f"{var} = {self.value(var)}", end=" ")
        print()

    def solution_count(self) -> int:
        return self.__solution_count


class NoImprovement(CpSolverSolutionCallback):
    """
    Stops the search if no improved solution has been found for a given
    amount of time.

    Parameters
    ----------
    time_limit
        Time limit in seconds after which the search will stop if no improved
        solution has been found.
    """

    def __init__(self, time_limit: int):
        super().__init__()
        self._time_limit = time_limit
        self._timer = None
        self._reset_timer()

    def on_solution_callback(self):  # found improved solution
        self._reset_timer()

    def _reset_timer(self):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self._time_limit, self.stop_search)
        self._timer.start()
