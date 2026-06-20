from __future__ import annotations

from tibs import Tibs, Mutibs

from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, Iterator, Any


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


def _to_u(tibs: Tibs | Mutibs) -> int:
    if len(tibs) <= 128:
        return tibs.to_u()
    return _fallback_to_u(tibs)


def _to_i(tibs: Tibs | Mutibs) -> int:
    if len(tibs) <= 128:
        return tibs.to_i()
    return _fallback_to_i(tibs)


class ConstBitStore:
    """A light wrapper around tibs.Tibs"""

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
    def from_bytes(cls, b: Union[bytes, bytearray, memoryview], /, offset: Optional[int] = None,
                   length: Optional[int] = None) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bytes(b, offset=offset, length=length)
        return x

    @classmethod
    def from_bools(cls, iterable: Iterable[Any], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bools(iterable)
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None, offset: Optional[int] = None) -> ConstBitStore:  #TODO: Shouldn't need a default here.
        mv = memoryview(buffer)
        if offset is None:
            offset = 0
        if offset < 0:
            raise CreationError("Can't create bitstring with a negative offset.")
        if offset > mv.nbytes * 8:
            raise CreationError(
                f"Can't create bitstring with an offset of {offset} from {mv.nbytes * 8} bits of data.")
        if length is not None:
            if length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if offset + length > mv.nbytes * 8:
                raise CreationError(
                    f"Can't create bitstring with a length of {length} from {mv.nbytes * 8 - offset} bits of data.")
            return cls.from_bytes(mv, offset=offset, length=length)
        return cls.from_bytes(mv, offset=offset)

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

    def read_bytes(self, start: int, length: int) -> bytes:
        return self.tibs.to_bytes(start, start + length)

    def byte_swapped(self, start: Optional[int] = None, end: Optional[int] = None) -> ConstBitStore:
        return ConstBitStore(self.tibs.byte_swapped(start=start, end=end))

    def to_u(self) -> int:
        return _to_u(self.tibs)

    def read_u(self, start: int, length: int) -> int:
        if length <= 128:
            return self.tibs.to_u(start, start + length)
        return _fallback_to_u(self.tibs[start:start + length])

    def to_i(self) -> int:
        return _to_i(self.tibs)

    def read_i(self, start: int, length: int) -> int:
        if length <= 128:
            return self.tibs.to_i(start, start + length)
        return _fallback_to_i(self.tibs[start:start + length])

    def to_hex(self) -> str:
        return self.tibs.to_hex()

    def read_hex(self, start: int, length: int) -> str:
        return self.tibs.to_hex(start, start + length)

    def to_bin(self) -> str:
        return self.tibs.to_bin()

    def read_bin(self, start: int, length: int) -> str:
        return self.tibs.to_bin(start, start + length)

    def to_oct(self) -> str:
        return self.tibs.to_oct()

    def read_oct(self, start: int, length: int) -> str:
        return self.tibs.to_oct(start, start + length)

    def __add__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs + other.tibs)

    def __eq__(self, other: Any, /) -> bool:
        if not isinstance(other, ConstBitStore):
            return NotImplemented
        return self.tibs == other.tibs

    def __and__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs & other.tibs)

    def __or__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs | other.tibs)

    def __xor__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore(self.tibs ^ other.tibs)

    def __invert__(self) -> ConstBitStore:
        return ConstBitStore(~self.tibs)

    def __lshift__(self, n: int, /) -> ConstBitStore:
        return ConstBitStore(self.tibs << n)

    def __rshift__(self, n: int, /) -> ConstBitStore:
        return ConstBitStore(self.tibs >> n)

    def find(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> int | None:
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> int | None:
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def findall(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.find_all_iter(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def rfindall(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.rfind_all_iter(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

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

    def getindex(self, index: int, /) -> bool:
        return self.tibs[index]

    def getslice_withstep(self, key: slice, /) -> ConstBitStore:
        return ConstBitStore(self.tibs[key])

    def getslice(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        return ConstBitStore(self.tibs[start:stop])

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
    """A light wrapper around tibs.Mutibs"""

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
    def from_bytes(cls, b: Union[bytes, bytearray, memoryview], /, offset: Optional[int] = None,
                   length: Optional[int] = None) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_bytes(b, offset=offset, length=length)
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

    def read_bytes(self, start: int, length: int) -> bytes:
        return self.tibs.to_bytes(start, start + length)

    def byte_swapped(self, start: Optional[int] = None, end: Optional[int] = None) -> MutableBitStore:
        return MutableBitStore(self.tibs.byte_swapped(start=start, end=end))

    def to_u(self) -> int:
        return _to_u(self.tibs)

    def read_u(self, start: int, length: int) -> int:
        if length <= 128:
            return self.tibs.to_u(start, start + length)
        return _fallback_to_u(self.tibs[start:start + length])

    def to_i(self) -> int:
        return _to_i(self.tibs)

    def read_i(self, start: int, length: int) -> int:
        if length <= 128:
            return self.tibs.to_i(start, start + length)
        return _fallback_to_i(self.tibs[start:start + length])

    def to_hex(self) -> str:
        return self.tibs.to_hex()

    def read_hex(self, start: int, length: int) -> str:
        return self.tibs.to_hex(start, start + length)

    def to_bin(self) -> str:
        return self.tibs.to_bin()

    def read_bin(self, start: int, length: int) -> str:
        return self.tibs.to_bin(start, start + length)

    def to_oct(self) -> str:
        return self.tibs.to_oct()

    def read_oct(self, start: int, length: int) -> str:
        return self.tibs.to_oct(start, start + length)

    def __ilshift__(self, n: int, /) -> MutableBitStore:
        self.tibs <<= n
        return self

    def __irshift__(self, n: int, /) -> MutableBitStore:
        self.tibs >>= n
        return self

    def __add__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore(self.tibs + other.tibs)

    def __iadd__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs += other.tibs
        return self

    def __eq__(self, other: Any, /) -> bool:
        if not isinstance(other, (MutableBitStore, ConstBitStore)):
            return NotImplemented
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

    def __lshift__(self, n: int, /) -> MutableBitStore:
        return MutableBitStore(self.tibs << n)

    def __rshift__(self, n: int, /) -> MutableBitStore:
        return MutableBitStore(self.tibs >> n)

    def find(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> int:
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False):
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def findall(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.to_tibs().find_all_iter(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def rfindall(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.to_tibs().rfind_all_iter(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def clear(self) -> None:
        self.tibs.clear()

    def reverse(self) -> None:
        self.tibs.reverse()

    def byte_swap(self, start: Optional[int], end: Optional[int]) -> None:
        self.tibs.byte_swap(start=start, end=end)

    # TODO: Should we remove iter from this mutable type?
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

    def getindex(self, index: int, /) -> bool:
        return self.tibs[index]

    def getslice_withstep(self, key: slice, /) -> MutableBitStore:
        return MutableBitStore(self.tibs[key])

    def getslice(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        return MutableBitStore(self.tibs[start:stop])

    def invert(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self.tibs.invert(index)
        else:
            self.tibs.invert()

    def set(self, value: Any, pos: Any, /) -> None:
        if value:
            self.tibs.set(pos)
        else:
            self.tibs.unset(pos)

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
                count: Optional[int] = None, bytealigned: bool = False) -> int:
        return self.tibs.replace(old.tibs, new.tibs, start=start, end=end, count=count,
                                 byte_aligned=bytealigned)

    def rotate_left(self, n: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        self.tibs.rotate_left(n, start=start, end=end)

    def rotate_right(self, n: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        self.tibs.rotate_right(n, start=start, end=end)

    def __len__(self) -> int:
        return len(self.tibs)

    def __setitem__(self, key, value, /):
        if isinstance(value, (MutableBitStore, ConstBitStore)):
            self.tibs.__setitem__(key, value.tibs)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            if value:
                self.tibs.set(key)
            else:
                self.tibs.unset(key)

    def __delitem__(self, key, /):
        self.tibs.__delitem__(key)
