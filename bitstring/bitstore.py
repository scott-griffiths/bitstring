from __future__ import annotations

import functools

from tibs import Tibs, Mutibs, ByteOrder, DtypeKind, DtypeSingle, DtypeTuple

from bitstring.exceptions import CreationError
from typing import Any, TypeVar
from collections.abc import Iterable, Iterator


# The bitstring dtypes that have an exactly equivalent tibs dtype, letting values be
# packed and unpacked in bulk instead of one at a time. Every entry here has been
# checked to round-trip identically to bitstring's own per-element code at each of its
# valid lengths. Names that are absent - the mxfp and binary8 formats, bfloat, mxint,
# bits, pad - have no tibs equivalent and keep using the per-element path, as do any
# dtype with a scale factor. More kinds can simply be added here as tibs grows them.
_TIBS_EQUIVALENT_DTYPES: dict[str, tuple[DtypeKind, ByteOrder]] = {
    'u': (DtypeKind.Uint, ByteOrder.Unspecified),
    'uint': (DtypeKind.Uint, ByteOrder.Unspecified),
    'ube': (DtypeKind.Uint, ByteOrder.Big),
    'uintbe': (DtypeKind.Uint, ByteOrder.Big),
    'ule': (DtypeKind.Uint, ByteOrder.Little),
    'uintle': (DtypeKind.Uint, ByteOrder.Little),
    'i': (DtypeKind.Int, ByteOrder.Unspecified),
    'int': (DtypeKind.Int, ByteOrder.Unspecified),
    'ibe': (DtypeKind.Int, ByteOrder.Big),
    'intbe': (DtypeKind.Int, ByteOrder.Big),
    'ile': (DtypeKind.Int, ByteOrder.Little),
    'intle': (DtypeKind.Int, ByteOrder.Little),
    'f': (DtypeKind.Float, ByteOrder.Big),
    'fbe': (DtypeKind.Float, ByteOrder.Big),
    'float': (DtypeKind.Float, ByteOrder.Big),
    'floatbe': (DtypeKind.Float, ByteOrder.Big),
    'fle': (DtypeKind.Float, ByteOrder.Little),
    'floatle': (DtypeKind.Float, ByteOrder.Little),
    'bool': (DtypeKind.Bool, ByteOrder.Unspecified),
    'bin': (DtypeKind.Bin, ByteOrder.Unspecified),
    'hex': (DtypeKind.Hex, ByteOrder.Unspecified),
    'oct': (DtypeKind.Oct, ByteOrder.Unspecified),
    'bytes': (DtypeKind.Bytes, ByteOrder.Unspecified),
}


@functools.lru_cache(256)
def tibs_dtype_for(name: str, bitlength: int | None) -> DtypeSingle | None:
    """Return the tibs dtype equivalent to a bitstring dtype, or None if there isn't one.

    bitlength is in bits, which is what tibs dtypes use for every kind - including
    'bytes', where bitstring's own length is a byte count.
    """
    if bitlength is None:
        return None
    try:
        kind, byte_order = _TIBS_EQUIVALENT_DTYPES[name]
    except KeyError:
        return None
    try:
        return DtypeSingle.from_params(kind, bitlength, byte_order)
    except ValueError:
        # A length this kind doesn't allow. The per-element path will handle it.
        return None


@functools.lru_cache(256)
def tibs_dtype_tuple_for(specs: tuple[tuple[str, int | None], ...]) -> DtypeTuple | None:
    """Return a tibs dtype covering a whole list of bitstring dtypes, or None.

    None if any of them has no tibs equivalent, which leaves the caller reading or
    packing one dtype at a time. specs are (bitstring dtype name, bitlength) pairs.
    """
    dtypes = []
    for name, bitlength in specs:
        dtype = tibs_dtype_for(name, bitlength)
        if dtype is None:
            return None
        dtypes.append(dtype)
    try:
        return DtypeTuple.from_params(dtypes)
    except ValueError:
        return None


def _normalise_byte_import_args(offset: int | None, length: int | None) -> tuple[int | None, int | None]:
    if length is None and isinstance(offset, int) and offset == 0:
        offset = None
    return offset, length


