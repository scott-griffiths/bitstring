from __future__ import annotations

import numbers
from typing import Any, List, Optional, Union, overload

import bitstring
from bitstring.bits import Bits, BitsType
from bitstring.dtypes import Dtype


class Reader:
    """Wrap a Bits or BitArray object with a bit position for sequential reading."""

    __slots__ = ("_bits", "_pos")

    def __init__(self, bits: Bits, pos: int = 0) -> None:
        self.bits = bits
        self.pos = pos

    @staticmethod
    def _validate_bits(value: Bits) -> None:
        if isinstance(value, Bits):
            return
        help_ = ""
        if isinstance(value, str):
            help_ = " Perhaps use Bits.fromstring() or Bits(...)?"
        elif isinstance(value, (bytes, bytearray, memoryview)):
            help_ = " Perhaps use Bits(bytes=...)?"
        raise TypeError(f"Reader should be initialised with a Bits or BitArray object, "
                        f"but received a {type(value).__name__}.{help_}")

    @property
    def bits(self) -> Bits:
        """The wrapped Bits or BitArray object."""
        return self._bits

    @bits.setter
    def bits(self, value: Bits) -> None:
        Reader._validate_bits(value)
        self._bits = value

    @property
    def pos(self) -> int:
        """The current bit position."""
        return self._pos

    @pos.setter
    def pos(self, value: int) -> None:
        self._pos = int(value)

    @property
    def bitpos(self) -> int:
        """An alias for pos."""
        return self._pos

    @bitpos.setter
    def bitpos(self, value: int) -> None:
        self._pos = int(value)

    @property
    def bytepos(self) -> int:
        """The current byte position. Requires the bit position to be byte aligned."""
        if self._pos % 8:
            raise bitstring.ByteAlignError("Not byte aligned when using bytepos property.")
        return self._pos // 8

    @bytepos.setter
    def bytepos(self, value: int) -> None:
        self._pos = int(value) * 8

    def _ensure_valid_pos(self) -> None:
        if not 0 <= self._pos <= len(self._bits):
            raise ValueError(f"Invalid bit position {self._pos} for bitstring of length {len(self._bits)}.")

    @staticmethod
    def _dtype_with_length(dtype: Dtype, items: int) -> Dtype:
        return Dtype(dtype.name, items, dtype.scale)

    @overload
    def read(self, fmt: int) -> Bits:
        ...

    @overload
    def read(self, fmt: str) -> Any:
        ...

    def read(self, fmt: Union[int, str, Dtype]) -> Union[int, float, str, Bits, bool, bytes, None]:
        """Read from the current bit position and interpret according to fmt."""
        old_pos = self._pos
        try:
            self._ensure_valid_pos()
            if isinstance(fmt, numbers.Integral):
                if fmt < 0:
                    raise ValueError("Cannot read negative amount.")
                if fmt > len(self._bits) - self._pos:
                    raise bitstring.ReadError(
                        f"Cannot read {fmt} bits, only {len(self._bits) - self._pos} available.")
                value = self._bits._slice(self._pos, self._pos + int(fmt))
                self._pos += int(fmt)
                return value

            dtype = Dtype(fmt)
            if dtype.bitlength is None and not dtype.variable_length:
                bitlength = len(self._bits) - self._pos
                items, remainder = divmod(bitlength, dtype.bits_per_item)
                if remainder != 0:
                    raise ValueError(
                        f"The '{dtype.name}' type must have a bit length that is a multiple of "
                        f"{dtype.bits_per_item} so cannot be read from the {bitlength} bits that are available.")
                dtype = Reader._dtype_with_length(dtype, items)
            if dtype.bitlength is not None:
                value = dtype.read_fn(self._bits, self._pos)
                self._pos += dtype.bitlength
            else:
                value, self._pos = dtype.read_fn(self._bits, self._pos)
            if self._pos > len(self._bits):
                raise bitstring.ReadError(
                    f"Reading off end of bitstring with fmt '{fmt}'. Only {len(self._bits) - old_pos} bits available.")
            return value
        except Exception:
            self._pos = old_pos
            raise

    def readlist(self, fmt: Union[str, List[Union[int, str, Dtype]]], **kwargs) \
            -> List[Union[int, float, str, Bits, bool, bytes, None]]:
        """Read and interpret one or more format tokens from the current bit position."""
        old_pos = self._pos
        try:
            self._ensure_valid_pos()
            value, self._pos = self._bits._readlist(fmt, self._pos, **kwargs)
            if self._pos > len(self._bits):
                raise bitstring.ReadError(
                    f"Reading off end of bitstring. Only {len(self._bits) - old_pos} bits available.")
            return value
        except Exception:
            self._pos = old_pos
            raise

    @overload
    def peek(self, fmt: int) -> Bits:
        ...

    @overload
    def peek(self, fmt: str) -> Any:
        ...

    def peek(self, fmt: Union[int, str, Dtype]) -> Union[int, float, str, Bits, bool, bytes, None]:
        """Read from the current bit position without changing the position."""
        old_pos = self._pos
        try:
            return self.read(fmt)
        finally:
            self._pos = old_pos

    def peeklist(self, fmt: Union[str, List[Union[int, str, Dtype]]], **kwargs) \
            -> List[Union[int, float, str, Bits, bool, bytes, None]]:
        """Read one or more format tokens without changing the position."""
        old_pos = self._pos
        try:
            return self.readlist(fmt, **kwargs)
        finally:
            self._pos = old_pos

    def readto(self, bs: BitsType, /, *, bytealigned: Optional[bool] = None) -> Bits:
        """Read up to and including the next occurrence of bs."""
        if isinstance(bs, numbers.Integral):
            raise ValueError("Integers cannot be searched for")
        old_pos = self._pos
        try:
            self._ensure_valid_pos()
            bs = Bits._create_from_bitstype(bs)
            p = self.find(bs, start=self._pos, bytealigned=bytealigned)
            if p is None:
                raise bitstring.ReadError("Substring not found")
            self._pos = p + len(bs)
            return self._bits._slice(old_pos, self._pos)
        except Exception:
            self._pos = old_pos
            raise

    def bytealign(self) -> int:
        """Align to the next byte boundary and return the number of skipped bits."""
        self._ensure_valid_pos()
        skipped = (8 - (self._pos % 8)) % 8
        if self._pos + skipped > len(self._bits):
            raise ValueError("Cannot seek past the end of the data.")
        self._pos += skipped
        return skipped

    def find(self, bs: BitsType, /, *, start: Optional[int] = None, end: Optional[int] = None,
             bytealigned: Optional[bool] = None) -> Optional[int]:
        """Find a bitstring and set pos to the match position if found."""
        p = self._bits.find(bs, start=start, end=end, bytealigned=bytealigned)
        if p is not None:
            self._pos = p
        return p

    def rfind(self, bs: BitsType, /, *, start: Optional[int] = None, end: Optional[int] = None,
              bytealigned: Optional[bool] = None) -> Optional[int]:
        """Find a bitstring from the end and set pos to the match position if found."""
        p = self._bits.rfind(bs, start=start, end=end, bytealigned=bytealigned)
        if p is not None:
            self._pos = p
        return p

    def __len__(self) -> int:
        return len(self._bits)

    def __repr__(self) -> str:
        return f"Reader(<{self._bits.__class__.__name__} of length {len(self._bits)} bits>, pos={self._pos})"

    __str__ = __repr__
