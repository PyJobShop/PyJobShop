from dataclasses import dataclass, field
from itertools import product
from typing import Optional

import numpy as np
from ortools.sat.python.cp_model import (
    BoolVarT,
    CpModel,
    IntervalVar,
    IntVar,
    LinearExpr,
)

from pyjobshop.ProblemData import ProblemData
from pyjobshop.Solution import Solution
from pyjobshop.utils import compute_min_max_durations


@dataclass
class JobVar:
    """
    Variables that represent a job in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the job.
    start
        The start time variable of the interval.
    duration
        The duration variable of the interval.
    end
        The end time variable of the interval.
    """

    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class TaskVar:
    """
    Variables that represent a task in the problem.

    Parameters
    ----------
    interval
        The interval variable representing the task.
    start
        The start time variable of the interval.
    duration
        The duration variable of the interval.
    end
        The end time variable of the interval.
    """

    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar


@dataclass
class TaskAltVar:
    """
    Variables that represent an assignment of a task to a machine.

    Parameters
    ----------
    task_idx
        The index of the task.
    interval
        The optional interval variable representing the assignment of the task.
    start
        The start time variable of the interval.
    duration
        The duration variable of the interval.
    end
        The end time variable of the interval.
    is_present
        The boolean variable indicating whether the interval is present.
    """

    task_idx: int
    interval: IntervalVar
    start: IntVar
    duration: IntVar
    end: IntVar
    is_present: IntVar


@dataclass
class SequenceVar:
    """
    Represents a sequence of interval variables of task alternatives. Relevant
    sequence variables are lazily generated when activated by constraints that
    call the ``activate`` method.

    Parameters
    ----------
    task_alts
        The task alternative variables in the sequence.
    starts
        The start literals for each task.
    ends
        The end literals for each task.
    ranks
        The rank variables of each interval on the machine. Used to define the
        ordering of the intervals in the machine sequence.
    arcs
        The arc literals between each pair of intervals in the sequence.
        Keys are tuples of indices.
    is_active
        A boolean that indicates whether the sequence is active, meaning that a
        circuit constraint must be added for this machine. Default ``False``.
    """

    task_alts: list[TaskAltVar]
    starts: list[BoolVarT] = field(default_factory=list)
    ends: list[BoolVarT] = field(default_factory=list)
    ranks: list[IntVar] = field(default_factory=list)
    arcs: dict[tuple[int, int], BoolVarT] = field(default_factory=dict)
    is_active: bool = False

    def activate(self, m: CpModel):
        """
        Activates the sequence variable by creating all relevant literals.
        """
        if self.is_active:
            return

        self.is_active = True
        num_tasks = len(self.task_alts)

        # Start and end literals define whether the corresponding interval
        # is first or last in the sequence, respectively.
        self.starts = [m.new_bool_var("") for _ in range(num_tasks)]
        self.ends = [m.new_bool_var("") for _ in range(num_tasks)]

        # Rank variables define the position of the task in the sequence.
        self.ranks = [
            m.new_int_var(-1, num_tasks, "") for _ in range(num_tasks)
        ]

        # Arcs indicate if two intervals are scheduled consecutively.
        self.arcs = {
            (i, j): m.new_bool_var(f"{i}->{j}")
            for i in range(num_tasks)
            for j in range(num_tasks)
        }


