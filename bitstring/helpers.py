import operator
from typing import Any


def validated_count(value: Any, description: str) -> int:
    """A count of bits or items as an int, rejecting anything that isn't a whole number.

    int() would truncate a float and parse a string, either of which quietly builds
    something of a size that wasn't asked for.
    """
    try:
        return operator.index(value)
    except TypeError:
        raise TypeError(f"The {description} must be an integer, but received a "
                        f"{type(value).__name__}.") from None


def _indices(s: slice, length: int) -> tuple[int, int | None, int]:
    """A better implementation of slice.indices such that a
    slice made from [start:stop:step] will actually equal the original slice."""
    if s.step is None or s.step > 0:
        return s.indices(length)
    assert s.step < 0
    start, stop, step = s.indices(length)
    if stop < 0:
        stop = None
    return start, stop, step


def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    try:
        t = s.split()
    except (AttributeError, TypeError):
        raise ValueError(f"Expected str object but received a {type(s)} with value {s}.")
    return ''.join(t).lower().replace('_', '')