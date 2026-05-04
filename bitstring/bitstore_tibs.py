from __future__ import annotations

from tibs import Tibs, Mutibs

from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any
from bitstring.helpers import offset_slice_indices_lsb0


def _fallback_to_u(tibs: Tibs | Mutibs) -> int:
    if len(tibs) == 0:
        # Keep tibs' validation behaviour for zero-length conversion.
        return tibs.to_u()
    padding = (-len(tibs)) % 8
    if padding:
        tibs = [0] * padding + tibs
    return int.from_bytes(tibs.to_bytes(), byteorder="big", signed=False)


def _fallback_to_i(tibs: Tibs | Mutibs) -> int:
    if len(tibs) == 0:
        # Keep tibs' validation behaviour for zero-length conversion.
        return tibs.to_i()
    padding = (-len(tibs)) % 8
    if padding:
        pad_bit = tibs[0]
        tibs = [pad_bit] * padding + tibs
    return int.from_bytes(tibs.to_bytes(), byteorder="big", signed=True)


class ConstBitStore:
    """A light wrapper around tibs.Tibs that does the LSB0 stuff"""

    __slots__ = ('tibs',)

    def __init__(self, initializer: Tibs) -> None:
        self.tibs = initializer

    @classmethod
    def join(cls, bitstores: Iterable[ConstBitStore], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_joined((b.tibs for b in bitstores))
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
    def from_bools(cls, iterable: Iterable[Any], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bools(iterable)
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None) -> ConstBitStore:  #TODO: Shouldn't need a default here.
        x = super().__new__(cls)
        x.tibs = Tibs.from_bytes(memoryview(buffer))
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
        try:
            return self.tibs.to_u()
        except ValueError:
            return _fallback_to_u(self.tibs)

    def to_i(self) -> int:
        try:
            return self.tibs.to_i()
        except ValueError:
            return _fallback_to_i(self.tibs)

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
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> int | None:
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def findall_msb0(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.find_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def rfindall_msb0(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.rfind_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def __iter__(self) -> Iterable[bool]:
        return self.tibs.__iter__()

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        return MutableBitStore(self.tibs.to_mutibs())

    def copy(self) -> ConstBitStore:
        return self

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, ConstBitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return self.tibs[index]

    def getslice_withstep_msb0(self, key: slice, /) -> ConstBitStore:
        return ConstBitStore(self.tibs[key])

    def getslice_withstep_lsb0(self, key: slice, /) -> ConstBitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return ConstBitStore(self.tibs[key])

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        return ConstBitStore(self.tibs[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return ConstBitStore(self.tibs[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self.tibs[-index - 1]

    def any(self) -> bool:
        return self.tibs.any()

    def all(self) -> bool:
        return self.tibs.all()

    def startswith(self, prefix: ConstBitStore) -> bool:
        return self.tibs.starts_with(prefix.tibs)

    def endswith(self, suffix: ConstBitStore) -> bool:
        return self.tibs.ends_with(suffix.tibs)

    def count(self, value: Any) -> int:
        return self.tibs.count(value)

    def __len__(self) -> int:
        return len(self.tibs)


class MutableBitStore:
    """A light wrapper around tibs.Mutibs that does the LSB0 stuff"""

    __slots__ = ('tibs',)

    def __init__(self, initializer: Mutibs) -> None:
        self.tibs = initializer

    @classmethod
    def join(cls, bitstores: Iterable[MutableBitStore], /) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_joined((b.tibs for b in bitstores))
        return x

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
    def from_bools(cls, iterable: Iterable[Any], /) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_bools(iterable)
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
        try:
            return self.tibs.to_u()
        except ValueError:
            return _fallback_to_u(self.tibs)

    def to_i(self) -> int:
        try:
            return self.tibs.to_i()
        except ValueError:
            return _fallback_to_i(self.tibs)

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

    def __iadd__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs += other.tibs
        return self

    def __eq__(self, other: Any, /) -> bool:
        return self.tibs == other.tibs

    def __and__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs & other.tibs)

    def __iand__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs &= other.tibs
        return self

    def __or__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs | other.tibs)

    def __ior__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs |= other.tibs
        return self

    def __xor__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs ^ other.tibs)

    def __ixor__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs ^= other.tibs
        return self

    def __invert__(self) -> MutableBitStore:
        return MutableBitStore(~self.tibs)

    def find(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> int:
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False):
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def findall_msb0(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.to_tibs().find_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def rfindall_msb0(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.to_tibs().rfind_all(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def clear(self) -> None:
        self.tibs.clear()

    def reverse(self) -> None:
        self.tibs.reverse()

    def __iter__(self) -> Iterable[bool]:
        for i in range(len(self)):
            yield self.getindex(i)

    def extend_left(self, other: MutableBitStore | ConstBitStore, /) -> None:
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
        return self.tibs[index]

    def getslice_withstep_msb0(self, key: slice, /) -> MutableBitStore:
        return MutableBitStore(self.tibs[key])

    def getslice_withstep_lsb0(self, key: slice, /) -> MutableBitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return MutableBitStore(self.tibs[key])

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        return MutableBitStore(self.tibs[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return MutableBitStore(self.tibs[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self.tibs[-index - 1]

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

    def startswith(self, prefix: MutableBitStore | ConstBitStore) -> bool:
        return self.tibs.starts_with(prefix.tibs)

    def endswith(self, suffix: MutableBitStore | ConstBitStore) -> bool:
        return self.tibs.ends_with(suffix.tibs)

    def count(self, value: Any) -> int:
        return self.tibs.count(value)

    def replace(self, old: MutableBitStore | ConstBitStore, new: MutableBitStore | ConstBitStore,
                start: Optional[int] = None, end: Optional[int] = None,
                count: Optional[int] = None, bytealigned: bool = False) -> None:
        self.tibs.replace(old.tibs, new.tibs, start=start, end=end, count=count, byte_aligned=bytealigned)

    def rotate_left(self, n: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        self.tibs.rotate_left(n, start=start, end=end)

    def rotate_right(self, n: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        self.tibs.rotate_right(n, start=start, end=end)

    def __len__(self) -> int:
        return len(self.tibs)

    def setitem_msb0(self, key, value, /):
        if isinstance(value, (MutableBitStore, ConstBitStore)):
            self.tibs.__setitem__(key, value.tibs)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            if value:
                self.tibs.set(key)
            else:
                self.tibs.unset(key)

    def delitem_msb0(self, key, /):
        self.tibs.__delitem__(key)
