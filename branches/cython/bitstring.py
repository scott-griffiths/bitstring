#!/usr/bin/env python
"""
This module defines classes that simplify bit-wise creation, manipulation and
interpretation of data.

Classes:

Bits -- An immutable container for binary data.
BitString -- A mutable container for binary data.

Functions:

pack -- Create BitString from a format string.

Exceptions:

Error -- Module exception base class.
CreationError -- Error during creation.
InterpretError -- Inappropriate interpretation of binary data.
ByteAlignError -- Whole byte position or length needed.
ReadError -- Reading or peeking past the end of a bitstring.

http://python-bitstring.googlecode.com
"""

from __future__ import print_function

__licence__ = """
The MIT License

Copyright (c) 2006-2010 Scott Griffiths (scott@griffiths.name)

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

__version__ = "2.1.0"

__author__ = "Scott Griffiths"

__all__ = ['BitString', 'Bits', 'pack', 'Error', 'ReadError', 'InterpretError',
           'ByteAlignError', 'CreationError']

import os
import struct
import re
import operator
import collections
import itertools
import sys
import binascii
import copy
import warnings
import functools
from cbits import * # TODO: cBits, Zero, One, CreationError, Error, InterpretError, ByteAlignError, ReadError, tokenparser, BYTE_REVERSAL_DICT, STRUCT_PACK_RE
from cbitstring import cBitString

_ = b"Python 2.6 or later is needed (otherwise this line generates a SyntaxError). For Python 2.4 and 2.5 you can download an earlier version of the bitstring module."

class Bits(cBits):
    
    def __copy__(self):
        """Return a new copy of the Bits for the copy module."""
        # Note that if you want a new copy (different ID), use _copy instead.
        # The copy can use the same datastore as it's immutable.
        s = Bits()
        s._datastore = self._datastore
        # Reset the bit position, don't copy it.
        s._pos = 0
        return s
    
    def findall(self, bs, start=None, end=None, count=None, bytealigned=False):
        """Find all occurences of bs. Return generator of bit positions.

        bs -- The bitstring to find.
        start -- The bit position to start the search. Defaults to 0.
        end -- The bit position one past the last bit to search.
               Defaults to self.len.
        count -- The maximum number of occurences to find.
        bytealigned -- If True the bitstring will only be found on
                       byte boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > self.len or
        if end < start.

        Note that all occurences of bs are found, even if they overlap.

        """
        if count is not None and count < 0:
            raise ValueError("In findall, count must be >= 0.")
        bs = self._converttobitstring(bs)
        start, end = self._validate_slice(start, end)
        c = 0
        while self.find(bs, start, end, bytealigned):
            if count is not None and c >= count:
                return
            c += 1
            yield self._pos
            if bytealigned:
                start = self._pos + 8
            else:
                start = self._pos + 1
            if start >= end:
                break
        return
    
    def cut(self, bits, start=None, end=None, count=None):
        """Return bitstring generator by cutting into bits sized chunks.

        bits -- The size in bits of the bitstring chunks to generate.
        start -- The bit position to start the first cut. Defaults to 0.
        end -- The bit position one past the last bit to use in the cut.
               Defaults to self.len.
        count -- If specified then at most count items are generated.
                 Default is to cut as many times as possible.

        """
        start, end = self._validate_slice(start, end)
        if count is not None and count < 0:
            raise ValueError("Cannot cut - count must be >= 0.")
        if bits <= 0:
            raise ValueError("Cannot cut - bits must be >= 0.")
        c = 0
        while count is None or c < count:
            c += 1
            nextchunk = self._slice(start, min(start + bits, end))
            if nextchunk.len != bits:
                return
            assert nextchunk._assertsanity()
            yield nextchunk
            start += bits
        return
  
    def split(self, delimiter, start=None, end=None, count=None,
              bytealigned=False):
        """Return bitstring generator by splittling using a delimiter.

        The first item returned is the initial bitstring before the delimiter,
        which may be an empty bitstring.

        delimiter -- The bitstring used as the divider.
        start -- The bit position to start the split. Defaults to 0.
        end -- The bit position one past the last bit to use in the split.
               Defaults to self.len.
        count -- If specified then at most count items are generated.
                 Default is to split as many times as possible.
        bytealigned -- If True splits will only occur on byte boundaries.

        Raises ValueError if the delimiter is empty.

        """
        delimiter = self._converttobitstring(delimiter)
        if not delimiter.len:
            raise ValueError("split delimiter cannot be empty.")
        start, end = self._validate_slice(start, end)
        if count is not None and count < 0:
            raise ValueError("Cannot split - count must be >= 0.")
        oldpos = self._pos
        self._pos = start
        if count == 0:
            return
        found = self.find(delimiter, start, end, bytealigned)
        if not found:
            # Initial bits are the whole bitstring being searched
            self._pos = oldpos
            yield self._slice(start, end)
            return
        # yield the bytes before the first occurence of the delimiter, even if empty
        yield self[start:self._pos]
        startpos = self._pos
        c = 1
        while count is None or c < count:
            self._pos += delimiter.len
            found = self.find(delimiter, self._pos, end, bytealigned)
            if not found:
                # No more occurences, so return the rest of the bitstring
                self._pos = oldpos
                yield self[startpos:end]
                return
            c += 1
            yield self[startpos:self._pos]
            startpos = self._pos
        # Have generated count BitStrings, so time to quit.
        self._pos = oldpos
        return

class BitString(Bits, cBitString):
    
    """A container holding a mutable sequence of bits.

    Subclass of the immutable Bits class. Inherits all of its methods (except
    __hash__) and adds mutating methods.
    
    Mutating methods:
    
    append() -- Append a bitstring.
    byteswap() -- Change byte endianness in-place.
    insert() -- Insert a bitstring.
    invert() -- Flip bit(s) between one and zero.
    overwrite() -- Overwrite a section with a new bitstring.
    prepend() -- Prepend a bitstring.
    replace() -- Replace occurences of one bitstring with another.
    reverse() -- Reverse bits in-place.
    rol() -- Rotate bits to the left.
    ror() -- Rotate bits to the right.
    set() -- Set bit(s) to 1 or 0.
    
    Methods inherited from Bits:
    
    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    bytealign() -- Align to next byte boundary.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurences of a sub-bitstring in the current bitstring.
    join() -- Join bitstrings together using current bitstring.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.
    rfind() -- Seek backwards to find a sub-bitstring.
    split() -- Create generator of chunks split by a delimiter.
    startswith() -- Return whether the bitstring starts with a sub-bitstring.
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.
    
    Special methods:

    Mutating operators are available: [], <<=, >>=, *=, &=, |= and ^=
    in addition to the inherited [], ==, !=, +, *, ~, <<, >>, &, | and ^.
    
    Properties:

    bin -- The bitstring as a binary string.
    bool -- For single bit bitstrings, interpret as True or False.
    bytepos -- The current byte position in the bitstring.
    bytes -- The bitstring as a bytes object.
    float -- Interpret as a floating point number.
    floatbe -- Interpret as a big-endian floating point number.
    floatle -- Interpret as a little-endian floating point number.
    floatne -- Interpret as a native-endian floating point number.
    hex -- The bitstring as a hexadecimal string.
    int -- Interpret as a two's complement signed integer.
    intbe -- Interpret as a big-endian signed integer.
    intle -- Interpret as a little-endian signed integer.
    intne -- Interpret as a native-endian signed integer.
    len -- Length of the bitstring in bits.
    oct -- The bitstring as an octal string.
    pos -- The current bit position in the bitstring.
    se -- Interpret as a signed exponential-Golomb code.
    ue -- Interpret as an unsigned exponential-Golomb code.
    uint -- Interpret as a two's complement unsigned integer.
    uintbe -- Interpret as a big-endian unsigned integer.
    uintle -- Interpret as a little-endian unsigned integer.
    uintne -- Interpret as a native-endian unsigned integer.
    
    """
    
    __slots__ = ()

    # As BitString objects are mutable, we shouldn't allow them to be hashed.
    __hash__ = None

    def __copy__(self):
        """Return a new copy of the BitString."""
        s_copy = BitString()
        s_copy._pos = self._pos
        if isinstance(self._datastore, FileArray):
            # Let them both point to the same (invariant) file.
            # If either gets modified then at that point they'll be read into memory.
            s_copy._datastore = self._datastore
            s_copy._filebased = True
        else:
            s_copy._datastore = copy.copy(self._datastore)
            s_copy._filebased = False
        return s_copy
    
def pack(fmt, *values, **kwargs):
    """Pack the values according to the format string and return a new BitString.

    fmt -- A string with comma separated tokens describing how to create the
           next bits in the BitString.
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
                    'ue'        : next bits as unsigned exp-Golomb code
                    'se'        : next bits as signed exp-Golomb code
                    'bits:5'    : 5 bits as a BitString object
                    'bytes:10'  : 10 bytes as a bytes object
                    'bool'      : 1 bit as a bool

    >>> s = pack('uint:12, bits', 100, '0xffe')
    >>> t = pack('bits, bin:3', s, '111')
    >>> u = pack('uint:8=a, uint:8=b, uint:55=a', a=6, b=44)

    """
    try:
        _, tokens = tokenparser(fmt, tuple(sorted(kwargs.keys())))
    except ValueError as e:
        raise CreationError(*e.args)
    value_iter = iter(values)
    s = BitString()
    try:
        for name, length, value in tokens:
            # If the value is in the kwd dictionary then it takes precedence.
            if value in kwargs:
                value = str(kwargs[value])
            # If the length is in the kwd dictionary then use that too.
            if length in kwargs:
                length = kwargs[length]
            # Also if we just have a dictionary name then we want to use it
            if name in kwargs and length is None and value is None:
                s.append(kwargs[name])
                continue
            if length is not None:
                length = int(length)
            if value is None:
                # Take the next value from the ones provided
                value = next(value_iter)
            s._append(BitString._init_with_token(name, length, value))
    except StopIteration:
        raise CreationError("Not enough parameters present to pack according to the "
                            "format. {0} values are needed.", len(tokens))
    try:
        next(value_iter)
    except StopIteration:
        # Good, we've used up all the *values.
        return s
    raise CreationError("Too many parameters present to pack according to the format.")



if __name__=='__main__':
    print("Running bitstring module unit tests:")
    try:
        import sys, os
        sys.path.insert(0, 'test')
        import test_bitstring
        os.chdir('test')
        test_bitstring.unittest.main(test_bitstring)
    except ImportError:
        print("Error: cannot find test_bitstring.py")
