from __future__ import annotations

import bitarray
from bitstring.exceptions import CreationError
from typing import Union, Iterable, Optional, overload


def offset_slice_indices_lsb0(key: slice, length: int, offset: int) -> slice:
    # First convert slice to all integers
    # Length already should take account of the offset
    start, stop, step = key.indices(length)
    new_start = length - stop - offset
    new_stop = length - start - offset
    # For negative step we sometimes get a negative stop, which can't be used correctly in a new slice
    return slice(new_start, None if new_stop < 0 else new_stop, step)


def offset_slice_indices_msb0(key: slice, length: int, offset: int) -> slice:
    # First convert slice to all integers
    # Length already should take account of the offset
    start, stop, step = key.indices(length)
    start += offset
    stop += offset
    # For negative step we sometimes get a negative stop, which can't be used correctly in a new slice
    return slice(start, None if stop < 0 else stop, step)


class BitStore:
    """A light wrapper around bitarray that does the LSB0 stuff"""

    __slots__ = ('_bitarray', 'modified', 'length', 'offset', 'filename', 'immutable')

    def __init__(self, initializer: Union[int, str, Iterable, None] = None, buffer = None, immutable: bool = False, frombytes: Optional[Union[bytes, bytearray]] = None,
                 offset: int = 0, filename: str = '', length: Optional[int] = None) -> None:
        if buffer is None:
            self._bitarray = bitarray.bitarray(initializer)
        else:
            self._bitarray = bitarray.bitarray(buffer=buffer)
        if frombytes is not None:
            self._bitarray = bitarray.bitarray()
            self._bitarray.frombytes(frombytes)
        self.immutable = immutable
        self.offset = offset

        self.offset = 0  # TODO: Can we remove the offset altogether?
        self.length = None
        self.filename = filename
        # Here 'modified' means that it isn't just the underlying bitarray. It could have a different start and end, and be from a file.
        # This also means that it shouldn't be changed further, so setting deleting etc. are disallowed.
        self.modified = offset != 0 or length is not None or filename != ''
        if self.modified:
            assert immutable is True
            # These class variable only exist if modified is True.

            self.length = self._bitarray.__len__() - self.offset if length is None else length

            if self.length < 0:
                raise CreationError("Can't create bitstring with a negative length.")
            if self.length + self.offset > self._bitarray.__len__():
                self.length = self._bitarray.__len__() - self.offset
                raise CreationError(
                    f"Can't create bitstring with a length of {self.length} and an offset of {self.offset} from {self._bitarray.__len__()} bits of data.")

    # def __new__(cls, *args, **kwargs) -> bitarray.bitarray:
    #     # Just pass on the buffer keyword, not the length, offset, filename and frombytes
    #     new_kwargs = {'buffer': kwargs.get('buffer', None)}
    #     return bitarray.bitarray.__new__(cls, *args, **new_kwargs)

    @classmethod
    def _create_empty_instance(cls):
        return bitarray.bitarray()

    def setall(self, /, value: int) -> None:
        self._bitarray.setall(value)

    def tobytes(self) -> bytes:
        return self._bitarray.tobytes()

    def slice_to_uint(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return bitarray.util.ba2int(self.getslice(slice(start, end, None))._bitarray, signed=False)

    def slice_to_int(self, start: Optional[int] = None, end: Optional[int] = None) -> int:
        return bitarray.util.ba2int(self.getslice(slice(start, end, None))._bitarray, signed=True)

    def slice_to_hex(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return bitarray.util.ba2hex(self.getslice(slice(start, end, None))._bitarray)

    def slice_to_bin(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return self.getslice(slice(start, end, None))._bitarray.to01()

    def slice_to_oct(self, start: Optional[int] = None, end: Optional[int] = None) -> str:
        return bitarray.util.ba2base(8, self.getslice(slice(start, end, None))._bitarray)

    def __iadd__(self, other: BitStore) -> BitStore:
        # assert not self.immutable
        self._bitarray += other._bitarray
        return self

    def __add__(self, other: BitStore) -> BitStore:
        bs = self._copy()
        bs += other
        return bs

    def __eq__(self, other: Any) -> bool:
        return self._bitarray == other._bitarray

    def __and__(self, other: BitStore) -> BitStore:
        return BitStore(self._bitarray & other._bitarray)

    def __or__(self, other: BitStore) -> BitStore:
        return BitStore(self._bitarray | other._bitarray)

    def __xor__(self, other: BitStore) -> BitStore:
        return BitStore(self._bitarray ^ other._bitarray)

    # TODO: iand, ior, ixor ?

    def find(self, /, bs, start, stop) -> int:
        return self._bitarray.find(bs._bitarray, start, stop)

    def itersearch(self, bs) -> Iterator[int]:
        return self._bitarray.itersearch(bs._bitarray)

    def count(self, value) -> int:
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
        return self.getslice(slice(None, self.length, None))

    def copy(self) -> BitStore:
        if self.immutable:
            return self
        x = BitStore(self._bitarray)
        return x

    def __getitem__(self, item: Union[int, slice]) -> Union[int, BitStore]:
        # Use getindex or getslice instead
        raise NotImplementedError

    def getindex_msb0(self, index: int) -> bool:
        if self.modified and index >= 0:
            index += self.offset
        return bool(self._bitarray.__getitem__(index))

    def getslice_msb0(self, key: slice) -> BitStore:
        if self.modified:
            key = offset_slice_indices_msb0(key, len(self), self.offset)
        return BitStore(self._bitarray.__getitem__(key))

    def getindex_lsb0(self, index: int) -> bool:
        if self.modified and index >= 0:
            index += self.offset
        return bool(self._bitarray.__getitem__(-index - 1))

    def getslice_lsb0(self, key: slice) -> BitStore:
        if self.modified:
            key = offset_slice_indices_lsb0(key, len(self), self.offset)
        else:
            key = offset_slice_indices_lsb0(key, len(self), 0)
        return BitStore(self._bitarray.__getitem__(key))

    @overload
    def setitem_lsb0(self, key: int, value: int) -> None:
        ...

    @overload
    def setitem_lsb0(self, key: slice, value: BitStore) -> None:
        ...

    def setitem_lsb0(self, key: Union[int, slice], value: Union[int, BitStore]) -> None:
        assert not self.immutable
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self), 0)
            if isinstance(value, BitStore):
                self._bitarray.__setitem__(new_slice, value._bitarray)
            else:
                self._bitarray.__setitem__(new_slice, value)
        else:
            self._bitarray.__setitem__(-key - 1, value)

    def delitem_lsb0(self, key: Union[int, slice]) -> None:
        assert not self.immutable
        if isinstance(key, slice):
            new_slice = offset_slice_indices_lsb0(key, len(self), 0)
            self._bitarray.__delitem__(new_slice)
        else:
            self._bitarray.__delitem__(-key - 1)

    def invert_msb0(self, index: Optional[int] = None) -> None:
        assert not self.immutable
        if index is not None:
            self._bitarray.invert(index)
        else:
            self._bitarray.invert()

    def invert_lsb0(self, index: Optional[int] = None) -> None:
        assert not self.immutable
        if index is not None:
            self._bitarray.invert(-index - 1)
        else:
            self._bitarray.invert()

    def any_set(self) -> bool:
        if self.modified:
            return self._bitarray.__getitem__(slice(self.offset, self.offset + self.length, None)).any()
        else:
            return self._bitarray.any()

    def all_set(self) -> bool:
        if self.modified:
            return self._bitarray.__getitem__(slice(self.offset, self.offset + self.length, None)).all()
        else:
            return self._bitarray.all()

    def __len__(self) -> int:
        if self.modified:
            return self.length
        return len(self._bitarray)

    def setitem_msb0(self, key, value):
        if isinstance(value, BitStore):
            self._bitarray.__setitem__(key, value._bitarray)
        else:
            self._bitarray.__setitem__(key, value)

    def delitem_msb0(self, key):
        self._bitarray.__delitem__(key)

    # Default to the MSB0 methods (mainly to stop mypy from complaining)
    getslice = getslice_msb0
    getindex = getindex_msb0
    # __setitem__ = bitarray.bitarray.__setitem__
    __delitem__ = bitarray.bitarray.__delitem__

