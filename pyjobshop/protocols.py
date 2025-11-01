from typing import Any, ClassVar, Protocol, Sized


class DataclassInstance(Protocol):
    """Protocol specifying that a given class is a dataclass."""

    __dataclass_fields__: ClassVar[dict[str, Any]]

    def __init__(self, *args, **kwargs) -> None: ...


class SizedDataclassInstance(DataclassInstance, Sized, Protocol):
    """Protocol specifying that a given class is a dataclass which can be
    iterated over."""

    pass
