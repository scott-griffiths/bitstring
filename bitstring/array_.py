from __future__ import annotations

import math
import numbers
from collections.abc import Sized
from bitstring.exceptions import CreationError
from typing import Any, BinaryIO, overload, TextIO
from collections.abc import Iterable
from bitstring.bits import Bits, BitsType
from bitstring.bitarray_ import BitArray
from bitstring.dtypes import Dtype, dtype_register
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

MutableBitStore = bitstring.bitstore.MutableBitStore


def _array_typecode_to_dtype(typecode: str) -> Dtype | None:
    endian = '<' if sys.byteorder == 'little' else '>'
    name_value = utils.parse_single_struct_token(endian + typecode)
    if name_value is None:
        return None
    return dtype_register.get_dtype(*name_value, scale=None)


class Array:
    """Return an Array whose elements are initialised according to the fmt string.
    The dtype string can be typecode as used in the struct module or any fixed-length bitstring
    format.

    a = Array('>H', [1, 15, 105])
    b = Array('i5', [-9, 0, 4])

    The Array data is stored compactly as a BitArray object and the Array behaves very like
    a list of items of the given format. Both the Array data and fmt properties can be freely
    modified after creation. If the data length is not a multiple of the fmt length then the
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

    data -- The BitArray binary data of the Array. Can be freely modified.
    dtype -- The format string or typecode. Can be freely modified.
    itemsize -- The length *in bits* of a single item. Read only.
    trailing_bits -- If the data length is not a multiple of the fmt length, this BitArray
                     gives the leftovers at the end of the data.


    """

    def __init__(self, dtype: str | Dtype, initializer: Array | array.array | Iterable | None = None,
                 trailing_bits: BitsType | None = None) -> None:
        self.data = BitArray()
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
        if isinstance(dtype, Dtype) and dtype.scale == 'auto':
            auto_scale = self._calculate_auto_scale(initializer, dtype.name, dtype.length)
            dtype = Dtype(dtype.name, dtype.length, scale=auto_scale)
        try:
            self._set_dtype(dtype)
        except ValueError as e:
            raise CreationError(e)

        if initializer is not None:
            self.extend(initializer)

        if trailing_bits is not None:
            self.data += BitArray._create_from_bitstype(trailing_bits)

    @classmethod
    def from_zeros(cls, dtype: str | Dtype, n: int, /) -> Array:
        """Create a new Array containing n zeroed items."""
        n = int(n)
        if n < 0:
            raise ValueError(f"Can't create an Array of negative length {n}.")
        x = cls(dtype)
        x.data = BitArray.from_zeros(n * x.itemsize)
        return x

    @classmethod
    def from_bytes(cls, dtype: str | Dtype, data: bytes | bytearray | memoryview, /) -> Array:
        """Create a new Array with its binary data taken from a bytes-like object."""
        if not isinstance(data, (bytes, bytearray, memoryview)):
            raise TypeError(f"Array.from_bytes() needs a bytes-like object, but received a {type(data).__name__}.")
        x = cls(dtype)
        x.data += data
        return x

    _largest_values = None

    @staticmethod
    def _calculate_auto_scale(initializer, name: str, length: int | None) -> float:
        # Now need to find the largest power of 2 representable with this format.
        if Array._largest_values is None:
            Array._largest_values = {
                'mxint8': Bits('0b01111111').mxint8,  # 1.0 + 63.0/64.0,
                'e2m1mxfp4': Bits('0b0111').e2m1mxfp4,  # 6.0
                'e2m3mxfp6': Bits('0b011111').e2m3mxfp6,  # 7.5
                'e3m2mxfp6': Bits('0b011111').e3m2mxfp6,  # 28.0
                'e4m3mxfp_saturate8': Bits('0b01111110').e4m3mxfp_saturate8,  # 448.0
                'e4m3mxfp_overflow8': Bits('0b01111110').e4m3mxfp_overflow8,  # 448.0
                'e5m2mxfp_saturate8': Bits('0b01111011').e5m2mxfp_saturate8,  # 57344.0
                'e5m2mxfp_overflow8': Bits('0b01111011').e5m2mxfp_overflow8,  # 57344.0
                'p4binary8': Bits('0b01111110').p4binary8,  # 224.0
                'p3binary8': Bits('0b01111110').p3binary8,  # 49152.0
                'f16': Bits('0x7bff').f16,  # 65504.0
                # The bfloat range is so large the scaling algorithm doesn't work well, so I'm disallowing it.
                # 'bfloat16': Bits('0x7f7f').bfloat16,  # 3.38953139e38,
            }
        if f'{name}{length}' in Array._largest_values.keys():
            float_values = Array('f64', initializer).to_list()
            if not float_values:
                raise ValueError("Can't calculate an 'auto' scale with an empty Array initializer.")
            max_float_value = max(abs(x) for x in float_values)
            if max_float_value == 0:
                # This special case isn't covered in the standard. I'm choosing to return no scale.
                return 1.0
            # We need to find the largest power of 2 that is less than the max value
            log2 = math.floor(math.log2(max_float_value))
            lp2 = math.floor(math.log2(Array._largest_values[f'{name}{length}']))
            lg_scale = log2 - lp2
            # Saturate at values representable in E8M0 format.
            if lg_scale > 127:
                lg_scale = 127
            elif lg_scale < -127:
                lg_scale = -127
            return 2 ** lg_scale
        else:
            raise ValueError(f"Can't calculate auto scale for format '{name}{length}'. "
                             f"This feature is only available for these formats: {list(Array._largest_values.keys())}.")

    @property
    def itemsize(self) -> int:
        bitlength = self._dtype.bitlength
        if bitlength is None:
            raise ValueError("A fixed length format is needed for an Array.")
        return bitlength

    @property
    def trailing_bits(self) -> BitArray:
        trailing_bit_length = len(self.data) % self._dtype.bitlength
        return BitArray() if trailing_bit_length == 0 else self.data[-trailing_bit_length:]

    @property
    def dtype(self) -> Dtype:
        return self._dtype

    @dtype.setter
    def dtype(self, new_dtype: str | Dtype) -> None:
        self._set_dtype(new_dtype)

    def _set_dtype(self, new_dtype: str | Dtype) -> None:
        if isinstance(new_dtype, Dtype):
            self._dtype = new_dtype
        else:
            if not isinstance(new_dtype, str):
                raise TypeError(f"An Array dtype must be a str or a Dtype, not a {type(new_dtype).__name__}.")
            try:
                dtype = Dtype(new_dtype)
            except ValueError:
                name_length = utils.parse_single_struct_token(new_dtype)
                if name_length is not None:
                    dtype = Dtype(name_length[0], name_length[1])
                else:
                    raise ValueError(f"Inappropriate Dtype for Array: '{new_dtype}'.")
            if dtype.length is None:
                raise ValueError(f"A fixed length format is needed for an Array, received '{new_dtype}'.")
            self._dtype = dtype
        if self._dtype.scale == 'auto':
            raise ValueError("A Dtype with an 'auto' scale factor can only be used when creating a new Array.")

    def _create_element(self, value: ElementType) -> Bits:
        """Create Bits from value according to the token_name and token_length"""
        b = self._dtype.pack(value)
        if len(b) != self.itemsize:
            raise ValueError(f"The value {value!r} has the wrong length for the format '{self._dtype}'.")
        return b

    def __len__(self) -> int:
        return len(self.data) // self.itemsize

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
                    d.append(self.data[s: s + itemsize])
                a = self.__class__(self._dtype)
                a.data = d
                return a
            else:
                itemsize = self.itemsize
                a = self.__class__(self._dtype)
                a.data = self.data[start * itemsize: stop * itemsize]
                return a
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f"Index {key} out of range for Array of length {len(self)}.")
            return self._dtype._read_fn(self.data, start=self.itemsize * key)

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
                new_data = BitArray()
                for x in value:
                    new_data += self._create_element(x)
                itemsize = self.itemsize
                self.data[start * itemsize: stop * itemsize] = new_data
                return
            items_in_slice = len(range(start, stop, step))
            if not isinstance(value, Sized):
                value = list(value)
            if len(value) == items_in_slice:
                itemsize = self.itemsize
                for s, v in zip(range(start, stop, step), value):
                    self.data.overwrite(s * itemsize, self._create_element(v))
            else:
                raise ValueError(f"Can't assign {len(value)} values to an extended slice of length {items_in_slice}.")
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f"Index {key} out of range for Array of length {len(self)}.")
            start = self.itemsize * key
            self.data.overwrite(start, self._create_element(value))
            return

    def __delitem__(self, key: slice | int) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step == 1:
                itemsize = self.itemsize
                self.data.__delitem__(slice(start * itemsize, stop * itemsize))
                return
            # We need to delete from the end or the earlier positions will change
            r = reversed(range(start, stop, step)) if step > 0 else range(start, stop, step)
            itemsize = self.itemsize
            for s in r:
                self.data.__delitem__(slice(s * itemsize, (s + 1) * itemsize))
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError
            itemsize = self.itemsize
            start = itemsize * key
            del self.data[start: start + itemsize]

    def __repr__(self) -> str:
        list_str = f"{self.to_list()}"
        trailing_bit_length = len(self.data) % self.itemsize
        final_str = "" if trailing_bit_length == 0 else ", trailing_bits=" + repr(
            self.data[-trailing_bit_length:])
        return f"Array('{self._dtype}', {list_str}{final_str})"

    def astype(self, dtype: str | Dtype) -> Array:
        """Return Array with elements of new dtype, initialised from current Array."""
        new_array = self.__class__(dtype, self.to_list())
        return new_array

    def to_list(self) -> list[ElementType]:
        itemsize = self.itemsize
        return [self._dtype._read_fn(self.data, start=start)
                for start in range(0, len(self.data) - itemsize + 1, itemsize)]

    def tolist(self) -> list[ElementType]:
        """Compatibility alias for :meth:`to_list`."""
        return self.to_list()

    def append(self, x: ElementType) -> None:
        if len(self.data) % self.itemsize != 0:
            raise ValueError("Cannot append to Array as its length is not a multiple of the format length.")
        self.data += self._create_element(x)

    def extend(self, iterable: Array | array.array | Iterable[Any]) -> None:
        itemsize = self.itemsize
        if len(self.data) % itemsize != 0:
            raise ValueError(f"Cannot extend Array as its data length ({len(self.data)} bits) is not a multiple of the format length ({itemsize} bits).")
        if isinstance(iterable, Array):
            if self._dtype.name != iterable._dtype.name or self._dtype.length != iterable._dtype.length:
                raise TypeError(
                    f"Cannot extend an Array with format '{self._dtype}' from an Array of format '{iterable._dtype}'.")
            # No need to iterate over the elements, we can just append the data
            self.data.append(iterable.data)
        elif isinstance(iterable, array.array):
            # array.array stores bytes in host order; compare against an explicit dtype.
            other_dtype = _array_typecode_to_dtype(iterable.typecode)
            if other_dtype is None:
                raise ValueError(f"Cannot extend from array with typecode {iterable.typecode}.")
            if self._dtype.name != other_dtype.name or self.itemsize != other_dtype.bitlength:
                raise ValueError(
                    f"Cannot extend an Array with format '{self._dtype}' from an array with typecode '{iterable.typecode}'.")
            self.data += iterable.tobytes()
        else:
            if isinstance(iterable, str):
                raise TypeError("Can't extend an Array with a str.")
            for item in iterable:
                self.data += self._create_element(item)

    def insert(self, i: int, x: ElementType) -> None:
        """Insert a new element into the Array at position i.

        """
        # Match list.insert semantics: clamp both high and low indices.
        i = max(min(i, len(self)), -len(self))
        self.data.insert(i * self.itemsize, self._create_element(x))

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

        """
        if self.itemsize % 8 != 0:
            raise ValueError(
                f"byteswap can only be used for whole-byte elements. The '{self._dtype}' format is {self.itemsize} bits long.")
        self.data.byteswap(self.itemsize // 8)

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
            return sum(i == value for i in self)

    def to_bytes(self) -> bytes:
        """Return the Array data as a bytes object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        return self.data.to_bytes()

    def tobytes(self) -> bytes:
        """Compatibility alias for :meth:`to_bytes`."""
        return self.to_bytes()

    def to_file(self, f: BinaryIO) -> None:
        """Write the Array data to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        self.data.to_file(f)

    def tofile(self, f: BinaryIO) -> None:
        """Compatibility alias for :meth:`to_file`."""
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
            x.data._bitstore += MutableBitStore.from_bytes(b, length=bits_to_use)
        return x

    def reverse(self) -> None:
        itemsize = self.itemsize
        trailing_bit_length = len(self.data) % itemsize
        if trailing_bit_length != 0:
            raise ValueError(f"Cannot reverse the items in the Array as its data length ({len(self.data)} bits) is not a multiple of the format length ({itemsize} bits).")
        for start_bit in range(0, len(self.data) // 2, itemsize):
            start_swap_bit = len(self.data) - start_bit - itemsize
            temp = self.data[start_bit: start_bit + itemsize]
            self.data[start_bit: start_bit + itemsize] = self.data[
                                                               start_swap_bit: start_swap_bit + itemsize]
            self.data[start_swap_bit: start_swap_bit + itemsize] = temp

    def pp(self, fmt: str | None = None, width: int = 120,
           show_offset: bool = True, stream: TextIO | None = None, color: bool | None = None) -> None:
        """Pretty-print the Array contents.

        fmt -- Data format string. Defaults to current Array dtype.
        width -- Max width of printed lines in characters. Defaults to 120. A single group will always
                 be printed per line even if it exceeds the max width.
        show_offset -- If True shows the element offset in the first column of each line.
        stream -- A TextIO object with a write() method. Defaults to sys.stdout.
        color -- If True use ANSI colours, if False disable them. Defaults to honouring NO_COLOR.

        """
        if stream is None:
            stream = sys.stdout
        colour = Colour(should_use_color(color))
        sep = ' '
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

        trailing_bit_length = len(self.data) % token_length
        format_sep = " : "  # String to insert on each line between multiple formats
        if tidy_fmt is None:
            tidy_fmt = colour.purple + str(dtype1) + colour.off
            if dtype2 is not None:
                tidy_fmt += ', ' + colour.blue + str(dtype2) + colour.off
            tidy_fmt = "fmt='" + tidy_fmt + "'"
        data = self.data if trailing_bit_length == 0 else self.data[0: -trailing_bit_length]
        length = len(self.data) // token_length
        len_str = colour.green + str(length) + colour.off
        stream.write(f"<{self.__class__.__name__} {tidy_fmt}, length={len_str}, itemsize={token_length} bits, total data size={(len(self.data) + 7) // 8} bytes> [\n")
        data._pp(dtype1, dtype2, token_length, width, sep, format_sep, show_offset, stream, token_length, colour)
        stream.write("]")
        if trailing_bit_length != 0:
            stream.write(" + trailing_bits = " + str(self.data[-trailing_bit_length:]))
        stream.write("\n")

    def equals(self, other: Any) -> bool:
        """Return True if format and all Array items are equal."""
        if isinstance(other, Array):
            if self._dtype.length != other._dtype.length:
                return False
            if self._dtype.name != other._dtype.name:
                return False
            if self.data != other.data:
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
        start = 0
        itemsize = self.itemsize
        for _ in range(len(self)):
            yield self._dtype._read_fn(self.data, start=start)
            start += itemsize

    def __copy__(self) -> Array:
        a_copy = self.__class__(self._dtype)
        a_copy.data = copy.copy(self.data)
        return a_copy

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
        for i in range(len(self)):
            v = self._dtype._read_fn(self.data, start=itemsize * i)
            try:
                new_data.append(new_array._create_element(partial_op(v)))
            except (CreationError, ZeroDivisionError, ValueError) as e:
                if failures == 0:
                    msg = str(e)
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f"Applying operator '{op.__name__}' to Array caused {failures} errors. "
                             f'First error at index {index} was: "{msg}"')
        new_array.data = new_data
        return new_array

    def _apply_op_to_all_elements_inplace(self, op, value: int | float) -> Array:
        """Apply op with value to each element of the Array in place."""
        # This isn't really being done in-place, but it's simpler and faster for now?
        new_data = BitArray()
        failures = index = 0
        msg = ''
        itemsize = self.itemsize
        for i in range(len(self)):
            v = self._dtype._read_fn(self.data, start=itemsize * i)
            try:
                new_data.append(self._create_element(op(v, value)))
            except (CreationError, ZeroDivisionError, ValueError) as e:
                if failures == 0:
                    msg = str(e)
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f"Applying operator '{op.__name__}' to Array caused {failures} errors. "
                             f'First error at index {index} was: "{msg}"')
        self.data = new_data
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
            self.data[start: start + itemsize] = op(self.data[start: start + itemsize], value)
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
        for i in range(len(self)):
            a = self._dtype._read_fn(self.data, start=itemsize * i)
            b = other._dtype._read_fn(other.data, start=other_itemsize * i)
            try:
                new_data.append(new_array._create_element(op(a, b)))
            except (CreationError, ValueError, ZeroDivisionError) as e:
                if failures == 0:
                    msg = str(e)
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f"Applying operator '{op.__name__}' between Arrays caused {failures} errors. "
                             f'First error at index {index} was: "{msg}"')
        new_array.data = new_data
        return new_array

    def _apply_op_between_arrays_inplace(self, op, other: Array) -> Array:
        """Apply op between Arrays and update self in place."""
        result = self._apply_op_between_arrays(op, other)
        self._dtype = result._dtype
        self.data = result.data
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
