from bitstring.array_ import Array, ElementType
from typing import Union, List, Iterable, Any, Optional, BinaryIO, overload, TextIO
from bitstring.dtypes import Dtype

def scaled_get_fn(get_fn, scale: int):
    def wrapper(*args, **kwargs):
        return get_fn(*args, **kwargs) * (2 ** scale)
    return wrapper

def scaled_set_fn(set_fn, scale: int):
    def wrapper(bs, value, *args, **kwargs):
        return set_fn(bs, value / (2 ** scale), *args, **kwargs)
    return wrapper

def scaled_read_fn(read_fn, scale: int):
    def wrapper(*args, **kwargs):
        return read_fn(*args, **kwargs) * (2 ** scale)
    return wrapper

class ScaledArray(Array):
    """An experimental version of Array that includes a scale factor.
    This is a work in progress and may change or be removed in the future."""

    def __init__(self, dtype, initializer=None, trailing_bits=None, scale: int = 0):
        self.scaled_dtype = Dtype(dtype)
        self.unscaled_get_fn = self.scaled_dtype.get_fn
        self.unscaled_set_fn = self.scaled_dtype.set_fn
        self.unscaled_read_fn = self.scaled_dtype.read_fn
        self.scale = scale
        super().__init__(self.scaled_dtype, initializer, trailing_bits)

    @property
    def scale(self) -> int:
        return self._scale

    @scale.setter
    def scale(self, value: int) -> None:
        self._scale = value
        self.scaled_dtype.get_fn = scaled_get_fn(self.unscaled_get_fn, self._scale)
        self.scaled_dtype.set_fn = scaled_set_fn(self.unscaled_set_fn, self._scale)
        self.scaled_dtype.read_fn = scaled_read_fn(self.unscaled_read_fn, self._scale)

    def __repr__(self) -> str:
        r = super().__repr__()
        # Rather hacky
        return f"Scaled{r[:-1]}, scale={self.scale})"

    def __getitem__(self, key: Union[slice, int]) -> Union[Array, ElementType]:
        scale = self.scale
        val = super().__getitem__(key)
        if isinstance(val, ScaledArray):
            val._scale = scale
        return val
