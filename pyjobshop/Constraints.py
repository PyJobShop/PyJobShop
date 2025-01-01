from typing import NamedTuple, Optional


class StartAtStart(NamedTuple):
    """
    Start task 1 at the same time as task 2 starts.
    """

    task1: int
    task2: int


class StartAtEnd(NamedTuple):
    """
    Start task 1 at the same time as task 2 finishes.
    """

    task1: int
    task2: int


class StartBeforeStart(NamedTuple):
    """
    Start task 1 before task 2 starts.
    """

    task1: int
    task2: int


class StartBeforeEnd(NamedTuple):
    """
    Start task 1 before task 2 finishes.
    """

    task1: int
    task2: int


class EndAtStart(NamedTuple):
    """
    End task 1 at the same time as task 2 starts.
    """

    task1: int
    task2: int


class EndAtEnd(NamedTuple):
    """
    End task 1 at the same time as task 2 finishes.
    """

    task1: int
    task2: int


class EndBeforeStart(NamedTuple):
    """
    End task 1 before task 2 starts.
    """

    task1: int
    task2: int


class EndBeforeEnd(NamedTuple):
    """
    End task 1 before task 2 finishes.
    """

    task1: int
    task2: int


class IdenticalResources(NamedTuple):
    """
    Select a mode for task 1 and task 2 that use the same resources.
    """

    task1: int
    task2: int


class DifferentResources(NamedTuple):
    """
    Select a mode for task 1 and task 2 that use different resources, that is,
    the intersection of the resources used by the two modes is empty.
    """

    task1: int
    task2: int


class Consecutive(NamedTuple):
    """
    Sequence task 1 right before task 2 on the machines they are both assigned
    to, meaning that no task is allowed to schedule between them.
    """

    task1: int
    task2: int


class SetupTime(NamedTuple):
    """
    Sequence-dependent setup time between task 1 and task 2 on the given
    machine resource.
    """

    resource: int
    task1: int
    task2: int
    duration: int


class Constraints:
    """
    Container class for storing all constraints.

    Parameters
    ----------
    start_at_start
        List of start-at-start constraints.
    start_at_end
        List of start-at-end constraints.
    start_before_start
        List of start-before-start constraints.
    start_before_end
        List of start-before-end constraints.
    end_at_start
        List of end-at-start constraints.
    end_at_end
        List of end-at-end constraints.
    end_before_start
        List of end-before-start constraints.
    end_before_end
        List of end-before-end constraints.
    identical_resources
        List of identical resources constraints.
    different_resources
        List of different resources constraints.
    consecutive
        List of consecutive constraints.
    setup_times
        Optional sequence-dependent setup times between tasks on a given
        resource. The first dimension of the array is indexed by the resource
        index. The last two dimensions of the array are indexed by task
        indices.
    """

    def __init__(
        self,
        start_at_start: Optional[list[StartAtStart]] = None,
        start_at_end: Optional[list[StartAtEnd]] = None,
        start_before_start: Optional[list[StartBeforeStart]] = None,
        start_before_end: Optional[list[StartBeforeEnd]] = None,
        end_at_start: Optional[list[EndAtStart]] = None,
        end_at_end: Optional[list[EndAtEnd]] = None,
        end_before_start: Optional[list[EndBeforeStart]] = None,
        end_before_end: Optional[list[EndBeforeEnd]] = None,
        identical_resources: Optional[list[IdenticalResources]] = None,
        different_resources: Optional[list[DifferentResources]] = None,
        consecutive: Optional[list[Consecutive]] = None,
        setup_times: Optional[list[SetupTime]] = None,
    ):
        self._start_at_start = start_at_start or []
        self._start_at_end = start_at_end or []
        self._start_before_start = start_before_start or []
        self._start_before_end = start_before_end or []
        self._end_at_start = end_at_start or []
        self._end_at_end = end_at_end or []
        self._end_before_start = end_before_start or []
        self._end_before_end = end_before_end or []
        self._identical_resources = identical_resources or []
        self._different_resources = different_resources or []
        self._consecutive = consecutive or []
        self._setup_times = setup_times or []

    def __eq__(self, other) -> bool:
        return (
            self.start_at_start == other.start_at_start
            and self.start_at_end == other.start_at_end
            and self.start_before_start == other.start_before_start
            and self.start_before_end == other.start_before_end
            and self.end_at_start == other.end_at_start
            and self.end_at_end == other.end_at_end
            and self.end_before_start == other.end_before_start
            and self.end_before_end == other.end_before_end
            and self.identical_resources == other.identical_resources
            and self.different_resources == other.different_resources
            and self.consecutive == other.consecutive
            and self.setup_times == other.setup_times
        )

    def __len__(self) -> int:
        return (
            len(self.start_at_start)
            + len(self.start_at_end)
            + len(self.start_before_start)
            + len(self.start_before_end)
            + len(self.end_at_start)
            + len(self.end_at_end)
            + len(self.end_before_start)
            + len(self.end_before_end)
            + len(self.identical_resources)
            + len(self.different_resources)
            + len(self.consecutive)
            + len(self._setup_times)
        )

    @property
    def start_at_start(self) -> list[StartAtStart]:
        """
        Returns the list of start-at-start constraints.
        """
        return self._start_at_start

    @property
    def start_at_end(self) -> list[StartAtEnd]:
        """
        Returns the list of start-at-end constraints.
        """
        return self._start_at_end

    @property
    def start_before_start(self) -> list[StartBeforeStart]:
        """
        Returns the list of start-before-start constraints.
        """
        return self._start_before_start

    @property
    def start_before_end(self) -> list[StartBeforeEnd]:
        """
        Returns the list of start-before-end constraints.
        """
        return self._start_before_end

    @property
    def end_at_start(self) -> list[EndAtStart]:
        """
        Returns the list of end-at-start constraints.
        """
        return self._end_at_start

    @property
    def end_at_end(self) -> list[EndAtEnd]:
        """
        Returns the list of end-at-end constraints.
        """
        return self._end_at_end

    @property
    def end_before_start(self) -> list[EndBeforeStart]:
        """
        Returns the list of end-before-start constraints.
        """
        return self._end_before_start

    @property
    def end_before_end(self) -> list[EndBeforeEnd]:
        """
        Returns the list of end-before-end constraints.
        """
        return self._end_before_end

    @property
    def identical_resources(self) -> list[IdenticalResources]:
        """
        Returns the list of identical resources constraints.
        """
        return self._identical_resources

    @property
    def different_resources(self) -> list[DifferentResources]:
        """
        Returns the list of different resources constraints.
        """
        return self._different_resources

    @property
    def consecutive(self) -> list[Consecutive]:
        """
        Returns the list of consecutive task constraints.
        """
        return self._consecutive

    @property
    def setup_times(self) -> list[SetupTime]:
        """
        Returns the list of setup times constraints.
        """
        return self._setup_times
