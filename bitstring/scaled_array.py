from bitstring.array_ import Array, ElementType
from typing import Union, List, Iterable, Any, Optional, BinaryIO, overload, TextIO
from bitstring.dtypes import Dtype

class ScaledArray(Array):
    """An experimental version of Array that includes a scale factor.
    This is a work in progress and may change or be removed in the future."""

    def __init__(self, dtype, scale: int = 0, initializer=None, trailing_bits=None):
        dtype = Dtype(dtype)
        dtype.scale = scale
        super().__init__(dtype, initializer, trailing_bits)

    @property
    def scale(self) -> int:
        return self.dtype.scale

    @scale.setter
    def scale(self, value: int) -> None:
        self.dtype.scale = value

    def __repr__(self) -> str:
        r = super().__repr__()
        # Rather hacky
        return f"Scaled{r[:-1]}, scale={self.scale})"

    def __getitem__(self, key: Union[slice, int]) -> Union[Array, ElementType]:
        scale = self.scale
        val = super().__getitem__(key)
        if isinstance(val, ScaledArray):
            val.scale = scale
        return val
