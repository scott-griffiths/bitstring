from __future__ import annotations

from bitformat import MutableBits
from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any
from bitstring.helpers import offset_slice_indices_lsb0

class BitStore:
    """A light wrapper around bitformat.MutableBits that does the LSB0 stuff"""

    __slots__ = ('_mutablebits', 'modified_length', 'immutable')

    def __init__(self, initializer: Union[MutableBits, None] = None,
                 immutable: bool = False) -> None:
        if initializer is not None:
            assert isinstance(initializer, MutableBits)
            self._mutablebits = MutableBits()
            self._mutablebits += initializer
        else:
            self._mutablebits = MutableBits()
        self.immutable = immutable
        self.modified_length = None

    @classmethod
    def from_int(cls, i: int):
        x = super().__new__(cls)
        x._mutablebits = MutableBits.from_zeros(i)
        x.immutable = False
        x.modified_length = None
        return x

    @classmethod
    def from_mutablebits(cls, mb: MutableBits):
        x = super().__new__(cls)
        x._mutablebits = mb
        x.immutable = False
        x.modified_length = None
        return x

    @classmethod
    def frombytes(cls, b: Union[bytes, bytearray, memoryview], /) -> BitStore:
        x = super().__new__(cls)
        x._mutablebits = MutableBits.from_bytes(b)
        x.immutable = False
        x.modified_length = None
        return x

    @classmethod
    def frombuffer(cls, buffer, /, length: Optional[int] = None) -> BitStore:
        x = super().__new__(cls)
        x._mutablebits = MutableBits.from_bytes(bytes(buffer))
        x.immutable = True
        x.modified_length = length
        # Here 'modified' means it shouldn't be changed further, so setting, deleting etc. are disallowed.
        if x.modified_length is not None:
            if x.modified_length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if x.modified_length > len(x._mutablebits):
                raise CreationError(
                    f"Can't create bitstring with a length of {x.modified_length} from {len(x._mutablebits)} bits of data.")
        return x

    @classmethod
    def from_binary_string(cls, s: str) -> BitStore:
        x = super().__new__(cls)
        x._mutablebits = MutableBits.from_dtype('bin', s)
        x.immutable = False
        x.modified_length = None
        return x

    def set(self, value, pos) -> None:
        self._mutablebits.set(value, pos)

    @staticmethod
    def using_rust_core() -> bool:
        return True

    def tobitarray(self):
        raise TypeError("tobitarray() is not available when using the Rust core option.")

    def tobytes(self) -> bytes:
        if self.modified_length is not None:
            return self._mutablebits[:self.modified_length].to_bytes()
        return self._mutablebits.to_bytes()

    def slice_to_uint(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return self.getslice(start, end)._mutablebits.u

    def slice_to_int(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return self.getslice(start, end)._mutablebits.i

    def slice_to_hex(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self.getslice(start, end)._mutablebits.hex

    def slice_to_bin(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self.getslice(start, end)._mutablebits.bin

    def slice_to_oct(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self.getslice(start, end)._mutablebits.oct

    def __iadd__(self, other: BitStore, /) -> BitStore:
        self._mutablebits += other._mutablebits
        return self

    def __add__(self, other: BitStore, /) -> BitStore:
        bs = self._copy()
        bs += other
        return bs

    def __eq__(self, other: Any, /) -> bool:
        return self._mutablebits == other._mutablebits

    def __and__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._mutablebits & other._mutablebits)

    def __or__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._mutablebits | other._mutablebits)

    def __xor__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._mutablebits ^ other._mutablebits)

    def __iand__(self, other: BitStore, /) -> BitStore:
        self._mutablebits &= other._mutablebits
        return self

    def __ior__(self, other: BitStore, /) -> BitStore:
        self._mutablebits |= other._mutablebits
        return self

    def __ixor__(self, other: BitStore, /) -> BitStore:
        self._mutablebits ^= other._mutablebits
        return self

    def find(self, bs: BitStore, start: int, end: int, bytealigned: bool = False) -> int:
        assert start >= 0
        if bytealigned:
            # We need to take the slice on a byte boundary for the find to work properly.
            byte_offset = start % 8
            if byte_offset != 0:
                start += (8 - byte_offset)
        x = self._mutablebits[start:end].find(bs._mutablebits, byte_aligned=bytealigned)
        if x is None:
            return -1
        else:
            return x + start


    def rfind(self, bs: BitStore, start: int, end: int, bytealigned: bool = False):
        assert start >= 0
        if bytealigned:
            byte_offset = start % 8
            if byte_offset != 0:
                start += (8 - byte_offset)
        x = self._mutablebits[start:end].rfind(bs._mutablebits, byte_aligned=bytealigned)
        if x is None:
            return -1
        else:
            return x + start


    def findall_msb0(self, bs: BitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        if bytealigned is True and len(bs) % 8 == 0:
            # Special case, looking for whole bytes on whole byte boundaries
            bytes_ = bs.tobytes()
            # Round up start byte to next byte, and round end byte down.
            # We're only looking for whole bytes, so can ignore bits at either end.
            start_byte = (start + 7) // 8
            end_byte = end // 8
            b = self._mutablebits[start_byte * 8: end_byte * 8].to_bytes()
            byte_pos = 0
            bytes_to_search = end_byte - start_byte
            while byte_pos < bytes_to_search:
                byte_pos = b.find(bytes_, byte_pos)
                if byte_pos == -1:
                    break
                yield (byte_pos + start_byte) * 8
                byte_pos = byte_pos + 1
            return
        # General case
        if bytealigned:
            byte_offset = start % 8
            if byte_offset != 0:
                start += (8 - byte_offset)
        i = self._mutablebits[start:end].to_bits().find_all(bs._mutablebits, byte_aligned=bytealigned)
        for p in i:
            yield p + start

    def rfindall_msb0(self, bs: BitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        assert start >= 0
        if bytealigned:
            byte_offset = start % 8
            if byte_offset != 0:
                start += (8 - byte_offset)
        i = self._mutablebits[start:end].to_bits().rfind_all(bs._mutablebits, byte_aligned=bytealigned)
        for p in i:
            yield p + start

    def count(self, value, /) -> int:
        return self._mutablebits.count(value)

    def clear(self) -> None:
        self._mutablebits.clear()

    def reverse(self) -> None:
        self._mutablebits.reverse()

    def __iter__(self) -> Iterable[bool]:
        for i in range(len(self)):
            yield self.getindex(i)

    def _copy(self) -> BitStore:
        """Always creates a copy, even if instance is immutable."""
        return BitStore(self._mutablebits.__copy__())

    def copy(self) -> BitStore:
        return self if self.immutable else self._copy()

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, BitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return bool(self._mutablebits.__getitem__(index))

    def getslice_withstep_msb0(self, key: slice, /) -> BitStore:
        if self.modified_length is not None:
            key = slice(*key.indices(self.modified_length))
        return BitStore(self._mutablebits.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> BitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return BitStore(self._mutablebits.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> BitStore:
        if self.modified_length is not None:
            key = slice(*slice(start, stop, None).indices(self.modified_length))
            start = key.start
            stop = key.stop
        return BitStore(self._mutablebits[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> BitStore:
        s = offset_slice_indices_lsb0(slice(start, stop, None), len(self))
        return BitStore(self._mutablebits[s.start:s.stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return bool(self._mutablebits.__getitem__(-index - 1))

    @overload
    def setitem_lsb0(self, key: int, value: int, /) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: BitStore, /) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, BitStore], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._mutablebits.__setitem__(new_slice, value._mutablebits)
        else:
            self._mutablebits.__setitem__(-key -1, bool(value))

    def delitem_lsb0(self, key: Union[int, slice], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._mutablebits.__delitem__(new_slice)
        else:
            self._mutablebits.__delitem__(-key - 1)

    def invert_msb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._mutablebits.invert(index)
        else:
            self._mutablebits.invert()

    def invert_lsb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._mutablebits.invert(-index - 1)
        else:
            self._mutablebits.invert()

    def any_set(self) -> bool:
        return self._mutablebits.any()

    def all_set(self) -> bool:
        return self._mutablebits.all()

    def __len__(self) -> int:
        return self.modified_length if self.modified_length is not None else len(self._mutablebits)

    def setitem_msb0(self, key, value, /):
        if isinstance(value, BitStore):
            self._mutablebits.__setitem__(key, value._mutablebits)
        else:
            if isinstance(key, slice):
                key = range(*key.indices(len(self)))
            self._mutablebits.set(value, key)

    def delitem_msb0(self, key, /):
        self._mutablebits.__delitem__(key)
