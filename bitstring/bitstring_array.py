from __future__ import annotations

from collections.abc import Sized
from bitstring.exceptions import CreationError
from typing import Union, List, Iterable, Any, Optional, BinaryIO, overload, TextIO
from bitstring.classes import BitArray, Bits, BitsType
from bitstring.utils import tokenparser
import functools
import copy
import array
import operator
import io
import sys

# The possible types stored in each element of the Array
ElementType = Union[float, str, int, bytes, bool, Bits]


class Array:
    """Return an Array whose elements are initialised according to the fmt string.
    The fmt string can be typecode as used in the struct module or any fixed-length bitstring
    format.

    a = Array('>H', [1, 15, 105])
    b = Array('int5', [-9, 0, 4])

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
    fromfile() -- Append items read from a file object.
    insert() -- Insert an item at a given position.
    pop() -- Remove and return an item.
    pp() -- Pretty print the Array.
    reverse() -- Reverse the order of all items.
    tobytes() -- Return Array data as bytes object, padding with zero bits at the end if needed.
    tofile() -- Write Array data to a file, padding with zero bits at the end if needed.
    tolist() -- Return Array items as a list.

    Special methods:

    Also available are the operators [], ==, !=, +, *, <<, >>, &, |, ^,
    plus the mutating operators [], +=, *=, <<=, >>=, &=, |=, ^=.

    Properties:

    data -- The BitArray binary data of the Array. Can be freely modified.
    fmt -- The format string or typecode. Can be freely modified.
    itemsize -- The length *in bits* of a single item. Read only.
    trailing_bits -- If the data length is not a multiple of the fmt length, this BitArray
                     gives the leftovers at the end of the data.


    """

    def __init__(self, fmt: str, initializer: Optional[Union[int, Array, array.array, Iterable, Bits, bytes, bytearray, memoryview, BinaryIO]] = None,
                 trailing_bits: Optional[BitsType] = None) -> None:
        self.data = BitArray()
        try:
            self.fmt = fmt
        except ValueError as e:
            raise CreationError(e)

        if isinstance(initializer, int):
            self.data = BitArray(initializer * self._itemsize)
        elif isinstance(initializer, (Bits, bytes, bytearray, memoryview)):
            self.data += initializer
        elif isinstance(initializer, io.BufferedReader):
            self.fromfile(initializer)
        elif initializer is not None:
            self.extend(initializer)

        if trailing_bits is not None:
            self.data += BitArray._create_from_bitstype(trailing_bits)

    @property
    def itemsize(self) -> int:
        return self._itemsize

    @property
    def trailing_bits(self) -> BitArray:
        trailing_bit_length = len(self.data) % self._itemsize
        return BitArray() if trailing_bit_length == 0 else self.data[-trailing_bit_length:]

    # Converting array.array typecodes to our equivalents.
    _array_typecodes: dict[str, str] = {'b': 'int8',
                                        'B': 'uint8',
                                        'h': 'intne16',
                                        'H': 'uintne16',
                                        'l': 'intne32',
                                        'L': 'uintne32',
                                        'q': 'intne64',
                                        'Q': 'uintne64',
                                        'e': 'floatne16',
                                        'f': 'floatne32',
                                        'd': 'floatne64'}

    @property
    def fmt(self) -> str:
        return self._fmt

    @fmt.setter
    def fmt(self, new_fmt: str) -> None:
        tokens = tokenparser(new_fmt)[1]
        token_names_and_lengths = [(x[0], x[1]) for x in tokens]
        if len(token_names_and_lengths) != 1:
            raise ValueError(
                f"Only a single token can be used in an Array format - '{new_fmt}' has {len(token_names_and_lengths)} tokens.")
        token_name, token_length = token_names_and_lengths[0]
        if token_length is None:
            raise ValueError(f"The format '{new_fmt}' doesn't have a fixed length and so can't be used in an Array.")
        try:
            self._setter_func = functools.partial(Bits._setfunc[token_name], length=token_length)
        except KeyError:
            raise ValueError(f"The token '{token_name}' can't be used to set Array elements.")
        try:
            self._getter_func = functools.partial(Bits._name_to_read[token_name], length=token_length)
        except KeyError:
            raise ValueError(f"The token '{token_name}' can't be used to get Array elements.")
        self._itemsize = int(token_length)
        self._token_name = token_name
        # We save the user's fmt string so that we can use it in __repr__ etc.
        self._fmt = new_fmt

    def _create_element(self, value: ElementType) -> Bits:
        """Create Bits from value according to the token_name and token_length"""
        b = Bits()
        self._setter_func(b, value)
        if len(b) != self._itemsize:
            raise ValueError(f"The value {value!r} has the wrong length for the format '{self._fmt}'.")
        return b

    def __len__(self) -> int:
        return len(self.data) // self._itemsize

    @overload
    def __getitem__(self, key: slice) -> Array:
        ...

    @overload
    def __getitem__(self, key: int) -> ElementType:
        ...

    def __getitem__(self, key: Union[slice, int]) -> Union[Array, ElementType]:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step != 1:
                d = BitArray()
                for s in range(start * self._itemsize, stop * self._itemsize, step * self._itemsize):
                    d.append(self.data[s: s + self._itemsize])
                a = Array(fmt=self._fmt)
                a.data = d
                return a
            else:
                a = Array(fmt=self._fmt)
                a.data = self.data[start * self._itemsize: stop * self._itemsize]
                return a
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f"Index {key} out of range for Array of length {len(self)}.")
            return self._getter_func(self.data, start=self._itemsize * key)

    @overload
    def __setitem__(self, key: slice, value: Iterable[ElementType]) -> None:
        ...

    @overload
    def __setitem__(self, key: int, value: ElementType) -> None:
        ...

    def __setitem__(self, key: Union[slice, int], value: Union[Iterable[ElementType], ElementType]) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if not isinstance(value, Iterable):
                raise TypeError("Can only assign an iterable to a slice.")
            if step == 1:
                new_data = BitArray()
                for x in value:
                    new_data += self._create_element(x)
                self.data[start * self._itemsize: stop * self._itemsize] = new_data
                return
            items_in_slice = len(range(start, stop, step))
            if not isinstance(value, Sized):
                value = list(value)
            if len(value) == items_in_slice:
                for s, v in zip(range(start, stop, step), value):
                    self.data.overwrite(self._create_element(v), s * self._itemsize)
            else:
                raise ValueError(f"Can't assign {len(value)} values to an extended slice of length {stop - start}.")
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError(f"Index {key} out of range for Array of length {len(self)}.")
            start = self._itemsize * key
            self.data.overwrite(self._create_element(value), start)
            return

    def __delitem__(self, key: Union[slice, int]) -> None:
        if isinstance(key, slice):
            start, stop, step = key.indices(len(self))
            if step == 1:
                self.data.__delitem__(slice(start * self._itemsize, stop * self._itemsize))
                return
            # We need to delete from the end or the earlier positions will change
            r = reversed(range(start, stop, step)) if step > 0 else range(start, stop, step)
            for s in r:
                self.data.__delitem__(slice(s * self._itemsize, (s + 1) * self._itemsize))
        else:
            if key < 0:
                key += len(self)
            if key < 0 or key >= len(self):
                raise IndexError
            start = self._itemsize * key
            del self.data[start: start + self._itemsize]

    def __repr__(self) -> str:
        list_str = f"{self.tolist()}"
        trailing_bit_length = len(self.data) % self._itemsize
        final_str = "" if trailing_bit_length == 0 else ", trailing_bits=" + repr(
            self.data[-trailing_bit_length:])
        return f"Array('{self._fmt}', {list_str}{final_str})"

    def tolist(self) -> List[ElementType]:
        return [self._getter_func(self.data, start=start)
                for start in range(0, len(self.data) - self._itemsize + 1, self._itemsize)]

    def append(self, x: ElementType) -> None:
        if len(self.data) % self._itemsize != 0:
            raise ValueError(f"Cannot append to Array as its length is not a multiple of the format length.")
        self.data += self._create_element(x)

    def extend(self, iterable: Union[Array, array.array, Iterable]) -> None:
        if len(self.data) % self._itemsize != 0:
            raise ValueError(f"Cannot extend Array as its data length ({len(self.data)} bits) is not a multiple of the format length ({self._itemsize} bits).")
        if isinstance(iterable, Array):
            if self._token_name != iterable._token_name or self._itemsize != iterable._itemsize:
                raise TypeError(
                    f"Cannot extend an Array with format '{self._fmt}' from an Array of format '{iterable._fmt}'.")
            # No need to iterate over the elements, we can just append the data
            self.data.append(iterable.data)
        elif isinstance(iterable, array.array):
            other_fmt = Array._array_typecodes.get(iterable.typecode, iterable.typecode)
            token_name, token_length, _ = tokenparser(other_fmt)[1][0]
            if self._token_name != token_name or self._itemsize != token_length:
                raise ValueError(
                    f"Cannot extend an Array with format '{self._fmt}' from an array with typecode '{iterable.typecode}'.")
            self.data += iterable.tobytes()
        else:
            if isinstance(iterable, str):
                raise TypeError(f"Can't extend an Array with a str.")
            for item in iterable:
                self.data += self._create_element(item)

    def insert(self, i: int, x: ElementType) -> None:
        """Insert a new element into the Array.

        """
        i = min(i, len(self))  # Inserting beyond len of array inserts at the end (copying standard behaviour)
        self.data.insert(self._create_element(x), i * self._itemsize)

    def pop(self, i: int = -1) -> ElementType:
        """Return and remove an element of the Array.

        Default is to return and remove the final element.

        """
        x = self[i]
        del self[i]
        return x

    def byteswap(self) -> None:
        """Change the endianness in-place of all items in the Array.

        If the Array format is not a whole number of bytes a ValueError will be raised.

        """
        if self._itemsize % 8 != 0:
            raise ValueError(
                f"byteswap can only be used for whole-byte elements. The '{self._fmt}' format is {self._itemsize} bits long.")
        self.data.byteswap(self.itemsize // 8)

    def count(self, value: ElementType) -> int:
        """Return count of Array items that equal value.

        value -- The quantity to compare each Array element to. Type should be appropriate for the Array format.

        """
        return sum(i == value for i in self)

    def tobytes(self) -> bytes:
        """Return the Array data as a bytes object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        return self.data.tobytes()

    def tofile(self, f: BinaryIO) -> None:
        """Write the Array data to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        self.data.tofile(f)

    def fromfile(self, f: BinaryIO, n: Optional[int] = None) -> None:
        trailing_bit_length = len(self.data) % self._itemsize
        if trailing_bit_length != 0:
            raise ValueError(f"Cannot extend Array as its length is not a multiple of the format length.")

        new_data = Bits(f)
        max_items = len(new_data) // self._itemsize
        items_to_append = max_items if n is None else min(n, max_items)
        self.data += new_data[0: items_to_append * self._itemsize]
        if n is not None and items_to_append < n:
            raise EOFError(f"Only {items_to_append} were appended, not the {n} items requested.")

    def reverse(self) -> None:
        trailing_bit_length = len(self.data) % self._itemsize
        if trailing_bit_length != 0:
            raise ValueError(
                f"Cannot reverse the items in the Array as its length is not a multiple of the format length.")
        for start_bit in range(0, len(self.data) // 2, self._itemsize):
            start_swap_bit = len(self.data) - start_bit - self._itemsize
            temp = self.data[start_bit: start_bit + self._itemsize]
            self.data[start_bit: start_bit + self._itemsize] = self.data[
                                                               start_swap_bit: start_swap_bit + self._itemsize]
            self.data[start_swap_bit: start_swap_bit + self._itemsize] = temp

    def pp(self, fmt: Optional[str] = None, width: int = 120, sep: str = ' ',
           show_offset: bool = True, stream: TextIO = sys.stdout) -> None:
        """Pretty-print the Array contents.

        fmt -- Printed data format. Not yet supported! Defaults to either hex or bin.
        width -- Max width of printed lines. Defaults to 120. A single group will always be printed
                 per line even if it exceeds the max width.
        sep -- A separator string to insert between groups. Defaults to a single space.
        show_offset -- If True (the default) shows the element offset in the first column of each line.
        stream -- A TextIO object with a write() method. Defaults to sys.stdout.

        """
        trailing_bit_length = len(self.data) % self._itemsize
        # fmt is not yet supported
        name1 = 'hex' if self._itemsize % 4 == 0 else 'bin'
        format_sep = "   "  # String to insert on each line between multiple formats

        if trailing_bit_length == 0:
            data = self.data
        else:
            data = self.data[0: -trailing_bit_length]
        data._pp(name1, None, self._itemsize, width, sep, format_sep, show_offset, stream, False, self._itemsize)
        if trailing_bit_length != 0:
            stream.write(" + trailing_bits = " + str(self.data[-trailing_bit_length:]) + '\n')

    def __eq__(self, other: Any) -> bool:
        """Return True if format and all Array items are equal."""
        if isinstance(other, Array):
            if self._itemsize != other._itemsize:
                return False
            if self._token_name != other._token_name:
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
            if self.tolist() != other.tolist():
                return False
            return True
        return False

    def __iter__(self) -> Iterable[ElementType]:
        start = 0
        for i in range(len(self)):
            yield self._getter_func(self.data, start=start)
            start += self._itemsize

    def __copy__(self) -> Array:
        a_copy = Array(fmt=self._fmt)
        a_copy.data = copy.copy(self.data)
        return a_copy

    def _apply_op_to_all_elements(self, op, value: Union[int, float]) -> Array:
        """Apply op with value to each element of the Array and return a new Array"""
        return self[:]._apply_op_to_all_elements_inplace(op, value)

    def _apply_op_to_all_elements_inplace(self, op, value: Union[int, float]) -> Array:
        """Apply op with value to each element of the Array in place."""
        # This isn't really being done in-place, but it's simpler and faster for now?
        new_data = BitArray()
        failures = 0
        for i in range(len(self)):
            v = self._getter_func(self.data, start=self._itemsize * i)
            try:
                new_data.append(self._create_element(op(v, value)))
            except CreationError as e:
                if failures == 0:
                    msg = e.msg
                    index = i
                failures += 1
        if failures != 0:
            raise ValueError(f'Applying operator \'{op.__name__}\' to Array caused {failures} errors. '
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
        if len(value) != self._itemsize:
            raise ValueError(f"Bitwise op needs a bitstring of length {self._itemsize} to match format {self._fmt}.")
        for start in range(0, len(self) * self._itemsize, self._itemsize):
            self.data[start: start + self._itemsize] = op(self.data[start: start + self._itemsize], value)
        return self

    def __add__(self, other: Union[Array, array.array, Iterable, int, float]) -> Array:
        """Either extend the Array with an iterable or other Array, or add int or float to all elements."""
        if isinstance(other, (int, float)):
            return self._apply_op_to_all_elements(operator.add, other)
        if len(self.data) % self._itemsize != 0:
            raise ValueError(f"Cannot extend Array as its length is not a multiple of the format length.")
        new_array = copy.copy(self)
        if isinstance(other, Array):
            if self._token_name != other._token_name or self._itemsize != other._itemsize:
                raise ValueError(f"Cannot add an Array with format '{other._fmt}' to an Array with format '{self._fmt}'.")
            new_array.data += other.data
        elif isinstance(other, array.array):
            other_fmt = Array._array_typecodes.get(other.typecode, other.typecode)
            token_name, token_length, _ = tokenparser(other_fmt)[1][0]
            if self._token_name != token_name or self._itemsize != token_length:
                raise ValueError(
                    f"Cannot add an array with typecode '{other.typecode}' to an Array with format '{self._fmt}'.")
            new_array.data += other.tobytes()
        else:
            new_array.extend(other)
        return new_array

    def __radd__(self, other: Union[array.array, Iterable]) -> Array:
        # We know that the LHS can't be an Array otherwise __add__ would be used.
        if isinstance(other, array.array):
            other_fmt = Array._array_typecodes.get(other.typecode, other.typecode)
            token_name, token_length, _ = tokenparser(other_fmt)[1][0]
            if self._token_name != token_name or self._itemsize != token_length:
                raise ValueError(
                    f"Cannot add an array.array with typecode '{other.typecode}' to an Array with format '{self._fmt}'.")
            new_array = Array(self.fmt, other.tobytes())
            new_array.data.append(self.data)
            return new_array
        else:
            new_array = Array(self.fmt)
            new_array.extend(other)
            new_array.data.append(self.data)
            return new_array

    def __iadd__(self, other: Union[Array, array.array, Iterable, int, float]) -> Array:
        if isinstance(other, (int, float)):
            return self._apply_op_to_all_elements_inplace(operator.add, other)
        else:
            self.extend(other)
            return self

    def __isub__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements_inplace(operator.sub, other)

    def __sub__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements(operator.sub, other)

    def __mul__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements(operator.mul, other)

    def __imul__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements_inplace(operator.mul, other)

    def __floordiv__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements(operator.floordiv, other)

    def __ifloordiv__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements_inplace(operator.floordiv, other)

    def __truediv__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements(operator.truediv, other)

    def __itruediv__(self, other: Union[int, float]) -> Array:
        return self._apply_op_to_all_elements_inplace(operator.truediv, other)

    def __rshift__(self, other: int) -> Array:
        return self._apply_op_to_all_elements(operator.rshift, other)

    def __lshift__(self, other: int) -> Array:
        return self._apply_op_to_all_elements(operator.lshift, other)

    def __irshift__(self, other: int) -> Array:
        return self._apply_op_to_all_elements_inplace(operator.rshift, other)

    def __ilshift__(self, other: int) -> Array:
        return self._apply_op_to_all_elements_inplace(operator.lshift, other)

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
