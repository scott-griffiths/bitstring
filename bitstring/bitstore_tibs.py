from __future__ import annotations

from tibs import Tibs, Mutibs

from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any
from bitstring.helpers import offset_slice_indices_lsb0



class ConstBitStore:
    """A light wrapper around tibs.Tibs that does the LSB0 stuff"""

    __slots__ = ('_bits',)

    def __init__(self, initializer: Union[Mutibs, Tibs, None] = None) -> None:
        if initializer is not None:
            self._bits = initializer
        else:
            self._bits = Mutibs()

    @property
    def immutable(self) -> bool:
        return isinstance(self._bits, Tibs)

    @immutable.setter
    def immutable(self, value: bool) -> None:
        if value and not self.immutable:
            self._bits = self._bits.to_tibs()
        elif not value and self.immutable:
            self._bits = self._bits.to_mutibs()


    @classmethod
    def from_zeros(cls, i: int, immutable: bool):
        x = super().__new__(cls)
        if immutable:
            x._bits = Tibs.from_zeros(i)
        else:
            x._bits = Mutibs.from_zeros(i)
        return x

    @classmethod
    def _from_mutibs(cls, mb: Mutibs):
        x = super().__new__(cls)
        x._bits = mb.as_tibs()
        return x

    @classmethod
    def _from_tibs(cls, tb: Tibs):
        x = super().__new__(cls)
        x._bits = tb
        return x

    @classmethod
    def frombytes(cls, b: Union[bytes, bytearray, memoryview], /) -> ConstBitStore:
        x = super().__new__(cls)
        x._bits = Mutibs.from_bytes(b)
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None) -> ConstBitStore:
        x = super().__new__(cls)
        # TODO: tibs needs a Tibs.from_buffer method.
        x._bits = Tibs.from_bytes(bytes(buffer))
        if length is not None:
            if length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if length > len(x._bits):
                raise CreationError(
                    f"Can't create bitstring with a length of {length} from {len(x._bits)} bits of data.")
        return x.getslice(0, length) if length is not None else x

    @classmethod
    def from_binary_string(cls, s: str) -> ConstBitStore:
        x = super().__new__(cls)
        x._bits = Tibs.from_bin(s)
        return x

    def set(self, value, pos) -> None:
        self._bits.set(value, pos)

    @staticmethod
    def using_rust_core() -> bool:
        return True

    def tobitarray(self):
        raise TypeError("tobitarray() is not available when using the Rust core option.")

    def tobytes(self, pad_at_end: bool = True) -> bytes:
        excess_bits = len(self._bits) % 8
        if excess_bits != 0:
            # Pad with zeros to make full bytes
            if pad_at_end:
                padded_bits = self._bits + Mutibs.from_zeros(8 - excess_bits)
            else:
                padded_bits = Mutibs.from_zeros(8 - excess_bits) + self._bits
            return padded_bits.to_bytes()
        return self._bits.to_bytes()

    def to_uint(self) -> int:
        if len(self) > 128:
            return int.from_bytes(self.tobytes(pad_at_end=False), byteorder="big", signed=False)
        try:
            return self._bits.to_u()
        except OverflowError as e:
            raise ValueError(e)

    def to_int(self) -> int:
        if len(self) > 128:
            return int.from_bytes(self.tobytes(pad_at_end=False), byteorder="big", signed=True)
        try:
            return self._bits.to_i()
        except OverflowError as e:
            raise ValueError(e)

    def to_hex(self) -> str:
        return self._bits.to_hex()

    def to_bin(self) -> str:
        return self._bits.to_bin()

    def to_oct(self) -> str:
        return self._bits.to_oct()

    def imul(self, n: int, /) -> None:
        self._bits *= n

    def ilshift(self, n: int, /) -> None:
        self._bits <<= n

    def irshift(self, n: int, /) -> None:
        self._bits >>= n

    def __iadd__(self, other: ConstBitStore, /) -> ConstBitStore:
        self._bits += other._bits
        return self

    def __add__(self, other: ConstBitStore, /) -> ConstBitStore:
        newbits = self._bits + other._bits
        return ConstBitStore._from_tibs(newbits)

    def __eq__(self, other: Any, /) -> bool:
        return self._bits == other._bits

    def __and__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore._from_tibs(self._bits & other._bits)

    def __or__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore._from_tibs(self._bits | other._bits)

    def __xor__(self, other: ConstBitStore, /) -> ConstBitStore:
        return ConstBitStore._from_tibs(self._bits ^ other._bits)

    def __iand__(self, other: ConstBitStore, /) -> ConstBitStore:
        self._bits &= other._bits
        return self

    def __ior__(self, other: ConstBitStore, /) -> ConstBitStore:
        self._bits |= other._bits
        return self

    def __ixor__(self, other: ConstBitStore, /) -> ConstBitStore:
        self._bits ^= other._bits
        return self

    def find(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> int:
        assert start >= 0
        x = self._bits.find(bs._bits, start, end, byte_aligned=bytealigned)
        return -1 if x is None else x

    def rfind(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False):
        assert start >= 0
        x = self._bits.rfind(bs._bits, start, end, byte_aligned=bytealigned)
        return -1 if x is None else x

    def findall_msb0(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self._bits if self.immutable else self._bits.to_tibs()
        for p in x.find_all(bs._bits, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def rfindall_msb0(self, bs: ConstBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self._bits if self.immutable else self._bits.to_tibs()
        for p in x.rfind_all(bs._bits, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def count(self, value, /) -> int:
        return self._bits.count(value)

    def clear(self) -> None:
        self._bits.clear()

    def reverse(self) -> None:
        self._bits.reverse()

    def __iter__(self) -> Iterable[bool]:
        length = len(self)
        for i in range(length):
            yield self.getindex(i)

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        if self.immutable:
            return MutableBitStore._from_mutibs(self._bits.to_mutibs())
        return MutableBitStore._from_mutibs(self._bits.__copy__())

    def as_immutable(self) -> ConstBitStore:
        if self.immutable:
            return self
        return ConstBitStore(self._bits.as_tibs())

    def copy(self) -> ConstBitStore:
        return self if self.immutable else self._mutable_copy()

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, ConstBitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return self._bits.__getitem__(index)

    def getslice_withstep_msb0(self, key: slice, /) -> ConstBitStore:
        return ConstBitStore(self._bits.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> ConstBitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return ConstBitStore(self._bits.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        return ConstBitStore(self._bits[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> ConstBitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return ConstBitStore(self._bits[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self._bits.__getitem__(-index - 1)

    @overload
    def setitem_lsb0(self, key: int, value: int, /) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: ConstBitStore, /) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, ConstBitStore], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._bits.__setitem__(new_slice, value._bits)
        else:
            self._bits.__setitem__(-key - 1, bool(value))

    def delitem_lsb0(self, key: Union[int, slice], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._bits.__delitem__(new_slice)
        else:
            self._bits.__delitem__(-key - 1)

    def invert_msb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._bits.invert(index)
        else:
            self._bits.invert()

    def invert_lsb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._bits.invert(-index - 1)
        else:
            self._bits.invert()

    def any_set(self) -> bool:
        return self._bits.any()

    def all_set(self) -> bool:
        return self._bits.all()

    def __len__(self) -> int:
        return len(self._bits)

    def setitem_msb0(self, key, value, /):
        if isinstance(value, ConstBitStore):
            self._bits.__setitem__(key, value._bits)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            self._bits.set(value, key)

    def delitem_msb0(self, key, /):
        self._bits.__delitem__(key)


class MutableBitStore:
    """A light wrapper around tibs.Mutibs that does the LSB0 stuff"""

    __slots__ = ('_bits',)

    def __init__(self, initializer: Union[Mutibs, Tibs, None] = None) -> None:
        if initializer is not None:
            self._bits = initializer
        else:
            self._bits = Mutibs()

    @property
    def immutable(self) -> bool:
        return isinstance(self._bits, Tibs)

    @immutable.setter
    def immutable(self, value: bool) -> None:
        if value and not self.immutable:
            self._bits = self._bits.to_tibs()
        elif not value and self.immutable:
            self._bits = self._bits.to_mutibs()

    @classmethod
    def from_zeros(cls, i: int, immutable: bool):
        x = super().__new__(cls)
        if immutable:
            x._bits = Tibs.from_zeros(i)
        else:
            x._bits = Mutibs.from_zeros(i)
        return x

    @classmethod
    def _from_mutibs(cls, mb: Mutibs):
        assert isinstance(mb, Mutibs)
        x = super().__new__(cls)
        x._bits = mb
        return x

    @classmethod
    def frombytes(cls, b: Union[bytes, bytearray, memoryview], /) -> MutableBitStore:
        x = super().__new__(cls)
        x._bits = Mutibs.from_bytes(b)
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None) -> MutableBitStore:
        x = super().__new__(cls)
        # TODO: tibs needs a Bits.from_buffer method.
        x._bits = Tibs.from_bytes(bytes(buffer))
        if length is not None:
            if length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if length > len(x._bits):
                raise CreationError(
                    f"Can't create bitstring with a length of {length} from {len(x._bits)} bits of data.")
        return x.getslice(0, length) if length is not None else x

    @classmethod
    def from_binary_string(cls, s: str) -> MutableBitStore:
        x = super().__new__(cls)
        x._bits = Tibs.from_bin(s)
        return x

    def set(self, value, pos) -> None:
        self._bits.set(value, pos)

    @staticmethod
    def using_rust_core() -> bool:
        return True

    def tobitarray(self):
        raise TypeError("tobitarray() is not available when using the Rust core option.")

    def tobytes(self, pad_at_end: bool = True) -> bytes:
        excess_bits = len(self._bits) % 8
        if excess_bits != 0:
            # Pad with zeros to make full bytes
            if pad_at_end:
                padded_bits = self._bits + Mutibs.from_zeros(8 - excess_bits)
            else:
                padded_bits = Mutibs.from_zeros(8 - excess_bits) + self._bits
            return padded_bits.to_bytes()
        return self._bits.to_bytes()

    def to_uint(self) -> int:
        if len(self) > 128:
            return int.from_bytes(self.tobytes(pad_at_end=False), byteorder="big", signed=False)
        try:
            return self._bits.to_u()
        except OverflowError as e:
            raise ValueError(e)

    def to_int(self) -> int:
        if len(self) > 128:
            return int.from_bytes(self.tobytes(pad_at_end=False), byteorder="big", signed=True)
        try:
            return self._bits.to_i()
        except OverflowError as e:
            raise ValueError(e)

    def to_hex(self) -> str:
        return self._bits.to_hex()

    def to_bin(self) -> str:
        return self._bits.to_bin()

    def to_oct(self) -> str:
        return self._bits.to_oct()

    def imul(self, n: int, /) -> None:
        self._bits *= n

    def ilshift(self, n: int, /) -> None:
        self._bits <<= n

    def irshift(self, n: int, /) -> None:
        self._bits >>= n

    def __iadd__(self, other: MutableBitStore, /) -> MutableBitStore:
        self._bits += other._bits
        return self

    def __add__(self, other: MutableBitStore, /) -> MutableBitStore:
        bs = self._mutable_copy()
        bs += other
        return bs

    def __eq__(self, other: Any, /) -> bool:
        return self._bits == other._bits

    def __and__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore._from_mutibs(self._bits & other._bits)

    def __or__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore._from_mutibs(self._bits | other._bits)

    def __xor__(self, other: MutableBitStore, /) -> MutableBitStore:
        return MutableBitStore._from_mutibs(self._bits ^ other._bits)

    def __iand__(self, other: MutableBitStore, /) -> MutableBitStore:
        self._bits &= other._bits
        return self

    def __ior__(self, other: MutableBitStore, /) -> MutableBitStore:
        self._bits |= other._bits
        return self

    def __ixor__(self, other: MutableBitStore, /) -> MutableBitStore:
        self._bits ^= other._bits
        return self

    def find(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> int:
        assert start >= 0
        x = self._bits.find(bs._bits, start, end, byte_aligned=bytealigned)
        return -1 if x is None else x

    def rfind(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False):
        assert start >= 0
        x = self._bits.rfind(bs._bits, start, end, byte_aligned=bytealigned)
        return -1 if x is None else x

    def findall_msb0(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self._bits if self.immutable else self._bits.to_tibs()
        for p in x.find_all(bs._bits, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def rfindall_msb0(self, bs: MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self._bits if self.immutable else self._bits.to_tibs()
        for p in x.rfind_all(bs._bits, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def count(self, value, /) -> int:
        return self._bits.count(value)

    def clear(self) -> None:
        self._bits.clear()

    def reverse(self) -> None:
        self._bits.reverse()

    def __iter__(self) -> Iterable[bool]:
        for i in range(len(self)):
            yield self.getindex(i)

    def extend_left(self, other: MutableBitStore, /) -> None:
        self._bits.extend_left(other._bits)

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        if self.immutable:
            return MutableBitStore._from_mutibs(self._bits.to_mutibs())
        return MutableBitStore._from_mutibs(self._bits.__copy__())

    def as_immutable(self) -> MutableBitStore:
        if self.immutable:
            return self
        return MutableBitStore(self._bits.as_tibs())

    def copy(self) -> MutableBitStore:
        return self if self.immutable else self._mutable_copy()

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, MutableBitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return self._bits.__getitem__(index)

    def getslice_withstep_msb0(self, key: slice, /) -> MutableBitStore:
        return MutableBitStore(self._bits.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> MutableBitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return MutableBitStore(self._bits.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        return MutableBitStore(self._bits[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> MutableBitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return MutableBitStore(self._bits[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self._bits.__getitem__(-index - 1)

    @overload
    def setitem_lsb0(self, key: int, value: int, /) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: MutableBitStore, /) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, MutableBitStore], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._bits.__setitem__(new_slice, value._bits)
        else:
            self._bits.__setitem__(-key - 1, bool(value))

    def delitem_lsb0(self, key: Union[int, slice], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._bits.__delitem__(new_slice)
        else:
            self._bits.__delitem__(-key - 1)

    def invert_msb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._bits.invert(index)
        else:
            self._bits.invert()

    def invert_lsb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._bits.invert(-index - 1)
        else:
            self._bits.invert()

    def any_set(self) -> bool:
        return self._bits.any()

    def all_set(self) -> bool:
        return self._bits.all()

    def __len__(self) -> int:
        return len(self._bits)

    def setitem_msb0(self, key, value, /):
        if isinstance(value, (MutableBitStore, ConstBitStore)):
            self._bits.__setitem__(key, value._bits)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            self._bits.set(value, key)

    def delitem_msb0(self, key, /):
        self._bits.__delitem__(key)
