from __future__ import annotations

import numbers
import pathlib
import sys
import re
import mmap
import struct
import array
import io
from collections import abc
import functools
from typing import Tuple, Union, List, Iterable, Any, Optional, Pattern, Dict, \
    BinaryIO, TextIO, Callable, overload, Iterator, Type, TypeVar
import bitarray
import bitarray.util
from bitstring.utils import tokenparser
from bitstring.exceptions import CreationError, InterpretError, ReadError, Error
from bitstring.fp8 import e4m3float_fmt, e5m2float_fmt
from bitstring.bitstore import BitStore, offset_slice_indices_lsb0
from bitstring.bitstore_helpers import float2bitstore, uint2bitstore, ue2bitstore, str_to_bitstore, se2bitstore, \
    bfloat2bitstore, floatle2bitstore, uintbe2bitstore, uintle2bitstore, intbe2bitstore, intle2bitstore, bfloatle2bitstore, \
    bin2bitstore, bin2bitstore_unsafe, hex2bitstore, int2bitstore, oct2bitstore, sie2bitstore, uie2bitstore

# Things that can be converted to Bits when a Bits type is needed
BitsType = Union['Bits', str, Iterable[Any], bool, BinaryIO, bytearray, bytes, memoryview, bitarray.bitarray]

TBits = TypeVar("TBits", bound='Bits')

byteorder: str = sys.byteorder

# Maximum number of digits to use in __str__ and __repr__.
MAX_CHARS: int = 250


