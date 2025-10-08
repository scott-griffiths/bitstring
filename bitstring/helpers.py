from typing import Union, Tuple


def _indices(s: slice, length: int) -> Tuple[int, Union[int, None], int]:
    """A better implementation of slice.indices such that a
    slice made from [start:stop:step] will actually equal the original slice."""
    if s.step is None or s.step > 0:
        return s.indices(length)
    assert s.step < 0
    start, stop, step = s.indices(length)
    if stop < 0:
        stop = None
    return start, stop, step

def offset_slice_indices_lsb0(key: slice, length: int) -> slice:
    start, stop, step = _indices(key, length)
    if step is not None and step < 0:
        if stop is None:
            new_start = start + 1
            new_stop = None
        else:
            first_element = start
            last_element = start + ((stop + 1 - start) // step) * step
            new_start = length - last_element
            new_stop = length - first_element - 1
    else:
        first_element = start
        # The last element will usually be stop - 1, but needs to be adjusted if step != 1.
        last_element = start + ((stop - 1 - start) // step) * step
        new_start = length - last_element - 1
        new_stop = length - first_element
    return slice(new_start, new_stop, key.step)

def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    try:
        t = s.split()
    except (AttributeError, TypeError):
        raise ValueError(f"Expected str object but received a {type(s)} with value {s}.")
    return ''.join(t).lower().replace('_', '')