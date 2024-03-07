from __future__ import annotations

from bitstring.dtypes import Dtype
from typing import Optional, Union

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


class ScaledDtype(Dtype):

    def __new__(cls, token: Union[str, Dtype, None] = None, /, length: Optional[int] = None, scale: int = 0) -> ScaledDtype:
        x = super().__new__(cls)
        d = Dtype(token, length)
        for slot in Dtype.__slots__:
            setattr(x, slot, getattr(d, slot))
        x.unscaled_get_fn = d.get_fn
        x.unscaled_set_fn = d.set_fn
        x.unscaled_read_fn = d.read_fn
        x.scale = scale
        return x

    @property
    def scale(self) -> int:
        return self._scale

    @scale.setter
    def scale(self, value: int) -> None:
        self._scale = value
        self.get_fn = scaled_get_fn(self.unscaled_get_fn, self._scale)
        self.set_fn = scaled_set_fn(self.unscaled_set_fn, self._scale)
        self.read_fn = scaled_read_fn(self.unscaled_read_fn, self._scale)

    def __repr__(self) -> str:
        return super().__repr__()[:-1] + f", scale={self.scale})"

    def __str__(self) -> str:
        scale_str = ""
        if self.scale > 0:
            scale_str = f"_scale{self.scale}p"
        elif self.scale < 0:
            scale_str = f"_scale{-self.scale}n"
        return super().__str__() + scale_str