class Bits:
    """A container holding an immutable sequence of bits.

    For a mutable container use the BitArray class instead.

    Methods:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    copy() - Return a copy of the bitstring.
    count() -- Count the number of bits set to 1 or 0.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurrences of a sub-bitstring in the current bitstring.
    join() -- Join bitstrings together using current bitstring.
    pp() -- Pretty print the bitstring.
    rfind() -- Seek backwards to find a sub-bitstring.
    split() -- Create generator of chunks split by a delimiter.
    startswith() -- Return whether the bitstring starts with a sub-bitstring.
    tobitarray() -- Return bitstring as a bitarray from the bitarray package.
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Special methods:

    Also available are the operators [], ==, !=, +, *, ~, <<, >>, &, |, ^.

    Properties:

    bin -- The bitstring as a binary string.
    hex -- The bitstring as a hexadecimal string.
    oct -- The bitstring as an octal string.
    bytes -- The bitstring as a bytes object.
    int -- Interpret as a two's complement signed integer.
    uint -- Interpret as a two's complement unsigned integer.
    float / floatbe -- Interpret as a big-endian floating point number.
    bool -- For single bit bitstrings, interpret as True or False.
    se -- Interpret as a signed exponential-Golomb code.
    ue -- Interpret as an unsigned exponential-Golomb code.
    sie -- Interpret as a signed interleaved exponential-Golomb code.
    uie -- Interpret as an unsigned interleaved exponential-Golomb code.
    floatle -- Interpret as a little-endian floating point number.
    floatne -- Interpret as a native-endian floating point number.
    bfloat / bfloatbe -- Interpret as a big-endian 16-bit bfloat type.
    bfloatle -- Interpret as a little-endian 16-bit bfloat type.
    bfloatne -- Interpret as a native-endian 16-bit bfloat type.
    intbe -- Interpret as a big-endian signed integer.
    intle -- Interpret as a little-endian signed integer.
    intne -- Interpret as a native-endian signed integer.
    uintbe -- Interpret as a big-endian unsigned integer.
    uintle -- Interpret as a little-endian unsigned integer.
    uintne -- Interpret as a native-endian unsigned integer.

    len -- Length of the bitstring in bits.

    """

    __slots__ = ('_bitstore')

    _options = None
    _register = None

    @classmethod
    def _initialise_options(cls):
        # To avoid circular imports this happens after all the classes are initialised.
        from .options import Options
        cls._options = Options()
        from .dtypes import Register
        cls._register = Register()

    # Creates dictionaries to quickly reverse single bytes
    _int8ReversalDict: Dict[int, int] = {i: int("{0:08b}".format(i)[::-1], 2) for i in range(0x100)}
    _byteReversalDict: Dict[int, bytes] = {i: bytes([int("{0:08b}".format(i)[::-1], 2)]) for i in range(0x100)}

    def __init__(self, __auto: Optional[Union[BitsType, int]] = None, length: Optional[int] = None,
                 offset: Optional[int] = None, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        A string of comma separated tokens, an integer, a file object,
        a bytearray, a boolean iterable, an array or another bitstring.

        Or initialise via **kwargs with one (and only one) of:
        bin -- binary string representation, e.g. '0b001010'.
        hex -- hexadecimal string representation, e.g. '0x2ef'
        oct -- octal string representation, e.g. '0o777'.
        bytes -- raw data as a bytes object, for example read from a binary file.
        int -- a signed integer.
        uint -- an unsigned integer.
        float / floatbe -- a big-endian floating point number.
        bool -- a boolean (True or False).
        se -- a signed exponential-Golomb code.
        ue -- an unsigned exponential-Golomb code.
        sie -- a signed interleaved exponential-Golomb code.
        uie -- an unsigned interleaved exponential-Golomb code.
        floatle -- a little-endian floating point number.
        floatne -- a native-endian floating point number.
        bfloat / bfloatbe - a big-endian bfloat format 16-bit floating point number.
        bfloatle -- a little-endian bfloat format 16-bit floating point number.
        bfloatne -- a native-endian bfloat format 16-bit floating point number.
        intbe -- a signed big-endian whole byte integer.
        intle -- a signed little-endian whole byte integer.
        intne -- a signed native-endian whole byte integer.
        uintbe -- an unsigned big-endian whole byte integer.
        uintle -- an unsigned little-endian whole byte integer.
        uintne -- an unsigned native-endian whole byte integer.
        filename -- the path of a file which will be opened in binary read-only mode.

        Other keyword arguments:
        length -- length of the bitstring in bits, if needed and appropriate.
                  It must be supplied for all integer and float initialisers.
        offset -- bit offset to the data. These offset bits are
                  ignored and this is mainly intended for use when
                  initialising using 'bytes' or 'filename'.

        """
        self._bitstore.immutable = True

    def __new__(cls: Type[TBits], __auto: Optional[Union[BitsType, int]] = None, length: Optional[int] = None,
                offset: Optional[int] = None, pos: Optional[int] = None, **kwargs) -> TBits:
        x = object.__new__(cls)
        if __auto is None and not kwargs:
            # No initialiser so fill with zero bits up to length
            if length is not None:
                x._bitstore = BitStore(length)
                x._bitstore.setall(0)
            else:
                x._bitstore = BitStore()
            return x
        x._initialise(__auto, length, offset, **kwargs)
        return x

    @classmethod
    def _create_empty_instance(cls):
        x = object.__new__(cls)
        x._bitstore = BitStore._create_empty_instance()
        return x

    @classmethod
    def _create_from_bitstype(cls: Type[TBits], auto: Optional[BitsType]) -> TBits:
        b = cls._create_empty_instance()
        if auto is None:
            return b
        b._setauto(auto, None, None)
        return b

    def _initialise(self, __auto: Any, length: Optional[int], offset: Optional[int], **kwargs) -> None:
        if length is not None and length < 0:
            raise CreationError("bitstring length cannot be negative.")
        if offset is not None and offset < 0:
            raise CreationError("offset must be >= 0.")
        if __auto is not None:
            if isinstance(__auto, numbers.Integral):
                # Initialise with s zero bits.
                if __auto < 0:
                    raise CreationError(f"Can't create bitstring of negative length {__auto}.")
                self._bitstore = BitStore(int(__auto))
                self._bitstore.setall(0)
                return
            self._setauto(__auto, length, offset)
            return
        k, v = kwargs.popitem()
        try:
            setting_function = Bits._register.name_to_meta_dtype[k].set_fn
        except KeyError:
            if k == 'filename':
                setting_function = Bits._setfile
            elif k == 'bitarray':
                setting_function = Bits._setbitarray
            elif k == 'auto':
                raise CreationError(f"The 'auto' parameter should not be given explicitly - just use the first positional argument. "
                                    f"Instead of '{self.__class__.__name__}(auto=x)' use '{self.__class__.__name__}(x)'.")
            else:
                raise CreationError(f"Unrecognised keyword '{k}' used to initialise.")
        setting_function(self, v, length, offset)

    def __getattr__(self, attribute: str) -> Any:
        # Support for arbitrary attributes like u16 or f64.
        # Try to split into [name][length], then try standard properties
        name_length_pattern: Pattern[str] = re.compile(r'^(?P<name>[a-z]+):?(?P<len>\d+)$', re.IGNORECASE)
        name_length = name_length_pattern.match(attribute)
        if name_length:
            name = name_length.group('name')
            length = int(name_length.group('len'))
            if name == 'bytes' and length is not None:
                length *= 8
            if length is not None and self.len != int(length):
                raise InterpretError(f"bitstring length {self.len} doesn't match length of property {attribute}.")
            try:
                return getattr(self, name)
            except AttributeError:
                pass
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{attribute}'.")

    def __iter__(self) -> Iterable[bool]:
        return iter(self._bitstore)

    def __copy__(self: TBits) -> TBits:
        """Return a new copy of the Bits for the copy module."""
        # Note that if you want a new copy (different ID), use _copy instead.
        # The copy can return self as it's immutable.
        return self

    def __lt__(self, other: Any) -> bool:
        # bitstrings can't really be ordered.
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        return NotImplemented

    def __add__(self: TBits, bs: BitsType) -> TBits:
        """Concatenate bitstrings and return new bitstring.

        bs -- the bitstring to append.

        """
        bs = self.__class__._create_from_bitstype(bs)
        if bs.len <= self.len:
            s = self._copy()
            s._addright(bs)
        else:
            s = bs._copy()
            s = self.__class__(s)
            s._addleft(self)
        return s

    def __radd__(self: TBits, bs: BitsType) -> TBits:
        """Append current bitstring to bs and return new bitstring.

        bs -- An object that can be 'auto' initialised as a bitstring that will be appended to.

        """
        bs = self.__class__._create_from_bitstype(bs)
        return bs.__add__(self)

    @overload
    def __getitem__(self: TBits, key: slice) -> TBits:
        ...

    @overload
    def __getitem__(self, key: int) -> bool:
        ...

    def __getitem__(self: TBits, key: Union[slice, int]) -> Union[TBits, bool]:
        """Return a new bitstring representing a slice of the current bitstring.

        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.

        >>> print(BitArray('0b00110')[1:4])
        '0b011'
        >>> print(BitArray('0x00112233')[1:3:8])
        '0x1122'

        """
        if isinstance(key, numbers.Integral):
            return bool(self._bitstore.getindex(key))
        x = self._bitstore.getslice(key)
        bs = self.__class__()
        bs._bitstore = x
        return bs

    def __len__(self) -> int:
        """Return the length of the bitstring in bits."""
        return self._getlength()

    def __bytes__(self) -> bytes:
        return self.tobytes()

    def __str__(self) -> str:
        """Return approximate string representation of bitstring for printing.

        Short strings will be given wholly in hexadecimal or binary. Longer
        strings may be part hexadecimal and part binary. Very long strings will
        be truncated with '...'.

        """
        length = self.len
        if not length:
            return ''
        if length > MAX_CHARS * 4:
            # Too long for hex. Truncate...
            return ''.join(('0x', self._readhex(0, MAX_CHARS * 4), '...'))
        # If it's quite short and we can't do hex then use bin
        if length < 32 and length % 4 != 0:
            return '0b' + self.bin
        # If we can use hex then do so
        if not length % 4:
            return '0x' + self.hex
        # Otherwise first we do as much as we can in hex
        # then add on 1, 2 or 3 bits on at the end
        bits_at_end = length % 4
        return ''.join(('0x', self._readhex(0, length - bits_at_end),
                        ', ', '0b',
                        self._readbin(length - bits_at_end, bits_at_end)))

    def _repr(self, classname: str, length: int, offset: int, filename: str, pos: int):
        pos_string = f', pos={pos}' if pos else ''
        if filename:
            offsetstring = f', offset={offset}' if offset else ''
            return f"{classname}(filename={repr(filename)}, length={length}{offsetstring}{pos_string})"
        else:
            s = self.__str__()
            lengthstring = ''
            if s.endswith('...'):
                lengthstring = f'  # length={length}'
            return f"{classname}('{s}'{pos_string}){lengthstring}"

    def __repr__(self) -> str:
        """Return representation that could be used to recreate the bitstring.

        If the returned string is too long it will be truncated. See __str__().

        """
        return self._repr(self.__class__.__name__, len(self), self._bitstore.offset, self._bitstore.filename, 0)

    def __eq__(self, bs: Any) -> bool:
        """Return True if two bitstrings have the same binary representation.

        >>> BitArray('0b1110') == '0xe'
        True

        """
        try:
            bs = Bits._create_from_bitstype(bs)
        except TypeError:
            return False
        return self._bitstore == bs._bitstore

    def __ne__(self, bs: Any) -> bool:
        """Return False if two bitstrings have the same binary representation.

        >>> BitArray('0b111') == '0x7'
        False

        """
        return not self.__eq__(bs)

    def __invert__(self: TBits) -> TBits:
        """Return bitstring with every bit inverted.

        Raises Error if the bitstring is empty.

        """
        if not self.len:
            raise Error("Cannot invert empty bitstring.")
        s = self._copy()
        s._invert_all()
        return s

    def __lshift__(self: TBits, n: int) -> TBits:
        """Return bitstring with bits shifted by n to the left.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        n = min(n, self.len)
        s = self._absolute_slice(n, self.len)
        s._addright(Bits(n))
        return s

    def __rshift__(self: TBits, n: int) -> TBits:
        """Return bitstring with bits shifted by n to the right.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        if not n:
            return self._copy()
        s = self.__class__(length=min(n, self.len))
        n = min(n, self.len)
        s._addright(self._absolute_slice(0, self.len - n))
        return s

    def __mul__(self: TBits, n: int) -> TBits:
        """Return bitstring consisting of n concatenations of self.

        Called for expression of the form 'a = b*3'.
        n -- The number of concatenations. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        if not n:
            return self.__class__()
        s = self._copy()
        s._imul(n)
        return s

    def __rmul__(self: TBits, n: int) -> TBits:
        """Return bitstring consisting of n concatenations of self.

        Called for expressions of the form 'a = 3*b'.
        n -- The number of concatenations. Must be >= 0.

        """
        return self.__mul__(n)

    def __and__(self: TBits, bs: BitsType) -> TBits:
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        bs = Bits._create_from_bitstype(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for & operator.")
        s = self._copy()
        s._bitstore &= bs._bitstore
        return s

    def __rand__(self: TBits, bs: BitsType) -> TBits:
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- the bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__and__(bs)

    def __or__(self: TBits, bs: BitsType) -> TBits:
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        bs = Bits._create_from_bitstype(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for | operator.")
        s = self._copy()
        s._bitstore |= bs._bitstore
        return s

    def __ror__(self: TBits, bs: BitsType) -> TBits:
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__or__(bs)

    def __xor__(self: TBits, bs: BitsType) -> TBits:
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        bs = Bits._create_from_bitstype(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for ^ operator.")
        s = self._copy()
        s._bitstore ^= bs._bitstore
        return s

    def __rxor__(self: TBits, bs: BitsType) -> TBits:
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__xor__(bs)

    def __contains__(self, bs: BitsType) -> bool:
        """Return whether bs is contained in the current bitstring.

        bs -- The bitstring to search for.

        """
        found = Bits.find(self, bs, bytealigned=False)
        return bool(found)

    def __hash__(self) -> int:
        """Return an integer hash of the object."""
        # Only requirement is that equal bitstring should return the same hash.
        # For equal bitstrings the bytes at the start/end will be the same and they will have the same length
        # (need to check the length as there could be zero padding when getting the bytes). We do not check any
        # bit position inside the bitstring as that does not feature in the __eq__ operation.
        if self.len <= 2000:
            # Use the whole bitstring.
            return hash((self.tobytes(), self.len))
        else:
            # We can't in general hash the whole bitstring (it could take hours!)
            # So instead take some bits from the start and end.
            return hash(((self[:800] + self[-800:]).tobytes(), self.len))

    def __bool__(self) -> bool:
        """Return True if any bits are set to 1, otherwise return False."""
        return len(self) != 0

    def _clear(self) -> None:
        """Reset the bitstring to an empty state."""
        self._bitstore = BitStore()

    def _setauto(self, s: BitsType, length: Optional[int], offset: Optional[int]) -> None:
        """Set bitstring from a bitstring, file, bool, array, iterable or string."""
        # As s can be so many different things it's important to do the checks
        # in the correct order, as some types are also other allowed types.
        # So str must be checked before Iterable
        # and bytes/bytearray before Iterable but after str!
        if offset is None:
            offset = 0
        if isinstance(s, Bits):
            if length is None:
                length = s._getlength() - offset
            self._bitstore = s._bitstore.getslice(slice(offset, offset + length, None))
            return

        if isinstance(s, io.BytesIO):
            if length is None:
                length = s.seek(0, 2) * 8 - offset
            byteoffset, offset = divmod(offset, 8)
            bytelength = (length + byteoffset * 8 + offset + 7) // 8 - byteoffset
            if length + byteoffset * 8 + offset > s.seek(0, 2) * 8:
                raise CreationError("BytesIO object is not long enough for specified length and offset.")
            self._bitstore = BitStore(frombytes=s.getvalue()[byteoffset: byteoffset + bytelength]).getslice(
                slice(offset, offset + length))
            return

        if isinstance(s, io.BufferedReader):
            m = mmap.mmap(s.fileno(), 0, access=mmap.ACCESS_READ)
            self._bitstore = BitStore(buffer=m, offset=offset, length=length, filename=s.name, immutable=True)
            return

        if isinstance(s, bitarray.bitarray):
            if length is None:
                if offset > len(s):
                    raise CreationError(f"Offset of {offset} too large for bitarray of length {len(s)}.")
                self._bitstore = BitStore(s[offset:])
            else:
                if offset + length > len(s):
                    raise CreationError(
                        f"Offset of {offset} and length of {length} too large for bitarray of length {len(s)}.")
                self._bitstore = BitStore(s[offset: offset + length])
            return

        if length is not None:
            raise CreationError("The length keyword isn't applicable to this initialiser.")
        if offset > 0:
            raise CreationError("The offset keyword isn't applicable to this initialiser.")
        if isinstance(s, str):
            self._bitstore = str_to_bitstore(s)
            return
        if isinstance(s, (bytes, bytearray, memoryview)):
            self._bitstore = BitStore(frombytes=bytearray(s))
            return
        if isinstance(s, array.array):
            self._bitstore = BitStore(frombytes=bytearray(s.tobytes()))
            return
        if isinstance(s, abc.Iterable):
            # Evaluate each item as True or False and set bits to 1 or 0.
            self._setbin_unsafe(''.join(str(int(bool(x))) for x in s))
            return
        if isinstance(s, numbers.Integral):
            raise TypeError(f"It's no longer possible to auto initialise a bitstring from an integer."
                            f" Use '{self.__class__.__name__}({s})' instead of just '{s}' as this makes it "
                            f"clearer that a bitstring of {int(s)} zero bits will be created.")
        raise TypeError(f"Cannot initialise bitstring from {type(s)}.")

    def _setfile(self, filename: str, length: Optional[int], offset: Optional[int]) -> None:
        """Use file as source of bits."""
        with open(pathlib.Path(filename), 'rb') as source:
            if offset is None:
                offset = 0
            m = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)
            self._bitstore = BitStore(buffer=m, offset=offset, length=length, filename=source.name, immutable=True)

    def _setbitarray(self, ba: bitarray.bitarray, length: Optional[int], offset: Optional[int]) -> None:
        if offset is None:
            offset = 0
        if offset > len(ba):
            raise CreationError(f"Offset of {offset} too large for bitarray of length {len(ba)}.")
        if length is None:
            self._bitstore = BitStore(ba[offset:])
        else:
            if offset + length > len(ba):
                raise CreationError(
                    f"Offset of {offset} and length of {length} too large for bitarray of length {len(ba)}.")
            self._bitstore = BitStore(ba[offset: offset + length])

    def _setbits(self, bs: BitsType, length: None = None, offset: None = None) -> None:
        bs = Bits._create_from_bitstype(bs)
        self._bitstore = bs._bitstore

    def _sete5m2float(self, f: float, length: None = None, _offset: None = None):
        u = e5m2float_fmt.float_to_int8(f)
        self._bitstore = uint2bitstore(u, 8)

    def _sete4m3float(self, f: float, length: None = None, _offset: None = None):
        u = e4m3float_fmt.float_to_int8(f)
        self._bitstore = uint2bitstore(u, 8)

    def _setbytes(self, data: Union[bytearray, bytes],
                  length: Optional[int] = None, offset: Optional[int] = None) -> None:
        """Set the data from a bytes or bytearray object."""
        if offset is None and length is None:
            self._bitstore = BitStore(frombytes=bytearray(data))
            return
        data = bytearray(data)
        if offset is None:
            offset = 0
        if length is None:
            # Use to the end of the data
            length = len(data) * 8 - offset
        else:
            if length + offset > len(data) * 8:
                raise CreationError(f"Not enough data present. Need {length + offset} bits, have {len(data) * 8}.")
        self._bitstore = BitStore(buffer=data).getslice_msb0(slice(offset, offset + length, None))

    def _readbytes(self, start: int, length: int) -> bytes:
        """Read bytes and return them. Note that length is in bits."""
        assert length % 8 == 0
        assert start + length <= self.len
        return self._bitstore.getslice(slice(start, start + length, None)).tobytes()

    def _getbytes(self) -> bytes:
        """Return the data as an ordinary bytes object."""
        if self.len % 8:
            raise InterpretError("Cannot interpret as bytes unambiguously - not multiple of 8 bits.")
        return self._readbytes(0, self.len)

    _unprintable = list(range(0x00, 0x20))  # ASCII control characters
    _unprintable.extend(range(0x7f, 0xff))  # DEL char + non-ASCII

    def _getbytes_printable(self) -> str:
        """Return an approximation of the data as a string of printable characters."""
        bytes_ = self._getbytes()
        # For everything that isn't printable ASCII, use value from 'Latin Extended-A' unicode block.
        string = ''.join(chr(0x100 + x) if x in Bits._unprintable else chr(x) for x in bytes_)
        return string

    def _setuint(self, uint: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Reset the bitstring to have given unsigned int interpretation."""
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a uint initialiser.")
        if _offset is not None:
            raise CreationError("An offset can't be specified with an integer initialiser.")
        self._bitstore = uint2bitstore(uint, length)

    def _readuint(self, start: int, length: int) -> int:
        """Read bits and interpret as an unsigned int."""
        if length == 0:
            raise InterpretError("Cannot interpret a zero length bitstring as an integer.")
        ip = bitarray.util.ba2int(self._bitstore.getslice(slice(start, start + length, None)), signed=False)
        return ip

    def _getuint(self) -> int:
        """Return data as an unsigned int."""
        if self.len == 0:
            raise InterpretError("Cannot interpret a zero length bitstring as an integer.")
        bs = self._bitstore.copy() if self._bitstore.modified else self._bitstore
        return bitarray.util.ba2int(bs, signed=False)

    def _setint(self, int_: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Reset the bitstring to have given signed int interpretation."""
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with an int initialiser.")
        if _offset is not None:
            raise CreationError("An offset can't be specified with an integer initialiser.")
        self._bitstore = int2bitstore(int_, length)

    def _readint(self, start: int, length: int) -> int:
        """Read bits and interpret as a signed int"""
        if length == 0:
            raise InterpretError("Cannot interpret bitstring without a length as an integer.")
        ip = bitarray.util.ba2int(self._bitstore.getslice(slice(start, start + length, None)), signed=True)
        return ip

    def _getint(self) -> int:
        """Return data as a two's complement signed int."""
        if self.len == 0:
            raise InterpretError("Cannot interpret bitstring without a length as an integer.")
        bs = self._bitstore.copy() if self._bitstore.modified else self._bitstore
        return bitarray.util.ba2int(bs, signed=True)

    def _setuintbe(self, uintbe: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Set the bitstring to a big-endian unsigned int interpretation."""
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a uintbe initialiser.")
        self._bitstore = uintbe2bitstore(uintbe, length)

    def _readuintbe(self, start: int, length: int) -> int:
        """Read bits and interpret as a big-endian unsigned int."""
        if length % 8:
            raise InterpretError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
        return self._readuint(start, length)

    def _getuintbe(self) -> int:
        """Return data as a big-endian two's complement unsigned int."""
        return self._readuintbe(0, self.len)

    def _setintbe(self, intbe: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Set bitstring to a big-endian signed int interpretation."""
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a intbe initialiser.")
        self._bitstore = intbe2bitstore(intbe, length)

    def _readintbe(self, start: int, length: int) -> int:
        """Read bits and interpret as a big-endian signed int."""
        if length % 8:
            raise InterpretError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
        return self._readint(start, length)

    def _getintbe(self) -> int:
        """Return data as a big-endian two's complement signed int."""
        return self._readintbe(0, self.len)

    def _setuintle(self, uintle: int, length: Optional[int] = None, _offset: None = None) -> None:
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a uintle initialiser.")
        if _offset is not None:
            raise CreationError("An offset can't be specified with an integer initialiser.")
        self._bitstore = uintle2bitstore(uintle, length)

    def _readuintle(self, start: int, length: int) -> int:
        """Read bits and interpret as a little-endian unsigned int."""
        if length % 8:
            raise InterpretError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
        bs = BitStore(frombytes=self._bitstore.getslice(slice(start, start + length, None)).tobytes()[::-1])
        val = bitarray.util.ba2int(bs, signed=False)
        return val

    def _getuintle(self) -> int:
        return self._readuintle(0, self.len)

    def _setintle(self, intle: int, length: Optional[int] = None, _offset: None = None) -> None:
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with an intle initialiser.")
        if _offset is not None:
            raise CreationError("An offset can't be specified with an integer initialiser.")
        self._bitstore = intle2bitstore(intle, length)

    def _readintle(self, start: int, length: int) -> int:
        """Read bits and interpret as a little-endian signed int."""
        if length % 8:
            raise InterpretError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
        bs = BitStore(frombytes=self._bitstore.getslice(slice(start, start + length, None)).tobytes()[::-1])
        val = bitarray.util.ba2int(bs, signed=True)
        return val

    def _getintle(self) -> int:
        return self._readintle(0, self.len)

    def _readfloat(self, start: int, length: int, struct_dict: Dict[int, str]) -> float:
        """Read bits and interpret as a float."""
        try:
            fmt = struct_dict[length]
        except KeyError:
            raise InterpretError(f"Floats can only be 16, 32 or 64 bits long, not {length} bits")

        offset = start % 8
        if offset == 0:
            return struct.unpack(fmt, self._bitstore.getslice(slice(start, start + length, None)).tobytes())[0]
        else:
            return struct.unpack(fmt, self._readbytes(start, length))[0]

    def _reade4m3float(self, start: int, length: int = 0) -> float:
        # length is ignored - it's only present to make the function signature consistent.
        u = self._readuint(start, length=8)
        return e4m3float_fmt.lut_int8_to_float[u]

    def _gete4m3float(self) -> float:
        if len(self) != 8:
            raise InterpretError(f"A e4m3float must be 8 bits long, not {len(self)} bits.")
        return self._reade4m3float(0)

    def _reade5m2float(self, start: int, length: int = 0) -> float:
        # length is ignored - it's only present to make the function signature consistent.
        u = self._readuint(start, length=8)
        return e5m2float_fmt.lut_int8_to_float[u]

    def _gete5m2float(self) -> float:
        if len(self) != 8:
            raise InterpretError(f"A e5m2float must be 8 bits long, not {len(self)} bits.")
        return self._reade5m2float(start=0)

    def _setfloatbe(self, f: float, length: Optional[int] = None, _offset: None = None) -> None:
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length not in [16, 32, 64]:
            raise CreationError("A length of 16, 32, or 64 must be specified with a float initialiser.")
        self._bitstore = float2bitstore(f, length)

    def _readfloatbe(self, start: int, length: int) -> float:
        """Read bits and interpret as a big-endian float."""
        return self._readfloat(start, length, {16: '>e', 32: '>f', 64: '>d'})

    def _getfloatbe(self) -> float:
        """Interpret the whole bitstring as a big-endian float."""
        return self._readfloatbe(0, self.len)

    def _setfloatle(self, f: float, length: Optional[int] = None, _offset: None = None) -> None:
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length not in [16, 32, 64]:
            raise CreationError("A length of 16, 32, or 64 must be specified with a float initialiser.")
        self._bitstore = floatle2bitstore(f, length)

    def _readfloatle(self, start: int, length: int) -> float:
        """Read bits and interpret as a little-endian float."""
        return self._readfloat(start, length, {16: '<e', 32: '<f', 64: '<d'})

    def _getfloatle(self) -> float:
        """Interpret the whole bitstring as a little-endian float."""
        return self._readfloatle(0, self.len)

    def _getbfloatbe(self) -> float:
        return self._readbfloatbe(0, self.len)

    def _readbfloatbe(self, start: int, length: int) -> float:
        if length != 16:
            raise InterpretError(f"bfloats must be length 16, received a length of {length} bits.")
        two_bytes = self._slice(start, start + 16)
        zero_padded = two_bytes + Bits(16)
        return zero_padded._getfloatbe()

    def _setbfloatbe(self, f: Union[float, str], length: Optional[int] = None, _offset: None = None) -> None:
        if length is not None and length != 16:
            raise CreationError(f"bfloats must be length 16, received a length of {length} bits.")
        self._bitstore = bfloat2bitstore(f)

    def _getbfloatle(self) -> float:
        return self._readbfloatle(0, self.len)

    def _readbfloatle(self, start: int, length: int) -> float:
        two_bytes = self._slice(start, start + 16)
        zero_padded = Bits(16) + two_bytes
        return zero_padded._getfloatle()

    def _setbfloatle(self, f: Union[float, str], length: Optional[int] = None, _offset: None = None) -> None:
        if length is not None and length != 16:
            raise CreationError(f"bfloats must be length 16, received a length of {length} bits.")
        self._bitstore = bfloatle2bitstore(f)

    def _setue(self, i: int, _length: None = None, _offset: None = None) -> None:
        """Initialise bitstring with unsigned exponential-Golomb code for integer i.

        Raises CreationError if i < 0.

        """
        if _length is not None or _offset is not None:
            raise CreationError("Cannot specify a length of offset for exponential-Golomb codes.")
        if Bits._options.lsb0:
            raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
        self._bitstore = ue2bitstore(i)

    def _readue(self, pos: int, length: int = 0) -> Tuple[int, int]:
        """Return interpretation of next bits as unsigned exponential-Golomb code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        # _length is ignored - it's only present to make the function signature consistent.
        if Bits._options.lsb0:
            raise ReadError("Exp-Golomb codes cannot be read in lsb0 mode.")
        oldpos = pos
        try:
            while not self[pos]:
                pos += 1
        except IndexError:
            raise ReadError("Read off end of bitstring trying to read code.")
        leadingzeros = pos - oldpos
        codenum = (1 << leadingzeros) - 1
        if leadingzeros > 0:
            if pos + leadingzeros + 1 > self.len:
                raise ReadError("Read off end of bitstring trying to read code.")
            codenum += self._readuint(pos + 1, leadingzeros)
            pos += leadingzeros + 1
        else:
            assert codenum == 0
            pos += 1
        return codenum, pos

    def _getue(self) -> int:
        """Return data as unsigned exponential-Golomb code.

        Raises InterpretError if bitstring is not a single exponential-Golomb code.

        """
        try:
            value, newpos = self._readue(0)
            if value is None or newpos != self.len:
                raise ReadError
        except ReadError:
            raise InterpretError("Bitstring is not a single exponential-Golomb code.")
        return value

    def _setse(self, i: int, _length: None = None, _offset: None = None) -> None:
        """Initialise bitstring with signed exponential-Golomb code for integer i."""
        if _length is not None or _offset is not None:
            raise CreationError("Cannot specify a length of offset for exponential-Golomb codes.")
        if Bits._options.lsb0:
            raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
        self._bitstore = se2bitstore(i)

    def _getse(self) -> int:
        """Return data as signed exponential-Golomb code.

        Raises InterpretError if bitstring is not a single exponential-Golomb code.

        """
        try:
            value, newpos = self._readse(0)
            if value is None or newpos != self.len:
                raise ReadError
        except ReadError:
            raise InterpretError("Bitstring is not a single exponential-Golomb code.")
        return value

    def _readse(self, pos: int, length: int = 0) -> Tuple[int, int]:
        """Return interpretation of next bits as a signed exponential-Golomb code.

        Advances position to after the read code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        codenum, pos = self._readue(pos)
        m = (codenum + 1) // 2
        if not codenum % 2:
            return -m, pos
        else:
            return m, pos

    def _setuie(self, i: int, _length: None = None, _offset: None = None) -> None:
        """Initialise bitstring with unsigned interleaved exponential-Golomb code for integer i.

        Raises CreationError if i < 0.

        """
        if _length is not None or _offset is not None:
            raise CreationError("Cannot specify a length of offset for exponential-Golomb codes.")
        if Bits._options.lsb0:
            raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
        self._bitstore = uie2bitstore(i)

    def _readuie(self, pos: int, length: int = 0) -> Tuple[int, int]:
        """Return interpretation of next bits as unsigned interleaved exponential-Golomb code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        # _length is ignored - it's only present to make the function signature consistent.
        if Bits._options.lsb0:
            raise ReadError("Exp-Golomb codes cannot be read in lsb0 mode.")
        try:
            codenum: int = 1
            while not self[pos]:
                pos += 1
                codenum <<= 1
                codenum += self[pos]
                pos += 1
            pos += 1
        except IndexError:
            raise ReadError("Read off end of bitstring trying to read code.")
        codenum -= 1
        return codenum, pos

    def _getuie(self) -> int:
        """Return data as unsigned interleaved exponential-Golomb code.

        Raises InterpretError if bitstring is not a single exponential-Golomb code.

        """
        try:
            value, newpos = self._readuie(0)
            if value is None or newpos != self.len:
                raise ReadError
        except ReadError:
            raise InterpretError("Bitstring is not a single interleaved exponential-Golomb code.")
        return value

    def _setsie(self, i: int, length: None = None, _offset: None = None) -> None:
        """Initialise bitstring with signed interleaved exponential-Golomb code for integer i."""
        if length is not None or _offset is not None:
            raise CreationError("Cannot specify a length of offset for exponential-Golomb codes.")
        if Bits._options.lsb0:
            raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
        self._bitstore = sie2bitstore(i)

    def _getsie(self) -> int:
        """Return data as signed interleaved exponential-Golomb code.

        Raises InterpretError if bitstring is not a single exponential-Golomb code.

        """
        try:
            value, newpos = self._readsie(0)
            if value is None or newpos != self.len:
                raise ReadError
        except ReadError:
            raise InterpretError("Bitstring is not a single interleaved exponential-Golomb code.")
        return value

    def _readsie(self, pos: int, length: int = 0) -> Tuple[int, int]:
        """Return interpretation of next bits as a signed interleaved exponential-Golomb code.

        Advances position to after the read code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        codenum, pos = self._readuie(pos)
        if not codenum:
            return 0, pos
        try:
            if self[pos]:
                return -codenum, pos + 1
            else:
                return codenum, pos + 1
        except IndexError:
            raise ReadError("Read off end of bitstring trying to read code.")

    def _setbool(self, value: Union[bool, str], length: Optional[int] = None, _offset: None = None) -> None:
        # We deliberately don't want to have implicit conversions to bool here.
        # If we did then it would be difficult to deal with the 'False' string.
        if length is not None and length != 1:
            raise CreationError(f"bools must be length 1, received a length of {length} bits.")
        if value in (1, 'True'):
            self._bitstore = BitStore('1')
        elif value in (0, 'False'):
            self._bitstore = BitStore('0')
        else:
            raise CreationError(f"Cannot initialise boolean with {value}.")

    def _getbool(self) -> bool:
        if self.length != 1:
            raise InterpretError(f"For a bool interpretation a bitstring must be 1 bit long, not {self.length} bits.")
        return self[0]

    def _readbool(self, start: int, length: int = 0) -> int:
        # length is ignored - it's only present to make the function signature consistent.
        return self[start]

    def _readpad(self, pos, length) -> None:
        return None

    def _setbin_safe(self, binstring: str, length: None = None, _offset: None = None) -> None:
        """Reset the bitstring to the value given in binstring."""
        self._bitstore = bin2bitstore(binstring)

    def _setbin_unsafe(self, binstring: str, length: None = None, _offset: None = None) -> None:
        """Same as _setbin_safe, but input isn't sanity checked. binstring mustn't start with '0b'."""
        self._bitstore = bin2bitstore_unsafe(binstring)

    def _readbin(self, start: int, length: int) -> str:
        """Read bits and interpret as a binary string."""
        if length == 0:
            return ''
        return self._bitstore.getslice(slice(start, start + length, None)).to01()

    def _getbin(self) -> str:
        """Return interpretation as a binary string."""
        return self._readbin(0, self.len)

    def _setoct(self, octstring: str, length: None = None, _offset: None = None) -> None:
        """Reset the bitstring to have the value given in octstring."""
        self._bitstore = oct2bitstore(octstring)

    def _readoct(self, start: int, length: int) -> str:
        """Read bits and interpret as an octal string."""
        if length % 3:
            raise InterpretError("Cannot convert to octal unambiguously - not multiple of 3 bits long.")
        s = bitarray.util.ba2base(8, self._bitstore.getslice(slice(start, start + length, None)))
        return s

    def _getoct(self) -> str:
        """Return interpretation as an octal string."""
        if self.len % 3:
            raise InterpretError("Cannot convert to octal unambiguously - not multiple of 3 bits long.")
        ba = self._bitstore.copy() if self._bitstore.modified else self._bitstore
        return bitarray.util.ba2base(8, ba)

    def _sethex(self, hexstring: str, length: None = None, _offset: None = None) -> None:
        """Reset the bitstring to have the value given in hexstring."""
        self._bitstore = hex2bitstore(hexstring)

    def _readhex(self, start: int, length: int) -> str:
        """Read bits and interpret as a hex string."""
        if length % 4:
            raise InterpretError("Cannot convert to hex unambiguously - not a multiple of 4 bits long.")
        return bitarray.util.ba2hex(self._bitstore.getslice(slice(start, start + length, None)))

    def _gethex(self) -> str:
        """Return the hexadecimal representation as a string.

        Raises an InterpretError if the bitstring's length is not a multiple of 4.

        """
        if self.len % 4:
            raise InterpretError("Cannot convert to hex unambiguously - not a multiple of 4 bits long.")
        ba = self._bitstore.copy() if self._bitstore.modified else self._bitstore
        return bitarray.util.ba2hex(ba)

    def _getlength(self) -> int:
        """Return the length of the bitstring in bits."""
        return len(self._bitstore)

    def _copy(self: TBits) -> TBits:
        """Create and return a new copy of the Bits (always in memory)."""
        # Note that __copy__ may choose to return self if it's immutable. This method always makes a copy.
        s_copy = self.__class__()
        s_copy._bitstore = self._bitstore.copy()
        return s_copy

    def _slice(self: TBits, start: int, end: int) -> TBits:
        """Used internally to get a slice, without error checking."""
        bs = self.__class__()
        bs._bitstore = self._bitstore.getslice(slice(start, end, None))
        return bs

    def _absolute_slice(self: TBits, start: int, end: int) -> TBits:
        """Used internally to get a slice, without error checking.
        Uses MSB0 bit numbering even if LSB0 is set."""
        if end == start:
            return self.__class__()
        assert start < end, f"start={start}, end={end}"
        bs = self.__class__()
        bs._bitstore = self._bitstore.getslice_msb0(slice(start, end, None))
        return bs

    def _readtoken(self, name: str, pos: int, length: Optional[int]) -> Tuple[Union[float, int, str, None, Bits], int]:
        """Reads a token from the bitstring and returns the result."""
        if length is not None and length > self.length - pos:
            raise ReadError("Reading off the end of the data. "
                            f"Tried to read {length} bits when only {self.length - pos} available.")
        if length is None:
            meta_type = Bits._register.name_to_meta_dtype[name]
            if not meta_type.is_fixed_length and not meta_type.is_unknown_length:
                length = len(self) - pos
        dtype = Bits._register.get_dtype(name, length)
        try:
            val = dtype.read_fn(self, pos)
            if isinstance(val, tuple):
                return val
            else:
                assert length is not None
                return val, pos + length
        except KeyError:
            raise ValueError(f"Can't parse token {name}:{length}")

    def _addright(self, bs: Bits) -> None:
        """Add a bitstring to the RHS of the current bitstring."""
        self._bitstore += bs._bitstore

    def _addleft(self, bs: Bits) -> None:
        """Prepend a bitstring to the current bitstring."""
        if bs._bitstore.immutable:
            self._bitstore = bs._bitstore.copy() + self._bitstore
        else:
            self._bitstore = bs._bitstore + self._bitstore

    def _truncateleft(self: TBits, bits: int) -> TBits:
        """Truncate bits from the start of the bitstring. Return the truncated bits."""
        assert 0 <= bits <= self.len
        if not bits:
            return self.__class__()
        truncated_bits = self._absolute_slice(0, bits)
        if bits == self.len:
            self._clear()
            return truncated_bits
        self._bitstore = self._bitstore.getslice_msb0(slice(bits, None, None))
        return truncated_bits

    def _truncateright(self: TBits, bits: int) -> TBits:
        """Truncate bits from the end of the bitstring. Return the truncated bits."""
        assert 0 <= bits <= self.len
        if bits == 0:
            return self.__class__()
        truncated_bits = self._absolute_slice(self.length - bits, self.length)
        if bits == self.len:
            self._clear()
            return truncated_bits
        self._bitstore = self._bitstore.getslice_msb0(slice(None, -bits, None))
        return truncated_bits

    def _insert(self, bs: Bits, pos: int) -> None:
        """Insert bs at pos."""
        assert 0 <= pos <= self.len
        self._bitstore[pos: pos] = bs._bitstore
        return

    def _overwrite(self, bs: Bits, pos: int) -> None:
        """Overwrite with bs at pos."""
        assert 0 <= pos <= self.len
        if bs is self:
            # Just overwriting with self, so do nothing.
            assert pos == 0
            return
        self._bitstore[pos: pos + bs.len] = bs._bitstore

    def _delete(self, bits: int, pos: int) -> None:
        """Delete bits at pos."""
        assert 0 <= pos <= self.len
        assert pos + bits <= self.len, f"pos={pos}, bits={bits}, len={self.len}"
        del self._bitstore[pos: pos + bits]
        return

    def _reversebytes(self, start: int, end: int) -> None:
        """Reverse bytes in-place."""
        assert (end - start) % 8 == 0
        self._bitstore[start:end] = BitStore(frombytes=self._bitstore.getslice(slice(start, end, None)).tobytes()[::-1])

    def _invert(self, pos: int) -> None:
        """Flip bit at pos 1<->0."""
        assert 0 <= pos < self.len
        self._bitstore.invert(pos)

    def _invert_all(self) -> None:
        """Invert every bit."""
        self._bitstore.invert()

    def _ilshift(self: TBits, n: int) -> TBits:
        """Shift bits by n to the left in place. Return self."""
        assert 0 < n <= self.len
        self._addright(Bits(n))
        self._truncateleft(n)
        return self

    def _irshift(self: TBits, n: int) -> TBits:
        """Shift bits by n to the right in place. Return self."""
        assert 0 < n <= self.len
        self._addleft(Bits(n))
        self._truncateright(n)
        return self

    def _imul(self: TBits, n: int) -> TBits:
        """Concatenate n copies of self in place. Return self."""
        assert n >= 0
        if not n:
            self._clear()
            return self
        m: int = 1
        old_len: int = self.len
        while m * 2 < n:
            self._addright(self)
            m *= 2
        self._addright(self[0:(n - m) * old_len])
        return self

    def _readbits(self: TBits, start: int, length: int) -> TBits:
        """Read some bits from the bitstring and return newly constructed bitstring."""
        return self._slice(start, start + length)

    def _validate_slice(self, start: Optional[int], end: Optional[int]) -> Tuple[int, int]:
        """Validate start and end and return them as positive bit positions."""
        if start is None:
            start = 0
        elif start < 0:
            start += self._getlength()
        if end is None:
            end = self._getlength()
        elif end < 0:
            end += self._getlength()
        if not 0 <= end <= self._getlength():
            raise ValueError("end is not a valid position in the bitstring.")
        if not 0 <= start <= self._getlength():
            raise ValueError("start is not a valid position in the bitstring.")
        if end < start:
            raise ValueError("end must not be less than start.")
        return start, end

    def unpack(self, fmt: Union[str, List[Union[str, int]]], **kwargs) -> List[Union[int, float, str, Bits, bool, bytes, None]]:
        """Interpret the whole bitstring using fmt and return list.

        fmt -- A single string or a list of strings with comma separated tokens
               describing how to interpret the bits in the bitstring. Items
               can also be integers, for reading new bitstring of the given length.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        Raises ValueError if the format is not understood. If not enough bits
        are available then all bits to the end of the bitstring will be used.

        See the docstring for 'read' for token examples.

        """
        return self._readlist(fmt, 0, **kwargs)[0]

    def _readlist(self, fmt: Union[str, List[Union[str, int]]], pos: int, **kwargs: int) \
            -> Tuple[List[Union[int, float, str, Bits, bool, bytes, None]], int]:
        tokens: List[Tuple[str, Optional[Union[str, int]], Optional[str]]] = []
        if isinstance(fmt, str):
            fmt = [fmt]
        keys: Tuple[str, ...] = tuple(sorted(kwargs.keys()))

        def convert_length_strings(length_: Optional[Union[str, int]]) -> Optional[int]:
            int_length: Optional[int] = None
            if isinstance(length_, str):
                if length_ in kwargs:
                    int_length = kwargs[length_]
                    if name == 'bytes':
                        int_length *= 8
            else:
                int_length = length_
            return int_length

        has_stretchy_token = False
        for f_item in fmt:
            # Replace integers with 'bits' tokens
            if isinstance(f_item, numbers.Integral):
                tokens.append(('bits', f_item, None))
            else:
                stretchy, tkns = tokenparser(f_item, keys)
                if stretchy:
                    if has_stretchy_token:
                        raise Error("It's not possible to have more than one 'filler' token.")
                    has_stretchy_token = True
                tokens.extend(tkns)
        if not has_stretchy_token:
            lst = []
            for name, length, _ in tokens:
                length = convert_length_strings(length)
                if name in kwargs and length is None:
                    # Using default 'bits' - the name is really the length.
                    value, pos = self._readtoken('bits', pos, kwargs[name])
                    lst.append(value)
                    continue
                value, pos = self._readtoken(name, pos, length)
                if value is not None:  # Don't append pad tokens
                    lst.append(value)
            return lst, pos
        stretchy_token: Optional[tuple] = None
        bits_after_stretchy_token = 0
        for token in tokens:
            name, length, _ = token
            length = convert_length_strings(length)
            if stretchy_token:
                if name in Bits._register.unknowable_length_names():
                    raise Error(f"It's not possible to parse a variable length token ('{name}') after a 'filler' token.")
                else:
                    if length is None:
                        raise Error("It's not possible to have more than one 'filler' token.")
                    bits_after_stretchy_token += length
            if length is None and name not in Bits._register.unknowable_length_names():
                assert not stretchy_token
                stretchy_token = token
        bits_left = self.len - pos
        return_values = []
        for token in tokens:
            name, length, _ = token
            if token is stretchy_token:
                # Set length to the remaining bits
                length = max(bits_left - bits_after_stretchy_token, 0)
            length = convert_length_strings(length)
            value, newpos = self._readtoken(name, pos, length)
            bits_left -= newpos - pos
            pos = newpos
            if value is not None:
                return_values.append(value)
        return return_values, pos

    def find(self, bs: BitsType, start: Optional[int] = None, end: Optional[int] = None,
             bytealigned: Optional[bool] = None) -> Union[Tuple[int], Tuple[()]]:
        """Find first occurrence of substring bs.

        Returns a single item tuple with the bit position if found, or an
        empty tuple if not found. The bit position (pos property) will
        also be set to the start of the substring if it is found.

        bs -- The bitstring to find.
        start -- The bit position to start the search. Defaults to 0.
        end -- The bit position one past the last bit to search.
               Defaults to len(self).
        bytealigned -- If True the bitstring will only be
                       found on byte boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > len(self) or
        if end < start.

        >>> BitArray('0xc3e').find('0b1111')
        (6,)

        """
        bs = Bits._create_from_bitstype(bs)
        if len(bs) == 0:
            raise ValueError("Cannot find an empty bitstring.")
        start, end = self._validate_slice(start, end)
        ba = Bits._options.bytealigned if bytealigned is None else bytealigned
        p = self._find(bs, start, end, ba)
        return p

    def _find_lsb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        # A forward find in lsb0 is very like a reverse find in msb0.
        assert start <= end
        assert Bits._options.lsb0

        new_slice = offset_slice_indices_lsb0(slice(start, end, None), len(self), 0)
        msb0_start, msb0_end = self._validate_slice(new_slice.start, new_slice.stop)
        p = self._rfind_msb0(bs, msb0_start, msb0_end, bytealigned)

        if p:
            return (self.length - p[0] - bs.length,)
        else:
            return ()

    def _find_msb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        """Find first occurrence of a binary string."""
        while True:
            p = self._bitstore.find(bs._bitstore, start, end)
            if p == -1:
                return ()
            if not bytealigned or (p % 8) == 0:
                return (p,)
            # Advance to just beyond the non-byte-aligned match and try again...
            start = p + 1

    def findall(self, bs: BitsType, start: Optional[int] = None, end: Optional[int] = None, count: Optional[int] = None,
                bytealigned: Optional[bool] = None) -> Iterable[int]:
        """Find all occurrences of bs. Return generator of bit positions.

        bs -- The bitstring to find.
        start -- The bit position to start the search. Defaults to 0.
        end -- The bit position one past the last bit to search.
               Defaults to len(self).
        count -- The maximum number of occurrences to find.
        bytealigned -- If True the bitstring will only be found on
                       byte boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > len(self) or
        if end < start.

        Note that all occurrences of bs are found, even if they overlap.

        """
        if count is not None and count < 0:
            raise ValueError("In findall, count must be >= 0.")
        bs = Bits._create_from_bitstype(bs)
        start, end = self._validate_slice(start, end)
        ba = Bits._options.bytealigned if bytealigned is None else bytealigned
        return self._findall(bs, start, end, count, ba)

    def _findall_msb0(self, bs: Bits, start: int, end: int, count: Optional[int],
                      bytealigned: bool) -> Iterable[int]:
        c = 0
        for i in self._bitstore.getslice_msb0(slice(start, end, None)).itersearch(bs._bitstore):
            if count is not None and c >= count:
                return
            if bytealigned:
                if (start + i) % 8 == 0:
                    c += 1
                    yield start + i
            else:
                c += 1
                yield start + i
        return

    def _findall_lsb0(self, bs: Bits, start: int, end: int, count: Optional[int],
                      bytealigned: bool) -> Iterable[int]:
        assert start <= end
        assert Bits._options.lsb0

        new_slice = offset_slice_indices_lsb0(slice(start, end, None), len(self), 0)
        msb0_start, msb0_end = self._validate_slice(new_slice.start, new_slice.stop)

        # Search chunks starting near the end and then moving back.
        c = 0
        increment = max(8192, bs.len * 80)
        buffersize = min(increment + bs.len, msb0_end - msb0_start)
        pos = max(msb0_start, msb0_end - buffersize)
        while True:
            found = list(self._findall_msb0(bs, start=pos, end=pos + buffersize, count=None, bytealigned=False))
            if not found:
                if pos == msb0_start:
                    return
                pos = max(msb0_start, pos - increment)
                continue
            while found:
                if count is not None and c >= count:
                    return
                c += 1
                lsb0_pos = self.len - found.pop() - bs.len
                if not bytealigned or lsb0_pos % 8 == 0:
                    yield lsb0_pos

            pos = max(msb0_start, pos - increment)
            if pos == msb0_start:
                return

    def rfind(self, bs: BitsType, start: Optional[int] = None, end: Optional[int] = None,
              bytealigned: Optional[bool] = None) -> Union[Tuple[int], Tuple[()]]:
        """Find final occurrence of substring bs.

        Returns a single item tuple with the bit position if found, or an
        empty tuple if not found. The bit position (pos property) will
        also be set to the start of the substring if it is found.

        bs -- The bitstring to find.
        start -- The bit position to end the reverse search. Defaults to 0.
        end -- The bit position one past the first bit to reverse search.
               Defaults to len(self).
        bytealigned -- If True the bitstring will only be found on byte
                       boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > len(self) or
        if end < start.

        """
        bs = Bits._create_from_bitstype(bs)
        start, end = self._validate_slice(start, end)
        ba = Bits._options.bytealigned if bytealigned is None else bytealigned
        if not bs.len:
            raise ValueError("Cannot find an empty bitstring.")
        p = self._rfind(bs, start, end, ba)
        return p

    def _rfind_msb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        """Find final occurrence of a binary string."""
        increment = max(4096, len(bs) * 64)
        buffersize = increment + len(bs)
        p = end
        while p > start:
            start_pos = max(start, p - buffersize)
            ps = list(self._findall_msb0(bs, start_pos, p, count=None, bytealigned=False))
            if ps:
                while ps:
                    if not bytealigned or (ps[-1] % 8 == 0):
                        return (ps[-1],)
                    ps.pop()
            p -= increment
        return ()

    def _rfind_lsb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        # A reverse find in lsb0 is very like a forward find in msb0.
        assert start <= end
        assert Bits._options.lsb0
        new_slice = offset_slice_indices_lsb0(slice(start, end, None), len(self), 0)
        msb0_start, msb0_end = self._validate_slice(new_slice.start, new_slice.stop)

        p = self._find_msb0(bs, msb0_start, msb0_end, bytealigned)
        if p:
            return (self.len - p[0] - bs.length,)
        else:
            return ()

    def cut(self, bits: int, start: Optional[int] = None, end: Optional[int] = None,
            count: Optional[int] = None) -> Iterator[Bits]:
        """Return bitstring generator by cutting into bits sized chunks.

        bits -- The size in bits of the bitstring chunks to generate.
        start -- The bit position to start the first cut. Defaults to 0.
        end -- The bit position one past the last bit to use in the cut.
               Defaults to len(self).
        count -- If specified then at most count items are generated.
                 Default is to cut as many times as possible.

        """
        start_, end_ = self._validate_slice(start, end)
        if count is not None and count < 0:
            raise ValueError("Cannot cut - count must be >= 0.")
        if bits <= 0:
            raise ValueError("Cannot cut - bits must be >= 0.")
        c = 0
        while count is None or c < count:
            c += 1
            nextchunk = self._slice(start_, min(start_ + bits, end_))
            if nextchunk.len == 0:
                return
            yield nextchunk
            if nextchunk._getlength() != bits:
                return
            start_ += bits
        return

    def split(self, delimiter: BitsType, start: Optional[int] = None, end: Optional[int] = None,
              count: Optional[int] = None, bytealigned: Optional[bool] = None) -> Iterable[Bits]:
        """Return bitstring generator by splitting using a delimiter.

        The first item returned is the initial bitstring before the delimiter,
        which may be an empty bitstring.

        delimiter -- The bitstring used as the divider.
        start -- The bit position to start the split. Defaults to 0.
        end -- The bit position one past the last bit to use in the split.
               Defaults to len(self).
        count -- If specified then at most count items are generated.
                 Default is to split as many times as possible.
        bytealigned -- If True splits will only occur on byte boundaries.

        Raises ValueError if the delimiter is empty.

        """
        delimiter = Bits._create_from_bitstype(delimiter)
        if len(delimiter) == 0:
            raise ValueError("split delimiter cannot be empty.")
        start, end = self._validate_slice(start, end)
        bytealigned_: bool = Bits._options.bytealigned if bytealigned is None else bytealigned
        if count is not None and count < 0:
            raise ValueError("Cannot split - count must be >= 0.")
        if count == 0:
            return
        f = functools.partial(self._find_msb0, bs=delimiter, bytealigned=bytealigned_)
        found = f(start=start, end=end)
        if not found:
            # Initial bits are the whole bitstring being searched
            yield self._slice(start, end)
            return
        # yield the bytes before the first occurrence of the delimiter, even if empty
        yield self._slice(start, found[0])
        startpos = pos = found[0]
        c = 1
        while count is None or c < count:
            pos += delimiter.len
            found = f(start=pos, end=end)
            if not found:
                # No more occurrences, so return the rest of the bitstring
                yield self._slice(startpos, end)
                return
            c += 1
            yield self._slice(startpos, found[0])
            startpos = pos = found[0]
        # Have generated count bitstrings, so time to quit.
        return

    def join(self: TBits, sequence: Iterable[Any]) -> TBits:
        """Return concatenation of bitstrings joined by self.

        sequence -- A sequence of bitstrings.

        """
        s = self.__class__()
        if len(self) == 0:
            # Optimised version that doesn't need to add self between every item
            for item in sequence:
                s._addright(Bits._create_from_bitstype(item))
        else:
            i = iter(sequence)
            try:
                s._addright(Bits._create_from_bitstype(next(i)))
                while True:
                    n = next(i)
                    s._addright(self)
                    s._addright(Bits._create_from_bitstype(n))
            except StopIteration:
                pass
        return s

    def tobytes(self) -> bytes:
        """Return the bitstring as bytes, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        return self._bitstore.tobytes()

    def tobitarray(self) -> bitarray.bitarray:
        """Convert the bitstring to a bitarray object."""
        if self._bitstore.modified:
            # Removes the offset and truncates to length
            return bitarray.bitarray(self._bitstore.copy())
        else:
            return bitarray.bitarray(self._bitstore)

    def tofile(self, f: BinaryIO) -> None:
        """Write the bitstring to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        # If the bitstring is file based then we don't want to read it all in to memory first.
        chunk_size = 8 * 100 * 1024 * 1024  # 100 MiB
        for chunk in self.cut(chunk_size):
            f.write(chunk.tobytes())

    def startswith(self, prefix: BitsType, start: Optional[int] = None, end: Optional[int] = None) -> bool:
        """Return whether the current bitstring starts with prefix.

        prefix -- The bitstring to search for.
        start -- The bit position to start from. Defaults to 0.
        end -- The bit position to end at. Defaults to len(self).

        """
        prefix = self._create_from_bitstype(prefix)
        start, end = self._validate_slice(start, end)
        if end < start + prefix._getlength():
            return False
        end = start + prefix._getlength()
        return self._slice(start, end) == prefix

    def endswith(self, suffix: BitsType, start: Optional[int] = None, end: Optional[int] = None) -> bool:
        """Return whether the current bitstring ends with suffix.

        suffix -- The bitstring to search for.
        start -- The bit position to start from. Defaults to 0.
        end -- The bit position to end at. Defaults to len(self).

        """
        suffix = self._create_from_bitstype(suffix)
        start, end = self._validate_slice(start, end)
        if start + suffix.len > end:
            return False
        start = end - suffix._getlength()
        return self._slice(start, end) == suffix

    def all(self, value: Any, pos: Optional[Iterable[int]] = None) -> bool:
        """Return True if one or many bits are all set to bool(value).

        value -- If value is True then checks for bits set to 1, otherwise
                 checks for bits set to 0.
        pos -- An iterable of bit positions. Negative numbers are treated in
               the same way as slice indices. Defaults to the whole bitstring.

        """
        value = bool(value)
        length = self.len
        if pos is None:
            if value is True:
                return self._bitstore.all_set()
            else:
                return not self._bitstore.any_set()
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError(f"Bit position {p} out of range.")
            if not bool(self._bitstore.getindex(p)) is value:
                return False
        return True

    def any(self, value: Any, pos: Optional[Iterable[int]] = None) -> bool:
        """Return True if any of one or many bits are set to bool(value).

        value -- If value is True then checks for bits set to 1, otherwise
                 checks for bits set to 0.
        pos -- An iterable of bit positions. Negative numbers are treated in
               the same way as slice indices. Defaults to the whole bitstring.

        """
        value = bool(value)
        length = self.len
        if pos is None:
            if value is True:
                return self._bitstore.any_set()
            else:
                return not self._bitstore.all_set()
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError(f"Bit position {p} out of range.")
            if bool(self._bitstore.getindex(p)) is value:
                return True
        return False

    def count(self, value: Any) -> int:
        """Return count of total number of either zero or one bits.

        value -- If bool(value) is True then bits set to 1 are counted, otherwise bits set
                 to 0 are counted.

        >>> Bits('0xef').count(1)
        7

        """
        # count the number of 1s (from which it's easy to work out the 0s).
        count = self._bitstore.count(1)
        return count if value else self.len - count

    @staticmethod
    def _chars_in_pp_token(fmt: str) -> Tuple[str, Optional[int]]:
        """
        bin8 -> 'bin', 8
        hex12 -> 'hex', 3
        o9 -> 'oct', 3
        b -> 'bin', None
        """
        bpc_dict = {'bin': 1, 'oct': 3, 'hex': 4, 'bytes': 8}  # bits represented by each printed character
        short_token: Pattern[str] = re.compile(r'(?P<name>bytes|bin|oct|hex|b|o|h):?(?P<len>\d+)$')

        m1 = short_token.match(fmt)
        if m1:
            length = int(m1.group('len'))
            name = m1.group('name')
        else:
            length = None
            name = fmt
        aliases = {'hex': 'hex', 'oct': 'oct', 'bin': 'bin', 'bytes': 'bytes', 'b': 'bin', 'o': 'oct', 'h': 'hex'}
        try:
            name = aliases[name]
        except KeyError:
            pass  # Should be dealt with in the next check
        if name not in bpc_dict.keys():
            raise ValueError(f"Pretty print formats only support {'/'.join(bpc_dict.keys())}. Received '{fmt}'.")
        bpc = bpc_dict[name]
        if length is None:
            return name, None
        if length % bpc != 0:
            raise ValueError(f"Bits per group must be a multiple of {bpc} for '{fmt}' format.")
        return name, length

    @staticmethod
    def _format_bits(bits: Bits, chars_per_group: int, bits_per_group: int, sep: str, fmt: str, getter_fn=None) -> str:
        if fmt in ['bin', 'oct', 'hex', 'bytes']:
            raw = {'bin': bits._getbin,
                   'oct': bits._getoct,
                   'hex': bits._gethex,
                   'bytes': bits._getbytes_printable}[fmt]()
            if chars_per_group == 0:
                return raw
            formatted = sep.join(raw[i: i + chars_per_group] for i in range(0, len(raw), chars_per_group))
            return formatted

        else:
            if fmt == 'bits':
                formatted = sep.join(str(getter_fn(b, 0)) for b in bits.cut(bits_per_group))
                return formatted
            else:
                values = []
                for i in range(0, len(bits), bits_per_group):
                    b = bits[i: i + bits_per_group]
                    values.append(f"{getter_fn(b, 0): >{chars_per_group}}")
                formatted = sep.join(values)
                return formatted

    @staticmethod
    def _chars_per_group(bits_per_group: int, fmt: Optional[str]):
        # TODO: This method is very fragile, and should use the dtype register.
        if fmt is None:
            return 0
        bpc = {'bin': 1, 'b': 1, 'oct': 3, 'o': 3, 'hex': 4, 'h': 4, 'bytes': 8}  # bits represented by each printed character
        try:
            return bits_per_group // bpc[fmt]
        except KeyError:
            # Work out how many chars are needed for each format given the number of bits
            if fmt in ['u', 'uint', 'uintne', 'uintbe', 'uintle']:
                # How many chars is largest uint?
                chars_per_value = len(str((1 << bits_per_group) - 1))
            elif fmt in ['i', 'int', 'intne', 'intbe', 'intle']:
                # Use largest negative int so we get the '-' sign
                chars_per_value = len(str((-1 << (bits_per_group - 1))))
            elif fmt in ['bfloat', 'bfloatne', 'bfloatbe', 'bfloatle']:
                chars_per_value = 23  # Empirical value
            elif fmt in ['f', 'float', 'floatne', 'floatbe', 'floatle']:
                if bits_per_group in [16, 32]:
                    chars_per_value = 23  # Empirical value
                elif bits_per_group == 64:
                    chars_per_value = 24  # Empirical value
            elif fmt == 'e4m3float':
                chars_per_value = 13  # Empirical value
            elif fmt == 'e5m2float':
                chars_per_value = 19  # Empirical value
            elif fmt == 'bool':
                chars_per_value = 1   # '0' or '1'
            elif fmt == 'bits':
                temp = Bits(bits_per_group)
                chars_per_value = len(str(temp))
            else:
                assert False, f"Unsupported format string {fmt}."
                raise ValueError(f"Unsupported format string {fmt}.")
            return chars_per_value

    def _pp(self, name1: str, name2: Optional[str], bits_per_group: int, width: int, sep: str, format_sep: str,
            show_offset: bool, stream: TextIO, lsb0: bool, offset_factor: int, getter_fn=None, getter_fn2=None) -> None:
        """Internal pretty print method."""

        bpc = {'bin': 1, 'oct': 3, 'hex': 4, 'bytes': 8}  # bits represented by each printed character

        offset_width = 0
        offset_sep = ' :' if lsb0 else ': '
        if show_offset:
            # This could be 1 too large in some circumstances. Slightly recurrent logic needed to fix it...
            offset_width = len(str(len(self))) + len(offset_sep)
        if bits_per_group > 0:
            group_chars1 = Bits._chars_per_group(bits_per_group, name1)
            group_chars2 = Bits._chars_per_group(bits_per_group, name2)
            # The number of characters that get added when we add an extra group (after the first one)
            total_group_chars = group_chars1 + group_chars2 + len(sep) + len(sep) * bool(group_chars2)
            width_excluding_offset_and_final_group = width - offset_width - group_chars1 - group_chars2 - len(
                format_sep) * bool(group_chars2)
            width_excluding_offset_and_final_group = max(width_excluding_offset_and_final_group, 0)
            groups_per_line = 1 + width_excluding_offset_and_final_group // total_group_chars
            max_bits_per_line = groups_per_line * bits_per_group  # Number of bits represented on each line
        else:
            assert bits_per_group == 0  # Don't divide into groups
            group_chars1 = group_chars2 = 0
            width_available = width - offset_width - len(format_sep) * (name2 is not None)
            width_available = max(width_available, 1)
            if name2 is None:
                max_bits_per_line = width_available * bpc[name1]
            else:
                chars_per_24_bits = 24 // bpc[name1] + 24 // bpc[name2]
                max_bits_per_line = 24 * (width_available // chars_per_24_bits)
                if max_bits_per_line == 0:
                    max_bits_per_line = 24  # We can't fit into the width asked for. Show something small.
        assert max_bits_per_line > 0

        bitpos = 0
        first_fb_width = second_fb_width = None
        for bits in self.cut(max_bits_per_line):
            offset = bitpos // offset_factor
            if Bits._options.lsb0:
                offset_str = f'{offset_sep}{offset: >{offset_width - len(offset_sep)}}' if show_offset else ''
            else:
                offset_str = f'{offset: >{offset_width - len(offset_sep)}}{offset_sep}' if show_offset else ''
            fb = Bits._format_bits(bits, group_chars1, bits_per_group, sep, name1, getter_fn)
            if first_fb_width is None:
                first_fb_width = len(fb)
            if len(fb) < first_fb_width:  # Pad final line with spaces to align it
                if Bits._options.lsb0:
                    fb = ' ' * (first_fb_width - len(fb)) + fb
                else:
                    fb += ' ' * (first_fb_width - len(fb))
            fb2 = '' if name2 is None else format_sep + Bits._format_bits(bits, group_chars2, bits_per_group, sep, name2, getter_fn2)
            if second_fb_width is None:
                second_fb_width = len(fb2)
            if len(fb2) < second_fb_width:
                if Bits._options.lsb0:
                    fb2 = ' ' * (second_fb_width - len(fb2)) + fb2
                else:
                    fb2 += ' ' * (second_fb_width - len(fb2))
            if Bits._options.lsb0 is True:
                line_fmt = fb + fb2 + offset_str + '\n'
            else:
                line_fmt = offset_str + fb + fb2 + '\n'
            stream.write(line_fmt)
            bitpos += len(bits)
        return

    def pp(self, fmt: Optional[str] = None, width: int = 120, sep: str = ' ',
           show_offset: bool = True, stream: TextIO = sys.stdout) -> None:
        """Pretty print the bitstring's value.

        fmt -- Printed data format. One or two of 'bin', 'oct', 'hex' or 'bytes'.
              The number of bits represented in each printed group defaults to 8 for hex and bin,
              12 for oct and 32 for bytes. This can be overridden with an explicit length, e.g. 'hex:64'.
              Use a length of 0 to not split into groups, e.g. `bin:0`.
        width -- Max width of printed lines. Defaults to 120. A single group will always be printed
                 per line even if it exceeds the max width.
        sep -- A separator string to insert between groups. Defaults to a single space.
        show_offset -- If True (the default) shows the bit offset in the first column of each line.
        stream -- A TextIO object with a write() method. Defaults to sys.stdout.

        >>> s.pp('hex16')
        >>> s.pp('b, h', sep='_', show_offset=False)

        """
        if fmt is None:
            fmt = 'bin' if len(self) % 4 != 0 else 'bin, hex'

        bpc = {'bin': 1, 'oct': 3, 'hex': 4, 'bytes': 8}  # bits represented by each printed character

        formats = [f.strip() for f in fmt.split(',')]
        if len(formats) == 1:
            fmt1, fmt2 = formats[0], None
        elif len(formats) == 2:
            fmt1, fmt2 = formats[0], formats[1]
        else:
            raise ValueError(f"Either 1 or 2 comma separated formats must be specified, not {len(formats)}."
                             " Format string was {fmt}.")

        name1, length1 = Bits._chars_in_pp_token(fmt1)
        if fmt2 is not None:
            name2, length2 = Bits._chars_in_pp_token(fmt2)

        if fmt2 is not None and length2 is not None and length1 is not None:
            # Both lengths defined so must be equal
            if length1 != length2:
                raise ValueError(f"Differing bit lengths of {length1} and {length2} in format string '{fmt}'.")

        bits_per_group = None
        if fmt2 is not None and length2 is not None:
            bits_per_group = length2
        elif length1 is not None:
            bits_per_group = length1

        if bits_per_group is None:
            if fmt2 is None:
                bits_per_group = 8  # Default for 'bin' and 'hex'
                if name1 == 'oct':
                    bits_per_group = 12
                elif name1 == 'bytes':
                    bits_per_group = 32
            else:
                # Rule of thumb seems to work OK for all combinations.
                bits_per_group = 2 * bpc[name1] * bpc[name2]
                if bits_per_group >= 24:
                    bits_per_group //= 2

        format_sep = "   "  # String to insert on each line between multiple formats
        self._pp(name1, name2 if fmt2 is not None else None, bits_per_group, width, sep, format_sep, show_offset,
                 stream, Bits._options.lsb0, 1)
        return

    def copy(self: TBits) -> TBits:
        """Return a copy of the bitstring."""
        return self._copy()

    # Create native-endian functions as aliases depending on the byteorder
    if byteorder == 'little':
        _setfloatne = _setfloatle
        _readfloatne = _readfloatle
        _getfloatne = _getfloatle
        _setbfloatne = _setbfloatle
        _readbfloatne = _readbfloatle
        _getbfloatne = _getbfloatle
        _setuintne = _setuintle
        _readuintne = _readuintle
        _getuintne = _getuintle
        _setintne = _setintle
        _readintne = _readintle
        _getintne = _getintle
    else:
        _setfloatne = _setfloatbe
        _readfloatne = _readfloatbe
        _getfloatne = _getfloatbe
        _setbfloatne = _setbfloatbe
        _readbfloatne = _readbfloatbe
        _getbfloatne = _getbfloatbe
        _setuintne = _setuintbe
        _readuintne = _readuintbe
        _getuintne = _getuintbe
        _setintne = _setintbe
        _readintne = _readintbe
        _getintne = _getintbe

    len = length = property(_getlength, doc="The length of the bitstring in bits. Read only.")