class VariablesBuilder:
    """
    Helper class that creates the variables for the OR-Tools CP solver.
    """

    def __init__(self, m: CpModel, data: ProblemData):
        self.job_vars = self._job_variables(m, data)
        self.task_vars = self._task_variables(m, data)
        self.task_alt_vars = self._task_alternative_variables(m, data)
        self.sequence_vars = self._sequence_variables(
            m, data, self.task_alt_vars
        )

    def _job_variables(self, m: CpModel, data: ProblemData) -> list[JobVar]:
        """
        Creates an interval variable for each job.
        """
        variables = []

        for job in data.jobs:
            name = f"J{job}"
            start = m.new_int_var(
                lb=job.release_date,
                ub=data.horizon,
                name=f"{name}_start",
            )
            duration = m.new_int_var(
                lb=0,
                ub=min(job.deadline - job.release_date, data.horizon),
                name=f"{name}_duration",
            )
            end = m.new_int_var(
                lb=0,
                ub=min(job.deadline, data.horizon),
                name=f"{name}_end",
            )
            interval = m.NewIntervalVar(
                start, duration, end, f"{name}_interval"
            )
            variables.append(JobVar(interval, start, duration, end))

        return variables

    def _task_variables(self, m: CpModel, data: ProblemData) -> list[TaskVar]:
        """
        Creates an interval variable for each task.
        """
        variables = []
        min_durations, max_durations = compute_min_max_durations(data)

        for idx, task in enumerate(data.tasks):
            name = f"T{task}"
            start = m.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, data.horizon),
                name=f"{name}_start",
            )
            duration = m.new_int_var(
                lb=min_durations[idx],
                ub=max_durations[idx] if task.fixed_duration else data.horizon,
                name=f"{name}_duration",
            )
            end = m.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, data.horizon),
                name=f"{name}_end",
            )
            interval = m.NewIntervalVar(
                start, duration, end, f"interval_{task}"
            )
            variables.append(TaskVar(interval, start, duration, end))

        return variables

    def _task_alternative_variables(
        self, m: CpModel, data: ProblemData
    ) -> dict[tuple[int, int], TaskAltVar]:
        """
        Creates an optional interval variable for each eligible task and
        machine pair.

        Returns
        -------
        dict[tuple[int, int], TaskAltVar]
            A dictionary that maps each task index and machine index pair to
            its corresponding task alternative variable.
        """
        variables = {}

        for (
            task_idx,
            machine_idx,
        ), proc_time in data.processing_times.items():
            task = data.tasks[task_idx]
            machine = data.machines[machine_idx]
            name = f"A{task}_{machine}"
            start = m.new_int_var(
                lb=task.earliest_start,
                ub=min(task.latest_start, data.horizon),
                name=f"{name}_start",
            )
            duration = m.new_int_var(
                lb=proc_time,
                ub=proc_time if task.fixed_duration else data.horizon,
                name=f"{name}_duration",
            )
            end = m.new_int_var(
                lb=task.earliest_end,
                ub=min(task.latest_end, data.horizon),
                name=f"{name}_start",
            )
            is_present = m.new_bool_var(f"{name}_is_present")
            interval = m.new_optional_interval_var(
                start, duration, end, is_present, f"{name}_interval"
            )
            variables[task_idx, machine_idx] = TaskAltVar(
                task_idx=task_idx,
                interval=interval,
                start=start,
                duration=duration,
                end=end,
                is_present=is_present,
            )

        return variables

    def _sequence_variables(
        self,
        m: CpModel,
        data: ProblemData,
        task_alt_vars: dict[tuple[int, int], TaskAltVar],
    ) -> list[SequenceVar]:
        """
        Creates a sequence variable for each machine. Sequence variables are
        used to model the ordering of intervals on a given machine. This is
        used for modeling machine setups and sequencing task constraints, such
        as previous, before, first, last and permutations.
        """
        variables = []

        for machine in range(data.num_machines):
            tasks = data.machine2tasks[machine]
            alt_vars = [task_alt_vars[task, machine] for task in tasks]
            variables.append(SequenceVar(alt_vars))

        return variables


