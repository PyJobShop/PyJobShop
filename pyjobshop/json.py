import dataclasses
import json
import types
from typing import Callable, Iterable

_sentinel = object()


class JSONDataclassEncoder(json.JSONEncoder):
    """
    Allows for encoding objects of any ``@dataclass``\\ -decorated class into
    JSON.

    This is done by iterating over the dataclass's fields which were not
    explicitly declared as having ``init=False`` (or as ``InitVar``s) in the
    dataclass's definition.  A field ``__class__`` is added to the JSON for
    each object, specifying the name of the dataclass in question.
    """

    def default(self, obj):
        """This could be overridden in a subclass to support encoding other
        data types (e.g. ``datetime``).

        Example
        -------
        >>> def default(self, o):
        ...   from datetime import datetime
        ...   if isinstance(o, datetime):
        ...      return o.isoformat()
        ...   else:
        ...      return super().default(o)
        """
        if not dataclasses.is_dataclass(obj):
            return super().default(obj)

        init_flds = [f for f in dataclasses.fields(obj) if f.init]
        result = {"__class__": obj.__class__.__name__}
        result.update((f.name, getattr(obj, f.name)) for f in init_flds)
        return result


class AbstractJSONDataclassDecoder(json.JSONDecoder):
    """
    This class lays the groundwork for decoding objects of any
    ``@dataclass``\\ -decorated class from JSON.

    This is done by iterating over the dataclass's fields which were not
    explicitly declared as having ``init=False`` (or as ``InitVar``\\ s) in
    the dataclass's definition.  The name of the dataclass to deserialize is
    taken from ``__class__`` fields in the JSON, and has to be explicitly
    registered first.

    How this is done is the reponsibility of classes extending this class.
    Also, if a dataclass specifies ``InitVar``\\ s without a default value,
    this needs to be handled by a custom subclass.
    """

    # Map class names to classes
    _serializable_classes: dict[str, type] | None
    _delegate_object_hook: Callable[[object], object] | None = None

    def __init__(self, **kwargs):
        self._delegate_object_hook = kwargs.pop("object_hook", None)
        super().__init__(object_hook=self.object_hook, **kwargs)

    def __init_subclass__(cls, **kwargs):
        if not hasattr(cls, "_serializable_classes"):
            raise TypeError(
                f"{cls.__name__} must define _serializable_classes"
            )

    def object_hook(self, obj):
        if self._delegate_object_hook is not None:
            # Call the object_hook provided upon class construction and
            # return the result (if there is any)
            new_obj = self._delegate_object_hook(obj)
            if new_obj is not obj:
                return new_obj
        classname = obj.pop("__class__", _sentinel)
        if classname is _sentinel:
            # Don't have to handle this object, leave it as a dict.
            return obj
        if type(classname) is not str:
            raise ValueError(
                f"Invalid type for class name (__class__): "
                f"expected str, found {type(classname).__name__}"
            )
        cls: type = self._serializable_classes.get(classname, None)
        if not cls:
            raise TypeError(
                f"Class {classname} not registered for deserialization."
            )
        init_flds = [f for f in dataclasses.fields(cls) if f.init]
        kwargs = {}
        for fld in init_flds:
            val = obj.pop(fld.name, _sentinel)
            if val is _sentinel:
                # A field value required for instantiation was not provided.
                # (Note that we are ignoring fld.default and
                # fld.default_factory here.)
                raise ValueError(
                    f"Field {fld.name} not specified for class {classname}"
                )
            kwargs[fld.name] = val
        if len(obj) > 0:
            # More fields were provided in the JSON than specified in (the
            # current version of) the dataclass.
            keynames = " ".join(str(key) for key in obj)
            raise ValueError(
                f"Extraneous values specified for dataclass {classname}: "
                f"{keynames}"
            )
        try:
            return cls(**kwargs)
        except Exception as e:
            # Instantiation may fail; one of the most probable causes is that
            # it specifies init-only variables.
            raise ValueError(
                f"Instantiation of dataclass {cls.__name__} "
                "failed. (Does it specify InitVars?)"
            ) from e


def _build_serializable_classes_dict(
    class_list: Iterable[type],
) -> dict[str, type]:
    """Helper function to build the dictionary of serializable classes for a
    JSONDataclassDecoder from a list of dataclasses."""
    result: dict[str, type] = {}
    for cls in class_list:
        if cls.__name__ in result:
            raise ValueError(f"Duplicate name {cls.__name__} in class_list")
        if not dataclasses.is_dataclass(cls):
            raise TypeError(f"{cls.__name__} is not a dataclass")
        result[cls.__name__] = cls
    return result


class JSONDataclassDecoder(AbstractJSONDataclassDecoder):
    """
    Class for decoding objects of ``@dataclass``\\ -decorated classes from
    JSON, as previously encoded with `JSONDataclassDecoder`.

    A list of classes to be supported must be passed as a ``class_list``
    argument when using this decoder.

    Warnings
    --------
    If a dataclass specifies ``InitVar``\\ s without a default value, note
    that this class cannot deal with that and should be extended.

    Examples
    --------
    >>> json.loads(source, cls=JSONDataclassDecoder,
    ...            class_list=(Knight, Viking, Parrot))

    """

    _serializable_classes = None

    def __init__(self, class_list=(), **kwargs):
        self._serializable_classes = _build_serializable_classes_dict(
            class_list
        )
        super().__init__(**kwargs)


def decoder_factory(name: str, class_list: Iterable[type]):
    """
    Construct a new class for decoding objects of ``@dataclass``\\ -decorated
    classes from JSON, as previously encoded with `JSONDataclassDecoder`.

    Parameters
    ----------
    class_list : An iterable of dataclass types
        The dataclasses to be supported by the class.

    Warnings
    --------
    Note that the generated decoder cannot deal with dataclasses specifying
    ``InitVar``\\ s without a default value.

    Examples
    --------
    >>> class_list=(Knight, Viking, Parrot)
    >>> PythonDecoder = decoder_factory('PythonDecoder', class_list)
    >>> json.loads(source, cls=PythonDecoder)

    """

    def class_body(ns):
        ns["_serializable_classes"] = _build_serializable_classes_dict(
            class_list
        )

    return types.new_class(
        name, (AbstractJSONDataclassDecoder,), exec_body=class_body
    )
