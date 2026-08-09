from __future__ import annotations

import operator
import pathlib
from contextlib import contextmanager
from typing import Any, BinaryIO, Iterator

import bitstring
import bitstring.bitstore as bitstore
from bitstring.bits import Bits, BitsType
from bitstring.dtypes import Dtype

# fmt string -> (bitlength, tibs dtype or None, Dtype), for fixed-length dtypes only.
# Lets read_value() skip the Dtype call and, when there's a tibs equivalent, the whole
# read_fn wrapper chain - together several times the cost of the actual read.
_read_fmt_cache: dict[str, tuple[int, Any, Dtype]] = {}
_READ_FMT_CACHE_SIZE = 256

# Names that a version 4 stream had, with the version 5 method to use instead. Kept
# so that old code gets an explanation rather than a bare AttributeError.
_removed_names: dict[str, str] = {
    "read": "Use read_value() for a dtype, or read_bits() for a number of bits.",
    "readlist": "Use read_list().",
    "peek": "Use peek_value() for a dtype, or peek_bits() for a number of bits.",
    "peek_list": "Use bookmark() around read_list().",
    "peeklist": "Use bookmark() around read_list().",
    "readto": "Use read_past(), which like readto() includes the match. Note that "
              "read_to() is a different method that stops before it.",
    "byte_align": "Use align().",
    "bytealign": "Use align().",
    "find": "Use seek_to() or seek_past(), or self.bits.find() to search without moving.",
    "rfind": "Use seek_back_to(), or self.bits.rfind() to search without moving.",
    "bitpos": "Use pos.",
    "bytepos": "Use byte_pos.",
}