class ModelBuilder:
    """
    Handles the creation and solving of the OR-Tools CP model.
    """

    def __init__(self, data: ProblemData):
        self._data = data
        self._m = CpModel()
        self._variables = VariablesBuilder(self._m, data)
        self._objective = ObjectiveBuilder(
            self._m, data, self.job_vars, self.task_vars
        )

    @property
    def job_vars(self):
        return self._variables.job_vars

    @property
    def task_vars(self):
        return self._variables.task_vars

    @property
    def task_alt_vars(self):
        return self._variables.task_alt_vars

    @property
    def sequence_vars(self):
        return self._variables.sequence_vars

    def add_hint_to_vars(self, solution: Solution):
        """
        Adds hints to variables based on the given solution.
        """
        m, data = self._m, self._data
        job_vars, task_vars, task_alt_vars = (
            self.job_vars,
            self.task_vars,
            self.task_alt_vars,
        )

        for idx in range(data.num_jobs):
            job = data.jobs[idx]
            job_var = job_vars[idx]
            sol_tasks = [solution.tasks[task] for task in job.tasks]

            job_start = min(task.start for task in sol_tasks)
            job_end = max(task.end for task in sol_tasks)

            m.add_hint(job_var.start, job_start)
            m.add_hint(job_var.duration, job_end - job_start)
            m.add_hint(job_var.end, job_end)

        for idx in range(data.num_tasks):
            task_var = task_vars[idx]
            sol_task = solution.tasks[idx]

            m.add_hint(task_var.start, sol_task.start)
            m.add_hint(task_var.duration, sol_task.duration)
            m.add_hint(task_var.end, sol_task.end)

        for (task_idx, machine_idx), var in task_alt_vars.items():
            sol_task = solution.tasks[task_idx]

            m.add_hint(var.start, sol_task.start)
            m.add_hint(var.duration, sol_task.duration)
            m.add_hint(var.end, sol_task.end)
            m.add_hint(var.is_present, machine_idx == sol_task.machine)

    def job_spans_tasks(self):
        """
        Ensures that the job variables span the related task variables.
        """
        for idx, job in enumerate(self._data.jobs):
            job_var = self.job_vars[idx]
            task_start_vars = [
                self.task_vars[task].start for task in job.tasks
            ]
            task_end_vars = [self.task_vars[task].end for task in job.tasks]

            self._m.add_min_equality(job_var.start, task_start_vars)
            self._m.add_max_equality(job_var.end, task_end_vars)

    def select_one_task_alternative(self):
        """
        Selects one optional interval for each task alternative, ensuring that
        each task is scheduled on exactly one machine.
        """
        m, data = self._m, self._data
        task_vars, task_alt_vars = self.task_vars, self.task_alt_vars

        for task in range(data.num_tasks):
            presences = []

            for machine in data.task2machines[task]:
                main = task_vars[task]
                alt = task_alt_vars[task, machine]
                is_present = alt.is_present
                presences.append(is_present)

                # Sync each optional interval variable with the main variable.
                m.add(main.start == alt.start).only_enforce_if(is_present)
                m.add(main.duration == alt.duration).only_enforce_if(
                    is_present
                )
                m.add(main.end == alt.end).only_enforce_if(is_present)

            # Select exactly one optional interval variable for each task.
            m.add_exactly_one(presences)

    def no_overlap_machines(self):
        """
        Creates the no overlap constraints for machines, ensuring that no two
        intervals in a sequence variable are overlapping.
        """
        m, data = self._m, self._data
        seq_vars = self.sequence_vars

        for machine in range(data.num_machines):
            m.add_no_overlap(
                [var.interval for var in seq_vars[machine].task_alts]
            )

    def activate_setup_times(self):
        """
        Activates the sequence variables for machines that have setup times.
        The ``circuit_constraints`` function will in turn add constraints to
        the CP-SAT model to enforce setup times.
        """
        m, data = self._m, self._data
        seq_vars = self.sequence_vars

        for machine in range(data.num_machines):
            setup_times = data.setup_times[machine]

            if np.any(setup_times != 0):
                seq_vars[machine].activate(m)

    def task_graph(self):
        """
        Creates constraints based on the task graph, ensuring that the
        tasks are scheduled according to the graph.
        """
        m, data = self._m, self._data
        task_vars, task_alt_vars = self.task_vars, self.task_alt_vars
        seq_vars = self.sequence_vars

        for (idx1, idx2), constraints in data.constraints.items():
            task_var1 = task_vars[idx1]
            task_var2 = task_vars[idx2]

            for prec_type in constraints:
                if prec_type == "start_at_start":
                    expr = task_var1.start == task_var2.start
                elif prec_type == "start_at_end":
                    expr = task_var1.start == task_var2.end
                elif prec_type == "start_before_start":
                    expr = task_var1.start <= task_var2.start
                elif prec_type == "start_before_end":
                    expr = task_var1.start <= task_var2.end
                elif prec_type == "end_at_start":
                    expr = task_var1.end == task_var2.start
                elif prec_type == "end_at_end":
                    expr = task_var1.end == task_var2.end
                elif prec_type == "end_before_start":
                    expr = task_var1.end <= task_var2.start
                elif prec_type == "end_before_end":
                    expr = task_var1.end <= task_var2.end
                else:
                    continue

                m.add(expr)

        # Separately handle assignment related constraints for efficiency.
        for machine, tasks in enumerate(data.machine2tasks):
            for task1, task2 in product(tasks, repeat=2):
                if task1 == task2 or (task1, task2) not in data.constraints:
                    continue

                sequence = seq_vars[machine]
                var1 = task_alt_vars[task1, machine]
                var2 = task_alt_vars[task2, machine]

                for constraint in data.constraints[task1, task2]:
                    if constraint == "previous":
                        sequence.activate(m)

                        idx1 = sequence.task_alts.index(var1)
                        idx2 = sequence.task_alts.index(var2)
                        arc = sequence.arcs[idx1, idx2]

                        # arc <=> var1.is_present & var2.is_present
                        m.add_bool_or(
                            [arc, ~var1.is_present, ~var2.is_present]
                        )
                        m.add_implication(arc, var1.is_present)
                        m.add_implication(arc, var2.is_present)
                    if constraint == "before":
                        sequence.activate(m)
                        both_present = m.new_bool_var("")

                        # both_present <=> var1.is_present & var2.is_present
                        m.add_bool_or(
                            [both_present, ~var1.is_present, ~var2.is_present]
                        )
                        m.add_implication(both_present, var1.is_present)
                        m.add_implication(both_present, var2.is_present)

                        # Schedule var1 before var2 when both are present.
                        idx1 = sequence.task_alts.index(var1)
                        idx2 = sequence.task_alts.index(var2)
                        rank1 = sequence.ranks[idx1]
                        rank2 = sequence.ranks[idx2]

                        m.add(rank1 <= rank2).only_enforce_if(both_present)
                    elif constraint == "same_machine":
                        expr = var1.is_present == var2.is_present
                        m.add(expr)
                    elif constraint == "different_machine":
                        expr = var1.is_present != var2.is_present
                        m.add(expr)

    def enforce_circuit(self):
        """
        Enforce the circuit constraints for each machine, ensuring that the
        sequencing constraints are respected.
        """
        data, m = self._data, self._m
        seq_vars = self.sequence_vars

        for machine in range(data.num_machines):
            sequence = seq_vars[machine]

            if not sequence.is_active:
                # No sequencing constraints found. Skip the creation of
                # (expensive) circuit constraints.
                continue

            task_alt_vars = sequence.task_alts
            starts = sequence.starts
            ends = sequence.ends
            ranks = sequence.ranks
            arcs = sequence.arcs
            circuit = []

            for idx1, var1 in enumerate(task_alt_vars):
                # Set initial arcs from the dummy node (-1) to/from a task.
                start = starts[idx1]
                end = ends[idx1]
                rank = ranks[idx1]

                circuit.append([-1, idx1, start])
                circuit.append([idx1, -1, end])

                # Set rank for first task in the sequence.
                m.add(rank == 0).only_enforce_if(start)

                # Self arc if the task is not present on this machine.
                circuit.append([idx1, idx1, ~var1.is_present])
                m.add(rank == -1).only_enforce_if(~var1.is_present)

                for idx2, var2 in enumerate(task_alt_vars):
                    if idx1 == idx2:
                        continue

                    arc = arcs[idx1, idx2]
                    circuit.append([idx1, idx2, arc])

                    m.add_implication(arc, var1.is_present)
                    m.add_implication(arc, var2.is_present)

                    # Maintain rank incrementally.
                    m.add(rank + 1 == ranks[idx2]).only_enforce_if(arc)

                    # TODO Validate that this cannot be combined with overlap.
                    task1, task2 = var1.task_idx, var2.task_idx
                    setup = data.setup_times[machine][task1, task2]
                    m.add(var1.end + setup <= var2.start).only_enforce_if(arc)

            if circuit:
                m.add_circuit(circuit)

    def build(self, solution: Optional[Solution] = None):
        objective = self._data.objective

        if solution is not None:
            self.add_hint_to_vars(solution)

        if objective == "makespan":
            self._objective.makespan()
        elif objective == "tardy_jobs":
            self._objective.tardy_jobs()
        elif objective == "total_tardiness":
            self._objective.total_tardiness()
        elif objective == "total_completion_time":
            self._objective.total_completion_time()
        else:
            raise ValueError(f"Unknown objective: {objective}")

        self.job_spans_tasks()
        self.select_one_task_alternative()
        self.no_overlap_machines()
        self.activate_setup_times()
        self.task_graph()

        # From here onwards we know which sequence constraints are active.
        self.enforce_circuit()

        return self._m