def _validated_buffer(buffer, offset: int | None, length: int | None) -> memoryview:
    """Validate offset and length in bits against a buffer, returning it as a memoryview."""
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
    return mv


_Self = TypeVar('_Self', bound='_BitStoreBase')


class _BitStoreBase:
    """Shared pass-through behaviour for ConstBitStore and MutableBitStore.

    The classmethod constructors (join, from_zeros, from_bytes, etc.) are NOT here:
    each needs to call Tibs.from_x or Mutibs.from_x, and doing that via an extra
    lookup method would add a call on a hot path just to avoid a few lines of
    duplication. They're defined directly on each subclass instead.
    """

    __slots__ = ('tibs',)

    def __init__(self, initializer: Tibs | Mutibs) -> None:
        self.tibs = initializer

    def __getstate__(self) -> bytes:
        # The tibs types can't be pickled directly, so use their own encoded form.
        return self.tibs.encode()

    @classmethod
    def from_buffer(cls: type[_Self], buffer, /, offset: int | None, length: int | None) -> _Self:
        mv = _validated_buffer(buffer, offset, length)
        return cls.from_bytes(mv, offset=offset or 0, length=length)

    def to_bytes(self) -> bytes:
        return self.tibs.to_padded_bytes()

    def to_bools(self) -> list[bool]:
        return self.tibs.to_bools()

    def read_bytes(self, start: int, length: int) -> bytes:
        return self.tibs.to_bytes(start, start + length)

    def byte_swapped(self: _Self, start: int | None = None, end: int | None = None) -> _Self:
        return type(self)(self.tibs.byte_swapped(start=start, end=end))

    def to_u(self) -> int:
        return self.tibs.to_u()

    def read_u(self, start: int, length: int) -> int:
        return self.tibs.to_u(start, start + length)

    def to_i(self) -> int:
        return self.tibs.to_i()

    def read_i(self, start: int, length: int) -> int:
        return self.tibs.to_i(start, start + length)

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

    def __add__(self: _Self, other: _BitStoreBase, /) -> _Self:
        return type(self)(self.tibs + other.tibs)

    def __eq__(self, other: Any, /) -> bool:
        if not isinstance(other, _BitStoreBase):
            return NotImplemented
        return self.tibs == other.tibs

    def __and__(self: _Self, other: _BitStoreBase, /) -> _Self:
        return type(self)(self.tibs & other.tibs)

    def __or__(self: _Self, other: _BitStoreBase, /) -> _Self:
        return type(self)(self.tibs | other.tibs)

    def __xor__(self: _Self, other: _BitStoreBase, /) -> _Self:
        return type(self)(self.tibs ^ other.tibs)

    def __invert__(self: _Self) -> _Self:
        return type(self)(~self.tibs)

    def __lshift__(self: _Self, n: int, /) -> _Self:
        return type(self)(self.tibs << n)

    def __rshift__(self: _Self, n: int, /) -> _Self:
        return type(self)(self.tibs >> n)

    def find(self, bs: _BitStoreBase, start: int, end: int, bytealigned: bool = False) -> int | None:
        return self.tibs.find(bs.tibs, start, end, byte_aligned=bytealigned)

    def rfind(self, bs: _BitStoreBase, start: int, end: int, bytealigned: bool = False) -> int | None:
        return self.tibs.rfind(bs.tibs, start, end, byte_aligned=bytealigned)

    def __imul__(self: _Self, n: int, /) -> _Self:
        self.tibs *= n
        return self

    def getindex(self, index: int, /) -> bool:
        return self.tibs[index]

    def getslice_withstep(self: _Self, key: slice, /) -> _Self:
        return type(self)(self.tibs[key])

    def getslice(self: _Self, start: int | None, stop: int | None, /) -> _Self:
        return type(self)(self.tibs[start:stop])

    def any(self) -> bool:
        return self.tibs.any()

    def all(self) -> bool:
        return self.tibs.all()

    def startswith(self, prefix: _BitStoreBase) -> bool:
        return self.tibs.starts_with(prefix.tibs)

    def endswith(self, suffix: _BitStoreBase) -> bool:
        return self.tibs.ends_with(suffix.tibs)

    def count(self, value: Any) -> int:
        return self.tibs.count(value)

    def to_values(self, dtype: DtypeSingle, end: int) -> list[Any]:
        """Unpack the bits up to end as a list of dtype values.

        end must be a multiple of the dtype's length - tibs won't unpack a partial
        final item the way bitstring's Array tolerates trailing bits.
        """
        return dtype.unpack_values(self.tibs, 0, end)

    def to_values_iter(self, dtype: DtypeSingle, end: int) -> Iterator[Any]:
        """As to_values, but yields the values rather than building a list."""
        return dtype.unpack_values_iter(self.tibs, 0, end)

    def to_value(self, dtype: DtypeSingle, start: int, end: int) -> Any:
        """Unpack a single dtype value from the given bit range."""
        return dtype.unpack(self.tibs, start, end)

    def to_value_tuple(self, dtype: DtypeTuple, start: int, end: int) -> tuple[Any, ...]:
        """Unpack a whole list of dtypes from the given bit range in one call."""
        return dtype.unpack(self.tibs, start, end)

    def __len__(self) -> int:
        return len(self.tibs)


