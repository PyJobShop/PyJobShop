from typing import Optional, Union

from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel

from fjsp.ProblemData import Machine, Operation, Silo


class CpModel(CpoModel):
    """
    Wrapper around ``docplex.cp.model.CpoModel`` with opinionated naming of
    interval and sequence variables.
    """

    def __init__(self):
        super().__init__()

        self._variables = {}

    def add_interval_var(
        self,
        letter: str,
        *args: Union[int, Optional[str], Operation, Machine],
        **kwargs,
    ) -> CpoIntervalVar:
        """
        Adds and names an interval variable with the given letter and arguments.
        """
        name = self._name_var(letter, *args)
        var = self.interval_var(name=name, **kwargs)
        self._variables[name] = var
        return var

    def add_sequence_var(
        self,
        letter: str,
        *args: Union[int, Optional[str], Operation, Machine],
        **kwargs,
    ) -> CpoSequenceVar:
        """
        Adds and names a sequence variable with the given letter and arguments.
        """
        name = self._name_var(letter, *args)
        var = self.sequence_var(name=name, **kwargs)
        self._variables[var.name] = var
        return var

    def get_var(
        self, letter: str, *args: Union[int, Optional[str], Operation, Machine]
    ):
        """
        Returns the variable with the given letter and arguments.

        Parameters
        ----------
        letter: str
            The letter of the variable type.
        args: list
            List of data objects (operation, product types, machines, etc.).
        """
        return self._variables[self._name_var(letter, *args)]

    def _name_var(
        self, letter: str, *args: Union[int, Optional[str], Operation, Machine]
    ):
        """
        Returns the name of the variable with the given letter and arguments.

        Parameters
        ----------
        letter: str
            The letter of the variable type.
        args: list
            List of data objects (operation, product types, machines, etc.).
        """
        if letter == "A":
            op, machine = args
            assert isinstance(op, Operation)
            assert isinstance(machine, Machine)

            return f"A_{op.idx}_{machine.idx}"
        elif letter == "O":
            op = args[0]
            assert isinstance(op, Operation)

            return f"O_{op.idx}"
        elif letter == "S":
            machine = args[0]
            assert isinstance(machine, Machine)

            return f"S_{machine.idx}"
        elif letter == "P":
            product_type, machine = args
            assert isinstance(machine, Silo)

            return f"P_{product_type}_{machine.idx}"
        else:
            raise ValueError(f"Unknown variable type: {letter}")
