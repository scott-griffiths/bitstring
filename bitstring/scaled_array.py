from __future__ import annotations

from bitstring.array_ import Array, ElementType
from typing import Union
from bitstring.dtypes import Dtype
import copy
import io

def scaled_get_fn(get_fn, s: int):
    def wrapper(*args, scale=s, **kwargs):
        return get_fn(*args, **kwargs) * (2 ** scale)
    return wrapper

def scaled_set_fn(set_fn, s: int):
    def wrapper(bs, value, *args, scale=s, **kwargs):
        return set_fn(bs, value / (2 ** scale), *args, **kwargs)
    return wrapper

def scaled_read_fn(read_fn, s: int):
    def wrapper(*args, scale=s, **kwargs):
        return read_fn(*args, **kwargs) * (2 ** scale)
    return wrapper



class ScaledArray(Array):
    """An experimental version of Array that includes a scale factor.
    This is a work in progress and may change or be removed in the future."""

    def __init__(self, dtype, initializer=None, trailing_bits=None, scale: int = 0):
        d = Dtype(dtype)
        self.dtype = copy.copy(d)
        self.unscaled_get_fn = self.dtype.get_fn
        self.unscaled_set_fn = self.dtype.set_fn
        self.unscaled_read_fn = self.dtype.read_fn
        self.scale = scale
        super().__init__(self.dtype, initializer, trailing_bits)

    @property
    def scale(self) -> int:
        return self._scale

    @scale.setter
    def scale(self, value: int) -> None:
        self._scale = value
        self.dtype.get_fn = scaled_get_fn(self.unscaled_get_fn, self._scale)
        self.dtype.set_fn = scaled_set_fn(self.unscaled_set_fn, self._scale)
        self.dtype.read_fn = scaled_read_fn(self.unscaled_read_fn, self._scale)

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

    def pp(self):
        s = io.StringIO()
        super().pp(stream=s)
        print(s.getvalue() + f" scale={self.scale}")

    def _apply_op_between_arrays(self, op, other: Array, is_comparison: bool = False) -> ScaledArray:
        result = super()._apply_op_between_arrays(op, other, is_comparison)
        result = ScaledArray(result.dtype, result, scale=0)
        result._scale = self.scale  # We want to fix the scale without causing another rescale.
        return result

    def _apply_op_to_all_elements(self, op, value: Union[int, float, None], is_comparison: bool = False) -> ScaledArray:
        result = super()._apply_op_to_all_elements(op, value, is_comparison)
        result =ScaledArray(result.dtype, result, scale=0)
        result._scale = self.scale  # We want to fix the scale without causing another rescale.
        return result