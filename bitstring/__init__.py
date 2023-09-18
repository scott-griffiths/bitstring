#!/usr/bin/env python
r"""
This package defines classes that simplify bit-wise creation, manipulation and
interpretation of data.

Classes:

Bits -- An immutable container for binary data.
BitArray -- A mutable container for binary data.
ConstBitStream -- An immutable container with streaming methods.
BitStream -- A mutable container with streaming methods.
Array -- An efficient list-like container where each item has a fixed-length binary format.

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

__version__ = "4.2.0"

__author__ = "Scott Griffiths"

import sys

from .bits import Bits
from .options import Options
from .bitarray import BitArray
from .bitstream import ConstBitStream, BitStream
from .methods import pack
from .array_ import Array
from .exceptions import Error, ReadError, InterpretError, ByteAlignError, CreationError
from .dtypes import MetaDtype, Register
import types
from typing import List, Tuple


# We initialise the Options singleton after the base classes have been created.
# This avoids a nasty circular import.
options = Options()
Bits._initialise_options()

# These get defined properly by the module magic below. This just stops mypy complaining about them.
bytealigned = lsb0 = None


# An opaque way of adding module level properties. Taken from https://peps.python.org/pep-0549/
class _MyModuleType(types.ModuleType):
    @property
    def bytealigned(self) -> bool:
        """Determines whether a number of methods default to working only on byte boundaries."""
        return options.bytealigned

    @bytealigned.setter
    def bytealigned(self, value: bool) -> None:
        """Determines whether a number of methods default to working only on byte boundaries."""
        options.bytealigned = value

    @property
    def lsb0(self) -> bool:
        """If True, the least significant bit (the final bit) is indexed as bit zero."""
        return options.lsb0

    @lsb0.setter
    def lsb0(self, value: bool) -> None:
        """If True, the least significant bit (the final bit) is indexed as bit zero."""
        options.lsb0 = value


sys.modules[__name__].__class__ = _MyModuleType


dtypes = [
    MetaDtype('uint', "a two's complement unsigned int",
              Bits._setuint, Bits._readuint, True, False, False, False, None),
    MetaDtype('uintle', "a two's complement little-endian unsigned int",
              Bits._setuintle, Bits._readuintle, True, False, False, False, None),
    MetaDtype('uintne', "a two's complement native-endian unsigned int",
              Bits._setuintne, Bits._readuintne, True, False, False, False, None),
    MetaDtype('uintbe', "a two's complement big-endian unsigned int",
              Bits._setuintbe, Bits._readuintbe, True, False, False, False, None),
    MetaDtype('int', "a two's complement signed int",
              Bits._setint, Bits._readint, True, False, True, False, None),
    MetaDtype('intle', "a two's complement little-endian signed int",
              Bits._setintle, Bits._readintle, True, False, True, False, None),
    MetaDtype('intne', "a two's complement native-endian signed int",
              Bits._setintne, Bits._readintne, True, False, True, False, None),
    MetaDtype('intbe', "a two's complement big-endian signed int",
              Bits._setintbe, Bits._readintbe, True, False, True, False, None),
    MetaDtype('hex', 'a hexadecimal string',
              Bits._sethex, Bits._readhex, False, False, False, False, None),
    MetaDtype('bin', 'a binary string',
              Bits._setbin_safe, Bits._readbin, False, False, False, False, None),
    MetaDtype('oct', 'an octal string',
              Bits._setoct, Bits._readoct, False, False, False, False, None),
    MetaDtype('float8_152', 'an 8 bit float with float8_152 format',
              Bits._setfloat152, Bits._readfloat152, False, True, True, False, 8),
    MetaDtype('float8_143', 'an 8 bit float with float8_143 format',
              Bits._setfloat143, Bits._readfloat143, False, True, True, False, 8),
    MetaDtype('float', 'a big-endian floating point number',
              Bits._setfloatbe, Bits._readfloatbe, False, True, True, False, None),
    MetaDtype('floatne', 'a native-endian floating point number',
              Bits._setfloatne, Bits._readfloatne, False, True, True, False, None),
    MetaDtype('floatle', 'a little-endian floating point number',
              Bits._setfloatle, Bits._readfloatle, False, True, True, False, None),
    MetaDtype('bfloat', 'a 16 bit big-endian bfloat floating point number',
              Bits._setbfloatbe, Bits._readbfloatbe, False, True, True, False, 16),
    MetaDtype('bfloatle', 'a 16 bit little-endian bfloat floating point number',
              Bits._setbfloatle, Bits._readbfloatle, False, True, True, False, 16),
    MetaDtype('bfloatne', 'a 16 bit native-endian bfloat floating point number',
              Bits._setbfloatne, Bits._readbfloatne, False, True, True, False, 16),
    MetaDtype('bits', 'a bitstring object',
              Bits._setbits, Bits._readbits, False, False, False, False, None),
    MetaDtype('bytes', 'a bytes object',
              Bits._setbytes, Bits._readbytes, False, False, False, False, None),
    MetaDtype('bool', 'a bool (True or False)',
              Bits._setbool, Bits._readbool, True, False, False, False, 1),
    MetaDtype('se', 'a signed exponential-Golomb code',
              Bits._setse, Bits._readse, True, False, True, True, None),
    MetaDtype('ue', 'an unsigned exponential-Golomb code',
              Bits._setue, Bits._readue, True, False, False, True, None),
    MetaDtype('sie', 'a signed interleaved exponential-Golomb code',
              Bits._setsie, Bits._readsie, True, False, True, True, None),
    MetaDtype('uie', 'an unsigned interleaved exponential-Golomb code',
              Bits._setuie, Bits._readuie, True, False, False, True, None),
    MetaDtype('pad', 'a skipped section of padding',
              None, Bits._readpad, False, False, False, False, None),
]

aliases: List[Tuple[str, str]] = [
    ('float', 'floatbe'),
    ('bfloat', 'bfloatbe'),
    ('int', 'i'),
    ('uint', 'u'),
    ('hex', 'h'),
    ('oct', 'o'),
    ('bin', 'b'),
    ('float', 'f')
]

register = Register()
for dt in dtypes:
    register.add_meta_dtype(dt)
for alias in aliases:
    register.add_meta_dtype_alias(alias[0], alias[1])


__all__ = ['ConstBitStream', 'BitStream', 'BitArray', 'Array',
           'Bits', 'pack', 'Error', 'ReadError', 'InterpretError',
           'ByteAlignError', 'CreationError', 'bytealigned', 'lsb0']
