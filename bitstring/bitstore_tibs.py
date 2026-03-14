from __future__ import annotations

from tibs import Tibs, Mutibs

from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any
from bitstring.helpers import offset_slice_indices_lsb0


class ConstBitStore:
    """A light wrapper around tibs.Tibs that does the LSB0 stuff"""

    __slots__ = ('tibs',)

    def __init__(self, initializer: Tibs) -> None:
        self.tibs = initializer

    @classmethod
    def join(cls, bitstores: Iterable[ConstBitStore], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_joined(b.tibs for b in bitstores)
        return x

    @classmethod
    def from_zeros(cls, i: int):
        x = super().__new__(cls)
        x.tibs = Tibs.from_zeros(i)
        return x

    @classmethod
    def from_bytes(cls, b: Union[bytes, bytearray, memoryview], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bytes(b)
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None) -> ConstBitStore:
        x = super().__new__(cls)
        # TODO: tibs needs a Tibs.from_buffer method.
        x.tibs = Tibs.from_bytes(bytes(buffer))
        if length is not None:
            if length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if length > len(x.tibs):
                raise CreationError(
                    f"Can't create bitstring with a length of {length} from {len(x.tibs)} bits of data.")
        return x.getslice(0, length) if length is not None else x

    @classmethod
    def from_bin(cls, s: str) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bin(s)
        return x

    def to_bytes(self) -> bytes:
        padding = 8 - len(self.tibs) % 8
        if padding == 8:
            return self.tibs.to_bytes()
        return (self.tibs + [0] * padding).to_bytes()

    def to_u(self) -> int:
        if len(self) > 128:
            padding = 8 - len(self.tibs) % 8
            if padding == 8:
                b = self.tibs.to_bytes()
            else:
                b = ([0] * padding + self.tibs).to_bytes()
            return int.from_bytes(b, byteorder="big", signed=False)
        try:
            return self.tibs.to_u()
        except OverflowError as e:
            raise ValueError(e)

    def to_i(self) -> int:
        if len(self) > 128:
            padding = 8 - len(self.tibs) % 8
            if padding == 8:
                b = self.tibs.to_bytes()
            else:
                pad_bit = self.tibs[0]  # Keep sign when padding
                b = ([pad_bit] * padding + self.tibs).to_bytes()
            return int.from_bytes(b, byteorder="big", signed=True)
        try:
            return self.tibs.to_i()
        except OverflowError as e:
            raise ValueError(e)

    def to_hex(self) -> str:
        return self.tibs.to_hex()

    def to_bin(self) -> str:
        return self.tibs.to_bin()

    def to_oct(self) -> str:
        return self.tibs.to_oct()

    def __add__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs + other.tibs)

    def __eq__(self, other: Any, /) -> bool:
        return self.tibs == other.tibs

    def __and__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs & other.tibs)

    def __or__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs | other.tibs)

    def __xor__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs ^ other.tibs)

    def __invert__(self) -> ConstBitStore:
        return ConstBitStore(~self.tibs)

    def find(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> int | None:
        assert start >= 0
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> int | None:
        assert start >= 0
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def findall_msb0(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self.tibs
        for p in x.find_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def rfindall_msb0(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self.tibs
        for p in x.rfind_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def __iter__(self) -> Iterable[bool]:
        length = len(self)
        for i in range(length):
            yield self.getindex(i)

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        return MutableBitStore(self.tibs.to_mutibs())

    def copy(self) -> ConstBitStore:
        return self

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, ConstBitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return self.tibs.__getitem__(index)

    def getslice_withstep_msb0(self, key: slice, /) -> ConstBitStore:
        return ConstBitStore(self.tibs.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> ConstBitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return ConstBitStore(self.tibs.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        return ConstBitStore(self.tibs[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return ConstBitStore(self.tibs[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self.tibs.__getitem__(-index - 1)

    def any(self) -> bool:
        return self.tibs.any()

    def all(self) -> bool:
        return self.tibs.all()

    def __len__(self) -> int:
        return len(self.tibs)


class MutableBitStore:
    """A light wrapper around tibs.Mutibs that does the LSB0 stuff"""

    __slots__ = ('tibs',)

    def __init__(self, initializer: Mutibs) -> None:
        self.tibs = initializer

    @classmethod
    def from_zeros(cls, i: int):
        x = super().__new__(cls)
        x.tibs = Mutibs.from_zeros(i)
        return x

    @classmethod
    def from_bytes(cls, b: Union[bytes, bytearray, memoryview], /) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_bytes(b)
        return x

    @classmethod
    def from_bin(cls, s: str) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_bin(s)
        return x

    def to_bytes(self, pad_at_end: bool = True) -> bytes:
        excess_bits = len(self.tibs) % 8
        if excess_bits != 0:
            # Pad with zeros to make full bytes
            if pad_at_end:
                padded_bits = self.tibs + Mutibs.from_zeros(8 - excess_bits)
            else:
                padded_bits = Mutibs.from_zeros(8 - excess_bits) + self.tibs
            return padded_bits.to_bytes()
        return self.tibs.to_bytes()

    def to_u(self) -> int:
        if len(self) > 128:
            return int.from_bytes(self.to_bytes(pad_at_end=False), byteorder="big", signed=False)
        try:
            return self.tibs.to_u()
        except OverflowError as e:
            raise ValueError(e)

    def to_i(self) -> int:
        if len(self) > 128:
            return int.from_bytes(self.to_bytes(pad_at_end=False), byteorder="big", signed=True)
        try:
            return self.tibs.to_i()
        except OverflowError as e:
            raise ValueError(e)

    def to_hex(self) -> str:
        return self.tibs.to_hex()

    def to_bin(self) -> str:
        return self.tibs.to_bin()

    def to_oct(self) -> str:
        return self.tibs.to_oct()

    def __ilshift__(self, n: int, /) -> None:
        self.tibs <<= n

    def __irshift__(self, n: int, /) -> None:
        self.tibs >>= n

    def __add__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs + other.tibs)

    def __eq__(self, other: Any, /) -> bool:
        return self.tibs == other.tibs

    def __and__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs & other.tibs)

    def __or__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs | other.tibs)

    def __xor__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs ^ other.tibs)

    def __invert__(self) -> MutableBitStore:
        return MutableBitStore(~self.tibs)

    def find(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> int:
        assert start >= 0
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False):
        assert start >= 0
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def findall_msb0(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self.tibs.to_tibs()
        for p in x.find_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def rfindall_msb0(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self.tibs.to_tibs()
        for p in x.rfind_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def clear(self) -> None:
        self.tibs.clear()

    def reverse(self) -> None:
        self.tibs.reverse()

    def __iter__(self) -> Iterable[bool]:
        for i in range(len(self)):
            yield self.getindex(i)

    def extend_left(self, other: MutableBitStore, /) -> None:
        self.tibs.extend_left(other.tibs)

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        return MutableBitStore(self.tibs.__copy__())

    def copy(self) -> MutableBitStore:
        return self._mutable_copy()

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, MutableBitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return self.tibs.__getitem__(index)

    def getslice_withstep_msb0(self, key: slice, /) -> MutableBitStore:
        return MutableBitStore(self.tibs.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> MutableBitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return MutableBitStore(self.tibs.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        return MutableBitStore(self.tibs[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return MutableBitStore(self.tibs[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self.tibs.__getitem__(-index - 1)

    @overload
    def setitem_lsb0(self, key: int, value: int, /) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: MutableBitStore, /) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, MutableBitStore], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self.tibs.__setitem__(new_slice, value.tibs)
        else:
            self.tibs.__setitem__(-key - 1, bool(value))

    def delitem_lsb0(self, key: Union[int, slice], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self.tibs.__delitem__(new_slice)
        else:
            self.tibs.__delitem__(-key - 1)

    def invert_msb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self.tibs.invert(index)
        else:
            self.tibs.invert()

    def invert_lsb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self.tibs.invert(-index - 1)
        else:
            self.tibs.invert()

    def any(self) -> bool:
        return self.tibs.any()

    def all(self) -> bool:
        return self.tibs.all()

    def __len__(self) -> int:
        return len(self.tibs)

    def setitem_msb0(self, key, value, /):
        if isinstance(value, (MutableBitStore, ConstBitStore)):
            self.tibs.__setitem__(key, value.tibs)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            self.tibs.set(value, key)

    def delitem_msb0(self, key, /):
        self.tibs.__delitem__(key)
