

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