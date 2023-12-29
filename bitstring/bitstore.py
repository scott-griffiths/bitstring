from __future__ import annotations

import bitarray
from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload, Iterator, Any


def offset_slice_indices_lsb0(key: slice, length: int) -> slice:
    # First convert slice to all integers
    # Length already should take account of the offset
    start, stop, step = key.indices(length)
    new_start = length - stop
    new_stop = length - start
    # For negative step we sometimes get a negative stop, which can't be used correctly in a new slice
    return slice(new_start, None if new_stop < 0 else new_stop, step)

def offset_start_stop_lsb0(start: Optional[int], stop: Optional[int], length: int) -> slice:
    # First convert slice to all integers
    # Length already should take account of the offset
    start, stop, _ = slice(start, stop, None).indices(length)
    new_start = length - stop
    new_stop = length - start
    return new_start, new_stop

class BitStore:
    """A light wrapper around bitarray that does the LSB0 stuff"""

    __slots__ = ('_bitarray', 'modified', 'length', 'filename', 'immutable')

    def __init__(self, initializer: Union[int, bitarray.bitarray, str, None] = None, buffer=None, immutable: bool = False,
                 frombytes: Optional[Union[bytes, bytearray]] = None, filename: str = '', length: Optional[int] = None) -> None:
        if buffer is None:
            self._bitarray = bitarray.bitarray(initializer)
        else:
            self._bitarray = bitarray.bitarray(buffer=buffer)
        if frombytes is not None:
            self._bitarray = bitarray.bitarray()
            self._bitarray.frombytes(frombytes)
        self.immutable = immutable
        self.length = None
        self.filename = filename
        # Here 'modified' means that it isn't just the underlying bitarray. It could have a different start and end, and be from a file.
        # This also means that it shouldn't be changed further, so setting deleting etc. are disallowed.
        self.modified = length is not None or filename != ''
        if self.modified:
            assert immutable is True

            self.length = len(self._bitarray) if length is None else length

            if self.length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if self.length > len(self._bitarray):
                raise CreationError(
                    f"Can't create bitstring with a length of {self.length} from {len(self._bitarray)} bits of data.")

    def setall(self, value: int, /) -> None:
        self._bitarray.setall(value)

    def tobytes(self) -> bytes:
        return self._bitarray.tobytes()

    def slice_to_uint(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return bitarray.util.ba2int(self.getslice(start, end)._bitarray, signed=False)

    def slice_to_int(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return bitarray.util.ba2int(self.getslice(start, end)._bitarray, signed=True)

    def slice_to_hex(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return bitarray.util.ba2hex(self.getslice(start, end)._bitarray)

    def slice_to_bin(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self.getslice(start, end)._bitarray.to01()

    def slice_to_oct(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return bitarray.util.ba2base(8, self.getslice(start, end)._bitarray)

    def __iadd__(self, other: BitStore, /) -> BitStore:
        self._bitarray += other._bitarray
        return self

    def __add__(self, other: BitStore, /) -> BitStore:
        bs = self._copy()
        bs += other
        return bs

    def __eq__(self, other: Any, /) -> bool:
        return self._bitarray == other._bitarray

    def __and__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._bitarray & other._bitarray)

    def __or__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._bitarray | other._bitarray)

    def __xor__(self, other: BitStore, /) -> BitStore:
        return BitStore(self._bitarray ^ other._bitarray)

    def __iand__(self, other: BitStore, /) -> BitStore:
        self._bitarray &= other._bitarray
        return self

    def __ior__(self, other: BitStore, /) -> BitStore:
        self._bitarray |= other._bitarray
        return self

    def __ixor__(self, other: BitStore, /) -> BitStore:
        self._bitarray ^= other._bitarray
        return self

    def find(self, bs: BitStore, start: int, end: int, bytealigned: bool = False) -> int:
        if not bytealigned:
            return self._bitarray.find(bs._bitarray, start, end)
        try:
            return next(self.findall_msb0(bs, start, end, bytealigned))
        except StopIteration:
            return -1

    def rfind(self, bs: BitStore, start: int, end: int, bytealigned: bool = False):
        if not bytealigned:
            return self._bitarray.find(bs._bitarray, start, end, right=True)
        try:
            return next(self.rfindall_msb0(bs, start, end, bytealigned))
        except StopIteration:
            return -1

    def findall_msb0(self, bs: BitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        i = self._bitarray.itersearch(bs._bitarray, start, end)
        if not bytealigned:
            for p in i:
                yield p
        else:
            for p in i:
                if (p % 8) == 0:
                    yield p

    def rfindall_msb0(self, bs: BitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        i = self._bitarray.itersearch(bs._bitarray, start, end, right=True)
        if not bytealigned:
            for p in i:
                yield p
        else:
            for p in i:
                if (p % 8) == 0:
                    yield p

    def count(self, value, /) -> int:
        return self._bitarray.count(value)

    def clear(self) -> None:
        self._bitarray.clear()

    def reverse(self) -> None:
        self._bitarray.reverse()

    def __iter__(self) -> Iterable[bool]:
        for i in range(len(self)):
            yield self.getindex(i)

    def _copy(self) -> BitStore:
        """Always creates a copy, even if instance is immutable."""
        return BitStore(self._bitarray)

    def copy(self) -> BitStore:
        return self if self.immutable else self._copy()

    def __getitem__(self, item: Union[int, slice], /) -> Union[int, BitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int, /) -> bool:
        return bool(self._bitarray.__getitem__(index))

    def getslice_withstep_msb0(self, key: slice, /) -> BitStore:
        if self.modified:
            key = slice(*key.indices(len(self)))
        return BitStore(self._bitarray.__getitem__(key))

    def getslice_withstep_lsb0(self, key: slice, /) -> BitStore:
        key = offset_slice_indices_lsb0(key, len(self))
        return BitStore(self._bitarray.__getitem__(key))

    def getslice_msb0(self, start: Optional[int], stop: Optional[int], /) -> BitStore:
        if self.modified:
            key = slice(*slice(start, stop, None).indices(len(self)))
            start = key.start
            stop = key.stop
        return BitStore(self._bitarray[start:stop])

    def getslice_lsb0(self, start: Optional[int], stop: Optional[int], /) -> BitStore:
        start, stop = offset_start_stop_lsb0(start, stop, len(self))
        return BitStore(self._bitarray[start:stop])

    def getindex_lsb0(self, index: int, /) -> bool:
        return bool(self._bitarray.__getitem__(-index - 1))


    @overload
    def setitem_lsb0(self, key: int, value: int, /) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: BitStore, /) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, BitStore], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._bitarray.__setitem__(new_slice, value._bitarray)
        else:
            self._bitarray.__setitem__(-key - 1, value)

    def delitem_lsb0(self, key: Union[int, slice], /) -> None:
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self))
            self._bitarray.__delitem__(new_slice)
        else:
            self._bitarray.__delitem__(-key - 1)

    def invert_msb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._bitarray.invert(index)
        else:
            self._bitarray.invert()

    def invert_lsb0(self, index: Optional[int] = None, /) -> None:
        if index is not None:
            self._bitarray.invert(-index - 1)
        else:
            self._bitarray.invert()

    def any_set(self) -> bool:
        return self._bitarray.any()

    def all_set(self) -> bool:
        return self._bitarray.all()

    def __len__(self) -> int:
        return self.length if self.length is not None else len(self._bitarray)

    def setitem_msb0(self, key, value, /):
        if isinstance(value, BitStore):
            self._bitarray.__setitem__(key, value._bitarray)
        else:
            self._bitarray.__setitem__(key, value)

    def delitem_msb0(self, key, /):
        self._bitarray.__delitem__(key)