#!/usr/bin/env python

from __future__ import print_function

import copy
import bitstring.constbitstream as constbitstream
import bitstring.bitarray as bitarray
from bitstring.errors import CreationError
from bitstring.bitstore import ByteArray

class BitStream(constbitstream.ConstBitStream, bitarray.BitArray):

    """A container or stream holding a mutable sequence of bits

    Subclass of the ConstBitStream and BitArray classes. Inherits all of
    their methods.

    Methods:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    append() -- Append a bitstring.
    bytealign() -- Align to next byte boundary.
    byteswap() -- Change byte endianness in-place.
    count() -- Count the number of bits set to 1 or 0.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurences of a sub-bitstring in the current bitstring.
    insert() -- Insert a bitstring.
    invert() -- Flip bit(s) between one and zero.
    join() -- Join bitstrings together using current bitstring.
    overwrite() -- Overwrite a section with a new bitstring.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    prepend() -- Prepend a bitstring.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.
    replace() -- Replace occurences of one bitstring with another.
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

    Mutating operators are available: [], <<=, >>=, *=, &=, |= and ^=
    in addition to [], ==, !=, +, *, ~, <<, >>, &, | and ^.

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


    # As BitStream objects are mutable, we shouldn't allow them to be hashed.
    __hash__ = None

    def __init__(self, auto=None, length=None, offset=None, **kwargs):
        """Either specify an 'auto' initialiser:
        auto -- a string of comma separated tokens, an integer, a file object,
                a bytearray, a boolean iterable or another bitstring.

        Or initialise via **kwargs with one (and only one) of:
        bytes -- raw data as a string, for example read from a binary file.
        bin -- binary string representation, e.g. '0b001010'.
        hex -- hexadecimal string representation, e.g. '0x2ef'
        oct -- octal string representation, e.g. '0o777'.
        uint -- an unsigned integer.
        int -- a signed integer.
        float -- a floating point number.
        uintbe -- an unsigned big-endian whole byte integer.
        intbe -- a signed big-endian whole byte integer.
        floatbe - a big-endian floating point number.
        uintle -- an unsigned little-endian whole byte integer.
        intle -- a signed little-endian whole byte integer.
        floatle -- a little-endian floating point number.
        uintne -- an unsigned native-endian whole byte integer.
        intne -- a signed native-endian whole byte integer.
        floatne -- a native-endian floating point number.
        se -- a signed exponential-Golomb code.
        ue -- an unsigned exponential-Golomb code.
        bool -- a boolean (True or False).
        filename -- a file which will be opened in binary read-only mode.

        Other keyword arguments:
        length -- length of the bitstring in bits, if needed and appropriate.
                  It must be supplied for all integer and float initialisers.
        offset -- bit offset to the data. These offset bits are
                  ignored and this is intended for use when
                  initialising using 'bytes' or 'filename'.

        """
        self._initialise(auto, length, offset, **kwargs)
        self._pos = 0
        # For mutable BitStreams we always read in files to memory:
        if not isinstance(self._datastore, ByteArray):
            self._ensureinmemory()

    def __copy__(self):
        """Return a new copy of the BitStream."""
        s_copy = BitStream()
        s_copy._pos = self._pos
        if not isinstance(self._datastore, ByteArray):
            # Let them both point to the same (invariant) array.
            # If either gets modified then at that point they'll be read into memory.
            s_copy._datastore = self._datastore
        else:
            s_copy._datastore = copy.copy(self._datastore)
        return s_copy

    def prepend(self, bs):
        bs = self._converttobitstring(bs)
        self._prepend(bs)
        self._pos += bs.len

    prepend.__doc__ = bitarray.BitArray.prepend.__doc__


def pack(fmt, *values, **kwargs):
    """Pack the values according to the format string and return a new BitStream.

    fmt -- A string with comma separated tokens describing how to create the
           next bits in the BitStream.
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
                    'bits:5'    : 5 bits as a bitstring object
                    'bytes:10'  : 10 bytes as a bytes object
                    'bool'      : 1 bit as a bool

    >>> s = pack('uint:12, bits', 100, '0xffe')
    >>> t = pack('bits, bin:3', s, '111')
    >>> u = pack('uint:8=a, uint:8=b, uint:55=a', a=6, b=44)

    """
    try:
        _, tokens = constbitstream.tokenparser(fmt, tuple(sorted(kwargs.keys())))
    except ValueError as e:
        raise CreationError(*e.args)
    value_iter = iter(values)
    s = BitStream()
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
            s._append(BitStream._init_with_token(name, length, value))
    except StopIteration:
        raise CreationError("Not enough parameters present to pack according to the "
                            "format. {0} values are needed.", len(tokens))
    try:
        next(value_iter)
    except StopIteration:
        # Good, we've used up all the *values.
        return s
    raise CreationError("Too many parameters present to pack according to the format.")

