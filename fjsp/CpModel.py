from itertools import product
from typing import Optional, Union

from docplex.cp.expression import CpoIntervalVar, CpoSequenceVar
from docplex.cp.model import CpoModel
from docplex.cp.solution import CpoSolveResult

from .ProblemData import Machine, Operation, ProblemData, Silo
from .Solution import ScheduledOperation, Solution


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


def create_cp_model(data: ProblemData) -> CpModel:
    """
    Creates a CP model for the given problem data.
    """
    m = CpModel()

    for op in data.operations:
        m.add_interval_var("O", op)

        for idx, machine in enumerate(op.machines):
            var = m.add_interval_var("A", op, machine, optional=True)

            if op.durations[idx] > 0:
                # If there is non-zero duration, then the duration is fixed.
                # This assumes that there is no blocking on the machine.
                # NOTE This considerably speeds up the model.
                m.add(m.size_of(var) == op.durations[idx] * m.presence_of(var))

            # Operation may not start before the job's release date if present.
            m.add(m.start_of(var) >= op.job.release_date * m.presence_of(var))

    for machine, ops in data.machine2ops.items():
        # Define a operation sequence variable for each machine.
        # For non-silos, this is defined on the operation interval variables.
        # For silos, this is defined on the product interval variables.
        if not isinstance(machine, Silo):
            intervals = [m.get_var("A", op, machine) for op in ops]
            m.add_sequence_var("S", machine, vars=intervals)
        else:
            product_types = {op.product_type for op in ops}
            product_vars = []

            # Create an optional interval variable for each product type.
            for product_type in product_types:
                var = m.add_interval_var(
                    "P", product_type, machine, optional=True
                )
                product_vars.append(var)

                # Each product optional interval variable spans the operations
                # with the same product type.
                op_intervals = [
                    m.get_var("A", op, machine)
                    for op in ops
                    if op.product_type == product_type
                ]
                m.add(m.span(var, op_intervals))

            # Then create a sequence variable for the machine using the product
            # interval variables.
            m.add_sequence_var("S", machine, vars=product_vars)

    # Objective: minimize the makespan
    completion_times = [m.end_of(m.get_var("O", op)) for op in data.operations]
    m.add(m.minimize(m.max(completion_times)))

    # Obey the operation timing precedence constraints.
    for frm, to, attr in data.operations_graph.edges(data=True):
        frm = m.get_var("O", data.operations[frm])
        to = m.get_var("O", data.operations[to])

        for prec_type in attr["precedence_types"]:
            if prec_type == "start_at_start":
                m.add(m.start_at_start(frm, to))
            elif prec_type == "start_at_end":
                m.add(m.start_at_end(frm, to))
            elif prec_type == "start_before_start":
                m.add(m.start_before_start(frm, to))
            elif prec_type == "start_before_end":
                m.add(m.start_before_end(frm, to))
            elif prec_type == "end_at_start":
                m.add(m.end_at_start(frm, to))
            elif prec_type == "end_at_end":
                m.add(m.end_at_end(frm, to))
            elif prec_type == "jnd_before_start":
                m.add(m.end_before_start(frm, to))
            elif prec_type == "end_before_end":
                m.add(m.end_before_end(frm, to))

    # Obey the operation ordering precedence constraints.
    for machine, ops in data.machine2ops.items():
        seq_var = m.get_var("S", machine)

        for op1, op2 in product(ops, repeat=2):
            if op1 == op2:
                continue

            if (op1.idx, op2.idx) not in data.operations_graph.edges:
                continue

            var1 = m.get_var("A", op1, machine)
            var2 = m.get_var("A", op2, machine)
            edge = data.operations_graph.edges[op1.idx, op2.idx]

            for prec_type in edge["precedence_types"]:
                if prec_type == "previous":
                    m.add(m.previous(seq_var, var1, var2))
                elif prec_type == "before":
                    m.add(m.before(seq_var, var1, var2))
                elif prec_type == "same_unit":
                    m.add(m.presence_of(var1) == m.presence_of(var2))

    # An operation must be scheduled on exactly one machine.
    for op in data.operations:
        must = m.get_var("O", op)
        optional = [m.get_var("A", op, mach) for mach in op.machines]
        m.add(m.alternative(must, optional))

    # Operations on a given processing machine cannot overlap.
    for machine in data.machines:
        m.add(m.no_overlap(m.get_var("S", machine)))

    # On silos, we allow overlap between operations of the same type,
    # as long as their is enough capacity.
    for silo in data.machines:
        if not isinstance(silo, Silo):
            continue

        ops = data.machine2ops[silo]

        # Load of operations may not exceed the capacity of the silo.
        expr = [m.pulse(m.get_var("A", op, silo), op.load) for op in ops]
        assert silo.capacity is not None
        m.add(sum(expr) <= silo.capacity)

    # Impose machine accessibility restrictions on precedent operations.
    # If an operation is scheduled on a machine, the next operation can only
    # be scheduled on a machine that is accessible from the current machine.
    for i, j in data.operations_graph.edges:
        op1, op2 = data.operations[i], data.operations[j]

        for m1, m2 in product(op1.machines, op2.machines):
            if m1 == m2:
                continue

            # # TODO this results in a lot of extra redundant constraints.
            # if (m1.idx, m2.idx) not in data.machine_graph.edges:
            #     # If (m1 -> m2) is not an edge in the machine graph, then
            #     # we cannot schedule operation 1 on m1 and operation 2 on m2.
            #     frm_var = m.get_var("A", op1, m1)
            #     to_var = m.get_var("A", op2, m2)
            #     m.add(m.presence_of(frm_var) + m.presence_of(to_var) <= 1)

    # Same sequence on machines that are related.
    for k, l, attr in data.machine_graph.edges(data=True):
        if attr["same_sequence"]:
            seq_k = m.get_var("S", data.machines[k])
            seq_l = m.get_var("S", data.machines[l])
            m.add(m.same_sequence(seq_k, seq_l))

    return m


def result2solution(data: ProblemData, result: CpoSolveResult) -> Solution:
    """
    Maps a ``CpoSolveResult`` object to a ``Solution`` object.
    """
    schedule = []

    for var in result.get_all_var_solutions():
        name = var.get_name()

        # Scheduled operations are inferred from variables start with an "A"
        # (assignment) and that are present in the solution.
        if name.startswith("A") and var.is_present():
            op_idx, mach_idx = [int(num) for num in name.split("_")[1:]]
            op = data.operations[op_idx]
            start = var.start
            duration = var.size

            schedule.append(ScheduledOperation(op, mach_idx, start, duration))

    return Solution(data, schedule)
