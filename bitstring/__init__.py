#!/usr/bin/env python
r"""
This package defines classes that simplify bit-wise creation, manipulation and
interpretation of data.

Classes:

Bits -- An immutable container for binary data.
BitArray -- A mutable container for binary data.
Reader -- Wraps a Bits or BitArray with a bit position for sequential reading.
Array -- An efficient list-like container where each item has a fixed-length binary format.
Dtype -- Encapsulate the data types used in the other classes.

Functions:

pack -- Create a Bits object from a format string.

Exceptions:

Error -- Module exception base class.
ReadError -- Reading or peeking past the end of a bitstring. Subclasses Error and IndexError.
ByteAlignError -- Whole byte position or length needed. Subclasses Error.
CreationError -- Error during creation. An alias for ValueError.
InterpretError -- Inappropriate interpretation of binary data. An alias for ValueError.

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

__version__ = "5.0.0b1"

__author__ = "Scott Griffiths"

import bitstring.bitstore as bitstore  # noqa: F401 - the core must be initialised before the classes that use it.

from .bits import Bits
from .bitarray_ import BitArray
from .reader import Reader
from .methods import pack
from .array_ import Array
from .exceptions import Error, ReadError, InterpretError, ByteAlignError, CreationError
from .dtypes import DtypeDefinition as _DtypeDefinition, dtype_register as _dtype_register, Dtype
from typing import Literal as _Literal
from .mxfp import decompress_luts as _mxfp_decompress_luts
from .fp8 import decompress_luts as _binary8_decompress_luts

# Decompress the LUTs for the exotic floating point formats
_mxfp_decompress_luts()
_binary8_decompress_luts()

# These methods convert a bit length to the number of characters needed to print it for different interpretations.
def _hex_bits2chars(bitlength: int):
    # One character for every 4 bits
    return bitlength // 4


def _oct_bits2chars(bitlength: int):
    # One character for every 3 bits
    return bitlength // 3


def _bin_bits2chars(bitlength: int):
    # One character for each bit
    return bitlength


def _bytes_bits2chars(bitlength: int):
    # One character for every 8 bits
    return bitlength // 8


def _uint_bits2chars(bitlength: int):
    # How many characters is largest possible int of this length?
    return len(str((1 << bitlength) - 1))


def _int_bits2chars(bitlength: int):
    # How many characters is largest negative int of this length? (To include minus sign).
    return len(str(-1 << (bitlength - 1)))


def _float_bits2chars(bitlength: _Literal[16, 32, 64]):
    # These bit lengths were found by looking at lots of possible values
    if bitlength in [16, 32]:
        return 23  # Empirical value
    else:
        return 24  # Empirical value


def _p3binary_bits2chars(_: _Literal[8]):
    return 19  # Empirical value


def _p4binary_bits2chars(_: _Literal[8]):
    # Found by looking at all the possible values
    return 13  # Empirical value


def _e4m3mxfp_bits2chars(_: _Literal[8]):
    return 13


def _e5m2mxfp_bits2chars(_: _Literal[8]):
    return 19


def _e3m2mxfp_bits2chars(_: _Literal[6]):
    # Not sure what the best value is here. It's 7 without considering the scale that could be applied.
    return 7


def _e2m3mxfp_bits2chars(_: _Literal[6]):
    # Not sure what the best value is here.
    return 7


def _e2m1mxfp_bits2chars(_: _Literal[4]):
    # Not sure what the best value is here.
    return 7


def _e8m0mxfp_bits2chars(_: _Literal[8]):
    # Has same range as float32
    return 23


def _mxint_bits2chars(_: _Literal[8]):
    # Not sure what the best value is here.
    return 10


def _bfloat_bits2chars(_: _Literal[16]):
    # Found by looking at all the possible values
    return 23  # Empirical value


def _bits_bits2chars(bitlength: int):
    # For bits type we can see how long it needs to be printed by trying any value
    temp = Bits.from_zeros(bitlength)
    return len(str(temp))


def _bool_bits2chars(_: _Literal[1]):
    # Bools are printed as 1 or 0, not True or False, so are one character each
    return 1

_dtype_definitions = [
    # Integer types
    _DtypeDefinition('u', Bits._setuint, Bits._getuint, int, False, _uint_bits2chars,
                    read_fn=Bits._readuint,
                    description="a two's complement unsigned int"),
    _DtypeDefinition('ule', Bits._setuintle, Bits._getuintle, int, False, _uint_bits2chars,
                    read_fn=Bits._readuintle,
                    allowed_lengths=(8, 16, 24, ...), description="a two's complement little-endian unsigned int"),
    _DtypeDefinition('ube', Bits._setuintbe, Bits._getuintbe, int, False, _uint_bits2chars,
                    read_fn=Bits._readuintbe,
                    allowed_lengths=(8, 16, 24, ...), description="a two's complement big-endian unsigned int"),
    _DtypeDefinition('i', Bits._setint, Bits._getint, int, True, _int_bits2chars,
                    read_fn=Bits._readint,
                    description="a two's complement signed int"),
    _DtypeDefinition('ile', Bits._setintle, Bits._getintle, int, True, _int_bits2chars,
                    read_fn=Bits._readintle,
                    allowed_lengths=(8, 16, 24, ...), description="a two's complement little-endian signed int"),
    _DtypeDefinition('ibe', Bits._setintbe, Bits._getintbe, int, True, _int_bits2chars,
                    read_fn=Bits._readintbe,
                    allowed_lengths=(8, 16, 24, ...), description="a two's complement big-endian signed int"),
    # String types
    _DtypeDefinition('hex', Bits._sethex, Bits._gethex, str, False, _hex_bits2chars,
                    read_fn=Bits._readhex,
                    allowed_lengths=(0, 4, 8, ...), description="a hexadecimal string"),
    _DtypeDefinition('bin', Bits._setbin, Bits._getbin, str, False, _bin_bits2chars,
                    read_fn=Bits._readbin,
                    description="a binary string"),
    _DtypeDefinition('oct', Bits._setoct, Bits._getoct, str, False, _oct_bits2chars,
                    read_fn=Bits._readoct,
                    allowed_lengths=(0, 3, 6, ...), description="an octal string"),
    # Float types
    _DtypeDefinition('f', Bits._setfloatbe, Bits._getfloatbe, float, True, _float_bits2chars,
                    read_fn=Bits._readfloatbe,
                    allowed_lengths=(16, 32, 64), description="a big-endian floating point number"),
    _DtypeDefinition('fle', Bits._setfloatle, Bits._getfloatle, float, True, _float_bits2chars,
                    read_fn=Bits._readfloatle,
                    allowed_lengths=(16, 32, 64), description="a little-endian floating point number"),
    _DtypeDefinition('bfloat', Bits._setbfloatbe, Bits._getbfloatbe, float, True, _bfloat_bits2chars,
                    read_fn=Bits._readbfloatbe,
                    allowed_lengths=(16,), description="a 16 bit big-endian bfloat floating point number"),
    _DtypeDefinition('bfloatle', Bits._setbfloatle, Bits._getbfloatle, float, True, _bfloat_bits2chars,
                    read_fn=Bits._readbfloatle,
                    allowed_lengths=(16,), description="a 16 bit little-endian bfloat floating point number"),
    # Other known length types
    _DtypeDefinition('bits', Bits._setbits, Bits._getbits, Bits, False, _bits_bits2chars,
                    description="a bitstring object"),
    _DtypeDefinition('bool', Bits._setbool, Bits._getbool, bool, False, _bool_bits2chars,
                    read_fn=Bits._readbool,
                    allowed_lengths=(1,), description="a bool (True or False)"),
    _DtypeDefinition('bytes', Bits._setbytes, Bits._getbytes, bytes, False, _bytes_bits2chars,
                    read_fn=Bits._readbytes,
                    multiplier=8, description="a bytes object"),
    # Unknown length types
    _DtypeDefinition('se', Bits._setse, Bits._getse, int, True, None,
                    variable_length=True, description="a signed exponential-Golomb code"),
    _DtypeDefinition('ue', Bits._setue, Bits._getue, int, False, None,
                    variable_length=True, description="an unsigned exponential-Golomb code"),
    _DtypeDefinition('sie', Bits._setsie, Bits._getsie, int, True, None,
                    variable_length=True, description="a signed interleaved exponential-Golomb code"),
    _DtypeDefinition('uie', Bits._setuie, Bits._getuie, int, False, None,
                    variable_length=True, description="an unsigned interleaved exponential-Golomb code"),
    # Special case pad type
    _DtypeDefinition('pad', Bits._setpad, Bits._getpad, None, False, None,
                    read_fn=Bits._readpad,
                    description="a skipped section of padding"),

    # MXFP and IEEE 8-bit float types
    _DtypeDefinition('p3binary', Bits._setp3binary, Bits._getp3binary, float, True, _p3binary_bits2chars,
                    read_fn=Bits._readp3binary,
                    allowed_lengths=(8,), description="an 8 bit float with binary8p3 format"),
    _DtypeDefinition('p4binary', Bits._setp4binary, Bits._getp4binary, float, True, _p4binary_bits2chars,
                    read_fn=Bits._readp4binary,
                    allowed_lengths=(8,), description="an 8 bit float with binary8p4 format"),
    _DtypeDefinition('e4m3mxfp_saturate', Bits._sete4m3mxfp_saturate, Bits._gete4m3mxfp, float, True, _e4m3mxfp_bits2chars,
                    read_fn=Bits._reade4m3mxfp,
                    allowed_lengths=(8,), description="an 8 bit float with MXFP E4M3 format, saturating out-of-range values"),
    _DtypeDefinition('e4m3mxfp_overflow', Bits._sete4m3mxfp_overflow, Bits._gete4m3mxfp, float, True, _e4m3mxfp_bits2chars,
                    read_fn=Bits._reade4m3mxfp,
                    allowed_lengths=(8,), description="an 8 bit float with MXFP E4M3 format, overflowing out-of-range values"),
    _DtypeDefinition('e5m2mxfp_saturate', Bits._sete5m2mxfp_saturate, Bits._gete5m2mxfp, float, True, _e5m2mxfp_bits2chars,
                    read_fn=Bits._reade5m2mxfp,
                    allowed_lengths=(8,), description="an 8 bit float with MXFP E5M2 format, saturating out-of-range values"),
    _DtypeDefinition('e5m2mxfp_overflow', Bits._sete5m2mxfp_overflow, Bits._gete5m2mxfp, float, True, _e5m2mxfp_bits2chars,
                    read_fn=Bits._reade5m2mxfp,
                    allowed_lengths=(8,), description="an 8 bit float with MXFP E5M2 format, overflowing out-of-range values"),
    _DtypeDefinition('e3m2mxfp', Bits._sete3m2mxfp, Bits._gete3m2mxfp, float, True, _e3m2mxfp_bits2chars,
                    read_fn=Bits._reade3m2mxfp,
                    allowed_lengths=(6,), description="a 6 bit float with MXFP E3M2 format"),
    _DtypeDefinition('e2m3mxfp', Bits._sete2m3mxfp, Bits._gete2m3mxfp, float, True, _e2m3mxfp_bits2chars,
                    read_fn=Bits._reade2m3mxfp,
                    allowed_lengths=(6,), description="a 6 bit float with MXFP E2M3 format"),
    _DtypeDefinition('e2m1mxfp', Bits._sete2m1mxfp, Bits._gete2m1mxfp, float, True, _e2m1mxfp_bits2chars,
                    read_fn=Bits._reade2m1mxfp,
                    allowed_lengths=(4,), description="a 4 bit float with MXFP E2M1 format"),
    _DtypeDefinition('e8m0mxfp', Bits._sete8m0mxfp, Bits._gete8m0mxfp, float, False, _e8m0mxfp_bits2chars,
                    read_fn=Bits._reade8m0mxfp,
                    allowed_lengths=(8,), description="an 8 bit float with MXFP E8M0 format"),
    _DtypeDefinition('mxint', Bits._setmxint, Bits._getmxint, float, True, _mxint_bits2chars,
                    read_fn=Bits._readmxint,
                    allowed_lengths=(8,), description="an 8 bit float with MXFP INT8 format"),
]


_aliases: list[tuple[str, str]] = [
    # Floats default to big endian
    ('f', 'float'),
    ('f', 'floatbe'),
    ('f', 'fbe'),
    ('bfloat', 'bfloatbe'),

    # Longer compatibility aliases for the short core type names
    ('i', 'int'),
    ('u', 'uint'),

    # Longer compatibility aliases for endian-specific type names
    ('ube', 'uintbe'),
    ('ule', 'uintle'),
    ('ibe', 'intbe'),
    ('ile', 'intle'),
    ('fle', 'floatle'),
]


for _dt in _dtype_definitions:
    _dtype_register.add_dtype(_dt)
for _alias in _aliases:
    _dtype_register.add_dtype_alias(_alias[0], _alias[1])
del _dt, _alias

_property_docstrings = [f'{name} -- Interpret as {_dtype_register[name].description}.' for name in _dtype_register.names]
_property_docstring = '\n    '.join(_property_docstrings)

# We can't be sure the docstrings are present, as it might be compiled without docstrings.
if Bits.__doc__ is not None:
    Bits.__doc__ = Bits.__doc__.replace('[GENERATED_PROPERTY_DESCRIPTIONS]', _property_docstring)
if BitArray.__doc__ is not None:
    BitArray.__doc__ = BitArray.__doc__.replace('[GENERATED_PROPERTY_DESCRIPTIONS]', _property_docstring)
__all__ = ['Reader', 'BitArray', 'Array',
           'Bits', 'pack', 'Error', 'ReadError', 'InterpretError',
           'ByteAlignError', 'CreationError', 'Dtype']