class ConstBitStore(_BitStoreBase):
    """A light wrapper around tibs.Tibs"""

    __slots__ = ()

    def __setstate__(self, state: bytes) -> None:
        self.tibs = Tibs.decode(state)

    @classmethod
    def join(cls, bitstores: Iterable[ConstBitStore], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_joined(b.tibs for b in bitstores)
        return x

    @classmethod
    def from_zeros(cls, i: int) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_zeros(i)
        return x

    @classmethod
    def from_ones(cls, i: int) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_ones(i)
        return x

    @classmethod
    def from_bytes(cls, b: bytes | bytearray | memoryview, /, offset: int | None = None,
                   length: int | None = None) -> ConstBitStore:
        x = super().__new__(cls)
        offset, length = _normalise_byte_import_args(offset, length)
        x.tibs = Tibs.from_bytes(b, offset=offset, length=length)
        return x

    @classmethod
    def from_bools(cls, iterable: Iterable[Any], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bools(iterable)
        return x

    @classmethod
    def from_bin(cls, s: str) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_bin(s)
        return x

    @classmethod
    def from_values(cls, dtype: DtypeSingle, values: Iterable[Any], /) -> ConstBitStore:
        x = super().__new__(cls)
        x.tibs = Tibs.from_values(dtype, values)
        return x

    @classmethod
    def from_value(cls, dtype: DtypeSingle | DtypeTuple, value: Any, /) -> ConstBitStore:
        """Pack a single value - or, for a DtypeTuple, a whole sequence of them."""
        x = super().__new__(cls)
        x.tibs = dtype.pack(value)
        return x

    def findall(self, bs: ConstBitStore | MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        return self.tibs.find_all_iter(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def __iter__(self) -> Iterable[bool]:
        return self.tibs.__iter__()

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        return MutableBitStore(self.tibs.to_mutibs())

    def copy(self) -> ConstBitStore:
        return self

    def _fresh_copy(self) -> ConstBitStore:
        """Return a new instance, sharing the immutable data."""
        return ConstBitStore(self.tibs)

    def to_const(self) -> ConstBitStore:
        return self

    @classmethod
    def from_tibs(cls, t: Tibs | Mutibs, /) -> ConstBitStore:
        if isinstance(t, Mutibs):
            return cls(t.to_tibs())
        if not isinstance(t, Tibs):
            raise TypeError(f"Expected tibs.Tibs or tibs.Mutibs, got {type(t).__name__}.")
        return cls(t)

    def to_tibs(self) -> Tibs:
        return self.tibs

    def chunks(self, bits: int, count: int | None = None) -> Iterator[ConstBitStore]:
        for chunk in self.tibs.chunks_iter(bits, count):
            yield ConstBitStore(chunk)


class MutableBitStore(_BitStoreBase):
    """A light wrapper around tibs.Mutibs"""

    __slots__ = ()

    def __setstate__(self, state: bytes) -> None:
        self.tibs = Mutibs.decode(state)

    @classmethod
    def join(cls, bitstores: Iterable[MutableBitStore], /) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_joined(b.tibs for b in bitstores)
        return x

    @classmethod
    def from_zeros(cls, i: int) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_zeros(i)
        return x

    @classmethod
    def from_ones(cls, i: int) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_ones(i)
        return x

    @classmethod
    def from_bytes(cls, b: bytes | bytearray | memoryview, /, offset: int | None = None,
                   length: int | None = None) -> MutableBitStore:
        x = super().__new__(cls)
        offset, length = _normalise_byte_import_args(offset, length)
        x.tibs = Mutibs.from_bytes(b, offset=offset, length=length)
        return x

    @classmethod
    def from_bools(cls, iterable: Iterable[Any], /) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_bools(iterable)
        return x

    @classmethod
    def from_values(cls, dtype: DtypeSingle, values: Iterable[Any], /) -> MutableBitStore:
        x = super().__new__(cls)
        x.tibs = Mutibs.from_values(dtype, values)
        return x

    def __ilshift__(self, n: int, /) -> MutableBitStore:
        self.tibs <<= n
        return self

    def __irshift__(self, n: int, /) -> MutableBitStore:
        self.tibs >>= n
        return self

    def __iadd__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs += other.tibs
        return self

    def __iand__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs &= other.tibs
        return self

    def __ior__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs |= other.tibs
        return self

    def __ixor__(self, other: MutableBitStore | ConstBitStore, /) -> MutableBitStore:
        self.tibs ^= other.tibs
        return self

    def findall(self, bs: ConstBitStore | MutableBitStore, start: int, end: int, bytealigned: bool = False) -> Iterator[int]:
        # Mutibs has no find_all_iter, so search an immutable snapshot. This copies the
        # data, but also makes the iteration safe if the bitstring is mutated during it.
        return self.tibs.to_tibs().find_all_iter(bs.tibs, start=start, end=end, byte_aligned=bytealigned)

    def clear(self) -> None:
        self.tibs.clear()

    def reverse(self) -> None:
        self.tibs.reverse()

    def byte_swap(self, start: int | None, end: int | None) -> None:
        self.tibs.byte_swap(start=start, end=end)

    def __iter__(self) -> Iterable[bool]:
        # Mutibs deliberately doesn't support iteration, so index bit-by-bit.
        # This is lazy and so reflects any mutations made while iterating.
        for i in range(len(self)):
            yield self.getindex(i)

    def extend_left(self, other: MutableBitStore | ConstBitStore, /) -> None:
        self.tibs.extend_left(other.tibs)

    def _mutable_copy(self) -> MutableBitStore:
        """Always creates a copy, even if instance is immutable."""
        return MutableBitStore(self.tibs.__copy__())

    def copy(self) -> MutableBitStore:
        return self._mutable_copy()

    def _fresh_copy(self) -> MutableBitStore:
        """Return a new instance with a copy of the data."""
        return self._mutable_copy()

    def to_const(self) -> ConstBitStore:
        """Return an immutable snapshot of the data."""
        return ConstBitStore(self.tibs.to_tibs())

    @classmethod
    def from_tibs(cls, t: Tibs | Mutibs, /) -> MutableBitStore:
        if isinstance(t, Tibs):
            return cls(t.to_mutibs())
        if not isinstance(t, Mutibs):
            raise TypeError(f"Expected tibs.Tibs or tibs.Mutibs, got {type(t).__name__}.")
        return cls(t.to_tibs().to_mutibs())

    def to_tibs(self) -> Tibs:
        return self.tibs.to_tibs()

    def invert(self, index: int | None = None, /) -> None:
        if index is not None:
            self.tibs.invert(index)
        else:
            self.tibs.invert()

    def set(self, value: Any, pos: Any, /) -> None:
        if value:
            self.tibs.set(pos)
        else:
            self.tibs.unset(pos)

    def replace(self, old: MutableBitStore | ConstBitStore, new: MutableBitStore | ConstBitStore,
                start: int | None = None, end: int | None = None,
                count: int | None = None, bytealigned: bool = False) -> int:
        return self.tibs.replace(old.tibs, new.tibs, start=start, end=end, count=count,
                                 byte_aligned=bytealigned)

    def rotate_left(self, n: int, start: int | None = None, end: int | None = None) -> None:
        self.tibs.rotate_left(n, start=start, end=end)

    def rotate_right(self, n: int, start: int | None = None, end: int | None = None) -> None:
        self.tibs.rotate_right(n, start=start, end=end)

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
