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

__version__ = "4.1.3"

__author__ = "Scott Griffiths"

import sys

from .bits import Bits
from .bitstring_options import _Options
from .bitarray import BitArray
from .bitstream import ConstBitStream, BitStream
from .methods import pack
from .bitstring_array import Array
from .exceptions import Error, ReadError, InterpretError, ByteAlignError, CreationError
import types

options = _Options()
Bits._initialise_options()
BitArray._initialise_options()

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

__all__ = ['ConstBitStream', 'BitStream', 'BitArray', 'Array',
           'Bits', 'pack', 'Error', 'ReadError', 'InterpretError',
           'ByteAlignError', 'CreationError', 'bytealigned', 'lsb0']
