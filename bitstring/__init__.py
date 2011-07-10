#!/usr/bin/env python
"""
This package defines classes that simplify bit-wise creation, manipulation and
interpretation of data.

Classes:

Bits -- An immutable container for binary data.
BitArray -- A mutable container for binary data.
ConstBitStream -- An immutable container with streaming methods.
BitStream -- A mutable container with streaming methods.

                      Bits (base class)
                     /    \ 
 + mutating methods /      \ + streaming methods
                   /        \ 
              BitArray   ConstBitStream
                   \        /
                    \      /
                     \    /
                    BitStream

Functions:

pack -- Create a BitStream from a format string.

Exceptions:

Error -- Module exception base class.
CreationError -- Error during creation.
InterpretError -- Inappropriate interpretation of binary data.
ByteAlignError -- Whole byte position or length needed.
ReadError -- Reading or peeking past the end of a bitstring.

http://python-bitstring.googlecode.com
"""

__licence__ = """
The MIT License

Copyright (c) 2006-2011 Scott Griffiths (scott@griffiths.name)

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

__version__ = "3.0.0"

__author__ = "Scott Griffiths"

bytealigned = False
"""Determines whether a number of methods default to working only on byte boundaries."""

class Error(Exception):
    """Base class for errors in the bitstring module."""

    def __init__(self, *params):
        self.msg = params[0] if params else ''
        self.params = params[1:]

    def __str__(self):
        if self.params:
            return self.msg.format(*self.params)
        return self.msg


class ReadError(Error, IndexError):
    """Reading or peeking past the end of a bitstring."""

    def __init__(self, *params):
        Error.__init__(self, *params)


class InterpretError(Error, ValueError):
    """Inappropriate interpretation of binary data."""

    def __init__(self, *params):
        Error.__init__(self, *params)


class ByteAlignError(Error):
    """Whole-byte position or length needed."""

    def __init__(self, *params):
        Error.__init__(self, *params)


class CreationError(Error, ValueError):
    """Inappropriate argument during bitstring creation."""

    def __init__(self, *params):
        Error.__init__(self, *params)

from bitstring.constbitstream import ConstBitStream
from bitstring.bitstream import BitStream, pack
from bitstring.bitarray import BitArray
from bitstring.bits import Bits


b"Python 2.6 or later is needed. For Python 2.4 and 2.5 you can download an earlier version of the bitstring module."

# Aliases for backward compatibility
ConstBitArray = Bits
BitString = BitStream

__all__ = ['ConstBitArray', 'ConstBitStream', 'BitStream', 'BitArray',
           'Bits', 'BitString', 'pack', 'Error', 'ReadError',
           'InterpretError', 'ByteAlignError', 'CreationError', 'bytealigned']