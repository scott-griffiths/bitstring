#!/usr/bin/env python
"""
This module defines classes that simplify bit-wise creation, manipulation and
interpretation of data.

Classes:

ConstBitArray -- An immutable container for binary data.
BitArray -- A mutable container for binary data.
ConstBitStream -- An immutable container with streaming methods.
BitStream -- A mutable container with streaming methods.

                  ConstBitArray (base class)
                     /    \ 
 + mutating methods /      \ + streaming methods
                   /        \ 
              BitArray   ConstBitStream
                   \        /
                    \      /
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

__version__ = "2.1.1"

__author__ = "Scott Griffiths"

from bitstring.constbitstream import ConstBitStream
from bitstring.bitstream import BitStream, pack
from bitstring.bitarray import BitArray
from bitstring.constbitarray import ConstBitArray
from bitstring.errors import Error, ByteAlignError, ReadError, InterpretError, CreationError

b"Python 2.6 or later is needed (otherwise this line generates a SyntaxError). For Python 2.4 and 2.5 you can download an earlier version of the bitstring module."

# Aliases for backward compatibility
Bits = ConstBitStream
BitString = BitStream