class Reader:
    """A cursor over Bits or BitArray data.

    The data belongs to the wrapped bitstring, which is available as the bits property.
    The reader adds a bit position, and methods that read from it and move it along.

    Methods:

    align() -- Move forward to the next multiple of a bit boundary.
    bookmark() -- Context manager that restores pos afterwards.
    from_file() -- Create a reader over the contents of a file.
    peek_bits() -- Peek at a number of bits.
    peek_value() -- Peek at and interpret the next bits as a single dtype.
    read_array() -- Read several items of one dtype as an Array.
    read_bits() -- Read a number of bits.
    read_list() -- Read and interpret the next bits as a list of items.
    read_past() -- Read up to and including the next occurrence of a bitstring.
    read_to() -- Read up to but not including the next occurrence of a bitstring.
    read_value() -- Read and interpret the next bits as a single dtype.
    seek_back_to() -- Search backwards, moving pos to the match.
    seek_past() -- Search forwards, moving pos past the match.
    seek_to() -- Search forwards, moving pos to the match.

    Properties:

    at_end -- Whether the position is at the end of the data.
    bits -- The wrapped Bits or BitArray object.
    byte_pos -- The current byte position.
    pos -- The current bit position.
    remaining -- The number of bits left to read.

    """

    __slots__ = ("_bits", "_pos")

    def __init__(self, bits: Bits, pos: int = 0) -> None:
        Reader._validate_bits(bits)
        self._bits = bits
        self._pos = 0
        self.pos = pos

    @classmethod
    def from_file(cls, source: str | pathlib.Path | BinaryIO, /, *,
                  length: int | None = None, offset: int = 0) -> Reader:
        """Create a Reader over the contents of a file, positioned at the start.

        The arguments are the same as for Bits.from_file, and the file is read as an
        immutable Bits.

        """
        return cls(Bits.from_file(source, length=length, offset=offset))

    @staticmethod
    def _validate_bits(value: Bits) -> None:
        if isinstance(value, Bits):
            return
        help_ = ""
        if isinstance(value, str):
            help_ = " Perhaps use Bits.from_string() or Bits(...)?"
        elif isinstance(value, (bytes, bytearray, memoryview)):
            help_ = " Perhaps use Bits.from_bytes(...)?"
        raise TypeError(f"Reader should be initialised with a Bits or BitArray object, "
                        f"but received a {type(value).__name__}.{help_}")

    @property
    def bits(self) -> Bits:
        """The wrapped Bits or BitArray object. This is the original object, not a copy."""
        return self._bits

    @property
    def pos(self) -> int:
        """The current bit position."""
        return self._pos

    @pos.setter
    def pos(self, value: int) -> None:
        self._pos = self._checked_pos(value)

    @property
    def byte_pos(self) -> int:
        """The current position in bytes. Requires the bit position to be byte aligned."""
        if self._pos % 8:
            raise ValueError(f"The bit position of {self._pos} is not byte aligned, "
                             f"so there is no byte position for it.")
        return self._pos // 8

    @byte_pos.setter
    def byte_pos(self, value: int) -> None:
        self._pos = self._checked_pos(Reader._as_int(value, "byte position") * 8)

    @property
    def remaining(self) -> int:
        """The number of bits between the current position and the end of the data."""
        return max(len(self._bits) - self._pos, 0)

    @property
    def at_end(self) -> bool:
        """Whether the position is at the end of the data, so nothing more can be read."""
        return self._pos >= len(self._bits)

    def __len__(self) -> int:
        return len(self._bits)

    def __repr__(self) -> str:
        return f"Reader(<{self._bits.__class__.__name__} of length {len(self._bits)} bits>, pos={self._pos})"

    __str__ = __repr__

    def __getattr__(self, name: str) -> Any:
        # Only called when the attribute wasn't found the usual way, so this costs
        # nothing except on the version 4 names that are gone.
        if name in _removed_names:
            raise AttributeError(f"'Reader.{name}' doesn't exist in bitstring 5. "
                                 f"{_removed_names[name]}")
        raise AttributeError(f"'Reader' object has no attribute '{name}'.")

    # ----- Position -----

    @staticmethod
    def _as_int(value: Any, description: str) -> int:
        try:
            return operator.index(value)
        except TypeError:
            raise TypeError(f"The {description} must be an integer, "
                            f"but received a {type(value).__name__}.") from None

    def _checked_pos(self, value: Any) -> int:
        pos = Reader._as_int(value, "bit position")
        length = len(self._bits)
        if not 0 <= pos <= length:
            raise ValueError(f"Cannot set a position of {pos} for the {length} bits available.")
        return pos

    def align(self, boundary: int = 8, /) -> int:
        """Move forward to the next multiple of boundary bits, returning the bits skipped.

        Nothing moves if the position is already on a boundary. The default is byte
        alignment.

        Raises ValueError if boundary isn't positive, or if aligning would move past the
        end of the data, in which case the position doesn't move.

        """
        boundary = Reader._as_int(boundary, "alignment boundary")
        if boundary <= 0:
            raise ValueError(f"The alignment boundary must be greater than zero, "
                             f"but received {boundary}.")
        skipped = (boundary - self._pos % boundary) % boundary
        if self._pos + skipped > len(self._bits):
            raise ValueError(f"Cannot align to {boundary} bits from position {self._pos}: "
                             f"it would move past the end of the {len(self._bits)} bits.")
        self._pos += skipped
        return skipped

    @contextmanager
    def bookmark(self) -> Iterator[Reader]:
        """Return a context manager that restores pos when its block ends.

        The position is restored whether the block completes normally or raises, and any
        mixture of reads and seeks can be used inside it.

        """
        pos = self._pos
        try:
            yield self
        finally:
            self._pos = pos

    # ----- Reading -----

    def _end_of_read(self, needed: int) -> int:
        """Return the position after reading needed bits, or raise if they aren't there."""
        end = self._pos + needed
        if end > len(self._bits):
            raise bitstring.ReadError(
                f"Cannot read {needed} bits at position {self._pos}: only {self.remaining} "
                f"of the {len(self._bits)} bits are left.")
        return end

    @staticmethod
    def _dtype_from(fmt: str | Dtype) -> Dtype:
        if isinstance(fmt, Dtype):
            return fmt
        if not isinstance(fmt, str):
            raise TypeError(f"A dtype is needed here, either as a string such as 'u12' or as a "
                            f"Dtype object, but received a {type(fmt).__name__}. "
                            f"Use read_bits() to read a number of bits.")
        try:
            return Dtype(fmt)
        except ValueError:
            if "," in fmt:
                raise ValueError(f"'{fmt}' has more than one dtype in it. Use read_list() "
                                 f"to read several values at once.") from None
            raise

    @staticmethod
    def _dtype_with_length(dtype: Dtype, items: int) -> Dtype:
        return Dtype(dtype.name, items, dtype.scale)

    def read_value(self, dtype: str | Dtype, /) -> int | float | str | Bits | bool | bytes | None:
        """Read a single dtype from the current position and return its value.

        The dtype is given either as a string such as 'u12' or as a Dtype object. A dtype
        with no length, such as 'u', uses all of the remaining bits.

        Raises ReadError if fewer bits remain than the dtype needs, in which case the
        position doesn't move.

        """
        if type(dtype) is str:
            # Fast path for a fixed-length dtype, which is much the most common read.
            # Anything else (variable length, a short read) falls through to the general
            # version below, which reports the errors.
            info = _read_fmt_cache.get(dtype)
            if info is None:
                d = Reader._dtype_from(dtype)
                bitlength = d._bitlength
                if bitlength is not None:
                    tibs_dtype = None if d._scale is not None else \
                        bitstore.tibs_dtype_for(d._name, bitlength)
                    info = (bitlength, tibs_dtype, d)
                    if len(_read_fmt_cache) < _READ_FMT_CACHE_SIZE:
                        _read_fmt_cache[dtype] = info
            if info is not None:
                bitlength, tibs_dtype, d = info
                pos = self._pos
                end = pos + bitlength
                if end <= len(self._bits):
                    if tibs_dtype is not None:
                        value = self._bits._bitstore.to_value(tibs_dtype, pos, end)
                    else:
                        value = d._read_fn(self._bits, pos)
                    self._pos = end
                    return value
        return self._read_dtype(dtype)

    def _read_dtype(self, fmt: str | Dtype) -> int | float | str | Bits | bool | bytes | None:
        old_pos = self._pos
        try:
            dtype = Reader._dtype_from(fmt)
            if dtype.bitlength is None and not dtype.variable_length:
                # An unsized dtype such as 'u' or 'hex' takes everything that's left.
                bitlength = self.remaining
                items, remainder = divmod(bitlength, dtype.bits_per_item)
                if remainder != 0:
                    raise ValueError(
                        f"The '{dtype.name}' type must have a bit length that is a multiple of "
                        f"{dtype.bits_per_item} so cannot be read from the {bitlength} bits that are available.")
                dtype = Reader._dtype_with_length(dtype, items)
            if dtype.bitlength is not None:
                self._end_of_read(dtype.bitlength)
                value = dtype._read_fn(self._bits, self._pos)
                self._pos += dtype.bitlength
            else:
                value, self._pos = dtype._read_fn(self._bits, self._pos)
                if self._pos > len(self._bits):
                    raise bitstring.ReadError(
                        f"Reading off the end of the bitstring with dtype '{fmt}'. "
                        f"Only {len(self._bits) - old_pos} bits were available.")
            return value
        except Exception:
            self._pos = old_pos
            raise

    def read_bits(self, n: int, /) -> Bits:
        """Read n bits and return them, advancing the position by n.

        Raises ReadError if fewer than n bits remain, in which case the position doesn't
        move, and ValueError if n is negative.

        """
        n = Reader._as_int(n, "number of bits")
        if n < 0:
            raise ValueError(f"Cannot read a negative number of bits ({n}).")
        end = self._end_of_read(n)
        value = self._bits._slice(self._pos, end)
        self._pos = end
        return value

    def read_list(self, fmt: str | list[int | str | Dtype], **kwargs) \
            -> list[int | float | str | Bits | bool | bytes | None]:
        """Read one or more dtypes from the current position and return a list of values."""
        old_pos = self._pos
        try:
            value, self._pos = self._bits._readlist(fmt, self._pos, **kwargs)
            if self._pos > len(self._bits):
                raise bitstring.ReadError(
                    f"Reading off the end of the bitstring. "
                    f"Only {len(self._bits) - old_pos} bits were available.")
            return value
        except Exception:
            self._pos = old_pos
            raise

    def read_array(self, dtype: str | Dtype, /, count: int | None = None) -> bitstring.Array:
        """Read count items of one dtype and return them as an Array.

        If count isn't given then as many whole items as fit in the remaining bits are
        read, and any bits left over are not read.

        Raises ReadError if count is given and there aren't enough bits for that many
        items, in which case the position doesn't move.

        """
        d = Reader._dtype_from(dtype)
        itemsize = d.bitlength
        if itemsize is None:
            raise ValueError(f"read_array() needs a dtype with a fixed length, "
                             f"but '{dtype}' doesn't have one.")
        if count is None:
            count = self.remaining // itemsize
        else:
            count = Reader._as_int(count, "count")
            if count < 0:
                raise ValueError(f"Cannot read a negative number of items ({count}).")
        end = self._end_of_read(count * itemsize)
        array = bitstring.Array(d)
        array.data = self._bits._slice(self._pos, end).to_bitarray()
        self._pos = end
        return array

    def peek_value(self, dtype: str | Dtype, /) -> int | float | str | Bits | bool | bytes | None:
        """As read_value(), but leave the position unchanged."""
        pos = self._pos
        try:
            return self.read_value(dtype)
        finally:
            self._pos = pos

    def peek_bits(self, n: int, /) -> Bits:
        """As read_bits(), but leave the position unchanged."""
        pos = self._pos
        try:
            return self.read_bits(n)
        finally:
            self._pos = pos

    # ----- Searching -----

    def _search(self, bs: BitsType, byte_aligned: bool, mask: BitsType | None,
                backwards: bool = False) -> tuple[int | None, int]:
        """Search for bs, returning the position it was found at (or None) and its length."""
        if isinstance(bs, int):
            raise TypeError("Integers cannot be searched for. "
                            "Perhaps use a string such as '0x00' or 'u8=0'?")
        needle = Bits._create_from_bitstype(bs)
        if len(needle) == 0:
            raise ValueError("Cannot search for an empty bitstring.")
        mask_store = None if mask is None else Bits._create_from_bitstype(mask)._bitstore
        # The position is clamped rather than checked, so that a reader left beyond the
        # end of a BitArray that has since shrunk searches what is there now.
        pos = min(self._pos, len(self._bits))
        if backwards:
            found = self._bits._bitstore.rfind(needle._bitstore, 0, pos, byte_aligned, mask_store)
        else:
            found = self._bits._bitstore.find(needle._bitstore, pos, len(self._bits), byte_aligned, mask_store)
        return found, len(needle)

    def _found_or_raise(self, found: int | None) -> int:
        if found is None:
            raise bitstring.ReadError(
                f"Cannot read: the bits to find were not found at or after position {self._pos}. "
                f"Use seek_to() or seek_past() if not finding them is expected.")
        return found

    def seek_to(self, bs: BitsType, /, byte_aligned: bool = False,
                mask: BitsType | None = None) -> bool:
        """Search forwards for bs, moving the position to the start of the match.

        Returns True if it was found, otherwise False with the position unchanged. A
        match already under the cursor is found where it is and nothing moves, so
        seek_past() is the one to loop on.

        """
        found, _ = self._search(bs, byte_aligned, mask)
        if found is None:
            return False
        self._pos = found
        return True

    def seek_past(self, bs: BitsType, /, byte_aligned: bool = False,
                  mask: BitsType | None = None) -> bool:
        """Search forwards for bs, moving the position to just after the match.

        Returns True if it was found, otherwise False with the position unchanged. This
        is the method to loop on, as it always makes progress.

        """
        found, needle_length = self._search(bs, byte_aligned, mask)
        if found is None:
            return False
        self._pos = found + needle_length
        return True

    def seek_back_to(self, bs: BitsType, /, byte_aligned: bool = False,
                     mask: BitsType | None = None) -> bool:
        """Search backwards for bs, moving the position to the start of the match.

        Only matches that end at or before the current position are considered, so the
        position always ends up further back than it started. Returns True if it was
        found, otherwise False with the position unchanged.

        """
        found, _ = self._search(bs, byte_aligned, mask, backwards=True)
        if found is None:
            return False
        self._pos = found
        return True

    def read_to(self, bs: BitsType, /, byte_aligned: bool = False,
                mask: BitsType | None = None) -> Bits:
        """Read up to but not including the next occurrence of bs.

        The position is left at the start of the match, so the match itself is read by
        whatever comes next. Raises ReadError if bs isn't found, in which case the
        position doesn't move.

        """
        found, _ = self._search(bs, byte_aligned, mask)
        found = self._found_or_raise(found)
        value = self._bits._slice(self._pos, found)
        self._pos = found
        return value

    def read_past(self, bs: BitsType, /, byte_aligned: bool = False,
                  mask: BitsType | None = None) -> Bits:
        """Read up to and including the next occurrence of bs.

        The position is left just after the match, so a loop of read_past() calls always
        makes progress. Raises ReadError if bs isn't found, in which case the position
        doesn't move.

        """
        found, needle_length = self._search(bs, byte_aligned, mask)
        found = self._found_or_raise(found)
        end = found + needle_length
        value = self._bits._slice(self._pos, end)
        self._pos = end
        return value