class ObjectiveBuilder:
    def __init__(
        self,
        model: CpModel,
        data: ProblemData,
        job_vars: list[JobVar],
        task_vars: list[TaskVar],
    ):
        self.model = model
        self.data = data
        self.job_vars = job_vars
        self.task_vars = task_vars

    def build(self, objective_type: str):
        if objective_type == "makespan":
            self.makespan()
        elif objective_type == "tardy_jobs":
            self.tardy_jobs()
        elif objective_type == "total_completion_time":
            self.total_completion_time()
        elif objective_type == "total_tardiness":
            self.total_tardiness()
        else:
            raise ValueError(f"Unknown objective type: {objective_type}")

    def makespan(self):
        """
        Minimizes the makespan.
        """
        makespan = self.model.new_int_var(0, self.data.horizon, "makespan")
        completion_times = [var.end for var in self.task_vars]

        self.model.add_max_equality(makespan, completion_times)
        self.model.minimize(makespan)

    def tardy_jobs(self):
        """
        Minimize the number of tardy jobs.
        """
        exprs = []

        for job, var in zip(self.data.jobs, self.job_vars):
            is_tardy = self.model.new_bool_var(f"is_tardy_{job}")
            exprs.append(is_tardy)

            self.model.add(var.end > job.due_date).only_enforce_if(is_tardy)
            self.model.add(var.end <= job.due_date).only_enforce_if(~is_tardy)

        self.model.minimize(LinearExpr.sum(exprs))

    def total_completion_time(self):
        """
        Minimizes the weighted sum of the completion times of each job.
        """
        exprs = [var.end for var in self.job_vars]
        weights = [job.weight for job in self.data.jobs]

        self.model.minimize(LinearExpr.weighted_sum(exprs, weights))

    def total_tardiness(self):
        """
        Minimizes the weighted sum of the tardiness of each job.
        """
        exprs = []

        for job, var in zip(self.data.jobs, self.job_vars):
            tardiness = self.model.new_int_var(
                0, self.data.horizon, f"tardiness_{job}"
            )
            exprs.append(tardiness)

            self.model.add_max_equality(tardiness, [0, var.end - job.due_date])

        weights = [job.weight for job in self.data.jobs]
        self.model.minimize(LinearExpr.weighted_sum(exprs, weights))
