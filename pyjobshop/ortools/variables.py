from collections import defaultdict
from dataclasses import dataclass

from ortools.sat.python.cp_model import BoolVarT, CpModel, IntervalVar, IntVar

from pyjobshop.ProblemData import ProblemData


@dataclass
class JobVar:
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class OperationVar:
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class AssignmentVar:
    """
    Variables that represent an assignment of a task to a machine.

    Parameters
    ----------
    task_idx
        The index of the task.
    interval
        The interval variable representing the assignment of the task.
    start
        The start variable time of the interval.
    duration
        The duration variable of the interval.
    end
        The end variable time of the interval.
    is_present
        The boolean variable indicating whether the interval is present.
    rank
        The rank variable of the interval on the machine. Used to order the
        intervals in the sequence variable of the machine.
    """

    task_idx: int
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar
    is_present: IntVar
    rank: IntVar  # the rank of the task on machine


@dataclass
class SequenceVar:
    """
    Represents a sequence of tasks assigned to a machine.

    Parameters
    ----------
    tasks
        The task variables in the sequence.
    starts
        The start literals for each task.
    ends
        The end literals for each task.
    arcs
        The arc literals between each pair of tasks. Keys are tuples of
        indices.
    is_active
        A boolean that indicates whether the sequence is active, meaning that a
        circuit constraint must be added for this machine. Default ``False``.
    """

    tasks: list[AssignmentVar]
    starts: list[BoolVarT]
    ends: list[BoolVarT]
    arcs: dict[tuple[int, int], BoolVarT]
    is_active: bool = False

    def activate(self):
        """
        Activates the sequence variable, meaning that a circuit constraint
        must be added for this machine.
        """
        self.is_active = True


def job_variables(m: CpModel, data: ProblemData) -> list[JobVar]:
    """
    Creates an interval variable for each job.
    """
    jobs = []

    for job in data.jobs:
        name = f"J{job}"
        start_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        duration_var = m.NewIntVar(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.NewIntVar(0, data.planning_horizon, f"{name}_end")
        interval_var = m.NewIntervalVar(
            start_var, duration_var, end_var, f"interval_{job}"
        )
        jobs.append(JobVar(interval_var, start_var, duration_var, end_var))

    return jobs


def operation_variables(m: CpModel, data: ProblemData) -> list[OperationVar]:
    """
    Creates an interval variable for each operation.
    """
    tasks = []

    for op in data.operations:
        name = f"O{op}"
        start_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        duration_var = m.NewIntVar(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.NewIntVar(0, data.planning_horizon, f"{name}_end")
        interval_var = m.NewIntervalVar(
            start_var, duration_var, end_var, f"interval_{op}"
        )
        op_var = OperationVar(interval_var, start_var, duration_var, end_var)
        tasks.append(op_var)

    return tasks


def assignment_variables(
    m: CpModel, data: ProblemData
) -> dict[tuple[int, int], AssignmentVar]:
    """
    Creates an interval variable for each operation and eligible machine pair.
    """
    variables = {}

    for (machine, op), duration in data.processing_times.items():
        name = f"A{op}_{machine}"
        start_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        duration_var = m.NewIntVar(
            0, data.planning_horizon, f"{name}_duration"
        )
        end_var = m.NewIntVar(0, data.planning_horizon, f"{name}_start")
        is_present_var = m.NewBoolVar(f"{name}_is_present")
        interval_var = m.NewOptionalIntervalVar(
            start_var,
            duration_var,
            end_var,
            is_present_var,
            f"{name}_interval",
        )
        rank_var = m.NewIntVar(-1, data.num_jobs, f"{name}_rank")
        variables[op, machine] = AssignmentVar(
            task_idx=op,
            interval=interval_var,
            start=start_var,
            duration=duration_var,
            end=end_var,
            is_present=is_present_var,
            rank=rank_var,
        )

        m.Add(duration_var >= duration)

    return variables


def sequence_variables(
    m: CpModel, data: ProblemData, assign: dict[tuple[int, int], AssignmentVar]
) -> list[SequenceVar]:
    """
    Creates a sequence variable for each machine. Sequence variables are used
    to model the ordering of intervals on a given machine. This is used for
    modeling machine setups and sequencing task constraints, such as previous,
    before, first, last and permutations.
    """
    variables = []

    # Group the assignment variables by machine.
    machine2tasks = defaultdict(list)
    for (_, machine), var in assign.items():
        machine2tasks[machine].append(var)

    for machine in range(data.num_machines):
        tasks = machine2tasks[machine]
        num_tasks = len(tasks)

        # Start and end literals define whether the corresponding interval
        # is first or last in the sequence, respectively.
        starts = [m.NewBoolVar("") for _ in range(num_tasks)]
        ends = [m.NewBoolVar("") for _ in range(num_tasks)]

        # Arc literals indicate if two intervals are scheduled consecutively.
        arcs = {
            (i, j): m.NewBoolVar(f"{i}->{j}")
            for i in range(num_tasks)
            for j in range(num_tasks)
        }

        variables.append(SequenceVar(tasks, starts, ends, arcs))

    return variables
