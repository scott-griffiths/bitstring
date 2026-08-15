from __future__ import annotations

import math
import numbers
from collections.abc import Sized
from typing import Any, BinaryIO, overload, TextIO
from collections.abc import Iterable
from bitstring.bits import Bits, BitsType
from bitstring.bitarray_ import BitArray
from bitstring.dtypes import Dtype, dtype_register
import bitstring.bitstore as bitstore
from bitstring import utils
from bitstring.colour import Colour, should_use_color
import copy
import array
import pathlib
import operator
import io
import sys
import bitstring

# The possible types stored in each element of the Array
ElementType = float | str | int | bytes | bool | Bits

# Longer Arrays have their repr truncated, with this many elements shown in total,
# half from each end. Bits does the equivalent with MAX_CHARS.
MAX_ITEMS: int = 100

MutableBitStore = bitstring.bitstore.MutableBitStore


def _array_typecode_to_dtype(typecode: str) -> Dtype | None:
    endian = '<' if sys.byteorder == 'little' else '>'
    name_value = utils.parse_single_struct_token(endian + typecode)
    if name_value is None:
        return None
    return dtype_register.get_dtype(*name_value)


class Array:
    """Return an Array whose elements are initialised according to the dtype string.
    The dtype string can be a typecode as used in the struct module or any fixed-length bitstring
    format.

    a = Array('>H', [1, 15, 105])
    b = Array('i5', [-9, 0, 4])

    The Array data is stored compactly as a BitArray object and the Array behaves very like
    a list of items of the given format. Both the Array data and dtype properties can be freely
    modified after creation. If the data length is not a multiple of the dtype length then the
    Array will have 'trailing_bits' which will prevent some methods from appending to the
    Array.

    Methods:

    append() -- Append a single item to the end of the Array.
    byteswap() -- Change byte endianness of all items.
    count() -- Count the number of occurences of a value.
    extend() -- Append new items to the end of the Array from an iterable.
    from_bytes() -- Create a new Array with binary data from a bytes-like object.
    from_file() -- Create a new Array with items read from a file path or binary file object.
    from_zeros() -- Create a new Array containing zeroed items.
    insert() -- Insert an item at a given position.
    pop() -- Remove and return an item.
    pp() -- Pretty print the Array.
    reverse() -- Reverse the order of all items.
    to_bytes() -- Return Array data as bytes object, padding with zero bits at the end if needed.
    to_file() -- Write Array data to a file, padding with zero bits at the end if needed.
    to_list() -- Return Array items as a list.

    Special methods:

    Also available are the operators [], ==, !=, +, *, <<, >>, &, |, ^,
    plus the mutating operators [], +=, *=, <<=, >>=, &=, |=, ^=.

    Properties:

    data -- The BitArray binary data of the Array. Can be modified in place, and can be
            set to another BitArray.
    dtype -- The format string or typecode. Can be freely modified.
    itemsize -- The length *in bits* of a single item. Read only.
    trailing_bits -- If the data length is not a multiple of the dtype length, this BitArray
                     gives the leftovers at the end of the data.


    """

    __slots__ = ('_dtype', '_tibs_dtype', '_data')

    def __init__(self, dtype: str | Dtype, initializer: Array | array.array | Iterable | None = None,
                 trailing_bits: BitsType | None = None) -> None:
        self._data = BitArray()
        if initializer is not None:
            # These reject initialiser forms that were removed in 5.0, and two of them are
            # abc instance checks. Constructing an empty Array to fill in later is very
            # common - every elementwise operator does it - so skip them in that case.
            self._reject_removed_initializer(initializer)
        try:
            self._set_dtype(dtype)
        except ValueError as e:
            raise ValueError(e)

        if initializer is not None:
            self.extend(initializer)

        if trailing_bits is not None:
            self._data += BitArray._create_from_bitstype(trailing_bits)

    @staticmethod
    def _reject_removed_initializer(initializer: Any, /) -> None:
        """Raise TypeError for Array initialiser forms that were removed in 5.0."""
        if isinstance(initializer, numbers.Integral):
            raise TypeError(
                f"It's no longer possible to create an Array from an item count. "
                f"Use 'Array.from_zeros(dtype, {int(initializer)})' to create an Array of zeroed items."
            )
        if isinstance(initializer, (Bits, bytes, bytearray, memoryview)):
            raise TypeError(
                "It's no longer possible to initialise an Array directly from binary data, as it is "
                "ambiguous with an iterable of values. Use 'Array.from_bytes(dtype, data)' instead."
            )
        if isinstance(initializer, io.IOBase):
            raise TypeError(
                "It's no longer possible to initialise an Array directly from a file object. "
                "Use 'Array.from_file(dtype, f)' instead."
            )

    @classmethod
    def from_zeros(cls, dtype: str | Dtype, n: int, /) -> Array:
        """Create a new Array containing n zeroed items."""
        n = int(n)
        if n < 0:
            raise ValueError(f"Can't create an Array of negative length {n}.")
        x = cls(dtype)
        x._data = BitArray.from_zeros(n * x.itemsize)
        return x

    @classmethod
    def from_bytes(cls, dtype: str | Dtype, data: bytes | bytearray | memoryview, /) -> Array:
        """Create a new Array with its binary data taken from a bytes-like object."""
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f"Array.from_bytes() needs a bytes-like object, but received a {type(data).__name__}.")
        x = cls(dtype)
        x._data += data
        return x

    @property
    def data(self) -> BitArray:
        """The binary data of the Array as a mutable BitArray.

        This is the Array's own buffer, not a copy, so modifying it in place changes the
        Array. Assigning to it requires a BitArray - the Array needs its data to be
        mutable, and anything else would leave it in a state its own methods can't work
        with.
        """
        return self._data

    @data.setter
    def data(self, value: BitArray) -> None:
        if not isinstance(value, BitArray):
            hint = (" Use BitArray(...) to convert it first." if isinstance(value, (Bits, str, bytes, bytearray, memoryview))
                    else "")
            raise TypeError(f"Array.data must be set to a BitArray, but received a "
                            f"{type(value).__name__}.{hint}")
        self._data = value

    @property
    def itemsize(self) -> int:
        bitlength = self._dtype.bitlength
        if bitlength is None:
            raise ValueError("A fixed length format is needed for an Array.")
        return bitlength

    @property
    def trailing_bits(self) -> BitArray:
        trailing_bit_length = len(self._data) % self._dtype.bitlength
        return BitArray() if trailing_bit_length == 0 else self._data[-trailing_bit_length:]

    @property
    def dtype(self) -> Dtype:
        return self._dtype

    @dtype.setter
    def dtype(self, new_dtype: str | Dtype) -> None:
        self._set_dtype(new_dtype)

    def _set_tibs_dtype(self) -> None:
        """Cache the tibs dtype matching self._dtype, for bulk packing and unpacking.

        None whenever there isn't an exact equivalent, which leaves every operation on
        the per-element path.
        """
        self._tibs_dtype = bitstore.tibs_dtype_for(self._dtype._name, self._dtype._bitlength)

    def _set_dtype(self, new_dtype: str | Dtype) -> None:
        if isinstance(new_dtype, Dtype):
            self._dtype = new_dtype
        else:
            if not isinstance(new_dtype, str):
                raise TypeError(f"An Array dtype must be a str or a Dtype, not a {type(new_dtype).__name__}.")
            try:
                # Dtype accepts compact struct codes such as '>H' as well as names.
                dtype = Dtype(new_dtype)
            except ValueError as e:
                if str(e) == utils.NATIVE_ENDIAN_STRUCT_ERROR:
                    raise  # Says exactly what's wrong, so don't replace it.
                raise ValueError(f"Inappropriate Dtype for Array: '{new_dtype}'.") from None
            if dtype.length is None:
                raise ValueError(f"A fixed length format is needed for an Array, received '{new_dtype}'.")
            self._dtype = dtype
        self._set_tibs_dtype()

    def _create_element(self, value: ElementType) -> Bits:
        """Create Bits from value according to the token_name and token_length"""
        b = self._dtype.pack(value)
        if len(b) != self.itemsize:
            raise ValueError(f"The value {value!r} has the wrong length for the format '{self._dtype}'.")
        return b

    def __len__(self) -> int:
        return len(self._data) // self.itemsize

    @overload
    def __getitem__(self, key: slice) -> Array:
        ...

    @overload
    def __getitem__(self, key: int) -> ElementType:
        ...

    def __getitem__(self, key: slice | int) -> Array | ElementType:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step != 1:
                d = BitArray()
                itemsize = self.itemsize
                for s in range(start * itemsize, stop * itemsize, step * itemsize):
                    d.append(self._data[s: s + itemsize])
                a = self.__class__(self._dtype)
                a._data = d
                return a
            else:
                itemsize = self.itemsize
                # Skip __init__: the dtype fields are just copied and the data is the slice.
                a = object.__new__(self.__class__)
                a._dtype = self._dtype
                a._tibs_dtype = self._tibs_dtype
                a._data = self._data[start * itemsize: stop * itemsize]
                return a
        else:
            itemsize = self._dtype._bitlength  # Always set for an Array; the property costs a call.
            length = len(self._data) // itemsize
            if key < 0:
                key += length
            if key < 0 or key >= length:
                raise IndexError(f"Index {key} out of range for Array of length {length}.")
            start = itemsize * key
            if self._tibs_dtype is not None:
                return self._data._bitstore.to_value(self._tibs_dtype, start, start + itemsize)
            return self._dtype._read_fn(self._data, start=start)

    @overload
    def __setitem__(self, key: slice, value: Iterable[ElementType]) -> None:
        ...

    @overload
    def __setitem__(self, key: int, value: ElementType) -> None:
        ...

    def __setitem__(self, key: slice | int, value: Iterable[ElementType] | ElementType) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if not isinstance(value, Iterable):
                raise TypeError("Can only assign an iterable to a slice.")
            if step == 1:
                itemsize = self.itemsize
                if self._tibs_dtype is not None and isinstance(value, (list, tuple, range)):
                    # Bulk pack, far quicker than an item at a time. Only for types that
                    # can be iterated twice, as a failure falls back to the loop below
                    # so that a bad value raises exactly the error it always did.
                    try:
                        packed = bitstore.MutableBitStore.from_values(self._tibs_dtype, value)
                    except Exception:
                        pass
                    else:
                        self._data._bitstore[start * itemsize: stop * itemsize] = packed
                        return
                new_data = BitArray()
                for x in value:
                    new_data += self._create_element(x)
                self._data[start * itemsize: stop * itemsize] = new_data
                return
            items_in_slice = len(range(start, stop, step))
            if not isinstance(value, Sized):
                value = list(value)
            if len(value) == items_in_slice:
                itemsize = self.itemsize
                for s, v in zip(range(start, stop, step), value):
                    self._data.overwrite(s * itemsize, self._create_element(v))
            else:
                raise ValueError(f"Can't assign {len(value)} values to an extended slice of length {items_in_slice}.")
        else:
            itemsize = self._dtype._bitlength  # Always set for an Array; the property costs a call.
            length = len(self._data) // itemsize
            if key < 0:
                key += length
            if key < 0 or key >= length:
                raise IndexError(f"Index {key} out of range for Array of length {length}.")
            start = itemsize * key
            if self._tibs_dtype is not None:
                # Pack straight into place. A bad value falls through to the general
                # version below, which raises what it always did.
                try:
                    packed = bitstore.ConstBitStore.from_value(self._tibs_dtype, value)
                except Exception:
                    pass
                else:
                    self._data._bitstore[start: start + itemsize] = packed
                    return
            self._data.overwrite(start, self._create_element(value))
            return

    def __delitem__(self, key: slice | int) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step == 1:
                itemsize = self.itemsize
                self._data.__delitem__(slice(start * itemsize, stop * itemsize))
                return
            # We need to delete from the end or the earlier positions will change
            r = reversed(range(start, stop, step)) if step > 0 else range(start, stop, step)
            itemsize = self.itemsize
            for s in r:
                self._data.__delitem__(slice(s * itemsize, (s + 1) * itemsize))
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError
            itemsize = self.itemsize
            start = itemsize * key
            del self._data[start: start + itemsize]

    def __repr__(self) -> str:
        length = len(self)
        length_str = ''
        if length > MAX_ITEMS:
            # Take the ends only, so that a huge Array doesn't build a huge string,
            # and note the real length the way a truncated Bits repr does.
            half = MAX_ITEMS // 2
            head = ', '.join(repr(x) for x in self[:half].to_list())
            tail = ', '.join(repr(x) for x in self[length - half:].to_list())
            list_str = f"[{head}, ..., {tail}]"
            length_str = f'  # length={length}'
        else:
            list_str = f"{self.to_list()}"
        trailing_bit_length = len(self._data) % self.itemsize
        final_str = "" if trailing_bit_length == 0 else ", trailing_bits=" + repr(
            self._data[-trailing_bit_length:])
        return f"Array('{self._dtype}', {list_str}{final_str}){length_str}"

    def astype(self, dtype: str | Dtype) -> Array:
        """Return Array with elements of new dtype, initialised from current Array."""
        new_array = self.__class__(dtype, self.to_list())
        return new_array

    def to_list(self) -> list[ElementType]:
        itemsize = self.itemsize
        if self._tibs_dtype is not None:
            # Bulk unpack, which is far quicker than reading an item at a time. Any
            # trailing bits are excluded, as tibs won't unpack a partial final item.
            return self._data._bitstore.to_values(self._tibs_dtype, len(self._data) // itemsize * itemsize)
        return [self._dtype._read_fn(self._data, start=start)
                for start in range(0, len(self._data) - itemsize + 1, itemsize)]

    def tolist(self) -> list[ElementType]:
        """Deprecated compatibility alias for :meth:`to_list`."""
        return self.to_list()

    def append(self, x: ElementType) -> None:
        if len(self._data) % self.itemsize != 0:
            raise ValueError("Cannot append to Array as its length is not a multiple of the format length.")
        self._data += self._create_element(x)

    def extend(self, iterable: Array | array.array | Iterable[Any]) -> None:
        itemsize = self.itemsize
        if len(self._data) % itemsize != 0:
            raise ValueError(f"Cannot extend Array as its data length ({len(self._data)} bits) is not a multiple of the format length ({itemsize} bits).")
        if isinstance(iterable, Array):
            if self._dtype.name != iterable._dtype.name or self._dtype.length != iterable._dtype.length:
                raise TypeError(
                    f"Cannot extend an Array with format '{self._dtype}' from an Array of format '{iterable._dtype}'.")
            # No need to iterate over the elements, we can just append the data
            self._data.append(iterable._data)
        elif isinstance(iterable, array.array):
            # array.array stores bytes in host order; compare against an explicit dtype.
            other_dtype = _array_typecode_to_dtype(iterable.typecode)
            if other_dtype is None:
                raise ValueError(f"Cannot extend from array with typecode {iterable.typecode}.")
            if self._dtype.name != other_dtype.name or self.itemsize != other_dtype.bitlength:
                raise ValueError(
                    f"Cannot extend an Array with format '{self._dtype}' from an array with typecode '{iterable.typecode}'.")
            self._data += iterable.tobytes()
        else:
            if isinstance(iterable, str):
                raise TypeError("Can't extend an Array with a str.")
            if self._tibs_dtype is not None and isinstance(iterable, (list, tuple, range)):
                # Bulk pack, which is far quicker than packing an item at a time. Only
                # for types that can be iterated twice, as a failure has to fall back to
                # the loop below - that way a bad value raises exactly the error it
                # always did, and leaves the same partially extended Array behind.
                try:
                    packed = bitstore.MutableBitStore.from_values(self._tibs_dtype, iterable)
                except Exception:
                    pass
                else:
                    self._data._addright_bitstore(packed)
                    return
            for item in iterable:
                self._data += self._create_element(item)

    def insert(self, i: int, x: ElementType) -> None:
        """Insert a new element into the Array at position i.

        """
        # Match list.insert semantics: clamp both high and low indices.
        i = max(min(i, len(self)), -len(self))
        self._data.insert(i * self.itemsize, self._create_element(x))

    def pop(self, i: int = -1) -> ElementType:
        """Return and remove an element of the Array.

        Default is to return and remove the final element.

        """
        if len(self) == 0:
            raise IndexError("Can't pop from an empty Array.")
        x = self[i]
        del self[i]
        return x

    def byteswap(self) -> None:
        """Change the endianness in-place of all items in the Array.

        If the Array format is not a whole number of bytes a ValueError will be raised.

        Note that this takes no arguments, unlike BitArray.byteswap(), which shares the
        name but not the signature. An Array knows its own item size, so it always swaps
        every item using that as the pattern. To swap part of an Array, or with a
        different pattern, use byteswap() on its data instead.

        """
        if self.itemsize % 8 != 0:
            raise ValueError(
                f"byteswap can only be used for whole-byte elements. The '{self._dtype}' format is {self.itemsize} bits long.")
        self._data.byteswap(self.itemsize // 8)

    def count(self, value: ElementType) -> int:
        """Return count of Array items that equal value.

        value -- The quantity to compare each Array element to. Type should be appropriate for the Array format.

        For floating point types using a value of float('nan') will count the number of elements that are NaN.

        """
        def is_nan(x: Any) -> bool:
            try:
                return math.isnan(x)
            except TypeError:
                return False

        if is_nan(value):
            return sum(is_nan(i) for i in self)
        else:
            # Bulk read, then let list.count do the comparing.
            return self.to_list().count(value)

    def to_bytes(self) -> bytes:
        """Return the Array data as a bytes object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        return self._data.to_bytes()

    def tobytes(self) -> bytes:
        """Deprecated compatibility alias for :meth:`to_bytes`."""
        return self.to_bytes()

    def to_file(self, f: BinaryIO) -> None:
        """Write the Array data to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        self._data.to_file(f)

    def tofile(self, f: BinaryIO) -> None:
        """Deprecated compatibility alias for :meth:`to_file`."""
        self.to_file(f)

    @classmethod
    def from_file(cls, dtype: str | Dtype, source: str | pathlib.Path | BinaryIO | None = None, /, n: int | None = None) -> Array:
        """Create a new Array with items read from a file path or binary file object.

        If a file object is given the items are read from its current file position.
        If n is given then exactly n items are read, and an EOFError is raised if
        not enough data is available. Otherwise as many whole items as possible are read.
        """
        if source is None:
            raise TypeError("Array.from_file() missing its 'source' argument: a file path or binary file object.")
        x = cls(dtype)
        if n is not None and n < 0:
            raise ValueError("n must be >= 0.")
        item_bits = x.itemsize
        bytes_wanted = None if n is None else (n * item_bits + 7) // 8
        if isinstance(source, (str, pathlib.Path)):
            with open(pathlib.Path(source), 'rb') as f:
                b = f.read() if bytes_wanted is None else f.read(bytes_wanted)
        else:
            b = source.read() if bytes_wanted is None else source.read(bytes_wanted)
        max_items = len(b) * 8 // item_bits
        items_to_use = max_items if n is None else min(n, max_items)
        if n is not None and items_to_use < n:
            raise EOFError(f"Only {items_to_use} items were available, not the {n} items requested.")
        bits_to_use = items_to_use * item_bits
        if bits_to_use:
            x._data._bitstore += MutableBitStore.from_bytes(b, length=bits_to_use)
        return x

    def reverse(self) -> None:
        itemsize = self.itemsize
        trailing_bit_length = len(self._data) % itemsize
        if trailing_bit_length != 0:
            raise ValueError(f"Cannot reverse the items in the Array as its data length ({len(self._data)} bits) is not a multiple of the format length ({itemsize} bits).")
        for start_bit in range(0, len(self._data) // 2, itemsize):
            start_swap_bit = len(self._data) - start_bit - itemsize
            temp = self._data[start_bit: start_bit + itemsize]
            self._data[start_bit: start_bit + itemsize] = self._data[
                                                               start_swap_bit: start_swap_bit + itemsize]
            self._data[start_swap_bit: start_swap_bit + itemsize] = temp

    def pp(self, fmt: str | None = None, width: int = 120, sep: str = ' ',
           show_offset: bool = True, stream: TextIO | None = None, color: bool | None = None) -> None:
        """Pretty-print the Array contents.

        fmt -- Data format string. Defaults to current Array dtype.
        width -- Max width of printed lines in characters. Defaults to 120. A single group will always
                 be printed per line even if it exceeds the max width.
        sep -- A separator string to insert between groups. Defaults to a single space.
        show_offset -- If True shows the element offset in the first column of each line.
        stream -- A TextIO object with a write() method. Defaults to sys.stdout.
        color -- If True use ANSI colours, if False disable them. Defaults to honouring NO_COLOR.

        """
        if stream is None:
            stream = sys.stdout
        colour = Colour(should_use_color(color))
        dtype2 = None
        tidy_fmt = None
        if fmt is None:
            fmt = self.dtype
            dtype1 = self.dtype
            tidy_fmt = "dtype='" + colour.purple + str(self.dtype) + "'" + colour.off
        else:
            token_list = utils.preprocess_tokens(fmt)
            if len(token_list) not in [1, 2]:
                raise ValueError(f"Only one or two tokens can be used in an Array.pp() format - '{fmt}' has {len(token_list)} tokens.")
            name1, length1 = utils.parse_name_length_token(token_list[0])
            dtype1 = Dtype(name1, length1)
            if len(token_list) == 2:
                name2, length2 = utils.parse_name_length_token(token_list[1])
                dtype2 = Dtype(name2, length2)

        token_length = dtype1.bitlength
        if dtype2 is not None:
            # For two types we're OK as long as they don't have different lengths given.
            if dtype1.bitlength is not None and dtype2.bitlength is not None and dtype1.bitlength != dtype2.bitlength:
                raise ValueError(f"Two different format lengths specified ('{fmt}'). Either specify just one, or two the same length.")
            if token_length is None:
                token_length = dtype2.bitlength
        if token_length is None:
            token_length = self.itemsize

        trailing_bit_length = len(self._data) % token_length
        format_sep = " : "  # String to insert on each line between multiple formats
        if tidy_fmt is None:
            tidy_fmt = colour.purple + str(dtype1) + colour.off
            if dtype2 is not None:
                tidy_fmt += ', ' + colour.blue + str(dtype2) + colour.off
            tidy_fmt = "fmt='" + tidy_fmt + "'"
        data = self._data if trailing_bit_length == 0 else self._data[0: -trailing_bit_length]
        length = len(self._data) // token_length
        len_str = colour.green + str(length) + colour.off
        stream.write(f"<{self.__class__.__name__} {tidy_fmt}, length={len_str}, itemsize={token_length} bits, total data size={(len(self._data) + 7) // 8} bytes> [\n")
        data._pp(dtype1, dtype2, token_length, width, sep, format_sep, show_offset, stream, token_length, colour)
        stream.write("]")
        if trailing_bit_length != 0:
            stream.write(" + trailing_bits = " + str(self._data[-trailing_bit_length:]))
        stream.write("\n")

    def equals(self, other: Any) -> bool:
        """Return True if format and all Array items are equal."""
        if isinstance(other, Array):
            if self._dtype.length != other._dtype.length:
                return False
            if self._dtype.name != other._dtype.name:
                return False
            if self._data != other._data:
                return False
            return True
        elif isinstance(other, array.array):
            # Assume we are comparing with an array type
            if self.trailing_bits:
                return False
            # array's itemsize is in bytes, not bits.
            if self.itemsize != other.itemsize * 8:
                return False
            if len(self) != len(other):
                return False
            if self.to_list() != other.tolist():
                return False
            return True
        return False

    def __iter__(self) -> Iterable[ElementType]:
        itemsize = self.itemsize
        if self._tibs_dtype is not None:
            yield from self._data._bitstore.to_values_iter(
                self._tibs_dtype, len(self._data) // itemsize * itemsize)
            return
        start = 0
        for _ in range(len(self)):
            yield self._dtype._read_fn(self._data, start=start)
            start += itemsize

    def __copy__(self) -> Array:
        a_copy = self.__class__(self._dtype)
        a_copy._data = copy.copy(self._data)
        return a_copy

    def __getstate__(self) -> dict[str, Any]:
        # The cached tibs dtype can't be pickled, and is derived anyway. There is no
        # __dict__ to copy now that the class uses __slots__.
        return {'_dtype': self._dtype, '_data': self._data}

    def __setstate__(self, state: dict[str, Any]) -> None:
        for name, value in state.items():
            setattr(self, name, value)
        self._set_tibs_dtype()

    def _bulk_pack_into(self, new_array: Array, values: Iterable[Any]) -> bool:
        """Pack values into an empty new_array in one go, returning False if it can't.

        A False return leaves new_array untouched, so the caller can fall back to
        packing an element at a time.
        """
        if new_array._tibs_dtype is None:
            return False
        try:
            packed = bitstore.MutableBitStore.from_values(new_array._tibs_dtype, values)
        except Exception:
            return False
        new_array._data._addright_bitstore(packed)
        return True

    def _apply_op_to_all_elements(self, op, value: int | float | None, is_comparison: bool = False) -> Array:
        """Apply op with value to each element of the Array and return a new Array"""
        new_array = self.__class__('bool' if is_comparison else self._dtype)
        new_data = BitArray()
        failures = index = 0
        msg = ''
        if value is not None:
            def partial_op(a):
                return op(a, value)
        else:
            def partial_op(a):
                return op(a)
        itemsize = self.itemsize
        if self._tibs_dtype is not None:
            # Bulk read, apply, bulk write. Anything that goes wrong - a bad operand or
            # a result that won't pack - falls through to the loop below, which reports
            # the failure count and message exactly as it always has.
            try:
                new_values = [partial_op(v) for v in self.to_list()]
            except Exception:
                new_values = None
            if new_values is not None and self._bulk_pack_into(new_array, new_values):
                return new_array
        for i in range(len(self)):
            v = self._dtype._read_fn(self._data, start=itemsize * i)
            try:
                new_data.append(new_array._create_element(partial_op(v)))
            except (ValueError, ZeroDivisionError) as e:
                if failures == 0:
                    msg = str(e)
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f"Applying operator '{op.__name__}' to Array caused {failures} errors. "
                             f'First error at index {index} was: "{msg}"')
        new_array._data = new_data
        return new_array

    def _apply_op_to_all_elements_inplace(self, op, value: int | float) -> Array:
        """Apply op with value to each element of the Array in place."""
        # This isn't really being done in-place, but it's simpler and faster for now?
        new_data = BitArray()
        failures = index = 0
        msg = ''
        itemsize = self.itemsize
        for i in range(len(self)):
            v = self._dtype._read_fn(self._data, start=itemsize * i)
            try:
                new_data.append(self._create_element(op(v, value)))
            except (ValueError, ZeroDivisionError) as e:
                if failures == 0:
                    msg = str(e)
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f"Applying operator '{op.__name__}' to Array caused {failures} errors. "
                             f'First error at index {index} was: "{msg}"')
        self._data = new_data
        return self

    def _apply_bitwise_op_to_all_elements(self, op, value: BitsType) -> Array:
        """Apply op with value to each element of the Array as an unsigned integer and return a new Array"""
        a_copy = self[:]
        a_copy._apply_bitwise_op_to_all_elements_inplace(op, value)
        return a_copy

    def _apply_bitwise_op_to_all_elements_inplace(self, op, value: BitsType) -> Array:
        """Apply op with value to each element of the Array as an unsigned integer in place."""
        value = BitArray._create_from_bitstype(value)
        itemsize = self.itemsize
        if len(value) != itemsize:
            raise ValueError(f"Bitwise op needs a bitstring of length {itemsize} to match format {self._dtype}.")
        for start in range(0, len(self) * itemsize, itemsize):
            self._data[start: start + itemsize] = op(self._data[start: start + itemsize], value)
        return self

    def _apply_op_between_arrays(self, op, other: Array, is_comparison: bool = False) -> Array:
        if len(self) != len(other):
            msg = f"Cannot operate element-wise on Arrays with different lengths ({len(self)} and {len(other)})."
            if op in [operator.add, operator.iadd]:
                msg += " Use extend() method to concatenate Arrays."
            if op in [operator.eq, operator.ne]:
                msg += " Use equals() method to compare Arrays for a single boolean result."
            raise ValueError(msg)
        if is_comparison:
            new_type = dtype_register.get_dtype('bool', 1)
        else:
            new_type = self._promotetype(self._dtype, other._dtype)
        new_array = self.__class__(new_type)
        new_data = BitArray()
        failures = index = 0
        msg = ''
        itemsize = self.itemsize
        other_itemsize = other.itemsize
        if self._tibs_dtype is not None and other._tibs_dtype is not None:
            # As in _apply_op_to_all_elements: bulk where possible, and fall through to
            # the per-element loop for exact error reporting when anything fails.
            try:
                new_values = list(map(op, self.to_list(), other.to_list()))
            except Exception:
                new_values = None
            if new_values is not None and self._bulk_pack_into(new_array, new_values):
                return new_array
        for i in range(len(self)):
            a = self._dtype._read_fn(self._data, start=itemsize * i)
            b = other._dtype._read_fn(other._data, start=other_itemsize * i)
            try:
                new_data.append(new_array._create_element(op(a, b)))
            except (ValueError, ZeroDivisionError) as e:
                if failures == 0:
                    msg = str(e)
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f"Applying operator '{op.__name__}' between Arrays caused {failures} errors. "
                             f'First error at index {index} was: "{msg}"')
        new_array._data = new_data
        return new_array

    def _apply_op_between_arrays_inplace(self, op, other: Array) -> Array:
        """Apply op between Arrays and update self in place."""
        result = self._apply_op_between_arrays(op, other)
        self._dtype = result._dtype
        self._data = result._data
        return self

    @classmethod
    def _promotetype(cls, type1: Dtype, type2: Dtype) -> Dtype:
        """When combining types which one wins?

        1. We only deal with types representing floats or integers.
        2. One of the two types gets returned. We never create a new one.
        3. Floating point types always win against integer types.
        4. Signed integer types always win against unsigned integer types.
        5. Longer types win against shorter types.
        6. In a tie the first type wins against the second type.

        """
        def is_float(x): return x.return_type is float
        def is_int(x): return x.return_type is int or x.return_type is bool
        if is_float(type1) + is_int(type1) + is_float(type2) + is_int(type2) != 2:
            raise ValueError(f"Only integer and floating point types can be combined - not '{type1}' and '{type2}'.")
        # If same type choose the widest
        if type1.name == type2.name:
            return type1 if type1.length > type2.length else type2
        # We choose floats above integers, irrespective of the widths
        if is_float(type1) and is_int(type2):
            return type1
        if is_int(type1) and is_float(type2):
            return type2
        if is_float(type1) and is_float(type2):
            return type2 if type2.length > type1.length else type1
        assert is_int(type1) and is_int(type2)
        if type1.is_signed and not type2.is_signed:
            return type1
        if type2.is_signed and not type1.is_signed:
            return type2
        return type2 if type2.length > type1.length else type1

    # Operators between Arrays or an Array and scalar value

    def __add__(self, other: int | float | Array) -> Array:
        """Add int or float to all elements."""
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.add, other)
        return self._apply_op_to_all_elements(operator.add, other)

    def __iadd__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.add, other)
        return self._apply_op_to_all_elements_inplace(operator.add, other)

    def __isub__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.sub, other)
        return self._apply_op_to_all_elements_inplace(operator.sub, other)

    def __sub__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.sub, other)
        return self._apply_op_to_all_elements(operator.sub, other)

    def __mul__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.mul, other)
        return self._apply_op_to_all_elements(operator.mul, other)

    def __imul__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.mul, other)
        return self._apply_op_to_all_elements_inplace(operator.mul, other)

    def __floordiv__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.floordiv, other)
        return self._apply_op_to_all_elements(operator.floordiv, other)

    def __ifloordiv__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.floordiv, other)
        return self._apply_op_to_all_elements_inplace(operator.floordiv, other)

    def __truediv__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.truediv, other)
        return self._apply_op_to_all_elements(operator.truediv, other)

    def __itruediv__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.truediv, other)
        return self._apply_op_to_all_elements_inplace(operator.truediv, other)

    def __rshift__(self, other: int | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.rshift, other)
        return self._apply_op_to_all_elements(operator.rshift, other)

    def __lshift__(self, other: int | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.lshift, other)
        return self._apply_op_to_all_elements(operator.lshift, other)

    def __irshift__(self, other: int | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.rshift, other)
        return self._apply_op_to_all_elements_inplace(operator.rshift, other)

    def __ilshift__(self, other: int | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.lshift, other)
        return self._apply_op_to_all_elements_inplace(operator.lshift, other)

    def __mod__(self, other: int | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.mod, other)
        return self._apply_op_to_all_elements(operator.mod, other)

    def __imod__(self, other: int | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays_inplace(operator.mod, other)
        return self._apply_op_to_all_elements_inplace(operator.mod, other)

    # Bitwise operators

    def __and__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.iand, other)

    def __iand__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements_inplace(operator.iand, other)

    def __or__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ior, other)

    def __ior__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements_inplace(operator.ior, other)

    def __xor__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ixor, other)

    def __ixor__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements_inplace(operator.ixor, other)

    # Reverse operators between a scalar value and an Array

    def __rmul__(self, other: int | float) -> Array:
        return self._apply_op_to_all_elements(operator.mul, other)

    def __radd__(self, other: int | float) -> Array:
        return self._apply_op_to_all_elements(operator.add, other)

    def __rsub__(self, other: int | float) -> Array:
        # i - A == (-A) + i
        neg = self._apply_op_to_all_elements(operator.neg, None)
        return neg._apply_op_to_all_elements(operator.add, other)

    # Reverse operators between a scalar and something that can be a BitArray.

    def __rand__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.iand, other)

    def __ror__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ior, other)

    def __rxor__(self, other: BitsType) -> Array:
        return self._apply_bitwise_op_to_all_elements(operator.ixor, other)

    # Comparison operators

    def __lt__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.lt, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.lt, other, is_comparison=True)

    def __gt__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.gt, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.gt, other, is_comparison=True)

    def __ge__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.ge, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.ge, other, is_comparison=True)

    def __le__(self, other: int | float | Array) -> Array:
        if isinstance(other, Array):
            return self._apply_op_between_arrays(operator.le, other, is_comparison=True)
        return self._apply_op_to_all_elements(operator.le, other, is_comparison=True)

    def _eq_ne(self, op, other: Any) -> Array:
        if isinstance(other, (int, float, str, Bits)):
            return self._apply_op_to_all_elements(op, other, is_comparison=True)
        other = self.__class__(self.dtype, other)
        return self._apply_op_between_arrays(op, other, is_comparison=True)

    def __eq__(self, other: Any) -> Array:
        return self._eq_ne(operator.eq, other)

    def __ne__(self, other: Any) -> Array:
        return self._eq_ne(operator.ne, other)

    # Unary operators

    def __neg__(self):
        return self._apply_op_to_all_elements(operator.neg, None)

    def __abs__(self):
        return self._apply_op_to_all_elements(operator.abs, None)
