from typing import NamedTuple, Optional

import numpy as np


class StartAtStart(NamedTuple):
    """
    Test docstring TODO
    """

    task1: int
    task2: int


class StartAtEnd(NamedTuple):
    task1: int
    task2: int


class StartBeforeStart(NamedTuple):
    task1: int
    task2: int


class StartBeforeEnd(NamedTuple):
    task1: int
    task2: int


class EndAtStart(NamedTuple):
    task1: int
    task2: int


class EndAtEnd(NamedTuple):
    task1: int
    task2: int


class EndBeforeStart(NamedTuple):
    task1: int
    task2: int


class EndBeforeEnd(NamedTuple):
    task1: int
    task2: int


class IdenticalResources(NamedTuple):
    task1: int
    task2: int


class DifferentResources(NamedTuple):
    task1: int
    task2: int


class Consecutive(NamedTuple):
    task1: int
    task2: int


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
        setup_times: Optional[np.ndarray] = None,
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
        self._setup_times = setup_times

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
            and (
                (self.setup_times is None and other.setup_times is None)
                or (
                    self.setup_times is not None
                    and other.setup_times is not None
                    and np.array_equal(self.setup_times, other.setup_times)
                )
            )
        )

    @property
    def start_at_start(self) -> list[StartAtStart]:
        return self._start_at_start

    @property
    def start_at_end(self) -> list[StartAtEnd]:
        return self._start_at_end

    @property
    def start_before_start(self) -> list[StartBeforeStart]:
        return self._start_before_start

    @property
    def start_before_end(self) -> list[StartBeforeEnd]:
        return self._start_before_end

    @property
    def end_at_start(self) -> list[EndAtStart]:
        return self._end_at_start

    @property
    def end_at_end(self) -> list[EndAtEnd]:
        return self._end_at_end

    @property
    def end_before_start(self) -> list[EndBeforeStart]:
        return self._end_before_start

    @property
    def end_before_end(self) -> list[EndBeforeEnd]:
        return self._end_before_end

    @property
    def identical_resources(self) -> list[IdenticalResources]:
        return self._identical_resources

    @property
    def different_resources(self) -> list[DifferentResources]:
        return self._different_resources

    @property
    def consecutive(self) -> list[Consecutive]:
        return self._consecutive

    @property
    def setup_times(self) -> Optional[np.ndarray]:
        return self._setup_times

    @setup_times.setter
    def setup_times(self, value: np.ndarray):
        self._setup_times = value
