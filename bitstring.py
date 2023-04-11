#!/usr/bin/env python
r"""
This package defines classes that simplify bit-wise creation, manipulation and
interpretation of data.

Classes:

Bits -- An immutable container for binary data.
BitArray -- A mutable container for binary data.
ConstBitStream -- An immutable container with streaming methods.
BitStream -- A mutable container with streaming methods.

Functions:

pack -- Create a BitStream from a format string.

Module Properties:

bytealigned -- Determines whether a number of methods default to working only on byte boundaries.
lsb0 -- If True, the least significant bit (the final bit) is indexed as bit zero.

Exceptions:

Error -- Module exception base class.
CreationError -- Error during creation.
InterpretError -- Inappropriate interpretation of binary data.
ByteAlignError -- Whole byte position or length needed.
ReadError -- Reading or peeking past the end of a bitstring.

https://github.com/scott-griffiths/bitstring
"""
from __future__ import annotations

__licence__ = """
The MIT License

Copyright (c) 2006 Scott Griffiths (dr.scottgriffiths@gmail.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

__version__ = "4.0.2"

__author__ = "Scott Griffiths"

import copy
import pathlib
import sys
import re
import mmap
import os
import struct
import operator
import array
import io
from collections import abc
import functools
import types
from typing import Generator, Sequence, Tuple, Union, List, Iterable, Any, Optional, Iterator, Pattern, Dict,\
    BinaryIO, TextIO, Callable, overload
from contextlib import suppress


# Things that can be converted to Bits when a Bits type is needed
BitsType = Union['Bits', int, float, str, Iterable[Any], bool, BinaryIO, bytearray, bytes]

byteorder: str = sys.byteorder

# An opaque way of adding module level properties. Taken from https://peps.python.org/pep-0549/
_bytealigned: bool = False
_lsb0: bool = False


class _MyModuleType(types.ModuleType):
    @property
    def bytealigned(self):
        """Determines whether a number of methods default to working only on byte boundaries."""
        return globals()['_bytealigned']

    @bytealigned.setter
    def bytealigned(self, value: bool):
        """Determines whether a number of methods default to working only on byte boundaries."""
        globals()['_bytealigned'] = value

    @property
    def lsb0(self):
        """If True, the least significant bit (the final bit) is indexed as bit zero."""
        return globals()['_lsb0']

    @lsb0.setter
    def lsb0(self, value: bool):
        """If True, the least significant bit (the final bit) is indexed as bit zero."""
        value = bool(value)
        _switch_lsb0_methods(value)
        globals()['_lsb0'] = value


sys.modules[__name__].__class__ = _MyModuleType

# Maximum number of digits to use in __str__ and __repr__.
MAX_CHARS: int = 250

# Maximum size of caches used for speed optimisations.
CACHE_SIZE: int = 1000


class Error(Exception):
    """Base class for errors in the bitstring module."""

    def __init__(self, *params: object):
        self.msg = params[0] if params else ''
        self.params = params[1:]


class ReadError(Error, IndexError):
    """Reading or peeking past the end of a bitstring."""

    def __init__(self, *params: object):
        Error.__init__(self, *params)


class InterpretError(Error, ValueError):
    """Inappropriate interpretation of binary data."""

    def __init__(self, *params: object):
        Error.__init__(self, *params)


class ByteAlignError(Error):
    """Whole-byte position or length needed."""

    def __init__(self, *params: object):
        Error.__init__(self, *params)


class CreationError(Error, ValueError):
    """Inappropriate argument during bitstring creation."""

    def __init__(self, *params: object):
        Error.__init__(self, *params)


class ByteStore:
    """Stores raw bytes together with a bit offset and length.

    Used internally - not part of public interface.
    """

    @classmethod
    def _setlsb0methods(cls, lsb0: bool) -> None:
        if lsb0:
            cls.getbit = cls._getbit_lsb0  # type: ignore
            cls.setbit = cls._setbit_lsb0  # type: ignore
            cls.unsetbit = cls._unsetbit_lsb0  # type: ignore
            cls.invertbit = cls._invertbit_lsb0  # type: ignore
            cls.__iter__ = cls._iter_lsb0  # type: ignore
        else:
            cls.getbit = cls._getbit_msb0  # type: ignore
            cls.setbit = cls._setbit_msb0  # type: ignore
            cls.unsetbit = cls._unsetbit_msb0  # type: ignore
            cls.invertbit = cls._invertbit_msb0  # type: ignore
            cls.__iter__ = cls._iter_msb0  # type: ignore

    __slots__ = ('offset', 'rawarray', 'bitlength')

    def __init__(self, data: Union[bytearray, MmapByteArray],
                 bitlength: Optional[int] = None, offset: int = 0) -> None:
        self.rawarray = data
        if bitlength is None:
            bitlength = 8 * len(data) - offset
        self.offset = offset
        self.bitlength = bitlength

    def _iter_lsb0(self) -> Iterator[bool]:
        # TODO: Rewrite like _iter_msb0
        # A rather slow but simple version
        for p in range(0, self.bitlength):
            yield self._getbit_lsb0(p)
        return

    def _iter_msb0(self) -> Iterator[bool]:
        start_byte, start_bit = divmod(self.offset, 8)
        end_byte, end_bit = divmod(self.offset + self.bitlength, 8)

        try:
            byte = self.rawarray[start_byte]
        except IndexError:
            return  # Empty
        if start_byte != end_byte:
            for bit in range(start_bit, 8):
                yield bool(byte & (128 >> bit))
            start_bit = 0
        else:
            for bit in range(start_bit, end_bit):
                yield bool(byte & (128 >> bit))
            return

        for byte in self.rawarray[start_byte + 1: end_byte]:
            reversed_int = Bits._int8ReversalDict[byte]
            for _ in range(0, 8):
                yield bool(reversed_int & 1)
                reversed_int >>= 1
            start_bit = 0

        if end_bit:
            byte = self.rawarray[end_byte]
            for bit in range(start_bit, end_bit):
                yield bool(byte & (128 >> bit))

    def _getbit_lsb0(self, pos: int) -> bool:
        assert 0 <= pos < self.bitlength
        pos = self.bitlength - pos - 1
        byte, bit = divmod(self.offset + pos, 8)
        return bool(self.rawarray[byte] & (128 >> bit))

    def _getbit_msb0(self, pos: int) -> bool:
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        return bool(self.rawarray[byte] & (128 >> bit))

    def getbyte(self, pos: int) -> int:
        """Direct access to byte data."""
        return self.rawarray[pos]

    def getbyteslice(self, start: int, end: int) -> bytearray:
        """Direct access to byte data."""
        return self.rawarray[start:end]

    @property
    def bytelength(self) -> int:
        if not self.bitlength:
            return 0
        sb = self.offset // 8
        eb = (self.offset + self.bitlength - 1) // 8
        return eb - sb + 1

    def __copy__(self) -> ByteStore:
        return ByteStore(self.rawarray[:], self.bitlength, self.offset)

    def appendstore(self, store: ByteStore) -> None:
        """Join another store on to the end of this one."""
        if not store.bitlength:
            return
        # Set new array offset to the number of bits in the final byte of current array.
        store = offsetcopy(store, (self.offset + self.bitlength) % 8)
        if store.offset != 0:
            # first do the byte with the join.
            joinval = (self.rawarray.pop() & (255 ^ (255 >> store.offset)) |
                       (store.getbyte(0) & (255 >> store.offset)))
            self.rawarray.append(joinval)
            self.rawarray.extend(store.rawarray[1:])
        else:
            self.rawarray.extend(store.rawarray)
        self.bitlength += store.bitlength

    def prependstore(self, store: ByteStore) -> None:
        """Join another store on to the start of this one."""
        if not store.bitlength:
            return
            # Set the offset of copy of store so that it's final byte
        # ends in a position that matches the offset of self,
        # then join self on to the end of it.
        store = offsetcopy(store, (self.offset - store.bitlength) % 8)
        assert (store.offset + store.bitlength) % 8 == self.offset % 8
        bit_offset = self.offset % 8
        if bit_offset:
            # first do the byte with the join.
            joinval = (store.getbyte(-1) & (255 ^ (255 >> bit_offset)) | 
                       (self.rawarray[self.byteoffset] & (255 >> bit_offset)))
            store.rawarray[-1] = joinval
            store.rawarray.extend(self.rawarray[self.byteoffset + 1: self.byteoffset + self.bytelength])
        else:
            store.rawarray.extend(self.rawarray[self.byteoffset: self.byteoffset + self.bytelength])
        self.rawarray = store.rawarray
        self.offset = store.offset
        self.bitlength += store.bitlength

    def _setbit_lsb0(self, pos: int) -> None:
        assert 0 <= pos < self.bitlength
        pos = self.bitlength - pos - 1
        byte, bit = divmod(self.offset + pos, 8)
        self.rawarray[byte] |= (128 >> bit)

    def _setbit_msb0(self, pos: int) -> None:
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        self.rawarray[byte] |= (128 >> bit)

    def _unsetbit_lsb0(self, pos: int) -> None:
        assert 0 <= pos < self.bitlength
        pos = self.bitlength - pos - 1
        byte, bit = divmod(self.offset + pos, 8)
        self.rawarray[byte] &= ~(128 >> bit)

    def _unsetbit_msb0(self, pos: int) -> None:
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        self.rawarray[byte] &= ~(128 >> bit)

    def _invertbit_lsb0(self, pos: int) -> None:
        assert 0 <= pos < self.bitlength
        pos = self.bitlength - pos - 1
        byte, bit = divmod(self.offset + pos, 8)
        self.rawarray[byte] ^= (128 >> bit)

    def _invertbit_msb0(self, pos: int) -> None:
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        self.rawarray[byte] ^= (128 >> bit)

    def setbyte(self, pos: int, value: int) -> None:
        self.rawarray[pos] = value

    def setbyteslice(self, start: int, end: int, value: bytearray) -> None:
        self.rawarray[start:end] = value

    @property
    def byteoffset(self) -> int:
        return self.offset // 8

    @property
    def rawbytes(self) -> Union[bytearray, MmapByteArray]:
        return self.rawarray


def offsetcopy(s: ByteStore, newoffset: int) -> ByteStore:
    """Return a copy of a ByteStore with the newoffset.

    Not part of public interface.
    """
    assert 0 <= newoffset < 8
    if s.bitlength == 0:
        return copy.copy(s)
    if newoffset == s.offset % 8:
        return type(s)(s.getbyteslice(s.byteoffset, s.byteoffset + s.bytelength), s.bitlength, newoffset)

    if isinstance(s.rawarray, MmapByteArray):
        # Need to make a copy in memory first
        v = int.from_bytes(s.rawarray[:], 'big')
    else:
        v = int.from_bytes(s.rawarray, 'big')
    if newoffset < s.offset % 8:
        # We need to shift everything left
        shiftleft = s.offset % 8 - newoffset
        v <<= shiftleft
        v &= (1 << 8 * len(s.rawarray)) - 1
        newdata = v.to_bytes(len(s.rawarray), 'big')
    else:
        # Shifting right, but we use a left shift as we don't want to lose any data
        shiftleft = 8 - newoffset + s.offset % 8
        v <<= shiftleft
        newdata = v.to_bytes(len(s.rawarray) + 1, 'big')

    bits_remaining_in_last_byte = (s.offset + s.bitlength) % 8
    if bits_remaining_in_last_byte == 0:
        bits_remaining_in_last_byte = 8
    bits_remaining_in_last_byte -= shiftleft
    if bits_remaining_in_last_byte <= 0 and len(newdata) > 1:
        newdata = newdata[:-1]

    new_s = type(s)(bytearray(newdata), s.bitlength, newoffset)
    return new_s


def equal(a: ByteStore, b: ByteStore) -> bool:
    """Return True if ByteStores a == b.

    Not part of public interface.
    """
    # We want to return False for inequality as soon as possible, which
    # means we get lots of special cases.
    # First the easy one - compare lengths:
    a_bitlength = a.bitlength
    b_bitlength = b.bitlength
    if a_bitlength != b_bitlength:
        return False
    if not a_bitlength:
        assert b_bitlength == 0
        return True
    # Make 'a' the one with the smaller offset
    if (a.offset % 8) > (b.offset % 8):
        a, b = b, a
    # and create some aliases
    a_bitoff = a.offset % 8
    b_bitoff = b.offset % 8
    a_byteoffset = a.byteoffset
    b_byteoffset = b.byteoffset
    a_bytelength = a.bytelength
    b_bytelength = b.bytelength
    da = a.rawarray
    db = b.rawarray

    # If they are pointing to the same data, they must be equal
    if da is db and a.offset == b.offset:
        return True

    if a_bitoff == b_bitoff:
        bits_spare_in_last_byte = 8 - (a_bitoff + a_bitlength) % 8
        if bits_spare_in_last_byte == 8:
            bits_spare_in_last_byte = 0
        # Special case for a, b contained in a single byte
        if a_bytelength == 1:
            a_val = ((da[a_byteoffset] << a_bitoff) & 0xff) >> (8 - a_bitlength)
            b_val = ((db[b_byteoffset] << b_bitoff) & 0xff) >> (8 - b_bitlength)
            return a_val == b_val
        # Otherwise check first byte
        if da[a_byteoffset] & (0xff >> a_bitoff) != db[b_byteoffset] & (0xff >> b_bitoff):
            return False
        # then everything up to the last
        b_a_offset = b_byteoffset - a_byteoffset
        for x in range(1 + a_byteoffset, a_byteoffset + a_bytelength - 1):
            if da[x] != db[b_a_offset + x]:
                return False
        # and finally the last byte
        return (da[a_byteoffset + a_bytelength - 1] >> bits_spare_in_last_byte ==
                db[b_byteoffset + b_bytelength - 1] >> bits_spare_in_last_byte)

    assert a_bitoff != b_bitoff
    # This is how much we need to shift a to the right to compare with b:
    shift = b_bitoff - a_bitoff
    # Special case for b only one byte long
    if b_bytelength == 1:
        assert a_bytelength == 1
        a_val = ((da[a_byteoffset] << a_bitoff) & 0xff) >> (8 - a_bitlength)
        b_val = ((db[b_byteoffset] << b_bitoff) & 0xff) >> (8 - b_bitlength)
        return a_val == b_val
    # Special case for a only one byte long
    if a_bytelength == 1:
        assert b_bytelength == 2
        a_val = ((da[a_byteoffset] << a_bitoff) & 0xff) >> (8 - a_bitlength)
        b_val = ((db[b_byteoffset] << 8) + db[b_byteoffset + 1]) << b_bitoff
        b_val &= 0xffff
        b_val >>= 16 - b_bitlength
        return a_val == b_val

    # Compare first byte of b with bits from first byte of a
    if (da[a_byteoffset] & (0xff >> a_bitoff)) >> shift != db[b_byteoffset] & (0xff >> b_bitoff):
        return False
    # Now compare every full byte of b with bits from 2 bytes of a
    for x in range(1, b_bytelength - 1):
        # Construct byte from 2 bytes in a to compare to byte in b
        b_val = db[b_byteoffset + x]
        a_val = ((da[a_byteoffset + x - 1] << 8) + da[a_byteoffset + x]) >> shift
        a_val &= 0xff
        if a_val != b_val:
            return False

    # Now check bits in final byte of b
    final_b_bits = (b.offset + b_bitlength) % 8
    if not final_b_bits:
        final_b_bits = 8
    b_val = db[b_byteoffset + b_bytelength - 1] >> (8 - final_b_bits)
    final_a_bits = (a.offset + a_bitlength) % 8
    if not final_a_bits:
        final_a_bits = 8
    if b.bytelength > a_bytelength:
        assert b_bytelength == a_bytelength + 1
        a_val = da[a_byteoffset + a_bytelength - 1] >> (8 - final_a_bits)
        a_val &= 0xff >> (8 - final_b_bits)
        return a_val == b_val
    assert a_bytelength == b_bytelength
    a_val = da[a_byteoffset + a_bytelength - 2] << 8
    a_val += da[a_byteoffset + a_bytelength - 1]
    a_val >>= (8 - final_a_bits)
    a_val &= 0xff >> (8 - final_b_bits)
    return a_val == b_val


class MmapByteArray:
    """Looks like a bytearray, but from an mmap.

    Not part of public interface.
    """

    __slots__ = ('filemap', 'filelength', 'source', 'byteoffset', 'bytelength')

    def __init__(self, source: Union[BinaryIO, io.BufferedReader], bytelength: Optional[int] = None,
                 byteoffset: Optional[int] = None) -> None:
        self.source = source
        source.seek(0, os.SEEK_END)
        self.filelength = source.tell()
        if byteoffset is None:
            byteoffset = 0
        if bytelength is None:
            bytelength = self.filelength - byteoffset
        self.byteoffset = byteoffset
        self.bytelength = bytelength
        self.filemap = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)

    @overload
    def __getitem__(self, key: slice) -> bytearray: ...
    @overload
    def __getitem__(self, key: int) -> int: ...

    def __getitem__(self, key: Union[slice, int]) -> Union[bytearray, int]:
        if isinstance(key, slice):
            start = key.start
            stop = key.stop
            if start is None:
                start = 0
            if stop is None:
                stop = self.bytelength
            assert key.step is None
            assert 0 <= start < self.bytelength
            assert 0 <= stop <= self.bytelength
            s = slice(start + self.byteoffset, stop + self.byteoffset)
            return bytearray(self.filemap.__getitem__(s))
        else:
            return self.filemap[key + self.byteoffset]

    def __len__(self) -> int:
        return self.bytelength

    # These methods shouldn't ever get called
    def pop(self, __index: int = ...) -> int:
        raise NotImplementedError
    
    def append(self, __item: Union[Sequence, int]) -> None:
        raise NotImplementedError

    def extend(self, __iterable_of_ints: Union[Iterable[Sequence], bytearray]) -> None:
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError
    
    def __setitem__(self, key: Union[slice, int], value: Any) -> None:
        raise NotImplementedError


def tidy_input_string(s: str) -> str:
    """Return string made lowercase and with all whitespace and underscores removed."""
    return ''.join(s.split()).lower().replace('_', '')


INIT_NAMES: List[str] = ['uint', 'int', 'ue', 'se', 'sie', 'uie', 'hex', 'oct', 'bin', 'bits',
                         'uintbe', 'intbe', 'uintle', 'intle', 'uintne', 'intne',
                         'float', 'floatbe', 'floatle', 'floatne', 'bfloat', 'bytes', 'bool', 'pad']
# Sort longest first as we want to match them in that order (so floatne before float etc.).
INIT_NAMES.sort(key=len, reverse=True)

TOKEN_RE: Pattern[str] = re.compile(r'^(?P<name>' + '|'.join(INIT_NAMES) +
                                    r'):?(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)
# Tokens such as 'u32', 'f64=4.5' or 'i6=-3'
SHORT_TOKEN_RE: Pattern[str] = re.compile(r'^(?P<name>[uifboh]):?(?P<len>\d+)?(=(?P<value>.*))?$', re.IGNORECASE)
DEFAULT_BITS: Pattern[str] = re.compile(r'^(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)

MULTIPLICATIVE_RE: Pattern[str] = re.compile(r'^(?P<factor>.*)\*(?P<token>.+)')

# Hex, oct or binary literals
LITERAL_RE: Pattern[str] = re.compile(r'^(?P<name>0([xob]))(?P<value>.+)', re.IGNORECASE)

# An endianness indicator followed by one or more struct.pack codes
STRUCT_PACK_RE: Pattern[str] = re.compile(r'^(?P<endian>[<>@])?(?P<fmt>(?:\d*[bBhHlLqQefd])+)$')

# A number followed by a single character struct.pack code
STRUCT_SPLIT_RE: Pattern[str] = re.compile(r'\d*[bBhHlLqQefd]')

# These replicate the struct.pack codes
# Big-endian
REPLACEMENTS_BE: Dict[str, str] = {'b': 'intbe:8', 'B': 'uintbe:8',
                                   'h': 'intbe:16', 'H': 'uintbe:16',
                                   'l': 'intbe:32', 'L': 'uintbe:32',
                                   'q': 'intbe:64', 'Q': 'uintbe:64',
                                   'e': 'floatbe:16', 'f': 'floatbe:32', 'd': 'floatbe:64'}
# Little-endian
REPLACEMENTS_LE: Dict[str, str] = {'b': 'intle:8', 'B': 'uintle:8',
                                   'h': 'intle:16', 'H': 'uintle:16',
                                   'l': 'intle:32', 'L': 'uintle:32',
                                   'q': 'intle:64', 'Q': 'uintle:64',
                                   'e': 'floatle:16', 'f': 'floatle:32', 'd': 'floatle:64'}

# Size in bytes of all the pack codes.
PACK_CODE_SIZE: Dict[str, int] = {'b': 1, 'B': 1, 'h': 2, 'H': 2, 'l': 4, 'L': 4,
                                  'q': 8, 'Q': 8, 'e': 2, 'f': 4, 'd': 8}

_tokenname_to_initialiser: Dict[str, str] = {'hex': 'hex', '0x': 'hex', '0X': 'hex', 'oct': 'oct', '0o': 'oct',
                                             '0O': 'oct', 'bin': 'bin', '0b': 'bin', '0B': 'bin', 'bits': 'auto',
                                             'bytes': 'bytes', 'pad': 'pad', 'bfloat': 'bfloat'}


def structparser(token: str) -> List[str]:
    """Parse struct-like format string token into sub-token list."""
    m = STRUCT_PACK_RE.match(token)
    if not m:
        return [token]
    else:
        endian = m.group('endian')
        if endian is None:
            return [token]
        # Split the format string into a list of 'q', '4h' etc.
        formatlist = re.findall(STRUCT_SPLIT_RE, m.group('fmt'))
        # Now deal with multiplicative factors, 4h -> hhhh etc.
        fmt = ''.join([f[-1] * int(f[:-1]) if len(f) != 1 else
                       f for f in formatlist])
        if endian == '@':
            # Native endianness
            if byteorder == 'little':
                endian = '<'
            else:
                assert byteorder == 'big'
                endian = '>'
        if endian == '<':
            tokens = [REPLACEMENTS_LE[c] for c in fmt]
        else:
            assert endian == '>'
            tokens = [REPLACEMENTS_BE[c] for c in fmt]
    return tokens


def tokenparser(fmt: str, keys: Optional[Tuple[str, ...]] = None, token_cache: Dict = {}) -> \
        Tuple[bool, List[Tuple[str, Optional[int], Optional[str]]]]:
    """Divide the format string into tokens and parse them.

    Return stretchy token and list of [initialiser, length, value]
    initialiser is one of: hex, oct, bin, uint, int, se, ue, 0x, 0o, 0b etc.
    length is None if not known, as is value.

    If the token is in the keyword dictionary (keys) then it counts as a
    special case and isn't messed with.

    tokens must be of the form: [factor*][initialiser][:][length][=value]

    """
    try:
        return token_cache[(fmt, keys)]
    except KeyError:
        token_key = (fmt, keys)
    # Very inefficient expanding of brackets.
    fmt = expand_brackets(fmt)
    # Split tokens by ',' and remove whitespace
    # The meta_tokens can either be ordinary single tokens or multiple
    # struct-format token strings.
    meta_tokens = (''.join(f.split()) for f in fmt.split(','))
    return_values = []
    stretchy_token = False
    for meta_token in meta_tokens:
        # See if it has a multiplicative factor
        m = MULTIPLICATIVE_RE.match(meta_token)
        if not m:
            factor = 1
        else:
            factor = int(m.group('factor'))
            meta_token = m.group('token')
        # See if it's a struct-like format
        tokens = structparser(meta_token)
        ret_vals = []
        for token in tokens:
            if keys and token in keys:
                # Don't bother parsing it, it's a keyword argument
                ret_vals.append([token, None, None])
                continue
            if token == '':
                continue
            # Match literal tokens of the form 0x... 0o... and 0b...
            m = LITERAL_RE.match(token)
            if m:
                name: str = m.group('name')
                value: str = m.group('value')
                ret_vals.append([name, None, value])
                continue
            # Match everything else:
            m1 = TOKEN_RE.match(token)
            if m1:
                name = m1.group('name')
                length = m1.group('len')
                value = m1.group('value')
            else:
                m1_short = SHORT_TOKEN_RE.match(token)
                if m1_short:
                    name = m1_short.group('name')
                    name = {'u': 'uint',
                            'i': 'int',
                            'f': 'float',
                            'b': 'bin',
                            'o': 'oct',
                            'h': 'hex'}[name]
                    length = m1_short.group('len')
                    value = m1_short.group('value')
                else:
                    # If you don't specify a 'name' then the default is 'bits':
                    name = 'bits'
                    m2 = DEFAULT_BITS.match(token)
                    if not m2:
                        raise ValueError(f"Don't understand token '{token}'.")
                    length = m2.group('len')
                    value = m2.group('value')

            if name == 'bool':
                if length is not None and length != '1':
                    raise ValueError(f"bool tokens can only be 1 bit long, not {length} bits.")
                length = '1'
            if name == 'bfloat':
                if length is not None and length != '16':
                    raise ValueError(f"bfloat tokens can only be 16 bits long, not {length} bits.")
                length = '16'
            if length is None and name not in ('se', 'ue', 'sie', 'uie'):
                stretchy_token = True
                
            if length is not None:
                # Try converting length to int, otherwise check it's a key.
                try:
                    length = int(length)
                    if length < 0:
                        raise Error
                    # For the 'bytes' token convert length to bits.
                    if name == 'bytes':
                        length *= 8
                except Error:
                    raise ValueError("Can't read a token with a negative length.")
                except ValueError:
                    if not keys or length not in keys:
                        raise ValueError(f"Don't understand length '{length}' of token.")
            ret_vals.append([name, length, value])
        # This multiplies by the multiplicative factor, but this means that
        # we can't allow keyword values as multipliers (e.g. n*uint:8).
        # The only way to do this would be to return the factor in some fashion
        # (we can't use the key's value here as it would mean that we couldn't
        # sensibly continue to cache the function's results. (TODO).
        return_values.extend(ret_vals * factor)
    return_values = [tuple(x) for x in return_values]
    if len(token_cache) < CACHE_SIZE:
        token_cache[token_key] = stretchy_token, return_values
    return stretchy_token, return_values


def expand_brackets(s: str) -> str:
    """Remove whitespace and expand all brackets."""
    s = ''.join(s.split())
    while True:
        start = s.find('(')
        if start == -1:
            break
        count = 1  # Number of hanging open brackets
        p = start + 1
        while p < len(s):
            if s[p] == '(':
                count += 1
            if s[p] == ')':
                count -= 1
            if not count:
                break
            p += 1
        if count:
            raise ValueError(f"Unbalanced parenthesis in '{s}'.")
        if start == 0 or s[start - 1] != '*':
            s = s[0:start] + s[start + 1:p] + s[p + 1:]
        else:
            # Looks for first number*(
            bracket_re = re.compile(r'(?P<factor>\d+)\*\(')
            m = bracket_re.search(s)
            if m:
                factor = int(m.group('factor'))
                matchstart = m.start('factor')
                s = s[0:matchstart] + (factor - 1) * (s[start + 1:p] + ',') + s[start + 1:p] + s[p + 1:]
            else:
                raise ValueError(f"Failed to parse '{s}'.")
    return s


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

    @classmethod
    def _setlsb0methods(cls, lsb0: bool) -> None:
        if lsb0:
            cls._find = cls._find_lsb0  # type: ignore
            cls._rfind = cls._rfind_lsb0  # type: ignore
            cls._findall = cls._findall_lsb0  # type: ignore
            cls._slice = cls._slice_lsb0  # type: ignore
            cls._truncatestart = cls._truncateright  # type: ignore
            cls._truncateend = cls._truncateleft  # type: ignore
            cls._validate_slice = cls._validate_slice_lsb0  # type: ignore
        else:
            cls._find = cls._find_msb0  # type: ignore
            cls._rfind = cls._rfind_msb0  # type: ignore
            cls._findall = cls._findall_msb0  # type: ignore
            cls._slice = cls._slice_msb0  # type: ignore
            cls._truncatestart = cls._truncateleft  # type: ignore
            cls._truncateend = cls._truncateright  # type: ignore
            cls._validate_slice = cls._validate_slice_msb0  # type: ignore

    __slots__ = ('_datastore', '_pos')
    # This converts a single octal digit to 3 bits.
    _octToBits: List[str] = ['{0:03b}'.format(i) for i in range(8)]

    # Creates dictionaries to quickly reverse single bytes
    _int8ReversalDict: Dict[int, int] = {i: int("{0:08b}".format(i)[::-1], 2) for i in range(0x100)}
    _byteReversalDict: Dict[int, bytes] = {i: bytes([int("{0:08b}".format(i)[::-1], 2)]) for i in range(0x100)}

    def __init__(self, auto: Optional[BitsType] = None, length: Optional[int] = None,
                 offset: Optional[int] = None, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        auto -- a string of comma separated tokens, an integer, a file object,
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
        pass

    def __new__(cls, auto: Optional[BitsType] = None, length: Optional[int] = None,
                offset: Optional[int] = None, _cache={}, **kwargs) -> Bits:
        # For instances auto-initialised with a string we intern the instance for re-use.
        if isinstance(auto, str):
            try:
                return _cache[auto]
            except KeyError:
                x = object.__new__(Bits)
                try:
                    _, tokens = tokenparser(auto)
                except ValueError as e:
                    raise CreationError(*e.args)
                if offset is not None:
                    raise CreationError("offset should not be specified when using string initialisation.")
                if length is not None:
                    raise CreationError("length should not be specified when using string initialisation.")
                x._datastore = ByteStore(bytearray(0), 0)
                for token in tokens:
                    x._datastore.appendstore(Bits._init_with_token(*token)._datastore)
                if len(_cache) < CACHE_SIZE:
                    _cache[auto] = x
                return x
        if type(auto) is Bits:
            return auto
        x = super(Bits, cls).__new__(cls)
        x._datastore = ByteStore(bytearray())
        x._initialise(auto, length, offset, **kwargs)
        return x

    def _initialise(self, auto: Any, length: Optional[int], offset: Optional[int], **kwargs) -> None:
        if length is not None and length < 0:
            raise CreationError("bitstring length cannot be negative.")
        if offset is not None and offset < 0:
            raise CreationError("offset must be >= 0.")
        if auto is not None:
            self._initialise_from_auto(auto, length, offset)
            return
        if not kwargs:
            # No initialisers, so initialise with nothing or zero bits
            if length is not None and length != 0:
                data = bytearray((length + 7) // 8)
                self._setbytes_unsafe(data, length, 0)
                return
            self._setbytes_unsafe(bytearray(0), 0, 0)
            return
        k, v = kwargs.popitem()

        try:
            self._setfunc[k](self, v, length, offset)
        except KeyError:
            raise CreationError(f"Unrecognised keyword '{k}' used to initialise.")

    def _initialise_from_auto(self, auto: Any, length: Optional[int], offset: Optional[int]) -> None:
        if offset is None:
            offset = 0
        self._setauto(auto, length, offset)
        return

    def __getattr__(self, attribute: str):
        if attribute == '_pos':
            # For the classes without pos it's easier to return None than throw an exception.
            return None
        # Support for arbitrary attributes like u16 or f64.
        letter_to_getter: Dict[str, Callable[..., Union[int, float, str]]] = \
            {'u': self._getuint,
             'i': self._getint,
             'f': self._getfloatbe,
             'b': self._getbin,
             'o': self._getoct,
             'h': self._gethex}
        short_token: Pattern[str] = re.compile(r'^(?P<name>[uifboh]):?(?P<len>\d+)$', re.IGNORECASE)
        m1_short = short_token.match(attribute)
        if m1_short:
            length = int(m1_short.group('len'))
            if length is not None and self.len != length:
                raise InterpretError(f"bitstring length {self.len} doesn't match length of property {attribute}.")
            name = m1_short.group('name')
            f = letter_to_getter[name]
            return f()
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
        return iter(self._datastore)

    def __copy__(self) -> Bits:
        """Return a new copy of the Bits for the copy module."""
        # Note that if you want a new copy (different ID), use _copy instead.
        # The copy can return self as it's immutable.
        return self

    def __lt__(self, other: Any):
        raise TypeError(f"unorderable type: {type(self).__name__}")

    def __gt__(self, other: Any):
        raise TypeError(f"unorderable type: {type(self).__name__}")

    def __le__(self, other: Any):
        raise TypeError(f"unorderable type: {type(self).__name__}")

    def __ge__(self, other: Any):
        raise TypeError(f"unorderable type: {type(self).__name__}")

    def __add__(self, bs: Any) -> Bits:
        """Concatenate bitstrings and return new bitstring.

        bs -- the bitstring to append.

        """
        bs = Bits(bs)
        if bs.len <= self.len:
            s = self._copy()
            s._addright(bs)
        else:
            s = bs._copy()
            s = self.__class__(s)
            s._addleft(self)
        return s

    def __radd__(self, bs: Any) -> Bits:
        """Append current bitstring to bs and return new bitstring.

        bs -- the string for the 'auto' initialiser that will be appended to.

        """
        bs = self._converttobitstring(bs)
        return bs.__add__(self)

    @overload
    def __getitem__(self, key: slice) -> Bits: ...
    @overload
    def __getitem__(self, key: int) -> bool: ...

    def __getitem__(self, key: Union[slice, int]) -> Union[Bits, bool]:
        """Return a new bitstring representing a slice of the current bitstring.

        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.

        >>> print(BitArray('0b00110')[1:4])
        '0b011'
        >>> print(BitArray('0x00112233')[1:3:8])
        '0x1122'

        """
        length = self._getlength()
        if isinstance(key, slice):
            step = key.step if key.step is not None else 1
            if step != 1:
                # convert to binary string and use string slicing
                bs = self.__class__()
                if _lsb0:
                    start = length - key.start - 1 if key.start is not None else None
                    stop = length - key.stop - 1 if key.stop is not None else None
                    bs._setbin_unsafe(self._getbin().__getitem__(slice(start, stop, -step))[::-1])
                else:
                    bs._setbin_unsafe(self._getbin().__getitem__(key))
                return bs
            start, stop = 0, length
            if key.start is not None:
                start = key.start
                if key.start < 0:
                    start += stop
            if key.stop is not None:
                stop = key.stop
                if key.stop < 0:
                    stop += length
            start = max(start, 0)
            stop = min(stop, length)
            if start < stop:
                return self._slice(start, stop)
            else:
                return self.__class__()
        else:
            # single element
            if key < 0:
                key += length
            if not 0 <= key < length:
                raise IndexError("Slice index out of range.")
            # Single bit, return True or False
            return self._datastore.getbit(key)

    def __len__(self) -> int:
        """Return the length of the bitstring in bits."""
        return self._getlength()

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

    def __repr__(self) -> str:
        """Return representation that could be used to recreate the bitstring.

        If the returned string is too long it will be truncated. See __str__().

        """
        length = self.len
        pos_string = "" if self._pos in (0, None) else f", pos={self._pos}"
        if isinstance(self._datastore.rawarray, MmapByteArray):
            offsetstring = ''
            if self._datastore.byteoffset or self._offset:
                offsetstring = ", offset=%d" % (self._datastore.rawarray.byteoffset * 8 + self._offset)
            lengthstring = ", length=%d" % length
            return "{0}(filename={1}{2}{3}{4})".format(self.__class__.__name__,
                                                       repr(str(self._datastore.rawarray.source.name)),
                                                       lengthstring, offsetstring, pos_string)
        else:
            s = self.__str__()
            lengthstring = ''
            if s.endswith('...'):
                lengthstring = "  # length={0}".format(length)
            return "{0}('{1}'{2}){3}".format(self.__class__.__name__, s, pos_string, lengthstring)

    def __eq__(self, bs: Any) -> bool:
        """Return True if two bitstrings have the same binary representation.

        >>> BitArray('0b1110') == '0xe'
        True

        """
        try:
            bs = Bits(bs)
        except TypeError:
            return False
        return equal(self._datastore, bs._datastore)

    def __ne__(self, bs: Any) -> bool:
        """Return False if two bitstrings have the same binary representation.

        >>> BitArray('0b111') == '0x7'
        False

        """
        return not self.__eq__(bs)

    def __invert__(self) -> Bits:
        """Return bitstring with every bit inverted.

        Raises Error if the bitstring is empty.

        """
        if not self.len:
            raise Error("Cannot invert empty bitstring.")
        s = self._copy()
        s._invert_all()
        return s

    def __lshift__(self, n: int) -> Bits:
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

    def __rshift__(self, n: int) -> Bits:
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

    def __mul__(self, n: int) -> Bits:
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

    def __rmul__(self, n: int) -> Bits:
        """Return bitstring consisting of n concatenations of self.

        Called for expressions of the form 'a = 3*b'.
        n -- The number of concatenations. Must be >= 0.

        """
        return self.__mul__(n)

    def __and__(self, bs: BitsType) -> Bits:
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        bs = Bits(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for & operator.")
        s = self._copy()
        s._iand(bs)
        return s

    def __rand__(self, bs: BitsType) -> Bits:
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- the bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__and__(bs)

    def __or__(self, bs: BitsType) -> Bits:
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        bs = Bits(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for | operator.")
        s = self._copy()
        s._ior(bs)
        return s

    def __ror__(self, bs: BitsType) -> Bits:
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__or__(bs)

    def __xor__(self, bs: BitsType) -> Bits:
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        bs = Bits(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for ^ operator.")
        s = self._copy()
        s._ixor(bs)
        return s

    def __rxor__(self, bs: BitsType) -> Bits:
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__xor__(bs)

    def __contains__(self, bs: BitsType) -> bool:
        """Return whether bs is contained in the current bitstring.

        bs -- The bitstring to search for.

        """
        # Don't want to change pos
        pos = self._pos
        found = Bits.find(self, bs, bytealigned=False)
        self._pos = pos
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
        return self.any(True)

    @classmethod
    def _init_with_token(cls, name: str, token_length: Optional[int], value: Optional[str]) -> Bits:
        if token_length == 0:
            return cls()
        # For pad token just return the length in zero bits
        if name == 'pad':
            return cls(token_length)
        if value is None:
            if token_length is None:
                raise ValueError(f"Token has no value ({name}=???).")
            else:
                raise ValueError(f"Token has no value ({name}:{token_length}=???).")
        try:
            b = cls(**{_tokenname_to_initialiser[name]: value})
        except KeyError:
            if name in ('se', 'ue', 'sie', 'uie'):
                if _lsb0:
                    raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
                b = cls(**{name: int(value)})
            elif name in ('uint', 'int', 'uintbe', 'intbe', 'uintle', 'intle', 'uintne', 'intne'):
                b = cls(**{name: int(value), 'length': token_length})
            elif name in ('float', 'floatbe', 'floatle', 'floatne'):
                b = cls(**{name: float(value), 'length': token_length})
            elif name == 'bool':
                if value in (1, 'True', '1'):
                    b = cls(bool=True)
                elif value in (0, 'False', '0'):
                    b = cls(bool=False)
                else:
                    raise CreationError("bool token can only be 'True' or 'False'.")
            else:
                raise CreationError(f"Can't parse token name {name}.")
        if token_length is not None and b.len != token_length:
            raise CreationError(f"Token with length {token_length} packed with value of length {b.len} "
                                f"({name}:{token_length}={value}).")
        return b

    def _clear(self) -> None:
        """Reset the bitstring to an empty state."""
        self._datastore = ByteStore(bytearray(0))

    def _setauto(self, s: Any, length: Optional[int], offset: int) -> None:
        """Set bitstring from a bitstring, file, bool, integer, array, iterable or string."""
        # As s can be so many different things it's important to do the checks
        # in the correct order, as some types are also other allowed types.
        # So str must be checked before Iterable
        # and bytes/bytearray before Iterable but after str!
        if isinstance(s, Bits):
            if length is None:
                length = s._getlength() - offset
            self._setbytes_unsafe(s._datastore.rawbytes, length, s._offset + offset)
            return

        if isinstance(s, io.BytesIO):
            if length is None:
                length = s.seek(0, 2) * 8 - offset
            byteoffset, offset = divmod(offset, 8)
            bytelength = (length + byteoffset * 8 + offset + 7) // 8 - byteoffset
            if length + byteoffset * 8 + offset > s.seek(0, 2) * 8:
                raise CreationError("BytesIO object is not long enough for specified length and offset.")
            self._datastore = ByteStore(bytearray(s.getvalue()[byteoffset: byteoffset + bytelength]),
                                        length, offset)
            return

        if isinstance(s, io.BufferedReader):
            if length is None:
                length = os.path.getsize(s.name) * 8 - offset
            byteoffset, offset = divmod(offset, 8)
            bytelength = (length + byteoffset * 8 + offset + 7) // 8 - byteoffset
            m = MmapByteArray(s, bytelength, byteoffset)
            if length + byteoffset * 8 + offset > m.filelength * 8:
                raise CreationError("File is not long enough for specified length and offset.")
            self._datastore = ByteStore(m, length, offset)
            return

        if length is not None:
            raise CreationError("The length keyword isn't applicable to this initialiser.")
        if offset > 0:
            raise CreationError("The offset keyword isn't applicable to this initialiser.")
        if isinstance(s, str):
            bs = self._converttobitstring(s)
            assert bs._offset == 0
            self._setbytes_unsafe(bs._datastore.rawbytes, bs.length, 0)
            return
        if isinstance(s, (bytes, bytearray)):
            self._setbytes_unsafe(bytearray(s), len(s) * 8, 0)
            return
        if isinstance(s, array.array):
            b = s.tobytes()
            self._setbytes_unsafe(bytearray(b), len(b) * 8, 0)
            return
        if isinstance(s, int):
            # Initialise with s zero bits.
            if s < 0:
                raise CreationError(f"Can't create bitstring of negative length {s}.")
            data = bytearray((s + 7) // 8)
            self._datastore = ByteStore(data, int(s), 0)
            return
        if isinstance(s, abc.Iterable):
            # Evaluate each item as True or False and set bits to 1 or 0.
            self._setbin_unsafe(''.join(str(int(bool(x))) for x in s))
            return
        raise TypeError(f"Cannot initialise bitstring from {type(s)}.")

    def _setfile(self, filename: str, length: Optional[int], offset: Optional[int]) -> None:
        """Use file as source of bits."""
        with open(pathlib.Path(filename), 'rb') as source:
            if offset is None:
                offset = 0
            if length is None:
                length = os.path.getsize(source.name) * 8 - offset
            byteoffset, offset = divmod(offset, 8)
            bytelength = (length + byteoffset * 8 + offset + 7) // 8 - byteoffset
            m = MmapByteArray(source, bytelength, byteoffset)
            if length + byteoffset * 8 + offset > m.filelength * 8:
                raise CreationError("File is not long enough for specified length and offset.")
            self._datastore = ByteStore(m, length, offset)

    def _setbytes_safe(self, data: Union[bytearray, bytes, MmapByteArray],
                       length: Optional[int] = None, offset: Optional[int] = None) -> None:
        """Set the data from a string."""
        data = bytearray(data)
        if offset is None:
            offset = 0
        if length is None:
            # Use to the end of the data
            length = len(data)*8 - offset
            self._datastore = ByteStore(data, length, offset)
        else:
            if length + offset > len(data) * 8:
                raise CreationError(f"Not enough data present. Need {length + offset} bits, have {len(data) * 8}.")
            if length == 0:
                self._datastore = ByteStore(bytearray(0))
            else:
                self._datastore = ByteStore(data, length, offset)

    def _setbytes_unsafe(self, data: Union[bytearray, MmapByteArray], length: int, offset: int):
        """Unchecked version of _setbytes_safe."""
        self._datastore = type(self._datastore)(data[:], length, offset)

    def _readbytes(self, start: int, length: int) -> bytes:
        """Read bytes and return them. Note that length is in bits."""
        assert length % 8 == 0
        assert start + length <= self.len
        if not (start + self._offset) % 8:
            return bytes(self._datastore.getbyteslice((start + self._offset) // 8,
                                                      (start + self._offset + length) // 8))
        return self._slice(start, start + length).tobytes()

    def _getbytes(self) -> bytes:
        """Return the data as an ordinary bytes object."""
        if self.len % 8:
            raise InterpretError("Cannot interpret as bytes unambiguously - not multiple of 8 bits.")
        return self._readbytes(0, self.len)

    _unprintable = list(range(0x00, 0x20))  # ASCII control characters
    _unprintable.extend(range(0x7f, 0xa1))  # More UTF-8 control characters
    _unprintable.append(0xad)  # Soft hyphen, usually rendered invisibly!

    def _getbytes_printable(self) -> str:
        """Return an approximation of the data as a string of printable characters."""
        bytes_ = self._getbytes()
        # Replace unprintable characters with '.'
        string = ''.join('.' if x in Bits._unprintable else chr(x) for x in bytes_)
        return string

    def _setuint(self, uint: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Reset the bitstring to have given unsigned int interpretation."""
        with suppress(AttributeError):  # bitstring will only have a _datastore if it's been created
            if length is None:
                # Use the whole length. Deliberately not using .len here.
                length = self._datastore.bitlength
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a uint initialiser.")
        if _offset is not None:
            raise CreationError("An offset can't be specified with an integer initialiser.")
        if uint >= (1 << length):
            msg = f"{uint} is too large an unsigned integer for a bitstring of length {length}. "\
                  f"The allowed range is [0, {(1 << length) - 1}]."
            raise CreationError(msg)
        if uint < 0:
            raise CreationError("uint cannot be initialised with a negative number.")
        data = int.to_bytes(uint, (length + 7) // 8, 'big')

        offset = 8 - (length % 8)
        if offset == 8:
            offset = 0
        self._setbytes_unsafe(bytearray(data), length, offset)

    def _readuint(self, start: int, length: int) -> int:
        # TODO: This needs to be refactored again.
        if _lsb0:
            return self._readuint_lsb0(start, length)
        else:
            return self._readuint_msb0(start, length)

    def _readuint_lsb0(self, start: int, length: int) -> int:
        return self._readuint_msb0(self.len - start - length, length)

    def _readuint_msb0(self, start: int, length: int) -> int:
        """Read bits and interpret as an unsigned int."""
        if length == 0:
            raise InterpretError("Cannot interpret a zero length bitstring as an integer.")
        offset = self._offset
        startbyte = (start + offset) // 8
        endbyte = (start + offset + length - 1) // 8

        i = int.from_bytes(self._datastore.getbyteslice(startbyte, endbyte + 1), 'big')
        final_bits = 8 - ((start + offset + length) % 8)
        if final_bits != 8:
            i >>= final_bits
        i &= (1 << length) - 1
        return i

    def _getuint(self) -> int:
        """Return data as an unsigned int."""
        return self._readuint(0, self.len)

    def _setint(self, int_: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Reset the bitstring to have given signed int interpretation."""
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with an int initialiser.")
        if int_ >= (1 << (length - 1)) or int_ < -(1 << (length - 1)):
            raise CreationError(f"{int_} is too large a signed integer for a bitstring of length {length}. "
                                f"The allowed range is [{-(1 << (length - 1))}, {(1 << (length - 1)) - 1}].")
        if int_ >= 0:
            self._setuint(int_, length)
            return
        # Do the 2's complement thing. Add one, set to minus number, then flip bits.
        self._setuint((-int_ - 1) ^ ((1 << length) - 1), length)

    def _readint(self, start: int, length: int) -> int:
        """Read bits and interpret as a signed int"""
        ui = self._readuint(start, length)
        if not ui >> (length - 1):
            # Top bit not set, number is positive
            return ui
        # Top bit is set, so number is negative
        tmp = (~(ui - 1)) & ((1 << length) - 1)
        return -tmp

    def _getint(self) -> int:
        """Return data as a two's complement signed int."""
        return self._readint(0, self.len)

    def _setuintbe(self, uintbe: int, length: Optional[int] = None, _offset: None = None) -> None:
        """Set the bitstring to a big-endian unsigned int interpretation."""
        if length is not None and length % 8 != 0:
            raise CreationError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
        self._setuint(uintbe, length)

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
        if length is not None and length % 8 != 0:
            raise CreationError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
        self._setint(intbe, length)

    def _readintbe(self, start: int, length: int) -> int:
        """Read bits and interpret as a big-endian signed int."""
        if length % 8:
            raise InterpretError(f"Big-endian integers must be whole-byte. Length = {length} bits.")
        return self._readint(start, length)

    def _getintbe(self) -> int:
        """Return data as a big-endian two's complement signed int."""
        return self._readintbe(0, self.len)

    def _setuintle(self, uintle: int, length: Optional[int] = None, _offset: None = None) -> None:
        if length is not None and length % 8 != 0:
            raise CreationError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
        self._setuint(uintle, length)
        self._datastore.rawarray = self._datastore.rawarray[::-1]

    def _readuintle(self, start: int, length: int) -> int:
        """Read bits and interpret as a little-endian unsigned int."""
        if length % 8:
            raise InterpretError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
        assert start + length <= self.len
        absolute_pos = start + self._offset
        startbyte, offset = divmod(absolute_pos, 8)
        val = 0
        if not offset:
            endbyte = (absolute_pos + length - 1) // 8
            chunksize = 4  # for 'L' format
            while endbyte - chunksize + 1 >= startbyte:
                val <<= 8 * chunksize
                val += struct.unpack('<L', bytes(self._datastore.getbyteslice(endbyte + 1 - chunksize, endbyte + 1)))[0]
                endbyte -= chunksize
            for b in range(endbyte, startbyte - 1, -1):
                val <<= 8
                val += self._datastore.getbyte(b)
        else:
            data = self._slice(start, start + length)
            assert data.len % 8 == 0
            data._reversebytes(0, self.len)
            for b in bytearray(data.bytes):
                val <<= 8
                val += b
        return val

    def _getuintle(self) -> int:
        return self._readuintle(0, self.len)

    def _setintle(self, intle: int, length: Optional[int] = None, _offset: None = None) -> None:
        if length is not None and length % 8 != 0:
            raise CreationError(f"Little-endian integers must be whole-byte. Length = {length} bits.")
        self._setint(intle, length)
        self._datastore.rawarray = self._datastore.rawarray[::-1]

    def _readintle(self, start: int, length: int) -> int:
        """Read bits and interpret as a little-endian signed int."""
        ui = self._readuintle(start, length)
        if not ui >> (length - 1):
            # Top bit not set, number is positive
            return ui
        # Top bit is set, so number is negative
        tmp = (~(ui - 1)) & ((1 << length) - 1)
        return -tmp

    def _getintle(self) -> int:
        return self._readintle(0, self.len)

    def _setfloat(self, f: float, struct_dict: Dict[int, str], length: Optional[int] = None):
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a float initialiser.")
        try:
            b = struct.pack(struct_dict[length], f)
            self._setbytes_unsafe(bytearray(b), length, 0)
        except KeyError:
            raise CreationError(f"Floats can only be 16, 32 or 64 bits long, not {length} bits")
        except (OverflowError, struct.error):
            # If float64 doesn't fit it automatically goes to 'inf'. This reproduces that behaviour for other types.
            if length in [16, 32]:
                b = struct.pack(struct_dict[length], float('inf') if f > 0 else float('-inf'))
                self._setbytes_unsafe(bytearray(b), length, 0)

    def _readfloat(self, start: int, length: int, struct_dict: Dict[int, str]) -> float:
        """Read bits and interpret as a float."""
        try:
            fmt = struct_dict[length]
        except KeyError:
            raise InterpretError(f"Floats can only be 16, 32 or 64 bits long, not {length} bits")

        if _lsb0:
            start = self._getlength() - start - length
        startbyte, offset = divmod(start + self._offset, 8)
        if offset == 0:
            return struct.unpack(fmt, bytes(self._datastore.getbyteslice(startbyte, startbyte + length // 8)))[0]
        else:
            return struct.unpack(fmt, self._readbytes(start, length))[0]

    def _setfloatbe(self, f: float, length: Optional[int] = None, _offset: None = None) -> None:
        self._setfloat(f, {16: '>e', 32: '>f', 64: '>d'}, length)

    def _readfloatbe(self, start: int, length: int) -> float:
        """Read bits and interpret as a big-endian float."""
        return self._readfloat(start, length, {16: '>e', 32: '>f', 64: '>d'})

    def _getfloatbe(self) -> float:
        """Interpret the whole bitstring as a big-endian float."""
        return self._readfloatbe(0, self.len)

    def _setfloatle(self, f: float, length: Optional[int] = None, _offset: None = None) -> None:
        self._setfloat(f, {16: '<e', 32: '<f', 64: '<d'}, length)

    def _readfloatle(self, start: int, length: int) -> float:
        """Read bits and interpret as a little-endian float."""
        return self._readfloat(start, length, {16: '<e', 32: '<f', 64: '<d'})

    def _getfloatle(self) -> float:
        """Interpret the whole bitstring as a little-endian float."""
        return self._readfloatle(0, self.len)

    def _getbfloatbe(self) -> float:
        return self._readbfloatbe(0, self.len)

    def _readbfloatbe(self, start: int, _length: int) -> float:
        if _length != 16:
            raise InterpretError(f"bfloats must be length 16, received a length of {_length} bits.")
        two_bytes = self._slice(start, start + 16)
        zero_padded = two_bytes + Bits(16)
        return zero_padded._getfloatbe()

    def _setbfloatbe(self, f: Union[float, str], length: Optional[int] = None, _offset: None = None) -> None:
        if length is not None and length != 16:
            raise CreationError(f"bfloats must be length 16, received a length of {length} bits.")
        f = float(f)
        four_byte_float = Bits(float=f, length=32)
        self._setbytes_unsafe(four_byte_float._datastore.rawarray[0:2], 16, 0)

    def _getbfloatle(self) -> float:
        return self._readbfloatle(0, self.len)

    def _readbfloatle(self, start: int, _length: int) -> float:
        two_bytes = self._slice(start, start + 16)
        zero_padded = Bits(16) + two_bytes
        return zero_padded._getfloatle()

    def _setbfloatle(self, f: Union[float, str], length: Optional[int] = None, _offset: None = None) -> None:
        if length is not None and length != 16:
            raise CreationError(f"bfloats must be length 16, received a length of {length} bits.")
        f = float(f)
        four_byte_float = Bits(floatle=f, length=32)
        self._setbytes_unsafe(four_byte_float._datastore.rawarray[2:4], 16, 0)

    def _setue(self, i: int, _length: None = None, _offset: None = None) -> None:
        """Initialise bitstring with unsigned exponential-Golomb code for integer i.

        Raises CreationError if i < 0.

        """
        if _lsb0:
            raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
        if _length is not None or _offset is not None:
            raise CreationError("Cannot specify a length of offset for exponential-Golomb codes.")
        if i < 0:
            raise CreationError("Cannot use negative initialiser for unsigned exponential-Golomb.")
        if not i:
            self._setbin_unsafe('1')
            return
        tmp = i + 1
        leadingzeros = -1
        while tmp > 0:
            tmp >>= 1
            leadingzeros += 1
        remainingpart = i + 1 - (1 << leadingzeros)
        binstring = '0' * leadingzeros + '1' + Bits(uint=remainingpart, length=leadingzeros).bin
        self._setbin_unsafe(binstring)

    def _readue(self, pos: int, _length: None = None) -> Tuple[int, int]:
        """Return interpretation of next bits as unsigned exponential-Golomb code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        if _lsb0:
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
        if i > 0:
            u = (i * 2) - 1
        else:
            u = -2 * i
        self._setue(u)

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

    def _readse(self, pos: int, _length: int = 0) -> Tuple[int, int]:
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
        if _lsb0:
            raise CreationError("Exp-Golomb codes cannot be used in lsb0 mode.")
        if i < 0:
            raise CreationError("Cannot use negative initialiser for unsigned interleaved exponential-Golomb.")
        self._setbin_unsafe('1' if i == 0 else '0' + '0'.join(bin(i + 1)[3:]) + '1')

    def _readuie(self, pos: int, _length: None = None) -> Tuple[int, int]:
        """Return interpretation of next bits as unsigned interleaved exponential-Golomb code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        if _lsb0:
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

    def _setsie(self, i: int, _length: None = None, _offset: None = None) -> None:
        """Initialise bitstring with signed interleaved exponential-Golomb code for integer i."""
        if not i:
            self._setbin_unsafe('1')
        else:
            self._setuie(abs(i))
            self._addright(Bits([i < 0]))

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

    def _readsie(self, pos: int, _length: int = 0) -> Tuple[int, int]:
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
            self._setbytes_unsafe(bytearray(b'\x80'), 1, 0)
        elif value in (0, 'False'):
            self._setbytes_unsafe(bytearray(b'\x00'), 1, 0)
        else:
            raise CreationError(f"Cannot initialise boolean with {value}.")

    def _getbool(self) -> bool:
        if self.length != 1:
            raise InterpretError(f"For a bool interpretation a bitstring must be 1 bit long, not {self.length} bits.")
        return self[0]

    def _readbool(self, pos: int, _length: None = None) -> Tuple[int, int]:
        return self[pos], pos + 1

    def _readpad(self, _pos, _length) -> None:
        return None

    def _setbin_safe(self, binstring: str, _length: None = None, _offset: None = None) -> None:
        """Reset the bitstring to the value given in binstring."""
        binstring = tidy_input_string(binstring)
        # remove any 0b if present
        binstring = binstring.replace('0b', '')
        self._setbin_unsafe(binstring)

    def _setbin_unsafe(self, binstring: str, _length: None = None, _offset: None = None) -> None:
        """Same as _setbin_safe, but input isn't sanity checked. binstring mustn't start with '0b'."""
        if binstring == '':
            self._setbytes_unsafe(bytearray(), 0, 0)
            return
        try:
            i = int(binstring, 2)
        except ValueError:
            raise CreationError(f"Invalid character in bin initialiser {binstring}.")
        if len(binstring) % 8 != 0:
            i <<= 8 - (len(binstring) % 8)
        b = i.to_bytes((len(binstring) + 7) // 8, 'big')
        self._setbytes_unsafe(bytearray(b), len(binstring), 0)

    def _readbin(self, start: int, length: int) -> str:
        """Read bits and interpret as a binary string."""
        if length == 0:
            return ''
        b = self._slice(start, start + length).tobytes()
        integer = int.from_bytes(b, 'big')
        c = "{:0{}b}".format(integer, 8*len(b))
        return c[0:length]

    def _getbin(self) -> str:
        """Return interpretation as a binary string."""
        return self._readbin(0, self.len)

    def _setoct(self, octstring: str, _length: None = None, _offset: None = None) -> None:
        """Reset the bitstring to have the value given in octstring."""
        octstring = tidy_input_string(octstring)
        # remove any 0o if present
        octstring = octstring.replace('0o', '')
        binlist = []
        for i in octstring:
            try:
                binlist.append(Bits._octToBits[int(i)])
            except (ValueError, IndexError):
                raise CreationError(f"Invalid symbol '{i}' in oct initialiser.")
        self._setbin_unsafe(''.join(binlist))

    def _readoct(self, start: int, length: int) -> str:
        """Read bits and interpret as an octal string."""
        if length % 3:
            raise InterpretError("Cannot convert to octal unambiguously - not multiple of 3 bits long.")
        if not length:
            return ''
        # Get main octal bit by converting from int.
        # Strip starting '0o'.
        end = oct(self._readuint(start, length))[2:]
        middle = '0' * (length // 3 - len(end))
        return middle + end

    def _getoct(self) -> str:
        """Return interpretation as an octal string."""
        return self._readoct(0, self.len)

    def _sethex(self, hexstring: str, _length: None = None, _offset: None = None) -> None:
        """Reset the bitstring to have the value given in hexstring."""
        hexstring = tidy_input_string(hexstring)
        # remove any 0x if present
        hexstring = hexstring.replace('0x', '')
        length = len(hexstring)
        if length % 2:
            hexstring += '0'
        try:
            data = bytearray.fromhex(hexstring)
        except ValueError:
            raise CreationError("Invalid symbol in hex initialiser.")
        self._setbytes_unsafe(data, length * 4, 0)

    def _readhex(self, start: int, length: int) -> str:
        """Read bits and interpret as a hex string."""
        if length % 4:
            raise InterpretError("Cannot convert to hex unambiguously - not a multiple of 4 bits long.")
        if not length:
            return ''
        s = self._slice(start, start + length).tobytes()
        s = s.hex()
        # If there's one nibble too many then cut it off
        return s[:-1] if (length // 4) % 2 else s

    def _gethex(self) -> str:
        """Return the hexadecimal representation as a string prefixed with '0x'.

        Raises an InterpretError if the bitstring's length is not a multiple of 4.

        """
        return self._readhex(0, self.len)

    def _getoffset(self) -> int:
        return self._datastore.offset

    def _getlength(self) -> int:
        """Return the length of the bitstring in bits."""
        return self._datastore.bitlength

    @classmethod
    def _converttobitstring(cls, bs: BitsType, offset: int = 0, cache: Dict = {}) -> Bits:
        """Convert bs to a bitstring and return it.

        offset gives the suggested bit offset of first significant
        bit, to optimise append etc.

        """
        if isinstance(bs, Bits):
            return bs
        try:
            return cache[(bs, offset)]
        except KeyError:
            if isinstance(bs, str):
                b = cls()
                try:
                    _, tokens = tokenparser(bs)
                except ValueError as e:
                    raise CreationError(*e.args)
                if tokens:
                    b._addright(Bits._init_with_token(*tokens[0]))
                    b._datastore = offsetcopy(b._datastore, offset)
                    for token in tokens[1:]:
                        b._addright(Bits._init_with_token(*token))
                assert b.len == 0 or b._offset == offset
                if len(cache) < CACHE_SIZE:
                    cache[(bs, offset)] = b
                return b
        except TypeError:
            # Unhashable type
            pass
        return cls(bs)

    def _copy(self) -> Bits:
        """Create and return a new copy of the Bits (always in memory)."""
        s_copy = self.__class__()
        s_copy._setbytes_unsafe(self._datastore.getbyteslice(0, self._datastore.bytelength),
                                self.len, self._offset)
        return s_copy

    def _slice_lsb0(self, start: int, end: int) -> Bits:
        """Used internally to get a slice, without error checking (LSB0)."""
        return self._absolute_slice(self.length - end, self.length - start)

    def _slice_msb0(self, start: int, end: int) -> Bits:
        """Used internally to get a slice, without error checking (MSB0)."""
        return self._absolute_slice(start, end)

    def _absolute_slice(self, start: int, end: int) -> Bits:
        """Used internally to get a slice, without error checking.
        Uses MSB0 bit numbering even if LSB0 is set."""
        if end == start:
            return self.__class__()
        assert start < end, f"start={start}, end={end}"
        offset = self._offset
        startbyte, newoffset = divmod(start + offset, 8)
        endbyte = (end + offset - 1) // 8
        bs = self.__class__()
        bs._setbytes_unsafe(self._datastore.getbyteslice(startbyte, endbyte + 1), end - start, newoffset)
        return bs

    def _readtoken(self, name: str, pos: int, length: Optional[int]) -> Tuple[Union[float, int, str, None, Bits], int]:
        """Reads a token from the bitstring and returns the result."""
        if length is not None and int(length) > self.length - pos:
            raise ReadError("Reading off the end of the data. "
                            f"Tried to read {int(length)} bits when only {self.length - pos} available.")
        try:
            val = self._name_to_read[name](self, pos, length)
            if isinstance(val, tuple):
                return val
            else:
                assert length is not None
                return val, pos + length
        except KeyError:
            raise ValueError(f"Can't parse token {name}:{length}")

    def _addright(self, bs: Bits) -> None:
        """Add a bitstring to the RHS of the current bitstring."""
        self._datastore.appendstore(bs._datastore)

    def _addleft(self, bs: Bits) -> None:
        """Prepend a bitstring to the current bitstring."""
        self._datastore.prependstore(bs._datastore)

    def _reverse(self) -> None:
        """Reverse all bits in-place."""
        # Reverse the contents of each byte
        n = [Bits._byteReversalDict[b] for b in self._datastore.rawbytes]
        # Then reverse the order of the bytes
        n.reverse()
        # The new offset is the number of bits that were unused at the end.
        newoffset = 8 - (self._offset + self.len) % 8
        if newoffset == 8:
            newoffset = 0
        self._setbytes_unsafe(bytearray().join(n), self.length, newoffset)

    def _truncateleft(self, bits: int) -> Bits:
        """Truncate bits from the start of the bitstring. Return the truncated bits."""
        assert 0 <= bits <= self.len
        if not bits:
            return Bits()
        truncated_bits = self._absolute_slice(0, bits)
        if bits == self.len:
            self._clear()
            return truncated_bits
        bytepos, offset = divmod(self._offset + bits, 8)
        self._setbytes_unsafe(self._datastore.getbyteslice(bytepos, self._datastore.bytelength), self.len - bits,
                              offset)
        return truncated_bits

    def _truncateright(self, bits: int) -> Bits:
        """Truncate bits from the end of the bitstring. Return the truncated bits."""
        assert 0 <= bits <= self.len
        if not bits:
            return Bits()
        truncated_bits = self._absolute_slice(self.length - bits, self.length)
        if bits == self.len:
            self._clear()
            return truncated_bits
        newlength_in_bytes = (self._offset + self.len - bits + 7) // 8
        self._setbytes_unsafe(self._datastore.getbyteslice(0, newlength_in_bytes), self.len - bits,
                              self._offset)
        return truncated_bits

    def _insert_lsb0(self, bs: Bits, pos: int) -> None:
        """Insert bs at pos (LSB0)."""
        self._insert_msb0(bs, self.len - pos)

    def _insert_msb0(self, bs: Bits, pos: int) -> None:
        """Insert bs at pos."""
        assert 0 <= pos <= self.len
        if pos > self.len // 2:
            # Inserting nearer end, so cut off end.
            end = self._truncateright(self.len - pos)
            self._addright(bs)
            self._addright(end)
        else:
            # Inserting nearer start, so cut off start.
            start = self._slice(0, pos)
            self._truncateleft(pos)
            self._addleft(bs)
            self._addleft(start)
        if self._pos is not None:
            self._pos = pos + bs.len

    def _overwrite_lsb0(self, bs: Bits, pos: int) -> None:
        """Overwrite with bs at pos (LSB0)."""
        self._overwrite_msb0(bs, self.len - pos - bs.len)

    def _overwrite_msb0(self, bs: Bits, pos: int) -> None:
        """Overwrite with bs at pos."""
        assert 0 <= pos <= self.len
        if bs is self:
            # Just overwriting with self, so do nothing.
            assert pos == 0
            return
        if pos + bs.len > self.len:
            # The overwrite goes past the end. Easiest thing is to extend with zeros then overwrite.
            self._addright(Bits(pos + bs.len - self.len))
        firstbytepos = (self._offset + pos) // 8
        lastbytepos = (self._offset + pos + bs.len - 1) // 8
        bytepos, bitoffset = divmod(self._offset + pos, 8)
        if firstbytepos == lastbytepos:
            mask = ((1 << bs.len) - 1) << (8 - bs.len - bitoffset)
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) & (~mask))
            d = offsetcopy(bs._datastore, bitoffset)
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) | (d.getbyte(0) & mask))
        else:
            # Do first byte
            mask = (1 << (8 - bitoffset)) - 1
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) & (~mask))
            d = offsetcopy(bs._datastore, bitoffset)
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) | (d.getbyte(0) & mask))
            # Now do all the full bytes
            self._datastore.setbyteslice(firstbytepos + 1, lastbytepos, d.getbyteslice(1, lastbytepos - firstbytepos))
            # and finally the last byte
            bitsleft = (self._offset + pos + bs.len) % 8
            if not bitsleft:
                bitsleft = 8
            mask = (1 << (8 - bitsleft)) - 1
            self._datastore.setbyte(lastbytepos, self._datastore.getbyte(lastbytepos) & mask)
            self._datastore.setbyte(lastbytepos,
                                    self._datastore.getbyte(lastbytepos) | (d.getbyte(d.bytelength - 1) & ~mask))

    def _delete_lsb0(self, bits: int, pos: int) -> None:
        """Delete bits at pos (LSB0)."""
        self._delete_msb0(bits, self.len - pos - bits)

    def _delete_msb0(self, bits: int, pos: int) -> None:
        """Delete bits at pos."""
        assert 0 <= pos <= self.len
        assert pos + bits <= self.len, f"pos={pos}, bits={bits}, len={self.len}"
        if not pos:
            # Cutting bits off at the start.
            self._truncateleft(bits)
            return
        if pos + bits == self.len:
            # Cutting bits off at the end.
            self._truncateright(bits)
            return
        if pos > self.len - pos - bits:
            # More bits before cut point than after it, so do bit shifting
            # on the final bits.
            end = self._slice_msb0(pos + bits, self.len)
            assert self.len - pos > 0
            self._truncateright(self.len - pos)
            self._addright(end)
            return
        # More bits after the cut point than before it.
        start = self._slice_msb0(0, pos)
        self._truncateleft(pos + bits)
        self._addleft(start)
        return

    def _reversebytes(self, start: int, end: int) -> None:
        """Reverse bytes in-place."""
        # Make the start occur on a byte boundary
        # TODO: We could be cleverer here to avoid changing the offset.
        newoffset = 8 - (start % 8)
        if newoffset == 8:
            newoffset = 0
        self._datastore = offsetcopy(self._datastore, newoffset)
        # Now just reverse the byte data
        toreverse = bytearray(self._datastore.getbyteslice((newoffset + start) // 8, (newoffset + end) // 8))
        toreverse.reverse()
        self._datastore.setbyteslice((newoffset + start) // 8, (newoffset + end) // 8, toreverse)

    def _set(self, pos: int) -> None:
        """Set bit at pos to 1."""
        assert 0 <= pos < self.len
        self._datastore.setbit(pos)

    def _unset(self, pos: int) -> None:
        """Set bit at pos to 0."""
        assert 0 <= pos < self.len
        self._datastore.unsetbit(pos)

    def _invert(self, pos: int) -> None:
        """Flip bit at pos 1<->0."""
        assert 0 <= pos < self.len
        self._datastore.invertbit(pos)

    def _invert_all(self) -> None:
        """Invert every bit."""
        for p in range(self._datastore.byteoffset, self._datastore.byteoffset + self._datastore.bytelength):
            self._datastore.rawarray[p] = 256 + ~self._datastore.rawarray[p]

    def _ilshift(self, n: int) -> Bits:
        """Shift bits by n to the left in place. Return self."""
        assert 0 < n <= self.len
        self._addright(Bits(n))
        self._truncateleft(n)
        return self

    def _irshift(self, n: int) -> Bits:
        """Shift bits by n to the right in place. Return self."""
        assert 0 < n <= self.len
        self._addleft(Bits(n))
        self._truncateright(n)
        return self

    def _imul(self, n: int) -> Bits:
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

    def _inplace_logical_helper(self, bs: Bits, f: Callable[[int, int], int]) -> Bits:
        """Helper function containing most of the __ior__, __iand__, __ixor__ code."""
        # Give the two bitstrings the same offset (modulo 8)
        self_byteoffset, self_bitoffset = divmod(self._getoffset(), 8)
        bs_byteoffset, bs_bitoffset = divmod(bs._getoffset(), 8)
        if bs_bitoffset != self_bitoffset:
            if not self_bitoffset:
                bs._datastore = offsetcopy(bs._datastore, 0)
            else:
                self._datastore = offsetcopy(self._datastore, bs_bitoffset)
        a = self._datastore.rawbytes
        b = bs._datastore.rawbytes
        for i in range(len(a)):
            a[i] = f(a[i + self_byteoffset], b[i + bs_byteoffset])
        return self

    def _ior(self, bs: Bits) -> Bits:
        return self._inplace_logical_helper(bs, operator.ior)

    def _iand(self, bs: Bits) -> Bits:
        return self._inplace_logical_helper(bs, operator.iand)

    def _ixor(self, bs: Bits) -> Bits:
        return self._inplace_logical_helper(bs, operator.xor)

    def _readbits(self, start: int, length: int) -> Bits:
        """Read some bits from the bitstring and return newly constructed bitstring."""
        return self._slice(start, start + length)

    def _validate_slice_msb0(self, start: Optional[int], end: Optional[int]) -> Tuple[int, int]:
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

    def _validate_slice_lsb0(self, start: Optional[int], end: Optional[int]) -> Tuple[int, int]:
        start, end = self._validate_slice_msb0(start, end)
        return self._getlength() - end, self._getlength() - start

    def unpack(self, fmt: Union[str, List[Union[str, int]]], **kwargs) -> List[Union[float, int, str, None, Bits]]:
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

    def _readlist(self, fmt: Union[str, List[Union[str, int]]], pos: int, **kwargs: int)\
            -> Tuple[List[Union[float, int, str, None, Bits]], int]:
        tokens: List[Tuple[str, Optional[Union[str, int]], Optional[str]]] = []
        if isinstance(fmt, str):
            fmt = [fmt]
        keys = tuple(sorted(kwargs.keys()))

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
            if isinstance(f_item, int):
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
                if name in ('se', 'ue', 'sie', 'uie'):
                    raise Error("It's not possible to parse a variable length token after a 'filler' token.")
                else:
                    if length is None:
                        raise Error("It's not possible to have more than one 'filler' token.")
                    bits_after_stretchy_token += length
            if length is None and name not in ('se', 'ue', 'sie', 'uie'):
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

    def _findbytes(self, bytes_: bytes, start: int, end: int) -> Union[Tuple[int], Tuple[()]]:
        """Quicker version of find when everything's whole byte
        and byte aligned.

        """
        assert self._datastore.offset == 0
        # Extract data bytes from bitstring to be found.
        bytepos = (start + 7) // 8
        found = False
        p = bytepos
        finalpos = end // 8
        increment = max(1024, len(bytes_) * 10)
        buffersize = increment + len(bytes_)
        while p < finalpos:
            # Read in file or from memory in overlapping chunks and search the chunks.
            buf = bytearray(self._datastore.getbyteslice(p, min(p + buffersize, finalpos)))
            pos: int = buf.find(bytes_)
            if pos != -1:
                found = True
                p += pos
                break
            p += increment
        if not found:
            return ()
        return (p * 8,)

    def _findbin(self, binstr: str, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        """Find first occurrence of a binary string."""
        p = start
        length = len(binstr)
        # We grab overlapping chunks of the binary representation and
        # do an ordinary string search within that.
        increment = max(4096, length * 64)
        buffersize = increment + length
        while p < end:
            buf = self._readbin(p, min(buffersize, end - p))
            pos = buf.find(binstr)
            if pos != -1:
                if not bytealigned:
                    return (p + pos,)
                if (p + pos) % 8 == 0:  # TODO: Is this logic only right for MSB0?
                    return (p + pos,)
                # Advance to just beyond the non-byte-aligned match and try again...
                p += pos + 1
                continue
            p += increment
        # Not found, return empty tuple
        return ()

    def _rfindbin(self, binstr: str, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        """Find final occurrence of a binary string."""
        p = end
        # We grab overlapping chunks of the binary representation and
        # do an ordinary string search within that.
        increment = max(4096, len(binstr) * 64)
        buffersize = increment + len(binstr)
        while p > start:
            start_pos = max(start, p - buffersize)
            if not _lsb0:
                buf = self._readbin(start_pos, p - start_pos)
            else:
                buf = self._readbin(self.len - p, p - start_pos)
            pos = buf.rfind(binstr)
            if pos != -1:
                if not bytealigned:
                    return (pos + start_pos,)
                if (pos + start_pos) % 8 == 0:
                    return (pos + start_pos,)
                # Advance to just beyond the non-byte-aligned match and try again...
                p = pos + start_pos + len(binstr) - 1
                continue
            p -= increment
        # Not found, return empty tuple
        return ()

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
        bs = Bits(bs)
        if bs.len == 0:
            raise ValueError("Cannot find an empty bitstring.")
        start, end = self._validate_slice(start, end)
        ba = _bytealigned if bytealigned is None else bytealigned
        return self._find(bs, start, end, ba)

    def _find_lsb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        assert start <= end
        p = self._rfindbin(bs._getbin(), start, end, bytealigned)

        if p:
            newpos = self.length - p[0] - bs.length
            if self._pos is not None:
                self._pos = newpos
            return (newpos,)
        else:
            return ()

    def _find_msb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        if bytealigned and not bs.len % 8 and not self._datastore.offset:
            p = self._findbytes(bs.bytes, start, end)
        else:
            p = self._findbin(bs._getbin(), start, end, bytealigned)
        # If called from a class that has a pos, set it
        if p and self._pos is not None:
            self._pos = p[0]
        return p

    def findall(self, bs: Any, start: Optional[int] = None, end: Optional[int] = None, count: Optional[int] = None,
                bytealigned: Optional[bool] = None) -> Generator[int, None, None]:
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
        bs = Bits(bs)
        start, end = self._validate_slice(start, end)
        ba = _bytealigned if bytealigned is None else bytealigned
        return self._findall(bs, start, end, count, ba)

    def _findall_msb0(self, bs: Bits, start: int, end: int, count: Optional[int],
                      bytealigned: bool) -> Generator[int, None, None]:
        c = 0
        if bytealigned and not bs.len % 8 and not self._datastore.offset:
            # Use the quick find method
            f = functools.partial(self._findbytes, bytes_=bs._getbytes())
        else:
            f = functools.partial(self._findbin, binstr=bs._getbin(), bytealigned=bytealigned)
        while True:
            if count is not None and c >= count:
                return
            p = f(start=start, end=end)
            if not p:
                break
            c += 1
            if self._pos is not None:
                self._pos = p[0]
            yield p[0]
            if bytealigned:
                start = p[0] + 8
            else:
                start = p[0] + 1
            if start >= end:
                break
        return

    def _findall_lsb0(self, bs: Bits, start: int, end: int, count: Optional[int],
                      bytealigned: bool) -> Generator[int, None, None]:
        assert start <= end
        # Search chunks starting near the end and then moving back.
        c = 0
        increment = max(8192, bs.len * 80)
        buffersize = min(increment + bs.len, end - start)
        pos = max(start, end - buffersize)
        while True:
            found = list(self._findall_msb0(bs, start=pos, end=pos + buffersize, count=None,
                                            bytealigned=bytealigned))
            if not found:
                if pos == start:
                    return
                pos = max(start, pos - increment)
                continue
            while found:
                if count is not None and c >= count:
                    return
                c += 1
                yield self.len - found.pop() - bs.len
            pos = max(start, pos - increment)
            if pos == start:
                return

    def rfind(self, bs: Any, start: Optional[int] = None, end: Optional[int] = None,
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
        bs = Bits(bs)
        start, end = self._validate_slice(start, end)
        ba = _bytealigned if bytealigned is None else bytealigned
        if not bs.len:
            raise ValueError("Cannot find an empty bitstring.")
        p = self._rfind(bs, start, end, ba)
        # If called from a class that has a pos, set it
        if p and self._pos is not None:
            self._pos = p[0]
        return p

    def _rfind_msb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        return self._rfindbin(bs.bin, start, end, bytealigned)

    def _rfind_lsb0(self, bs: Bits, start: int, end: int, bytealigned: bool) -> Union[Tuple[int], Tuple[()]]:
        # A reverse find in lsb0 is very like a forward find in msb0.
        p = self._find_msb0(bs, start, end, bytealigned)
        if p:
            newpos = self.len - p[0] - bs.length
            if self._pos is not None:
                self._pos = newpos
            return (newpos,)
        else:
            return ()

    def cut(self, bits: int, start: Optional[int] = None, end: Optional[int] = None,
            count: Optional[int] = None) -> Generator[Bits, None, None]:
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

    def split(self, delimiter: Any, start: Optional[int] = None, end: Optional[int] = None,
              count: Optional[int] = None, bytealigned: Optional[bool] = None) -> Generator[Bits, None, None]:
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
        delimiter = Bits(delimiter)
        if not delimiter.len:
            raise ValueError("split delimiter cannot be empty.")
        start, end = self._validate_slice(start, end)
        bytealigned_: bool = _bytealigned if bytealigned is None else bytealigned
        if count is not None and count < 0:
            raise ValueError("Cannot split - count must be >= 0.")
        if count == 0:
            return
        if bytealigned_ and not delimiter.len % 8 and not self._datastore.offset:
            # Use the quick find method
            f = functools.partial(self._findbytes, bytes_=delimiter._getbytes())
        else:
            f = functools.partial(self._findbin, binstr=delimiter._getbin(), bytealigned=bytealigned_)
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

    def join(self, sequence: Iterable[Any]) -> Bits:
        """Return concatenation of bitstrings joined by self.

        sequence -- A sequence of bitstrings.

        """
        s = self.__class__()
        i = iter(sequence)
        try:
            s._addright(Bits(next(i)))
            while True:
                n = next(i)
                s._addright(self)
                s._addright(Bits(n))
        except StopIteration:
            pass
        return s

    def tobytes(self) -> bytes:
        """Return the bitstring as bytes, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        d = offsetcopy(self._datastore, 0).rawbytes
        # Need to ensure that unused bits at end are set to zero
        unusedbits = 8 - self.len % 8
        if unusedbits != 8:
            d[-1] &= (0xff << unusedbits)
        return bytes(d)

    def tofile(self, f: BinaryIO) -> None:
        """Write the bitstring to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        # If the bitstring is file based then we don't want to read it all
        # in to memory.
        chunksize = 1024 * 1024  # 1 MiB chunks
        if self._offset == 0:
            a = 0
            bytelen = self._datastore.bytelength
            p = self._datastore.getbyteslice(a, min(a + chunksize, bytelen - 1))
            while len(p) == chunksize:
                f.write(p)
                a += chunksize
                p = self._datastore.getbyteslice(a, min(a + chunksize, bytelen - 1))
            f.write(p)
            # Now the final byte, ensuring that unused bits at end are set to 0.
            bits_in_final_byte = self.len % 8
            if not bits_in_final_byte:
                bits_in_final_byte = 8
            f.write(self[-bits_in_final_byte:].tobytes())
        else:
            # Really quite inefficient...
            a = 0
            b = a + chunksize * 8
            while b <= self.len:
                f.write(self._slice(a, b)._getbytes())
                a += chunksize * 8
                b += chunksize * 8
            if a != self.len:
                f.write(self._slice(a, self.len).tobytes())

    def startswith(self, prefix: BitsType, start: Optional[int] = None, end: Optional[int] = None) -> bool:
        """Return whether the current bitstring starts with prefix.

        prefix -- The bitstring to search for.
        start -- The bit position to start from. Defaults to 0.
        end -- The bit position to end at. Defaults to len(self).

        """
        prefix = Bits(prefix)
        start, end = self._validate_slice_msb0(start, end)  # the _slice deals with msb0/lsb0
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
        suffix = Bits(suffix)
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
            pos = range(self.len)
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError(f"Bit position {p} out of range.")
            if not self._datastore.getbit(p) is value:
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
            pos = range(self.len)
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError(f"Bit position {p} out of range.")
            if self._datastore.getbit(p) is value:
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
        count = (self._getbin()).count('1')
        return count if value else self.len - count

    def pp(self, fmt: str = 'bin', width: int = 120, sep: Optional[str] = ' ',
           show_offset: bool = True, stream: TextIO = sys.stdout) -> None:
        """Pretty print the bitstring's value.

        fmt -- Printed data format. One of 'bin', 'oct', 'hex' or 'bytes'. Defaults to 'bin'.
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
        bpc = {'bin': 1, 'oct': 3, 'hex': 4, 'bytes': 8}  # bits represented by each printed character

        formats = [f.strip() for f in fmt.split(',')]
        if len(formats) == 1:
            fmt1, fmt2 = formats[0], None
        elif len(formats) == 2:
            fmt1, fmt2 = formats[0], formats[1]
        else:
            raise ValueError(f"Either 1 or 2 comma separated formats must be specified, not {len(formats)}."
                             " Format string was {fmt}.")

        short_token: Pattern[str] = re.compile(r'(?P<name>bytes|bin|oct|hex|b|o|h):?(?P<len>\d+)$', re.IGNORECASE)
        m1 = short_token.match(fmt1)
        if m1:
            length1 = int(m1.group('len'))
            fmt1 = m1.group('name')
        else:
            length1 = None
        length2 = None
        if fmt2 is not None:
            m2 = short_token.match(fmt2)
            if m2:
                length2 = int(m2.group('len'))
                fmt2 = m2.group('name')

        aliases = {'hex': 'hex', 'oct': 'oct', 'bin': 'bin', 'bytes': 'bytes',
                   'b': 'bin', 'o': 'oct', 'h': 'hex'}
        try:
            fmt1 = aliases[fmt1]
            if fmt2 is not None:
                fmt2 = aliases[fmt2]
        except KeyError:
            pass  # Should be dealt with in the next check
        if fmt1 not in bpc.keys() or (fmt2 is not None and fmt2 not in bpc.keys()):
            raise ValueError(f"Pretty print formats only support {'/'.join(bpc.keys())}. Received '{fmt}'.")
        if len(self) % bpc[fmt1] != 0:
            raise InterpretError(f"Cannot convert bitstring of length {len(self)} to {fmt1} - not a multiple of {bpc[fmt1]} bits long.")
        if fmt2 is not None and len(self) % bpc[fmt2] != 0:
            raise InterpretError(f"Cannot convert bitstring of length {len(self)} to {fmt2} - not a multiple of {bpc[fmt2]} bits long.")

        if fmt2 is not None and length2 is not None and length1 is not None:
            # Both lengths defined so must be equal
            if length1 != length2:
                raise ValueError(f"Differing bit lengths of {length1} and {length2} in format string '{fmt}'.")
        bits_per_group = None
        if fmt2 is not None and length2 is not None:
            bits_per_group = length2
        elif length1 is not None:
            bits_per_group = length1

        if bits_per_group is not None:
            if bits_per_group % bpc[fmt1] != 0:
                raise ValueError(f"Bits per group must be a multiple of {bpc[fmt1]} for {fmt1} format.")
            if fmt2 is not None and bits_per_group % bpc[fmt2] != 0:
                raise ValueError(f"Bits per group must be a multiple of {bpc[fmt2]} for {fmt2} format.")

        if bits_per_group is None:
            if fmt2 is None:
                bits_per_group = 8  # Default for 'bin' and 'hex'
                if fmt1 == 'oct':
                    bits_per_group = 12
                elif fmt1 == 'bytes':
                    bits_per_group = 32
            else:
                # Rule of thumb seems to work OK for all combinations.
                bits_per_group = 2 * bpc[fmt1] * bpc[fmt2]
                if bits_per_group >= 24:
                    bits_per_group //= 2

        if sep is None:
            sep = ''
        format_sep = "   "  # String to insert on each line between multiple formats

        offset_width = 0
        offset_sep = ' :' if _lsb0 else ': '
        if show_offset:
            # This could be 1 too large in some circumstances. Slightly recurrent logic needed to fix it...
            offset_width = len(str(len(self))) + len(offset_sep)
        if bits_per_group > 0:
            group_chars1 = bits_per_group // bpc[fmt1]
            group_chars2 = 0 if fmt2 is None else bits_per_group // bpc[fmt2]
            # The number of characters that get added when we add an extra group (after the first one)
            total_group_chars = group_chars1 + group_chars2 + len(sep) + len(sep) * bool(group_chars2)
            width_excluding_offset_and_final_group = width - offset_width - group_chars1 - group_chars2 - len(format_sep)*bool(group_chars2)
            width_excluding_offset_and_final_group = max(width_excluding_offset_and_final_group, 0)
            groups_per_line = 1 + width_excluding_offset_and_final_group // total_group_chars
            max_bits_per_line = groups_per_line * bits_per_group  # Number of bits represented on each line
        else:
            assert bits_per_group == 0  # Don't divide into groups
            group_chars1 = group_chars2 = 0
            width_available = width - offset_width - len(format_sep)*(fmt2 is not None)
            width_available = max(width_available, 1)
            if fmt2 is None:
                max_bits_per_line = width_available * bpc[fmt1]
            else:
                chars_per_24_bits = 24 // bpc[fmt1] + 24 // bpc[fmt2]
                max_bits_per_line = 24 * (width_available // chars_per_24_bits)
                if max_bits_per_line == 0:
                    max_bits_per_line = 24  # We can't fit into the width asked for. Show something small.
        assert max_bits_per_line > 0

        def format_bits(bits_, bits_per_group_, sep_, fmt_):
            raw = {'bin': bits_._getbin,
                   'oct': bits_._getoct,
                   'hex': bits_._gethex,
                   'bytes': bits_._getbytes_printable}[fmt_]()
            if bits_per_group_ == 0:
                return raw
            formatted = sep_.join(raw[i: i + bits_per_group_] for i in range(0, len(raw), bits_per_group_))
            return formatted

        bitpos = 0
        first_fb_width = second_fb_width = None
        for bits in self.cut(max_bits_per_line):
            if _lsb0:
                offset_str = f'{offset_sep}{bitpos: >{offset_width - len(offset_sep)}}' if show_offset else ''
            else:
                offset_str = f'{bitpos: >{offset_width - len(offset_sep)}}{offset_sep}' if show_offset else ''
            fb = format_bits(bits, group_chars1, sep, fmt1)
            if first_fb_width is None:
                first_fb_width = len(fb)
            if len(fb) < first_fb_width:  # Pad final line with spaces to align it
                if _lsb0:
                    fb = ' ' * (first_fb_width - len(fb)) + fb
                else:
                    fb += ' ' * (first_fb_width - len(fb))
            fb2 = '' if fmt2 is None else format_sep + format_bits(bits, group_chars2, sep, fmt2)
            if second_fb_width is None:
                second_fb_width = len(fb2)
            if len(fb2) < second_fb_width:
                if _lsb0:
                    fb2 = ' ' * (second_fb_width - len(fb2)) + fb2
                else:
                    fb2 += ' ' * (second_fb_width - len(fb2))
            if _lsb0 is True:
                line_fmt = fb + fb2 + offset_str + '\n'
            else:
                line_fmt = offset_str + fb + fb2 + '\n'
            stream.write(line_fmt)
            bitpos += len(bits)
        return

    def copy(self) -> Bits:
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

    _offset = property(_getoffset)

    len = property(_getlength,
                   doc="""The length of the bitstring in bits. Read only.
                      """)
    length = property(_getlength,
                      doc="""The length of the bitstring in bits. Read only.
                      """)
    bool = property(_getbool,
                    doc="""The bitstring as a bool (True or False). Read only.
                    """)
    hex = property(_gethex,
                   doc="""The bitstring as a hexadecimal string. Read only.
                   """)
    bin = property(_getbin,
                   doc="""The bitstring as a binary string. Read only.
                   """)
    oct = property(_getoct,
                   doc="""The bitstring as an octal string. Read only.
                   """)
    bytes = property(_getbytes,
                     doc="""The bitstring as a bytes object. Read only.
                      """)
    int = property(_getint,
                   doc="""The bitstring as a two's complement signed int. Read only.
                      """)
    uint = property(_getuint,
                    doc="""The bitstring as a two's complement unsigned int. Read only.
                      """)
    float = property(_getfloatbe,
                     doc="""The bitstring as a big-endian floating point number. Read only.
                      """)
    bfloat = property(_getbfloatbe,
                      doc="""The bitstring as a 16 bit big-endian bfloat floating point number. Read only.
                      """)
    bfloatbe = property(_getbfloatbe,
                        doc="""The bitstring as a 16 bit big-endian bfloat floating point number. Read only.
                        """)
    bfloatle = property(_getbfloatle,
                        doc="""The bitstring as a 16 bit little-endian bfloat floating point number. Read only.
                        """)
    bfloatne = property(_getbfloatne,
                        doc="""The bitstring as a 16 bit native-endian bfloat floating point number. Read only.
                        """)
    intbe = property(_getintbe,
                     doc="""The bitstring as a two's complement big-endian signed int. Read only.
                     """)
    uintbe = property(_getuintbe,
                      doc="""The bitstring as a two's complement big-endian unsigned int. Read only.
                      """)
    floatbe = property(_getfloatbe,
                       doc="""The bitstring as a big-endian floating point number. Read only.
                      """)
    intle = property(_getintle,
                     doc="""The bitstring as a two's complement little-endian signed int. Read only.
                      """)
    uintle = property(_getuintle,
                      doc="""The bitstring as a two's complement little-endian unsigned int. Read only.
                      """)
    floatle = property(_getfloatle,
                       doc="""The bitstring as a little-endian floating point number. Read only.
                      """)
    intne = property(_getintne,
                     doc="""The bitstring as a two's complement native-endian signed int. Read only.
                      """)
    uintne = property(_getuintne,
                      doc="""The bitstring as a two's complement native-endian unsigned int. Read only.
                      """)
    floatne = property(_getfloatne,
                       doc="""The bitstring as a native-endian floating point number. Read only.
                      """)
    ue = property(_getue,
                  doc="""The bitstring as an unsigned exponential-Golomb code. Read only.
                      """)
    se = property(_getse,
                  doc="""The bitstring as a signed exponential-Golomb code. Read only.
                      """)
    uie = property(_getuie,
                   doc="""The bitstring as an unsigned interleaved exponential-Golomb code. Read only.
                      """)
    sie = property(_getsie,
                   doc="""The bitstring as a signed interleaved exponential-Golomb code. Read only.
                      """)
    # Some shortened aliases of the above properties
    i = int
    u = uint
    f = float
    b = bin
    o = oct
    h = hex

    # Dictionary that maps token names to the function that reads them
    _name_to_read = {'uint': _readuint,
                     'u': _readuint,
                     'uintle': _readuintle,
                     'uintbe': _readuintbe,
                     'uintne': _readuintne,
                     'int': _readint,
                     'i': _readint,
                     'intle': _readintle,
                     'intbe': _readintbe,
                     'intne': _readintne,
                     'float': _readfloatbe,
                     'f': _readfloatbe,
                     'floatbe': _readfloatbe,  # floatbe is a synonym for float
                     'floatle': _readfloatle,
                     'floatne': _readfloatne,
                     'bfloat': _readbfloatbe,
                     'bfloatbe': _readbfloatbe,
                     'bfloatle': _readbfloatle,
                     'bfloatne': _readbfloatne,
                     'hex': _readhex,
                     'h': _readhex,
                     'oct': _readoct,
                     'o': _readoct,
                     'bin': _readbin,
                     'b': _readbin,
                     'bits': _readbits,
                     'bytes': _readbytes,
                     'ue': _readue,
                     'se': _readse,
                     'uie': _readuie,
                     'sie': _readsie,
                     'bool': _readbool,
                     'pad': _readpad}

    # Mapping token names to the methods used to set them
    _setfunc = {'bin': _setbin_safe,
                'hex': _sethex,
                'oct': _setoct,
                'ue': _setue,
                'se': _setse,
                'uie': _setuie,
                'sie': _setsie,
                'bool': _setbool,
                'uint': _setuint,
                'int': _setint,
                'float': _setfloatbe,
                'bfloat': _setbfloatbe,
                'bfloatbe': _setbfloatbe,
                'bfloatle': _setbfloatle,
                'bfloatne': _setbfloatne,
                'uintbe': _setuintbe,
                'intbe': _setintbe,
                'floatbe': _setfloatbe,
                'uintle': _setuintle,
                'intle': _setintle,
                'floatle': _setfloatle,
                'uintne': _setuintne,
                'intne': _setintne,
                'floatne': _setfloatne,
                'bytes': _setbytes_safe,
                'filename': _setfile}


class BitArray(Bits):
    """A container holding a mutable sequence of bits.

    Subclass of the immutable Bits class. Inherits all of its
    methods (except __hash__) and adds mutating methods.

    Mutating methods:

    append() -- Append a bitstring.
    byteswap() -- Change byte endianness in-place.
    clear() -- Remove all bits from the bitstring.
    insert() -- Insert a bitstring.
    invert() -- Flip bit(s) between one and zero.
    overwrite() -- Overwrite a section with a new bitstring.
    prepend() -- Prepend a bitstring.
    replace() -- Replace occurrences of one bitstring with another.
    reverse() -- Reverse bits in-place.
    rol() -- Rotate bits to the left.
    ror() -- Rotate bits to the right.
    set() -- Set bit(s) to 1 or 0.

    Methods inherited from Bits:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    copy() -- Return a copy of the bitstring.
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
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Special methods:

    Mutating operators are available: [], <<=, >>=, +=, *=, &=, |= and ^=
    in addition to the inherited [], ==, !=, +, *, ~, <<, >>, &, | and ^.

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

    @classmethod
    def _setlsb0methods(cls, lsb0: bool) -> None:
        if lsb0:
            cls._overwrite = cls._overwrite_lsb0  # type: ignore
            cls._insert = cls._insert_lsb0  # type: ignore
            cls._delete = cls._delete_lsb0  # type: ignore
            cls._ror = cls._rol_msb0  # type: ignore
            cls._rol = cls._ror_msb0  # type: ignore
            cls._append = cls._append_lsb0  # type: ignore
            # An LSB0 prepend is an MSB0 append
            cls._prepend = cls._append_msb0  # type: ignore
        else:
            cls._overwrite = cls._overwrite_msb0  # type: ignore
            cls._insert = cls._insert_msb0  # type: ignore
            cls._delete = cls._delete_msb0  # type: ignore
            cls._ror = cls._ror_msb0  # type: ignore
            cls._rol = cls._rol_msb0  # type: ignore
            cls._append = cls._append_msb0  # type: ignore
            cls._prepend = cls._append_lsb0  # type: ignore

    __slots__ = ()

    # As BitArray objects are mutable, we shouldn't allow them to be hashed.
    __hash__: None = None

    def __init__(self, auto: Optional[BitsType] = None, length: Optional[int] = None,
                 offset: Optional[int] = None, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        auto -- a string of comma separated tokens, an integer, a file object,
                a bytearray, a boolean iterable or another bitstring.

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
                  ignored and this is intended for use when
                  initialising using 'bytes' or 'filename'.

        """
        # For mutable BitArrays we always read in files to memory:
        super().__init__()

    def __new__(cls, auto: Optional[BitsType] = None, length: Optional[int] = None,
                offset: Optional[int] = None, **kwargs) -> Bits:
        x = super(BitArray, cls).__new__(cls)
        y = Bits.__new__(BitArray, auto, length, offset, **kwargs)
        x._datastore = ByteStore(y._datastore.rawarray[:],
                                 y._datastore.bitlength,
                                 y._datastore.offset)
        return x

    def __setattr__(self, attribute, value):
        try:
            # First try the ordinary attribute setter
            super().__setattr__(attribute, value)
        except AttributeError:
            letter_to_setter: Dict[str, Callable[..., None]] =\
                {'u': self._setuint,
                 'i': self._setint,
                 'f': self._setfloatbe,
                 'b': self._setbin_safe,
                 'o': self._setoct,
                 'h': self._sethex}
            short_token: Pattern[str] = re.compile(r'^(?P<name>[uifboh])(?P<len>\d+)$', re.IGNORECASE)
            m1_short = short_token.match(attribute)
            if m1_short:
                length = int(m1_short.group('len'))
                name = m1_short.group('name')
                f = letter_to_setter[name]
                a_copy = self._copy()
                try:
                    f(value, length)
                except AttributeError:
                    raise AttributeError(f"Can't set attribute {attribute} with value {value}.")

                if self.len != length:
                    new_len = self.len
                    # Reset to previous value
                    self._setbytes_unsafe(a_copy._datastore.getbyteslice(0, a_copy._datastore.bytelength),
                                          a_copy.len, a_copy._offset)
                    raise CreationError(f"Can't initialise with value of length {new_len} bits, "
                                        f"as attribute has length of {length} bits.")
                return
            # Try to split into [name][length], then try standard properties
            name_length_pattern: Pattern[str] = re.compile(r'^(?P<name>[a-z]+)(?P<len>\d+)$', re.IGNORECASE)
            name_length = name_length_pattern.match(attribute)
            if name_length:
                name = name_length.group('name')
                length = name_length.group('len')
                if length is not None:
                    length = int(length)
                    if name == 'bytes':
                        if len(value) != length:
                            raise CreationError(f"Wrong amount of byte data preset - {length} bytes needed, have {len(value)} bytes.")
                        length *= 8
                try:
                    a_copy = self._copy()
                    self._initialise(auto=None, length=length, offset=None, **{name: value})
                    if length is not None and self.len != length:
                        new_len = self.len
                        # Reset to previous value
                        self._setbytes_unsafe(a_copy._datastore.getbyteslice(0, a_copy._datastore.bytelength),
                                              a_copy.len, a_copy._offset)
                        raise CreationError(f"Can't initialise with value of length {new_len} bits, "
                                            f"as attribute has length of {length} bits.")
                    return
                except AttributeError:
                    pass
            raise AttributeError(f"Can't set attribute {attribute} with value {value}.")

    def __iadd__(self, bs: BitsType) -> BitArray:
        """Append bs to current bitstring. Return self.

        bs -- the bitstring to append.

        """
        self._append(bs)
        return self

    def __copy__(self) -> BitArray:
        """Return a new copy of the BitArray."""
        s_copy = BitArray()
        if not isinstance(self._datastore, ByteStore):
            # Let them both point to the same (invariant) array.
            # If either gets modified then at that point they'll be read into memory.
            s_copy._datastore = self._datastore
        else:
            s_copy._datastore = copy.copy(self._datastore)
        return s_copy
    
    def __setitem__(self, key: Union[slice, int], value: BitsType) -> None:
        if isinstance(key, slice):
            # A slice
            start, step = 0, 1
            if key.step is not None:
                step = key.step
            if step != 1:
                # convert to binary string and use string slicing
                # TODO: Horribly inefficient
                temp = list(self._getbin())
                v = list(Bits(value)._getbin())
                temp.__setitem__(key, v)
                self._setbin_unsafe(''.join(temp))
                return

            # If value is an integer then we want to set the slice to that
            # value rather than initialise a new bitstring of that length.
            if not isinstance(value, int):
                try:
                    value = Bits(value)
                except TypeError:
                    raise TypeError(f"Bitstring, integer or string expected. Got {type(value)}.")
            if key.start is not None:
                start = key.start
                if key.start < 0:
                    start += self.len
                if start < 0:
                    start = 0
            stop = self.len
            if key.stop is not None:
                stop = key.stop
                if key.stop < 0:
                    stop += self.len
            if start > stop:
                # The standard behaviour for lists is to just insert at the
                # start position if stop < start and step == 1.
                stop = start
            if isinstance(value, int):
                if value >= 0:
                    value = self.__class__(uint=value, length=stop - start)
                else:
                    value = self.__class__(int=value, length=stop - start)
            stop = min(stop, self.len)
            start = max(start, 0)
            start = min(start, stop)
            if (stop - start) == value._getlength():
                if value.len == 0:
                    return
                if step >= 0:
                    self._overwrite(value, start)
                else:
                    self._overwrite(value.__getitem__(slice(None, None, 1)), start)
            else:
                # TODO: A delete then insert is wasteful - it could do unneeded shifts.
                # Could be either overwrite + insert or overwrite + delete.
                self._delete(stop - start, start)
                if step >= 0:
                    self._insert(value, start)
                else:
                    self._insert(value.__getitem__(slice(None, None, 1)), start)
                # pos is now after the inserted piece.
            return
        else:
            # single element
            if key < 0:
                key += self._getlength()
            if not 0 <= key < self.len:
                raise IndexError("Slice index out of range.")
            if isinstance(value, int):
                if not value:
                    self._unset(key)
                    return
                if value in (1, -1):
                    self._set(key)
                    return
                raise ValueError(f"Cannot set a single bit with integer {value}.")
            value = Bits(value)
            if value.len == 1:
                if value[0]:
                    self._set(key)
                else:
                    self._unset(key)
            else:
                self._delete(1, key)
                self._insert(value, key)
            return

    def __delitem__(self, key: Union[slice, int]) -> None:
        """Delete item or range.

        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.

        >>> a = BitArray('0x001122')
        >>> del a[1:2:8]
        >>> print a
        0x0022

        """
        if isinstance(key, slice):
            # A slice
            start = 0
            step = key.step if key.step is not None else 1
            if step != 1:
                # convert to binary string and use string slicing
                # TODO: Horribly inefficient
                temp = list(self._getbin())
                temp.__delitem__(key)
                self._setbin_unsafe(''.join(temp))
                return
            if key.start is not None:
                start = key.start
                if key.start < 0:
                    start += self.len
                if start < 0:
                    start = 0
            stop = self.len
            if key.stop is not None:
                stop = key.stop
                if key.stop < 0:
                    stop += self.len
            if start > stop:
                return
            stop = min(stop, self.len)
            start = max(start, 0)
            start = min(start, stop)
            self._delete(stop - start, start)
            return
        else:
            # single element
            if key < 0:
                key += self._getlength()
            if not 0 <= key < self._getlength():
                raise IndexError("Slice index out of range.")
            self._delete(1, key)
            return

    def __ilshift__(self, n: int) -> Bits:
        """Shift bits by n to the left in place. Return self.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        if not n:
            return self
        n = min(n, self.len)
        return self._ilshift(n)

    def __irshift__(self, n: int) -> Bits:
        """Shift bits by n to the right in place. Return self.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        if not n:
            return self
        n = min(n, self.len)
        return self._irshift(n)

    def __imul__(self, n: int) -> Bits:
        """Concatenate n copies of self in place. Return self.

        Called for expressions of the form 'a *= 3'.
        n -- The number of concatenations. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        return self._imul(n)

    def __ior__(self, bs: BitsType) -> Bits:
        bs = Bits(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for |= operator.")
        return self._ior(bs)

    def __iand__(self, bs: BitsType) -> Bits:
        bs = Bits(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for &= operator.")
        return self._iand(bs)

    def __ixor__(self, bs: BitsType) -> Bits:
        bs = Bits(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length for ^= operator.")
        return self._ixor(bs)

    def replace(self, old: BitsType, new: BitsType, start: Optional[int] = None, end: Optional[int] = None,
                count: Optional[int] = None, bytealigned: Optional[bool] = None) -> int:
        """Replace all occurrences of old with new in place.

        Returns number of replacements made.

        old -- The bitstring to replace.
        new -- The replacement bitstring.
        start -- Any occurrences that start before this will not be replaced.
                 Defaults to 0.
        end -- Any occurrences that finish after this will not be replaced.
               Defaults to len(self).
        count -- The maximum number of replacements to make. Defaults to
                 replace all occurrences.
        bytealigned -- If True replacements will only be made on byte
                       boundaries.

        Raises ValueError if old is empty or if start or end are
        out of range.

        """
        old = Bits(old)
        new = Bits(new)
        if not old.len:
            raise ValueError("Empty bitstring cannot be replaced.")
        start, end = self._validate_slice(start, end)
        if bytealigned is None:
            bytealigned = _bytealigned
        # Adjust count for use in split()
        if count is not None:
            count += 1
        sections = self.split(old, start, end, count, bytealigned)
        lengths = [s.len for s in sections]
        if len(lengths) == 1:
            # Didn't find anything to replace.
            return 0  # no replacements done
        if new is self:
            # Prevent self assignment woes
            new = copy.copy(self)
        positions = [lengths[0] + start]
        for le in lengths[1:-1]:
            # Next position is the previous one plus the length of the next section.
            positions.append(positions[-1] + le)
        # We have all the positions that need replacements. We do them
        # in reverse order so that they won't move around as we replace.
        positions.reverse()
        if self._pos is not None:
            # Need to calculate new pos, if this is a bitstream
            newpos = self._pos
            for p in positions:
                self[p:p + old.len] = new
            if old.len != new.len:
                diff = new.len - old.len
                for p in positions:
                    if p >= newpos:
                        continue
                    if p + old.len <= newpos:
                        newpos += diff
                    else:
                        newpos = p
            self._pos = newpos
        else:
            for p in positions:
                self[p:p + old.len] = new
        return len(lengths) - 1

    def insert(self, bs: BitsType, pos: Optional[int] = None) -> None:
        """Insert bs at bit position pos.

        bs -- The bitstring to insert.
        pos -- The bit position to insert at.

        Raises ValueError if pos < 0 or pos > len(self).

        """
        bs = Bits(bs)
        if not bs.len:
            return
        if bs is self:
            bs = self.__copy__()
        if pos is None:
            pos = self._pos
            if pos is None:
                raise TypeError("insert needs a bit position specified when used on a BitArray.")
        if pos < 0:
            pos += self._getlength()
        if not 0 <= pos <= self._getlength():
            raise ValueError("Invalid insert position.")
        self._insert(bs, pos)

    def overwrite(self, bs: BitsType, pos: Optional[int] = None) -> None:
        """Overwrite with bs at bit position pos.

        bs -- The bitstring to overwrite with.
        pos -- The bit position to begin overwriting from.

        Raises ValueError if pos < 0 or pos > len(self).

        """
        bs = Bits(bs)
        if not bs.len:
            return
        if pos is None:
            pos = self._pos
            if pos is None:
                raise TypeError("Overwrite needs a bit position specified when used on a BitArray.")
        if pos < 0:
            pos += self._getlength()
        if pos < 0 or pos > self.len:
            raise ValueError("Overwrite starts outside boundary of bitstring.")
        self._overwrite(bs, pos)
        if self._pos is not None:
            self._pos = pos + bs.len

    def append(self, bs: BitsType) -> None:
        """Append a bitstring to the current bitstring.

        bs -- The bitstring to append.

        """
        self._append(bs)

    def prepend(self, bs: BitsType) -> None:
        """Prepend a bitstring to the current bitstring.

        bs -- The bitstring to prepend.

        """
        self._prepend(bs)

    def _append_msb0(self, bs: BitsType) -> None:
        # The offset is a hint to make bs easily appendable.
        bs = self._converttobitstring(bs, offset=(self.len + self._offset) % 8)
        self._addright(bs)

    def _append_lsb0(self, bs: BitsType) -> None:
        bs = Bits(bs)
        self._addleft(bs)

    def reverse(self, start: Optional[int] = None, end: Optional[int] = None) -> None:
        """Reverse bits in-place.

        start -- Position of first bit to reverse. Defaults to 0.
        end -- One past the position of the last bit to reverse.
               Defaults to len(self).

        Using on an empty bitstring will have no effect.

        Raises ValueError if start < 0, end > len(self) or end < start.

        """
        start, end = self._validate_slice(start, end)
        if start == 0 and end == self.len:
            self._reverse()
            return
        s = self._slice(start, end)
        s._reverse()
        self[start:end] = s

    def set(self, value: Any, pos: Optional[Union[int, Iterable[int]]] = None) -> None:
        """Set one or many bits to 1 or 0.

        value -- If bool(value) is True bits are set to 1, otherwise they are set to 0.
        pos -- Either a single bit position or an iterable of bit positions.
               Negative numbers are treated in the same way as slice indices.
               Defaults to the entire bitstring.

        Raises IndexError if pos < -len(self) or pos >= len(self).

        """
        if pos is None:
            # Set all bits to either 1 or 0
            self._setint(-1 if value else 0)
            return
        f = self._set if value else self._unset
        if not isinstance(pos, abc.Iterable):
            pos = (pos,)
        length = self.len
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError(f"Bit position {p} out of range.")
            f(p)

    def invert(self, pos: Optional[Union[Iterable[int], int]] = None) -> None:
        """Invert one or many bits from 0 to 1 or vice versa.

        pos -- Either a single bit position or an iterable of bit positions.
               Negative numbers are treated in the same way as slice indices.

        Raises IndexError if pos < -len(self) or pos >= len(self).

        """
        if pos is None:
            self._invert_all()
            return
        if not isinstance(pos, abc.Iterable):
            pos = (pos,)
        length = self.len

        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError(f"Bit position {p} out of range.")
            self._invert(p)

    def ror(self, bits: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        """Rotate bits to the right in-place.

        bits -- The number of bits to rotate by.
        start -- Start of slice to rotate. Defaults to 0.
        end -- End of slice to rotate. Defaults to len(self).

        Raises ValueError if bits < 0.

        """
        if not self.len:
            raise Error("Cannot rotate an empty bitstring.")
        if bits < 0:
            raise ValueError("Cannot rotate by negative amount.")
        self._ror(bits, start, end)

    def _ror_msb0(self, bits: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        start, end = self._validate_slice_msb0(start, end)  # the _slice deals with msb0/lsb0
        bits %= (end - start)
        if not bits:
            return
        rhs = self._slice(end - bits, end)
        self._delete(bits, end - bits)
        self._insert(rhs, start)

    def rol(self, bits: int, start: Optional[int] = None, end: Optional[int] = None) -> None:
        """Rotate bits to the left in-place.

        bits -- The number of bits to rotate by.
        start -- Start of slice to rotate. Defaults to 0.
        end -- End of slice to rotate. Defaults to len(self).

        Raises ValueError if bits < 0.

        """
        if not self.len:
            raise Error("Cannot rotate an empty bitstring.")
        if bits < 0:
            raise ValueError("Cannot rotate by negative amount.")
        self._rol(bits, start, end)

    def _rol_msb0(self, bits: int, start: Optional[int] = None, end: Optional[int] = None):
        start, end = self._validate_slice_msb0(start, end)
        bits %= (end - start)
        if not bits:
            return
        lhs = self._slice(start, start + bits)
        self._delete(bits, start)
        self._insert(lhs, end - bits)

    def byteswap(self, fmt: Optional[Union[int, Iterable[int], str]] = None, start: Optional[int] = None,
                 end: Optional[int] = None, repeat: bool = True) -> int:
        """Change the endianness in-place. Return number of repeats of fmt done.

        fmt -- A compact structure string, an integer number of bytes or
               an iterable of integers. Defaults to 0, which byte reverses the
               whole bitstring.
        start -- Start bit position, defaults to 0.
        end -- End bit position, defaults to len(self).
        repeat -- If True (the default) the byte swapping pattern is repeated
                  as much as possible.

        """
        start_v, end_v = self._validate_slice(start, end)
        if fmt is None or fmt == 0:
            # reverse all of the whole bytes.
            bytesizes = [(end_v - start_v) // 8]
        elif isinstance(fmt, int):
            if fmt < 0:
                raise ValueError(f"Improper byte length {fmt}.")
            bytesizes = [fmt]
        elif isinstance(fmt, str):
            m = STRUCT_PACK_RE.match(fmt)
            if not m:
                raise ValueError(f"Cannot parse format string {fmt}.")
            # Split the format string into a list of 'q', '4h' etc.
            formatlist = re.findall(STRUCT_SPLIT_RE, m.group('fmt'))
            # Now deal with multiplicative factors, 4h -> hhhh etc.
            bytesizes = []
            for f in formatlist:
                if len(f) == 1:
                    bytesizes.append(PACK_CODE_SIZE[f])
                else:
                    bytesizes.extend([PACK_CODE_SIZE[f[-1]]] * int(f[:-1]))
        elif isinstance(fmt, abc.Iterable):
            bytesizes = fmt
            for bytesize in bytesizes:
                if not isinstance(bytesize, int) or bytesize < 0:
                    raise ValueError(f"Improper byte length {bytesize}.")
        else:
            raise TypeError("Format must be an integer, string or iterable.")

        repeats = 0
        totalbitsize: int = 8 * sum(bytesizes)
        if not totalbitsize:
            return 0
        if repeat:
            # Try to repeat up to the end of the bitstring.
            finalbit = end_v
        else:
            # Just try one (set of) byteswap(s).
            finalbit = start_v + totalbitsize
        for patternend in range(start_v + totalbitsize, finalbit + 1, totalbitsize):
            bytestart = patternend - totalbitsize
            for bytesize in bytesizes:
                byteend = bytestart + bytesize * 8
                self._reversebytes(bytestart, byteend)
                bytestart += bytesize * 8
            repeats += 1
        return repeats

    def clear(self) -> None:
        """Remove all bits, reset to zero length."""
        self._clear()

    int = property(Bits._getint, Bits._setint,
                   doc="""The bitstring as a two's complement signed int. Read and write.
                      """)
    uint = property(Bits._getuint, Bits._setuint,
                    doc="""The bitstring as a two's complement unsigned int. Read and write.
                      """)
    float = property(Bits._getfloatbe, Bits._setfloatbe,
                     doc="""The bitstring as a floating point number. Read and write.
                      """)
    bfloat = property(Bits._getbfloatbe, Bits._setbfloatbe,
                      doc="""The bitstring as a 16 bit bfloat floating point number. Read and write.
                      """)
    intbe = property(Bits._getintbe, Bits._setintbe,
                     doc="""The bitstring as a two's complement big-endian signed int. Read and write.
                      """)
    uintbe = property(Bits._getuintbe, Bits._setuintbe,
                      doc="""The bitstring as a two's complement big-endian unsigned int. Read and write.
                      """)
    floatbe = property(Bits._getfloatbe, Bits._setfloatbe,
                       doc="""The bitstring as a big-endian floating point number. Read and write.
                      """)
    intle = property(Bits._getintle, Bits._setintle,
                     doc="""The bitstring as a two's complement little-endian signed int. Read and write.
                      """)
    uintle = property(Bits._getuintle, Bits._setuintle,
                      doc="""The bitstring as a two's complement little-endian unsigned int. Read and write.
                      """)
    floatle = property(Bits._getfloatle, Bits._setfloatle,
                       doc="""The bitstring as a little-endian floating point number. Read and write.
                      """)
    intne = property(Bits._getintne, Bits._setintne,
                     doc="""The bitstring as a two's complement native-endian signed int. Read and write.
                      """)
    uintne = property(Bits._getuintne, Bits._setuintne,
                      doc="""The bitstring as a two's complement native-endian unsigned int. Read and write.
                      """)
    floatne = property(Bits._getfloatne, Bits._setfloatne,
                       doc="""The bitstring as a native-endian floating point number. Read and write.
                      """)
    ue = property(Bits._getue, Bits._setue,
                  doc="""The bitstring as an unsigned exponential-Golomb code. Read and write.
                      """)
    se = property(Bits._getse, Bits._setse,
                  doc="""The bitstring as a signed exponential-Golomb code. Read and write.
                      """)
    uie = property(Bits._getuie, Bits._setuie,
                   doc="""The bitstring as an unsigned interleaved exponential-Golomb code. Read and write.
                      """)
    sie = property(Bits._getsie, Bits._setsie,
                   doc="""The bitstring as a signed interleaved exponential-Golomb code. Read and write.
                      """)
    hex = property(Bits._gethex, Bits._sethex,
                   doc="""The bitstring as a hexadecimal string. Read and write.
                       """)
    bin = property(Bits._getbin, Bits._setbin_safe,
                   doc="""The bitstring as a binary string. Read and write.
                       """)
    oct = property(Bits._getoct, Bits._setoct,
                   doc="""The bitstring as an octal string. Read and write.
                       """)
    bool = property(Bits._getbool, Bits._setbool,
                    doc="""The bitstring as a bool (True or False). Read and write.
                    """)
    bytes = property(Bits._getbytes, Bits._setbytes_safe,
                     doc="""The bitstring as a ordinary string. Read and write.
                      """)
    # Aliases for some properties
    f = float
    i = int
    u = uint
    b = bin
    h = hex
    o = oct


class ConstBitStream(Bits):
    """A container or stream holding an immutable sequence of bits.

    For a mutable container use the BitStream class instead.

    Methods inherited from Bits:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    copy() -- Return a copy of the bitstring.
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
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Other methods:

    bytealign() -- Align to next byte boundary.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.
    readto() -- Read up to and including next occurrence of a bitstring.

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
    pos -- The current bit position in the bitstring.
    """

    __slots__ = ()

    def __init__(self, auto: Optional[BitsType] = None, length: Optional[int] = None,
                 offset: Optional[int] = None, pos: int = 0, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        auto -- a string of comma separated tokens, an integer, a file object,
                a bytearray, a boolean iterable or another bitstring.

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
        pos -- Initial bit position, defaults to 0.

        """
        pass

    def __new__(cls, auto: Optional[BitsType] = None, length: Optional[int] = None,
                offset: Optional[int] = None, pos: int = 0, **kwargs) -> Bits:
        x = super(ConstBitStream, cls).__new__(cls)
        x._initialise(auto, length, offset, **kwargs)
        x._pos = x._datastore.bitlength + pos if pos < 0 else pos
        if x._pos < 0 or x._pos > x._datastore.bitlength:
            raise CreationError(f"Cannot set pos to {pos} when length is {x._datastore.bitlength}.")
        return x

    def _setbytepos(self, bytepos: int) -> None:
        """Move to absolute byte-aligned position in stream."""
        self._setbitpos(bytepos * 8)

    def _getbytepos(self) -> int:
        """Return the current position in the stream in bytes. Must be byte aligned."""
        if self._pos % 8:
            raise ByteAlignError("Not byte aligned when using bytepos property.")
        return self._pos // 8

    def _setbitpos(self, pos: int) -> None:
        """Move to absolute position bit in bitstream."""
        if pos < 0:
            raise ValueError("Bit position cannot be negative.")
        if pos > self.len:
            raise ValueError("Cannot seek past the end of the data.")
        self._pos = pos

    def _getbitpos(self) -> int:
        """Return the current position in the stream in bits."""
        return self._pos

    def _clear(self) -> None:
        Bits._clear(self)
        self._pos = 0

    def __copy__(self) -> ConstBitStream:
        """Return a new copy of the ConstBitStream for the copy module."""
        # Note that if you want a new copy (different ID), use _copy instead.
        # The copy can use the same datastore as it's immutable.
        s = ConstBitStream()
        s._datastore = self._datastore
        # Reset the bit position, don't copy it.
        s._pos = 0
        return s

    def __add__(self, bs: BitsType) -> Bits:
        """Concatenate bitstrings and return new bitstring.

        bs -- the bitstring to append.

        """
        s = Bits.__add__(self, bs)
        s._pos = 0
        return s

    def read(self, fmt: Union[int, str]) -> Union[int, float, str, Bits, bool, bytes, None]:
        """Interpret next bits according to the format string and return result.

        fmt -- Token string describing how to interpret the next bits.

        Token examples: 'int:12'    : 12 bits as a signed integer
                        'uint:8'    : 8 bits as an unsigned integer
                        'float:64'  : 8 bytes as a big-endian float
                        'intbe:16'  : 2 bytes as a big-endian signed integer
                        'uintbe:16' : 2 bytes as a big-endian unsigned integer
                        'intle:32'  : 4 bytes as a little-endian signed integer
                        'uintle:32' : 4 bytes as a little-endian unsigned integer
                        'floatle:64': 8 bytes as a little-endian float
                        'intne:24'  : 3 bytes as a native-endian signed integer
                        'uintne:24' : 3 bytes as a native-endian unsigned integer
                        'floatne:32': 4 bytes as a native-endian float
                        'hex:80'    : 80 bits as a hex string
                        'oct:9'     : 9 bits as an octal string
                        'bin:1'     : single bit binary string
                        'ue'        : next bits as unsigned exp-Golomb code
                        'se'        : next bits as signed exp-Golomb code
                        'uie'       : next bits as unsigned interleaved exp-Golomb code
                        'sie'       : next bits as signed interleaved exp-Golomb code
                        'bits:5'    : 5 bits as a bitstring
                        'bytes:10'  : 10 bytes as a bytes object
                        'bool'      : 1 bit as a bool
                        'pad:3'     : 3 bits of padding to ignore - returns None

        fmt may also be an integer, which will be treated like the 'bits' token.

        The position in the bitstring is advanced to after the read items.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        """
        if isinstance(fmt, int):
            if fmt < 0:
                raise ValueError("Cannot read negative amount.")
            if fmt > self.len - self._pos:
                raise ReadError(f"Cannot read {fmt} bits, only {self.len - self._pos} available.")
            bs = self._slice(self._pos, self._pos + fmt)
            self._pos += fmt
            return bs
        p = self._pos
        _, token = tokenparser(fmt)
        if len(token) != 1:
            self._pos = p
            raise ValueError(f"Format string should be a single token, not {len(token)} "
                             "tokens - use readlist() instead.")
        name, length, _ = token[0]
        if length is None:
            length = self.len - self._pos
        value, self._pos = self._readtoken(name, self._pos, length)
        return value

    def readlist(self, fmt: Union[str, List[Union[int, str]]], **kwargs)\
            -> List[Union[float, int, str, None, Bits]]:
        """Interpret next bits according to format string(s) and return list.

        fmt -- A single string or list of strings with comma separated tokens
               describing how to interpret the next bits in the bitstring. Items
               can also be integers, for reading new bitstring of the given length.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        The position in the bitstring is advanced to after the read items.

        Raises ReadError is not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples. 'pad' tokens are skipped
        and not added to the returned list.

        >>> h, b1, b2 = s.readlist('hex:20, bin:5, bin:3')
        >>> i, bs1, bs2 = s.readlist(['uint:12', 10, 10])

        """
        value, self._pos = self._readlist(fmt, self._pos, **kwargs)
        return value

    def readto(self, bs: BitsType, bytealigned: Optional[bool] = None) -> Bits:
        """Read up to and including next occurrence of bs and return result.

        bs -- The bitstring to find. An integer is not permitted.
        bytealigned -- If True the bitstring will only be
                       found on byte boundaries.

        Raises ValueError if bs is empty.
        Raises ReadError if bs is not found.

        """
        if isinstance(bs, int):
            raise ValueError("Integers cannot be searched for")
        bs = Bits(bs)
        oldpos = self._pos
        p = self.find(bs, self._pos, bytealigned=bytealigned)
        if not p:
            raise ReadError("Substring not found")
        self._pos += bs.len
        return self._slice(oldpos, self._pos)

    def peek(self, fmt: Union[int, str]) -> Union[int, float, str, Bits, bool, bytes, None]:
        """Interpret next bits according to format string and return result.

        fmt -- Token string describing how to interpret the next bits.

        The position in the bitstring is not changed. If not enough bits are
        available then all bits to the end of the bitstring will be used.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples.

        """
        pos_before = self._pos
        value = self.read(fmt)
        self._pos = pos_before
        return value

    def peeklist(self, fmt: Union[str, List[Union[int, str]]], **kwargs)\
            -> List[Union[int, float, str, Bits, None]]:
        """Interpret next bits according to format string(s) and return list.

        fmt -- One or more integers or strings with comma separated tokens describing
               how to interpret the next bits in the bitstring.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        The position in the bitstring is not changed. If not enough bits are
        available then all bits to the end of the bitstring will be used.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples.

        """
        pos = self._pos
        return_values = self.readlist(fmt, **kwargs)
        self._pos = pos
        return return_values

    def bytealign(self) -> int:
        """Align to next byte and return number of skipped bits.

        Raises ValueError if the end of the bitstring is reached before
        aligning to the next byte.

        """
        skipped = (8 - (self._pos % 8)) % 8
        self.pos += self._offset + skipped
        return skipped

    pos = property(_getbitpos, _setbitpos,
                   doc="""The position in the bitstring in bits. Read and write.
                      """)
    bitpos = property(_getbitpos, _setbitpos,
                      doc="""The position in the bitstring in bits. Read and write.
                      """)
    bytepos = property(_getbytepos, _setbytepos,
                       doc="""The position in the bitstring in bytes. Read and write.
                      """)


class BitStream(ConstBitStream, BitArray):
    """A container or stream holding a mutable sequence of bits

    Subclass of the ConstBitStream and BitArray classes. Inherits all of
    their methods.

    Methods:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    append() -- Append a bitstring.
    bytealign() -- Align to next byte boundary.
    byteswap() -- Change byte endianness in-place.
    clear() -- Remove all bits from the bitstring.
    copy() -- Return a copy of the bitstring.
    count() -- Count the number of bits set to 1 or 0.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurrences of a sub-bitstring in the current bitstring.
    insert() -- Insert a bitstring.
    invert() -- Flip bit(s) between one and zero.
    join() -- Join bitstrings together using current bitstring.
    overwrite() -- Overwrite a section with a new bitstring.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    pp() -- Pretty print the bitstring.
    prepend() -- Prepend a bitstring.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.
    readto() -- Read up to and including next occurrence of a bitstring.
    replace() -- Replace occurrences of one bitstring with another.
    reverse() -- Reverse bits in-place.
    rfind() -- Seek backwards to find a sub-bitstring.
    rol() -- Rotate bits to the left.
    ror() -- Rotate bits to the right.
    set() -- Set bit(s) to 1 or 0.
    split() -- Create generator of chunks split by a delimiter.
    startswith() -- Return whether the bitstring starts with a sub-bitstring.
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Special methods:

    Mutating operators are available: [], <<=, >>=, +=, *=, &=, |= and ^=
    in addition to [], ==, !=, +, *, ~, <<, >>, &, | and ^.

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
    pos -- The current bit position in the bitstring.
    """

    __slots__ = ()

    def __init__(self, auto: Optional[BitsType] = None, length: Optional[int] = None,
                 offset: Optional[int] = None, pos: int = 0, **kwargs) -> None:
        """Either specify an 'auto' initialiser:
        auto -- a string of comma separated tokens, an integer, a file object,
                a bytearray, a boolean iterable or another bitstring.

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
                  ignored and this is intended for use when
                  initialising using 'bytes' or 'filename'.
        pos -- Initial bit position, defaults to 0.

        """
        pass

    def __new__(cls, auto: Optional[BitsType] = None, length: Optional[int] = None,
                offset: Optional[int] = None, pos: int = 0, **kwargs) -> Bits:
        x = super(BitStream, cls).__new__(cls)
        y = ConstBitStream.__new__(BitStream, auto, length, offset, pos, **kwargs)
        x._datastore = ByteStore(y._datastore.rawarray[:],
                                 y._datastore.bitlength,
                                 y._datastore.offset)
        x._pos = y._pos
        return x

    def __copy__(self) -> BitStream:
        """Return a new copy of the BitStream."""
        s_copy = BitStream()
        s_copy._pos = 0
        if not isinstance(self._datastore, ByteStore):
            # Let them both point to the same (invariant) array.
            # If either gets modified then at that point they'll be read into memory.
            s_copy._datastore = self._datastore
        else:
            s_copy._datastore = ByteStore(self._datastore.rawarray[:],
                                          self._datastore.bitlength,
                                          self._datastore.offset)
        return s_copy

    def prepend(self, bs: BitsType) -> None:
        """Prepend a bitstring to the current bitstring.

        bs -- The bitstring to prepend.

        """
        bs = self._converttobitstring(bs)
        self._addleft(bs)
        self._pos += bs.len


def pack(fmt: Union[str, List[str]], *values, **kwargs) -> BitStream:
    """Pack the values according to the format string and return a new BitStream.

    fmt -- A single string or a list of strings with comma separated tokens
           describing how to create the BitStream.
    values -- Zero or more values to pack according to the format.
    kwargs -- A dictionary or keyword-value pairs - the keywords used in the
              format string will be replaced with their given value.

    Token examples: 'int:12'    : 12 bits as a signed integer
                    'uint:8'    : 8 bits as an unsigned integer
                    'float:64'  : 8 bytes as a big-endian float
                    'intbe:16'  : 2 bytes as a big-endian signed integer
                    'uintbe:16' : 2 bytes as a big-endian unsigned integer
                    'intle:32'  : 4 bytes as a little-endian signed integer
                    'uintle:32' : 4 bytes as a little-endian unsigned integer
                    'floatle:64': 8 bytes as a little-endian float
                    'intne:24'  : 3 bytes as a native-endian signed integer
                    'uintne:24' : 3 bytes as a native-endian unsigned integer
                    'floatne:32': 4 bytes as a native-endian float
                    'hex:80'    : 80 bits as a hex string
                    'oct:9'     : 9 bits as an octal string
                    'bin:1'     : single bit binary string
                    'ue' / 'uie': next bits as unsigned exp-Golomb code
                    'se' / 'sie': next bits as signed exp-Golomb code
                    'bits:5'    : 5 bits as a bitstring object
                    'bytes:10'  : 10 bytes as a bytes object
                    'bool'      : 1 bit as a bool
                    'pad:3'     : 3 zero bits as padding

    >>> s = pack('uint:12, bits', 100, '0xffe')
    >>> t = pack(['bits', 'bin:3'], s, '111')
    >>> u = pack('uint:8=a, uint:8=b, uint:55=a', a=6, b=44)

    """
    tokens = []
    if isinstance(fmt, str):
        fmt = [fmt]
    try:
        for f_item in fmt:
            _, tkns = tokenparser(f_item, tuple(sorted(kwargs.keys())))
            tokens.extend(tkns)
    except ValueError as e:
        raise CreationError(*e.args)
    value_iter = iter(values)
    s = BitStream()
    try:
        for name, length, value in tokens:
            # If the value is in the kwd dictionary then it takes precedence.
            if value in kwargs:
                value = kwargs[value]
            # If the length is in the kwd dictionary then use that too.
            if length in kwargs:
                length = kwargs[length]
            # Also if we just have a dictionary name then we want to use it
            if name in kwargs and length is None and value is None:
                s._append(kwargs[name])
                continue
            if length is not None:
                length = int(length)
            if value is None and name != 'pad':
                # Take the next value from the ones provided
                value = next(value_iter)
            s._append(BitStream._init_with_token(name, length, value))
    except StopIteration:
        raise CreationError(f"Not enough parameters present to pack according to the "
                            "format. {len(tokens)} values are needed.")
    try:
        next(value_iter)
    except StopIteration:
        # Good, we've used up all the *values.
        return s
    raise CreationError("Too many parameters present to pack according to the format.")


# Whether to label the Least Significant Bit as bit 0. Default is False.

def _switch_lsb0_methods(lsb0: bool) -> None:
    global _lsb0
    _lsb0 = lsb0
    Bits._setlsb0methods(lsb0)
    BitArray._setlsb0methods(lsb0)
    ByteStore._setlsb0methods(lsb0)


# Initialise the default behaviour
_switch_lsb0_methods(False)


__all__ = ['ConstBitStream', 'BitStream', 'BitArray',
           'Bits', 'pack', 'Error', 'ReadError', 'InterpretError',
           'ByteAlignError', 'CreationError', 'bytealigned', 'lsb0']


def main() -> None:
    dummy = Bits()  # We need an instance to query the _name_to_read
    # check if final parameter is an interpretation string
    fp = sys.argv[-1]
    if fp in ['-h', '--help'] or len(sys.argv) == 1:
        print("""Create and interpret a bitstring from command-line parameters.

Command-line parameters are concatenated and a bitstring created
from them. If the final parameter is either an interpretation string
or ends with a '.' followed by an interpretation string then that
interpretation of the bitstring will be used when printing it.

Typical usage might be invoking the Python module from a console
as a one-off calculation:

$ python -m bitstring int:16=-400
0xfe70
$ python -m bitstring float:32=0.2 bin
00111110010011001100110011001101
$ python -m bitstring 0xff 3*0b01,0b11 uint
65367
$ python -m bitstring hex=01, uint:12=352.hex
01160
        """)
        return
    if fp in dummy._name_to_read.keys():
        # concatenate all other parameters and interpret using the final one
        b1 = Bits(','.join(sys.argv[1: -1]))
        print(b1._readtoken(fp, 0, b1.__len__())[0])
    else:
        # does final parameter end with a dot then an interpretation string?
        interp = fp[fp.rfind('.') + 1:]
        if interp in dummy._name_to_read.keys():
            sys.argv[-1] = fp[:fp.rfind('.')]
            b1 = Bits(','.join(sys.argv[1:]))
            print(b1._readtoken(interp, 0, b1.__len__())[0])
        else:
            # No interpretation - just use default print
            b1 = Bits(','.join(sys.argv[1:]))
            print(b1)


if __name__ == '__main__':
    main()
