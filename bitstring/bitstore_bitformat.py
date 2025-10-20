from __future__ import annotations

from bitformat import MutableBits, Bits, DtypeSingle

from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any
from bitstring.helpers import offset_slice_indices_lsb0


u_dtype = DtypeSingle('u')
i_dtype = DtypeSingle('i')
bin_dtype = DtypeSingle('bin')
oct_dtype = DtypeSingle('oct')
hex_dtype = DtypeSingle('hex')


class _BitStore:
    """A light wrapper around bitformat.MutableBits/Bits that does the LSB0 stuff"""

    __slots__ = ('_bits',)

    def __init__(self, initializer: Union[MutableBits, Bits, None] = None) -> None:
        if initializer is not None:
            self._bits = initializer
        else:
            self._bits = MutableBits()

    @property
    def immutable(self) -> bool:
        return isinstance(self._bits, Bits)

    @immutable.setter
    def immutable(self, value: bool) -> None:
        if value and not self.immutable:
            self._bits = self._bits.to_bits()
        elif not value and self.immutable:
            self._bits = self._bits.to_mutable_bits()

    @classmethod
    def from_int(cls, i: int, immutable: bool):
        x = super().__new__(cls)
        if immutable:
            x._bits = Bits.from_zeros(i)
        else:
            x._bits = MutableBits.from_zeros(i)
        return x

    @classmethod
    def _from_mutablebits(cls, mb: MutableBits):
        x = super().__new__(cls)
        x._bits = mb
        return x

    @classmethod
    def frombytes(cls, b: Union[bytes, bytearray, memoryview], /) -> _BitStore:
        x = super().__new__(cls)
        x._bits = MutableBits.from_bytes(b)
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None) -> _BitStore:
        x = super().__new__(cls)
        # TODO: bitformat needs a Bits.from_buffer method.
        x._bits = Bits.from_bytes(bytes(buffer))
        if length is not None:
            if length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if length > len(x._bits):
                raise CreationError(
                    f"Can't create bitstring with a length of {length} from {len(x._bits)} bits of data.")
        return x.getslice(0, length) if length is not None else x

    @classmethod
    def from_binary_string(cls, s: str) -> _BitStore:
        x = super().__new__(cls)
        x._bits = Bits.from_dtype(bin_dtype, s)
        return x

    def set(self, value, pos) -> None:
        self._bits.set(value, pos)

    @staticmethod
    def using_rust_core() -> bool:
        return True

    def tobitarray(self):
        raise TypeError("tobitarray() is not available when using the Rust core option.")

    def tobytes(self) -> bytes:
        return self._bits.to_bytes()

    def slice_to_uint(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return self._bits.unpack(u_dtype, start=start, end=end)

    def slice_to_int(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return self._bits.unpack(i_dtype, start=start, end=end)

    def slice_to_hex(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self._bits.unpack(hex_dtype, start=start, end=end)

    def slice_to_bin(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self._bits.unpack(bin_dtype, start=start, end=end)

    def slice_to_oct(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self._bits.unpack(oct_dtype, start=start, end=end)

    def imul(self, n: int, /) -> None:
        self._bits *= n

    def ilshift(self, n: int, /) -> None:
        self._bits <<= n

    def irshift(self, n: int, /) -> None:
        self._bits >>= n

    def __iadd__(self, other: _BitStore, /) -> _BitStore:
        self._bits += other._bits
        return self

    def __add__(self, other: _BitStore, /) -> _BitStore:
        bs = self._mutable_copy()
        bs += other
        return bs

    def __eq__(self, other: Any, /) -> bool:
        return self._bits == other._bits

    def __and__(self, other: _BitStore, /) -> _BitStore:
        return _BitStore._from_mutablebits(self._bits & other._bits)

    def __or__(self, other: _BitStore, /) -> _BitStore:
        return _BitStore._from_mutablebits(self._bits | other._bits)

    def __xor__(self, other: _BitStore, /) -> _BitStore:
        return _BitStore._from_mutablebits(self._bits ^ other._bits)

    def __iand__(self, other: _BitStore, /) -> _BitStore:
        self._bits &= other._bits
        return self

    def __ior__(self, other: _BitStore, /) -> _BitStore:
        self._bits |= other._bits
        return self

    def __ixor__(self, other: _BitStore, /) -> _BitStore:
        self._bits ^= other._bits
        return self

    def find(self, bs: _BitStore, start: int, end: int, bytealigned: bool = False) -> int:
        assert start >= 0
        x = self._bits.find(bs._bits, start, end, byte_aligned=bytealigned)
        return -1 if x is None else x

    def rfind(self, bs: _BitStore, start: int, end: int, bytealigned: bool = False):
        assert start >= 0
        x = self._bits.rfind(bs._bits, start, end, byte_aligned=bytealigned)
        return -1 if x is None else x

    def findall_msb0(self, bs: _BitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self._bits if self.immutable else self._bits.to_bits()
        for p in x.find_all(bs._bits, start=start, end=end, byte_aligned=bytealigned):
            yield p

    def rfindall_msb0(self, bs: _BitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        x = self._bits if self.immutable else self._bits.to_bits()
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

    def _mutable_copy(self) -> _BitStore:
        """Always creates a copy, even if instance is immutable."""
        if self.immutable:
            return _BitStore._from_mutablebits(self._bits.to_mutable_bits())
        return _BitStore._from_mutablebits(self._bits.__copy__())

    def as_immutable(self) -> _BitStore:
        if self.immutable:
            return self
        return _BitStore(self._bits.as_bits())

    def copy(self) -> _BitStore:
        return self if self.immutable else self._mutable_copy()

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, _BitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return self._bits.__getitem__(index)

    def getslice_withstep_msb0(self, key: slice, /) -> _BitStore:
        return _BitStore(self._bits.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> _BitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return _BitStore(self._bits.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> _BitStore:
        return _BitStore(self._bits[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> _BitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return _BitStore(self._bits[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return self._bits.__getitem__(-index - 1)

    @overload
    def setitem_lsb0(self, key: int, value: int, /) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: _BitStore, /) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, _BitStore], /) -> None:
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
        if isinstance(value, _BitStore):
            self._bits.__setitem__(key, value._bits)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            self._bits.set(value, key)

    def delitem_msb0(self, key, /):
        self._bits.__delitem__(key)


ConstBitStore = _BitStore
MutableBitStore = _BitStore