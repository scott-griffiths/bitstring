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

__version__ = "4.1.0"

__author__ = "Scott Griffiths"

import sys

from bitstring.classes import Bits, BitArray, bytealigned, lsb0, _MyModuleType
from bitstring.bitstream import ConstBitStream, BitStream
from bitstring.methods import pack
from bitstring.bitstring_array import Array
from bitstring.exceptions import Error, ReadError, InterpretError, ByteAlignError, CreationError


sys.modules[__name__].__class__ = _MyModuleType


__all__ = ['ConstBitStream', 'BitStream', 'BitArray', 'Array',
           'Bits', 'pack', 'Error', 'ReadError', 'InterpretError',
           'ByteAlignError', 'CreationError', 'bytealigned', 'lsb0']


def main() -> None:
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
    if fp in Bits._name_to_read.keys():
        # concatenate all other parameters and interpret using the final one
        b1 = Bits(','.join(sys.argv[1: -1]))
        print(b1._readtoken(fp, 0, b1.__len__())[0])
    else:
        # does final parameter end with a dot then an interpretation string?
        interp = fp[fp.rfind('.') + 1:]
        if interp in Bits._name_to_read.keys():
            sys.argv[-1] = fp[:fp.rfind('.')]
            b1 = Bits(','.join(sys.argv[1:]))
            print(b1._readtoken(interp, 0, b1.__len__())[0])
        else:
            # No interpretation - just use default print
            b1 = Bits(','.join(sys.argv[1:]))
            print(b1)


if __name__ == '__main__':
    main()
