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


def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    # An explicit check, as bytes has a split() too and so got part of the way through.
    if not isinstance(s, str):
        raise ValueError(f"Expected str object but received a {type(s)} with value {s}.")
    return ''.join(s.split()).lower().replace('_', '')