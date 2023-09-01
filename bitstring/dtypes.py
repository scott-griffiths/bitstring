from __future__ import annotations

import functools
from bitstring.utils import parse_name_length_token
from bitstring.exceptions import InterpretError
from bitstring.classes import Bits, BitArray


class Dtype:
    def __init__(self, fmt: str) -> None:
        self.name, self.length = parse_name_length_token(fmt)
        try:
            self.set = functools.partial(Bits._setfunc[self.name], length=self.length)
        except KeyError:
            raise ValueError(f"The token '{self.name}' is not a valid Dtype name.")
        try:
            self.get = functools.partial(Bits._name_to_read[self.name], length=self.length)
        except KeyError:
            raise ValueError(f"The token '{self.name}' is not a valid Dtype name.")
        # Test if the length makes sense by trying out the getter.
        if self.length != 0:
            temp = BitArray(self.length)
            try:
                _ = self.get(temp, 0)
            except InterpretError as e:
                raise ValueError(f"Invalid Dtype: {e.msg}")

    def __str__(self) -> str:
        return f"{self.name}{self.length if self.length != 0 else ''}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}('{self.name}{self.length if self.length != 0 else ''}')"

