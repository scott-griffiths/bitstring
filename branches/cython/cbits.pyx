# cython: profile=True

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
from cbitstore import FileArray, ByteArray
# In future there could be other memory based array types,
# for example a C-based implementation.
MemArray = ByteArray

byteorder = sys.byteorder

# For 2.6 / 3.x coexistence
# Yes this is very very hacky.
PYTHON_VERSION = sys.version_info[0]
assert PYTHON_VERSION in [2, 3]
if PYTHON_VERSION == 2:
    from future_builtins import zip
    LEADING_OCT_CHARS = 1 # e.g. 0755
    # TODO: Python 3 hacks
#else:
#    from io import IOBase
#    xrange = range
#    long = int
#    basestring = str
#    file = IOBase
#    LEADING_OCT_CHARS = 2 # e.g. 0o755
#    # Use memoryview as buffer isn't available.
#    def buffer(data, start, size):
#        return memoryview(data)[start:start + size]

# Maximum number of digits to use in __str__ and __repr__.
MAX_CHARS = 250

def tidy_input_string(s):
    """Return string made lowercase and with all whitespace removed."""
    s = ''.join(s.split()).lower()
    return s

INIT_NAMES = ('uint', 'int', 'ue', 'se', 'hex', 'oct', 'bin', 'bits',
              'uintbe', 'intbe', 'uintle', 'intle', 'uintne', 'intne',
              'float', 'floatbe', 'floatle', 'floatne', 'bytes', 'bool')

INIT_NAMES_ORED = '|'.join(INIT_NAMES)
TOKEN_RE = re.compile(r'(?P<name>' + INIT_NAMES_ORED +
                      r')((:(?P<len>[^=]+)))?(=(?P<value>.*))?$', re.IGNORECASE)
DEFAULT_UINT = re.compile(r'(?P<len>[^=]+)?(=(?P<value>.*))?$', re.IGNORECASE)

MULTIPLICATIVE_RE = re.compile(r'(?P<factor>.*)\*(?P<token>.+)')

# Hex, oct or binary literals
LITERAL_RE = re.compile(r'(?P<name>0(x|o|b))(?P<value>.+)', re.IGNORECASE)

# An endianness indicator followed by one or more struct.pack codes
STRUCT_PACK_RE = re.compile(r'(?P<endian><|>|@)?(?P<fmt>(?:\d*[bBhHlLqQfd])+)$')

# A number followed by a single character struct.pack code
STRUCT_SPLIT_RE = re.compile(r'\d*[bBhHlLqQfd]')

# These replicate the struct.pack codes
# Big-endian
REPLACEMENTS_BE = {'b': 'intbe:8',    'B': 'uintbe:8',
                   'h': 'intbe:16',   'H': 'uintbe:16',
                   'l': 'intbe:32',   'L': 'uintbe:32',
                   'q': 'intbe:64',   'Q': 'uintbe:64',
                   'f': 'floatbe:32', 'd': 'floatbe:64'}
# Little-endian
REPLACEMENTS_LE = {'b': 'intle:8',    'B': 'uintle:8',
                   'h': 'intle:16',   'H': 'uintle:16',
                   'l': 'intle:32',   'L': 'uintle:32',
                   'q': 'intle:64',   'Q': 'uintle:64',
                   'f': 'floatle:32', 'd': 'floatle:64'}

# Size in bytes of all the pack codes.
PACK_CODE_SIZE = {'b': 1, 'B': 1, 'h': 2, 'H': 2, 'l': 4, 'L': 4,
                  'q': 8, 'Q': 8, 'f': 4, 'd': 8}

def structparser(token):
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
        # Now deal with mulitplicative factors, 4h -> hhhh etc.
        fmt = ''.join([f[-1]*int(f[:-1]) if len(f) != 1 else
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

def tokenparser(fmt, keys=None, token_cache={}):
    """Divide the format string into tokens and parse them.

    Return stretchy token and list of [initialiser, length, value]
    initialiser is one of: hex, oct, bin, uint, int, se, ue, 0x, 0o, 0b
    length is None if not known, as is value.

    If the token is in the keyword dictionary (keys) then it counts as a
    special case and isn't messed with.

    tokens must be of the form: [factor*][initialiser][:][length][=value]

    """
    try:
        return token_cache[(fmt, keys)]
    except KeyError:
        token_key = (fmt, keys)
    # Very inefficent expanding of brackets.
    fmt = expand_brackets(fmt)
    # Split tokens by ',' and remove whitespace
    # The meta_tokens can either be ordinary single tokens or multiple
    # struct-format token strings.
    meta_tokens = [''.join(f.split()) for f in fmt.split(',')]
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
            value = length = None
            if token == '':
                continue
            # Match literal tokens of the form 0x... 0o... and 0b...
            m = LITERAL_RE.match(token)
            if m:
                name = m.group('name')
                value = m.group('value')
                ret_vals.append([name, length, value])
                continue
            # Match everything else:
            m1 = TOKEN_RE.match(token)
            # and if you don't specify a 'name' then the default is 'uint':
            m2 = DEFAULT_UINT.match(token)
            if not (m1 or m2):
                raise ValueError("Don't understand token '{0}'.".format(token))
            if m1:
                name = m1.group('name')
                length = m1.group('len')
                if m1.group('value'):
                    value = m1.group('value')
            else:
                assert m2
                name = 'uint'
                length = m2.group('len')
                if m2.group('value'):
                    value = m2.group('value')
            if name == 'bool':
                if length is not None:
                    raise ValueError("You can't specify a length with bool tokens - they are always one bit.")
                length = 1
            if length is None and name not in ('se', 'ue'):
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
                        raise ValueError("Don't understand length '{0}' of token.".format(length))
            ret_vals.append([name, length, value])
        # This multiplies by the multiplicative factor, but this means that
        # we can't allow keyword values as multipliers (e.g. n*uint:8).
        # The only way to do this would be to return the factor in some fashion
        # (we can't use the key's value here as it would mean that we couldn't
        # sensibly continue to cache the function's results. (TODO).
        return_values.extend(ret_vals*factor)
    return_values = [tuple(x) for x in return_values]
    token_cache[token_key] = stretchy_token, return_values
    return stretchy_token, return_values

# Looks for first number*(
BRACKET_RE = re.compile(r'(?P<factor>\d+)\*\(')

def expand_brackets(s):
    """Remove whitespace and expand all brackets."""
    s = ''.join(s.split())
    while True:
        start = s.find('(')
        if start == -1:
            break
        count = 1 # Number of hanging open brackets
        for p in xrange(start + 1, len(s)):
            if s[p] == '(':
                count += 1
            if s[p] == ')':
                count -= 1
            if count == 0:
                break
        if count != 0:
            raise ValueError("Unbalanced parenthesis in '{0}'.".format(s))
        if start == 0 or s[start-1] != '*':
            s = s[0:start] + s[start + 1:p] + s[p + 1:]
        else:
            m = BRACKET_RE.search(s)
            if m:
                factor = int(m.group('factor'))
                matchstart = m.start('factor')
                s = s[0:matchstart] + (factor - 1)*(s[start + 1:p] + ',') + s[start + 1:p] + s[p + 1:]
            else:
                raise ValueError("Failed to parse '{0}'.".format(s))
    return s


# This byte to bitstring lookup really speeds things up.
BYTE_TO_BITS = tuple(['{0:08b}'.format(i) for i in xrange(256)])

# And this convers a single octal digit to 3 bits.
OCT_TO_BITS = tuple(['{0:03b}'.format(i) for i in xrange(8)])

# This creates a dictionary for every possible byte with the value being
# the key with its bits reversed.
REVERSED = b"\x00\x80\x40\xc0\x20\xa0\x60\xe0\x10\x90\x50\xd0\x30\xb0\x70\xf0" \
           b"\x08\x88\x48\xc8\x28\xa8\x68\xe8\x18\x98\x58\xd8\x38\xb8\x78\xf8" \
           b"\x04\x84\x44\xc4\x24\xa4\x64\xe4\x14\x94\x54\xd4\x34\xb4\x74\xf4" \
           b"\x0c\x8c\x4c\xcc\x2c\xac\x6c\xec\x1c\x9c\x5c\xdc\x3c\xbc\x7c\xfc" \
           b"\x02\x82\x42\xc2\x22\xa2\x62\xe2\x12\x92\x52\xd2\x32\xb2\x72\xf2" \
           b"\x0a\x8a\x4a\xca\x2a\xaa\x6a\xea\x1a\x9a\x5a\xda\x3a\xba\x7a\xfa" \
           b"\x06\x86\x46\xc6\x26\xa6\x66\xe6\x16\x96\x56\xd6\x36\xb6\x76\xf6" \
           b"\x0e\x8e\x4e\xce\x2e\xae\x6e\xee\x1e\x9e\x5e\xde\x3e\xbe\x7e\xfe" \
           b"\x01\x81\x41\xc1\x21\xa1\x61\xe1\x11\x91\x51\xd1\x31\xb1\x71\xf1" \
           b"\x09\x89\x49\xc9\x29\xa9\x69\xe9\x19\x99\x59\xd9\x39\xb9\x79\xf9" \
           b"\x05\x85\x45\xc5\x25\xa5\x65\xe5\x15\x95\x55\xd5\x35\xb5\x75\xf5" \
           b"\x0d\x8d\x4d\xcd\x2d\xad\x6d\xed\x1d\x9d\x5d\xdd\x3d\xbd\x7d\xfd" \
           b"\x03\x83\x43\xc3\x23\xa3\x63\xe3\x13\x93\x53\xd3\x33\xb3\x73\xf3" \
           b"\x0b\x8b\x4b\xcb\x2b\xab\x6b\xeb\x1b\x9b\x5b\xdb\x3b\xbb\x7b\xfb" \
           b"\x07\x87\x47\xc7\x27\xa7\x67\xe7\x17\x97\x57\xd7\x37\xb7\x77\xf7" \
           b"\x0f\x8f\x4f\xcf\x2f\xaf\x6f\xef\x1f\x9f\x5f\xdf\x3f\xbf\x7f\xff"

if PYTHON_VERSION == 2:
    BYTE_REVERSAL_DICT = dict(zip(xrange(256), REVERSED))
else:
    BYTE_REVERSAL_DICT = dict(zip(xrange(256), [bytes([x]) for x in REVERSED]))

BIT_COUNT = dict(zip(xrange(256), [bin(i).count('1') for i in xrange(256)]))

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

cdef class cBits:    
    """A container holding an immutable sequence of bits.
    
    For a mutable container use the BitString class instead.
    
    Methods:
    
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

    Also available are the operators [], ==, !=, +, *, ~, <<, >>, &, |, ^.
    
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
                  ignored and this is mainly intended for use when
                  initialising using 'bytes' or 'filename'.

        """
        self._mutable = False
        self._filebased = False
        self._initialise(auto, length, offset, **kwargs)

    def _initialise(self, auto, length, offset, **kwargs):
        if length is not None and length < 0:
            raise CreationError("bitstring length cannot be negative.")
        if offset is not None and offset < 0:
            raise CreationError("offset must be >= 0.")
        self._pos = 0
        if auto is not None:
            self._initialise_from_auto(auto, length, offset)
            return
        if not kwargs:
            # No initialisers, so initialise with nothing or zero bits
            if length is not None and length != 0:
                data = bytearray((length + 7) // 8)
                self._setbytes_safe(data, length)
                return
            self._setbytes_unsafe(b'', 0, 0)
            return
        k, v = kwargs.popitem()
        try:
            init_without_length_or_offset[k](self, v)
            if length is not None or offset is not None:
                raise CreationError("Cannot use length or offset with this initialiser.")
        except KeyError:
            try:
                init_with_length_only[k](self, v, length)
                if offset is not None:
                    raise CreationError("Cannot use offset with this initialiser.")
            except KeyError:
                if offset is None:
                    offset = 0
                try:
                    init_with_length_and_offset[k](self, v, length, offset)
                except KeyError:
                    raise CreationError("Unrecognised keyword '{0}' used to initialise.", k)

    def _initialise_from_auto(self, auto, length, offset):
        if offset is None:
            offset = 0
        self._setauto(auto, length, offset)
        return

    def __add__(self, bs):
        """Concatenate bitstrings and return new bitstring.

        bs -- the bitstring to append.

        """
        if not isinstance(self, cBits):
            # This is really __radd__.
            self, bs = bs, self
            bs = self._converttobitstring(bs)
            s = bs._copy()
            s._append(self)
            return s
        bs = self._converttobitstring(bs)
        s = self._copy()
        s._append(bs)
        s._pos = 0
        return s

    def __getitem__(self, key):
        """Return a new bitstring representing a slice of the current bitstring.

        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.

        >>> print Bits('0b00110')[1:4]
        '0b011'
        >>> print Bits('0x00112233')[1:3:8]
        '0x1122'

        """
        cdef long start, stop, step, i, length
        length = self.len
        try:
            step = key.step if key.step is not None else 1
        except AttributeError:
            # single element
            i = key
            if i < 0:
                i += length
            if not 0 <= i < length:
                raise IndexError("Slice index out of range.")
            # Single bit, return True or False
            return self._datastore.getbit(i)
        else:
            start = 0
            if step != 0:
                stop = length - (length % abs(step))
            else:
                stop = 0
            if key.start is not None:
                start = key.start * abs(step)
                if key.start < 0:
                    start += stop
            if key.stop is not None:
                stop = key.stop * abs(step)
                if key.stop < 0:
                    stop += length - (length % abs(step))
            start = max(start, 0)
            stop = min(stop, length - length % abs(step))
            # Adjust start and stop if we're stepping backwards
            if step < 0:
                # This compensates for negative indices being inclusive of the
                # final index rather than the first.
                if key.start is not None and key.start < 0:
                    start += step
                if key.stop is not None and key.stop < 0:
                    stop += step
                if key.start is None:
                    start = self.len - (self.len % abs(step)) + step
                if key.stop is None:
                    stop = step
                start, stop = stop - step, start - step
            if start < stop:
                if step >= 0:
                    return self._slice(start, stop)
                else:
                    # Negative step, so reverse the BitString in chunks of step.
                    # TODO: Replace xrange (could fail with 32-bit Python 2.x).
                    bsl = [self._slice(x, x - step) for x in xrange(start, stop, -step)]
                    bsl.reverse()
                    return self.__class__().join(bsl)
            else:
                return self.__class__()

    def __len__(self):
        """Return the length of the bitstring in bits."""
        return self._getlength()

    def __str__(self):
        """Return approximate string representation of bitstring for printing.

        Short strings will be given wholly in hexadecimal or binary. Longer
        strings may be part hexadecimal and part binary. Very long strings will
        be truncated with '...'.

        """
        length = self.len
        if length == 0:
            return ''
        if length > MAX_CHARS*4:
            # Too long for hex. Truncate...
            return ''.join((self._readhex(MAX_CHARS*4, 0), '...'))
        # If it's quite short and we can't do hex then use bin
        if length < 32 and length % 4 != 0:
            return self.bin
        # If we can use hex then do so
        if length % 4 == 0:
            return self.hex
        # Otherwise first we do as much as we can in hex
        # then add on 1, 2 or 3 bits on at the end
        bits_at_end = length % 4
        return ''.join((self._readhex(length - bits_at_end, 0),
                        ', ',
                        self._readbin(bits_at_end, length - bits_at_end)))

    def __repr__(self):
        """Return representation that could be used to recreate the bitstring.

        If the returned string is too long it will be truncated. See __str__().

        """
        length = self.len
        if isinstance(self._datastore, FileArray):
            offsetstring = ''
            if self._datastore.byteoffset or self._offset:
                offset = self._datastore.byteoffset * 8 + self._offset
                offsetstring = ", offset=%d" % offset
            lengthstring = ", length=%d" % length
            return "{0}(filename='{1}'{2}{3})".format(self.__class__.__name__,
                    self._datastore.source.name, lengthstring, offsetstring)
        else:
            s = self.__str__()
            lengthstring = ''
            if s.endswith('...'):
                lengthstring = " # length={0}".format(length)
            return "{0}('{1}'){2}".format(self.__class__.__name__, s, lengthstring)

    def __richcmp__(self, bs, n):
        if n == 2: # ==
            return self._eq(bs)
        if n == 3: # !=
            return self._ne(bs)

    def _eq(self, bs):
        """Return True if two bitstrings have the same binary representation.

        >>> Bits('0b1110') == '0xe'
        True

        """
        try:
            bs = self._converttobitstring(bs)
        except TypeError:
            return False
        if self.len != bs.len:
            return False
        # TODO: There's still a lot we can do to make this faster. We should be
        # looking at the raw data so that we don't change offsets unless we
        # really have to.
        # Check in chunks so that we can exit early if possible.
        chunk_size = (1 << 21)
        if self.len <= chunk_size:
            return self.tobytes() == bs.tobytes()
        for s_chunk, bs_chunk in zip(self.cut(chunk_size), bs.cut(chunk_size)):
            if s_chunk.tobytes() != bs_chunk.tobytes():
                return False
        final_bits = self.len % chunk_size
        if self[-final_bits:].tobytes() != bs[-final_bits:].tobytes():
            return False
        return True

    def _ne(self, bs):
        """Return False if two bitstrings have the same binary representation.

        >>> Bits('0b111') == '0x7'
        False

        """
        return not self._eq(bs)

    def __invert__(self):
        """Return bitstring with every bit inverted.

        Raises Error if the bitstring is empty.

        """
        if not self.len:
            raise Error("Cannot invert empty bitstring.")
        s = self._copy()
        s._invert_all()
        return s

    def __lshift__(self, n):
        """Return bitstring with bits shifted by n to the left.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        s = self[n:]
        s._append(cBits(length=min(n, self.len)))
        return s

    def __rshift__(self, n):
        """Return bitstring with bits shifted by n to the right.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        if n == 0:
            return self._copy()
        s = self.__class__(length=min(n, self.len))
        s._append(self[:-n])
        return s

    def __mul__(self, n):
        """Return bitstring consisting of n concatenations of self.

        Called for expression of the form 'a = b*3'.
        n -- The number of concatenations. Must be >= 0.

        """
        if not isinstance(self, cBits):
            # This is really __rmul__
            self, n = n, self
        if not isinstance(n, (int, long)):
            raise TypeError("Can only multiply a bitstring by an int, "
                            "but {0} was provided.".format(type(n)))
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        if n == 0:
            return self.__class__()
        s = self._copy()
        s._imul(n)
        return s

    def __rmul__(self, n):
        """Return bitstring consisting of n concatenations of self.

        Called for expressions of the form 'a = 3*b'.
        n -- The number of concatenations. Must be >= 0.

        """
        return self.__mul__(n)

    def __and__(self, bs):
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        if not isinstance(self, cBits):
            self, bs = bs, self
        bs = self._converttobitstring(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length "
                             "for & operator.")
        s = self._copy()
        s._iand(bs)
        return s

    def __rand__(self, bs):
        """Bit-wise 'and' between two bitstrings. Returns new bitstring.

        bs -- the bitstring to '&' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__and__(bs)

    def __or__(self, bs):
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        if not isinstance(self, cBits):
            self, bs = bs, self
        bs = self._converttobitstring(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length "
                             "for | operator.")
        s = self._copy()
        s._ior(bs)
        return s

    def __ror__(self, bs):
        """Bit-wise 'or' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '|' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__or__(bs)

    def __xor__(self, bs):
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitsntring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        if not isinstance(self, cBits):
            self, bs = bs, self
        bs = self._converttobitstring(bs)
        if self.len != bs.len:
            raise ValueError("BitStrings must have the same length "
                             "for ^ operator.")
        s = self._copy()
        s._ixor(bs)
        return s

    def __rxor__(self, bs):
        """Bit-wise 'xor' between two bitstrings. Returns new bitstring.

        bs -- The bitstring to '^' with.

        Raises ValueError if the two bitstrings have differing lengths.

        """
        return self.__xor__(bs)

    def __contains__(self, bs):
        """Return whether bs is contained in the current bitstring.

        bs -- The bitstring to search for.

        """
        oldpos = self._pos
        found = self.find(bs, bytealigned=False)
        self._pos = oldpos
        return bool(found)

    def __hash__(self):
        """Return an integer hash of the current Bits object."""
        # We can't in general hash the whole Bits (it could take hours!)
        # So instead take some bits from the start and end.
        if self.len <= 160:
            # Use the whole Bits.
            shorter = self
        else:
            # Take 10 bytes from start and end
            shorter = self[:80] + self[-80:]
        h = 0
        for byte in shorter.tobytes():
            if PYTHON_VERSION == 2:
                h = (h << 4) + ord(byte)
            else:
                h = (h << 4) + byte
            g = h & 0xf0000000
            if g & (1 << 31):
                h = h ^ (g >> 24)
                h = h ^ g
        return h % 1442968193

    # This is only used in Python 2.x...
    def __nonzero__(self):
        """Return True if any bits are set to 1, otherwise return False."""
        return self.len and self.uint
    
    # ...whereas this does the equivalent for Python 3.x
    def __bool__(self):
        """Return True if any bits are set to 1, otherwise return False."""
        if not self.len:
            return False
        return (self.uint != 0)
    
    def _assertsanity(self):
        """Check internal self consistency as a debugging aid."""
        assert self.len >= 0
        assert 0 <= self._offset < 8, "offset={0}".format(self._offset)
        if self.len == 0:
            assert self._pos == 0, "len=0, pos={0}".format(self._pos)
        else:
            assert 0 <= self._pos <= self.len, "len={0}, pos={1}".format(self.len, self._pos)
        assert (self.len + self._offset + 7) // 8 == self._datastore.bytelength
        return True

    @classmethod
    def _init_with_token(cls, name, token_length, value):
        if token_length is not None:
            token_length = int(token_length)
        if token_length == 0:
            return cls()
        if name in ('0x', '0X', 'hex'):
            b = cls(hex=value)
        elif name in ('0b', '0B', 'bin'):
            b = cls(bin=value)
        elif name in ('0o', '0O', 'oct'):
            b = cls(oct=value)
        elif name == 'se':
            b = cls(se=int(value))
        elif name == 'ue':
            b = cls(ue=int(value))
        elif name == 'uint':
            b = cls(uint=int(value), length=token_length)
        elif name == 'int':
            b = cls(int=int(value), length=token_length)
        elif name == 'uintbe':
            b = cls(uintbe=int(value), length=token_length)
        elif name == 'intbe':
            b = cls(intbe=int(value), length=token_length)
        elif name == 'uintle':
            b = cls(uintle=int(value), length=token_length)
        elif name == 'intle':
            b = cls(intle=int(value), length=token_length)
        elif name == 'uintne':
            b = cls(uintne=int(value), length=token_length)
        elif name == 'intne':
            b = cls(intne=int(value), length=token_length)
        elif name == 'float':
            b = cls(float=float(value), length=token_length)
        elif name == 'floatbe':
            b = cls(floatbe=float(value), length=token_length)
        elif name == 'floatle':
            b = cls(floatle=float(value), length=token_length)
        elif name == 'floatne':
            b = cls(floatne=float(value), length=token_length)
        elif name == 'bits':
            b = cls(value)
        elif name == 'bytes':
            b = cls(bytes=value)
        elif name == 'bool':
            if value is True or value == 'True':
                b = cls(bool=True)
            elif value is False or value == 'False':
                b = cls(bool=False)
            else:
                raise CreationError("bool token can only be 'True' or 'False'.")
        else:
            raise CreationError("Can't parse token name {0}.", name)
        if token_length is not None and b.len != token_length:
            msg = "Token with length {0} packed with value of length {1} ({2}:{3}={4})."
            raise CreationError(msg, token_length, b.len, name, token_length, value)
        return b

    def _clear(self):
        """Reset the bitstring to an empty state."""
        self._datastore = MemArray(b'')
        self._pos = 0

    def _setauto(self, s, length, offset):
        """Set bitstring from a bitstring, file, bool, integer, iterable or string."""
        # As s can be so many different things it's important to do the checks
        # in the correct order, as some types are also other allowed types.
        # So basestring must be checked before Iterable
        # and bytes/bytearray before Iterable but after basestring!
        if isinstance(s, cBits):
            if length is None:
                length = s.len - offset
            if s._filebased:
                self._setfile(s._datastore.source.name, length, s._offset + offset)
            else:
                self._setbytes_unsafe(s._datastore.rawbytes, length, s._offset + offset)
            return     
        if isinstance(s, file):
            self._datastore = FileArray(s, length, offset)
            if self._mutable:
                # For mutable BitStrings we immediately read into memory.
                self._ensureinmemory()
            else:
                self._filebased = True
            return
        if length is not None:
            raise CreationError("The length keyword isn't applicable to this initialiser.")
        if offset != 0:
            raise CreationError("The offset keyword isn't applicable to this initialiser.")
        if isinstance(s, basestring):
            bs = self._converttobitstring(s)
            self._setbytes_unsafe(bs._datastore.rawbytes, bs.length, bs._offset)
            return
        if isinstance(s, (bytes, bytearray)):
            self._setbytes_unsafe(s, len(s)*8, 0)
            return
        if isinstance(s, (int, long)):
            # Initialise with s zero bits.
            if s < 0:
                msg = "Can't create bitstring of negative length {0}."
                raise CreationError(msg, s)
            data = bytearray((s + 7) // 8)
            self._setbytes_unsafe(bytes(data), s, 0)
            return
        if isinstance(s, collections.Iterable):
            # Evaluate each item as True or False and set bits to 1 or 0.
            self._setbin_unsafe(''.join([str(int(bool(x))) for x in s]))
            return
        raise TypeError("Cannot initialise bitstring from {0}.".format(type(s)))

    def _setfile(self, filename, length, offset):
        "Use file as source of bits."
        source = open(filename, 'rb')
        self._datastore = FileArray(source, length, offset)
        if self._mutable:
            self._ensureinmemory()
        else:
            self._filebased = True

    def _setbytes_safe(self, data, length=None, offset=0):
        """Set the data from a string."""
        if length is None:
            # Use to the end of the data
            length = (len(data) - (offset // 8)) * 8 - offset
            self._datastore = MemArray(data, length, offset)
        else:
            if length + offset > len(data)*8:
                msg = "Not enough data present. Need {0} bits, have {1}."
                raise CreationError(msg, length + offset, len(data)*8)
            if length == 0:
                self._datastore = MemArray(b'')
            else:
                self._datastore = MemArray(data, length, offset)
    
    def _setbytes_unsafe(self, data, length, offset):
        """Unchecked version of _setbytes_safe."""
        self._datastore = MemArray(data, length, offset)
        assert self._assertsanity()

    def _readbytes(self, length, start):
        """Read bytes and return them."""
        # TODO: Optimise.
        assert length % 8 == 0
        assert start + length <= self.len
        return self[start:start + length].tobytes()

    def _getbytes(self):
        """Return the data as an ordinary string."""
        if self.len % 8 != 0:
            raise InterpretError("Cannot interpret as bytes unambiguously - "
                                  "not multiple of 8 bits.")
        return self._readbytes(self.len, 0)

    def _setuint(self, uint, length=None):
        """Reset the bitstring to have given unsigned int interpretation."""
        try:
            if length is None:
                # Use the whole length. Deliberately not using .len here.
                length = self._datastore.bitlength
        except AttributeError:
            # bitstring doesn't have a _datastore as it hasn't been created!
            pass
        # TODO: All this checking code should be hoisted out of here!
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a "
                                "uint initialiser.")
        if uint >= (1 << length):
            msg = "uint {0} is too large for a bitstring of length {1}."
            raise CreationError(msg, uint, length)
        if uint < 0:
            raise CreationError("uint cannot be initialsed by a negative number.")
        blist = []
        mask = 0xffff
        while uint:
            # Pack lowest bytes as little endian (as it will be reversed shortly)
            x = bytearray(struct.pack('>H', uint & mask))
            blist.append(x)
            uint >>= 16
        blist.reverse()
        # Now add or remove bytes as needed to get the right length.
        extrabytes = ((length + 7) // 8) - len(blist)*2
        if extrabytes > 0:
            data = bytes(bytearray(extrabytes) + bytearray().join(blist))
        elif extrabytes < 0:
            data = bytearray().join(blist)[-extrabytes:]
        else:
            data = bytearray().join(blist)
        offset = 8 - (length % 8)
        if offset == 8:
            offset = 0
        self._setbytes_unsafe(data, length, offset)

    def _readuint(self, length, start):
        """Read bits and interpret as an unsigned int."""
        if length == 0:
            raise InterpretError("Cannot interpret a zero length bitstring "
                                 "as an integer.")
        startbyte = (start + self._offset) // 8
        endbyte = (start + self._offset + length - 1) // 8
        val = 0
        chunksize = 4 # for 'L' format
        while startbyte + chunksize <= endbyte + 1:
            val <<= 8 * chunksize
            val += struct.unpack('>L', self._datastore.getbyteslice(startbyte, startbyte + chunksize))[0]
            startbyte += chunksize
        for b in xrange(startbyte, endbyte + 1):
            val <<= 8
            val += self._datastore.getbyte(b)
        final_bits = 8 - ((start + self._offset + length) % 8)
        if final_bits != 8:
            val >>= final_bits
        val &= (1 << length) - 1
        return val

    def _getuint(self):
        """Return data as an unsigned int."""
        return self._readuint(self.len, 0)

    def _setint(self, int_, length=None):
        """Reset the bitstring to have given signed int interpretation."""
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with an int initialiser.")
        if int_ >=  (1 << (length - 1)) or int_ < -(1 << (length - 1)):
            raise CreationError("int {0} is too large for a bitstring of length {1}.", int_, length)
        if int_ >= 0:
            self._setuint(int_, length)
            return
        # TODO: We should decide whether to just use the _setuint, or to do the bit flipping,
        # based upon which will be quicker. If the -ive number is less than half the maximum
        # possible then it's probably quicker to do the bit flipping...

        # Do the 2's complement thing. Add one, set to minus number, then flip bits.
        int_ += 1
        self._setuint(-int_, length)
        self._invert_all()

    def _readint(self, length, start):
        """Read bits and interpret as a signed int"""
        ui = self._readuint(length, start)
        if not ui >> (length - 1):
            # Top bit not set, number is positive
            return ui
        # Top bit is set, so number is negative
        tmp = (~(ui - 1)) & ((1 << length) - 1)
        return -tmp

    def _getint(self):
        """Return data as a two's complement signed int."""
        return self._readint(self.len, 0)

    def _setuintbe(self, uintbe, length=None):
        """Set the bitstring to a big-endian unsigned int interpretation."""
        if length is not None and length % 8 != 0:
            raise CreationError("Big-endian integers must be whole-byte. "
                                "Length = {0} bits.", length)
        self._setuint(uintbe, length)

    def _readuintbe(self, length, start):
        """Read bits and interpret as a big-endian unsigned int."""
        if length % 8 != 0:
            raise InterpretError("Big-endian integers must be whole-byte. "
                                 "Length = {0} bits.", length)
        return self._readuint(length, start)

    def _getuintbe(self):
        """Return data as a big-endian two's complement unsigned int."""
        return self._readuintbe(self.len, 0)

    def _setintbe(self, intbe, length=None):
        """Set bitstring to a big-endian signed int interpretation."""
        if length is not None and length % 8 != 0:
            raise CreationError("Big-endian integers must be whole-byte. "
                                "Length = {0} bits.", length)
        self._setint(intbe, length)

    def _readintbe(self, length, start):
        """Read bits and interpret as a big-endian signed int."""
        if length % 8 != 0:
            raise InterpretError("Big-endian integers must be whole-byte. "
                                 "Length = {0} bits.", length)
        return self._readint(length, start)

    def _getintbe(self):
        """Return data as a big-endian two's complement signed int."""
        return self._readintbe(self.len, 0)

    def _setuintle(self, uintle, length=None):
        if length is not None and length % 8 != 0:
            raise CreationError("Little-endian integers must be whole-byte. "
                                "Length = {0} bits.", length)
        self._setuint(uintle, length)
        self._reversebytes(0, self.len)

    def _readuintle(self, length, start):
        """Read bits and interpret as a little-endian unsigned int."""
        if length % 8 != 0:
            raise InterpretError("Little-endian integers must be whole-byte. "
                                 "Length = {0} bits.", length)
        assert start + length <= self.len
        absolute_pos = start + self._offset
        startbyte, offset = divmod(absolute_pos, 8)
        val = 0
        if not offset:
            endbyte = (absolute_pos + length - 1) // 8
            chunksize = 4 # for 'L' format
            while endbyte - chunksize + 1 >= startbyte:
                val <<= 8 * chunksize
                val += struct.unpack('<L', self._datastore.getbyteslice(endbyte + 1 - chunksize, endbyte + 1))[0]
                endbyte -= chunksize
            for b in xrange(endbyte, startbyte - 1, -1):
                val <<= 8
                val += self._datastore.getbyte(b)
        else:
            data = self[start:start + length]
            assert data.len % 8 == 0
            data._reversebytes(0, self.len)
            for b in bytearray(data.bytes):
                val <<= 8
                val += b
        return val

    def _getuintle(self):
        return self._readuintle(self.len, 0)

    def _setintle(self, intle, length=None):
        if length is not None and length % 8 != 0:
            raise CreationError("Little-endian integers must be whole-byte. "
                                "Length = {0} bits.", length)
        self._setint(intle, length)
        self._reversebytes(0, self.len)

    def _readintle(self, length, start):
        """Read bits and interpret as a little-endian signed int."""
        ui = self._readuintle(length, start)
        if not ui >> (length - 1):
            # Top bit not set, number is positive
            return ui
        # Top bit is set, so number is negative
        tmp = (~(ui - 1)) & ((1 << length) - 1)
        return -tmp

    def _getintle(self):
        return self._readintle(self.len, 0)

    def _setfloat(self, f, length=None):
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a "
                                "float initialiser.")
        if length == 32:
            b = struct.pack('>f', f)
        elif length == 64:
            b = struct.pack('>d', f)
        else:
            raise CreationError("floats can only be 32 or 64 bits long, "
                                "not {0} bits", length)
        self._setbytes_unsafe(b, length, 0)

    def _readfloat(self, length, start):
        """Read bits and interpret as a float."""
        f = None
        if (start + self._offset) % 8 == 0:
            startbyte = (start + self._offset) // 8
            if length == 32:
                f, = struct.unpack('>f', self._datastore.getbyteslice(startbyte, startbyte + 4))
            elif length == 64:
                f, = struct.unpack('>d', self._datastore.getbyteslice(startbyte, startbyte + 8))
        else:
            if length == 32:
                f, = struct.unpack('>f', self[start:start + 32].bytes)
            elif length == 64:
                f, = struct.unpack('>d', self[start:start + 64].bytes)
        if f is not None:
            return f
        raise InterpretError("floats can only be 32 or 64 bits long, not {0} bits", length)

    def _getfloat(self):
        """Interpret the whole bitstring as a float."""
        return self._readfloat(self.len, 0)

    def _setfloatle(self, f, length=None):
        # If no length given, and we've previously been given a length, use it.
        if length is None and hasattr(self, 'len') and self.len != 0:
            length = self.len
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a "
                                "float initialiser.")
        if length == 32:
            b = struct.pack('<f', f)
        elif length == 64:
            b = struct.pack('<d', f)
        else:
            raise CreationError("floats can only be 32 or 64 bits long, "
                                "not {0} bits", length)
        self._setbytes_unsafe(b, length, 0)

    def _readfloatle(self, length, start):
        """Read bits and interpret as a little-endian float."""
        startbyte, offset = divmod(start + self._offset, 8)
        if offset == 0:
            if length == 32:
                f, = struct.unpack('<f', self._datastore.getbyteslice(startbyte, startbyte + 4))
            elif length == 64:
                f, = struct.unpack('<d', self._datastore.getbyteslice(startbyte, startbyte + 8))
        else:
            if length == 32:
                f, = struct.unpack('<f', self[start:start + 32].bytes)
            elif length == 64:
                f, = struct.unpack('<d', self[start:start + 64].bytes)
        try:
            return f
        except NameError:
            raise InterpretError("floats can only be 32 or 64 bits long, "
                                 "not {0} bits", length)

    def _getfloatle(self):
        """Interpret the whole bitstring as a little-endian float."""
        return self._readfloatle(self.len, 0)

    def _setue(self, i):
        """Initialise bitstring with unsigned exponential-Golomb code for integer i.

        Raises CreationError if i < 0.

        """
        if i < 0:
            raise CreationError("Cannot use negative initialiser for unsigned "
                                "exponential-Golomb.")
        if i == 0:
            self._setbin_unsafe('1')
            return
        tmp = i + 1
        leadingzeros = -1
        while tmp > 0:
            tmp >>= 1
            leadingzeros += 1
        remainingpart = i + 1 - (1 << leadingzeros)
        binstring = '0'*leadingzeros + '1' + cBits(uint=remainingpart,
                                                       length=leadingzeros).bin[2:]
        self._setbin_unsafe(binstring)

    def _readue(self):
        """Return interpretation of next bits as unsigned exponential-Golomb code.

        Advances position to after the read code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        oldpos = self._pos
        foundone = self.find(One, self._pos)
        if not foundone:
            self._pos = self.len
            raise ReadError("Read off end of bitstring trying to read code.")
        leadingzeros = self._pos - oldpos
        codenum = (1 << leadingzeros) - 1
        if leadingzeros > 0:
            restofcode = self.read(leadingzeros + 1)
            if restofcode.len != leadingzeros + 1:
                raise ReadError("Read off end of bitstring trying to read code.")
            codenum += restofcode[1:].uint
        else:
            assert codenum == 0
            self._pos += 1
        return codenum

    def _getue(self):
        """Return data as unsigned exponential-Golomb code.

        Raises InterpretError if bitstring is not a single exponential-Golomb code.

        """
        oldpos = self._pos
        self._pos = 0
        try:
            value = self._readue()
            if self._pos != self.len:
                raise Error
        except Error:
            self._pos = oldpos
            raise InterpretError("Bitstring is not a single exponential-Golomb code.")
        self._pos = oldpos
        return value

    def _setse(self, i):
        """Initialise bitstring with signed exponential-Golomb code for integer i."""
        if i > 0:
            u = (i*2) - 1
        else:
            u = -2*i
        self._setue(u)

    def _getse(self):
        """Return data as signed exponential-Golomb code.

        Raises InterpretError if bitstring is not a single exponential-Golomb code.

        """
        oldpos = self._pos
        self._pos = 0
        try:
            value = self._readse()
            if value is None or self._pos != self.len:
                raise ReadError
        except ReadError:
            self._pos = oldpos
            raise InterpretError("Bitstring is not a single exponential-Golomb code.")
        self._pos = oldpos
        return value

    def _readse(self):
        """Return interpretation of next bits as a signed exponential-Golomb code.

        Advances position to after the read code.

        Raises ReadError if the end of the bitstring is encountered while
        reading the code.

        """
        codenum = self._readue()
        m = (codenum + 1) // 2
        if codenum % 2 == 0:
            return -m
        else:
            return m

    def _setbool(self, value):
        # We deliberately don't want to have implicit conversions to bool here.
        # If we did then it would be difficult to deal with the 'False' string.
        if value is True or value == 'True':
            self._setbytes_unsafe(b'\x80', 1, 0)
        elif value is False or value == 'False':
            self._setbytes_unsafe(b'\x00', 1, 0)
        else:
            raise CreationError('Cannot initialise boolean with {0}.', value)

    def _getbool(self):
        if self.length != 1:
            msg = "For a bool interpretation a bitstring must be 1 bit long, not {0} bits."
            raise InterpretError(msg, self.length)
        return self[0]

    def _readbool(self):
        b = self[self._pos]
        self._pos += 1
        return b

    def _setbin_safe(self, binstring):
        """Reset the bitstring to the value given in binstring."""
        binstring = tidy_input_string(binstring)
        # remove any 0b if present
        binstring = binstring.replace('0b', '')
        self._setbin_unsafe(binstring)
        
    def _setbin_unsafe(self, binstring):
        """Same as _setbin_safe, but input isn't sanity checked. binstring mustn't start with '0b'."""
        length = len(binstring)
        # pad with zeros up to byte boundary if needed
        boundary = ((length + 7) // 8) * 8
        padded_binstring = binstring + '0'*(boundary - length) \
                           if len(binstring) < boundary else binstring
        try:
            bytelist = [int(padded_binstring[x:x + 8], 2)
                        for x in xrange(0, len(padded_binstring), 8)]
        except ValueError:
            raise CreationError("Invalid character in bin initialiser {0}.", binstring)
        self._setbytes_unsafe(bytearray(bytelist), length, 0)

    def _readbin(self, length, start):
        """Read bits and interpret as a binary string."""
        if length == 0:
            return ''
        # Use lookup table to convert each byte to string of 8 bits.
        startbyte, startoffset = divmod(start + self._offset, 8)
        endbyte = (start + self._offset + length - 1) // 8
        c = [BYTE_TO_BITS[x] for x in bytearray(self._datastore.getbyteslice(startbyte,endbyte + 1))]
        return '0b' + ''.join(c)[startoffset:startoffset + length]

    def _getbin(self):
        """Return interpretation as a binary string."""
        return self._readbin(self.len, 0)

    def _setoct(self, octstring):
        """Reset the bitstring to have the value given in octstring."""
        octstring = tidy_input_string(octstring)
        # remove any 0o if present
        octstring = octstring.replace('0o', '')
        binlist = []
        for i in octstring:
            try:
                if not 0 <= int(i) < 8:
                    raise ValueError
                binlist.append(OCT_TO_BITS[int(i)])
            except ValueError:
                raise CreationError("Invalid symbol '{0}' in oct initialiser.", i)
        self._setbin_unsafe(''.join(binlist))

    def _readoct(self, length, start):
        """Read bits and interpret as an octal string."""
        if length % 3 != 0:
            raise InterpretError("Cannot convert to octal unambiguously - "
                                 "not multiple of 3 bits.")
        if length == 0:
            return ''
        beginning = '0o'
        # Get main octal bit by converting from int.
        # Strip starting 0 or 0o depending on Python version.
        end = oct(self._readuint(length, start))[LEADING_OCT_CHARS:]
        if end.endswith('L'):
            end = end[:-1]
        middle = '0'*(length // 3 - len(end))
        return ''.join((beginning, middle, end))

    def _getoct(self):
        """Return interpretation as an octal string."""
        return self._readoct(self.len, 0)

    def _sethex(self, hexstring):
        """Reset the bitstring to have the value given in hexstring."""
        hexstring = tidy_input_string(hexstring)
        # remove any 0x if present
        hexstring = hexstring.replace('0x', '')
        length = len(hexstring)
        if length % 2:
            hexstring += '0'
        try:
            data = binascii.unhexlify(hexstring)
        # Python 2.6 raises TypeError, Python 3 raises binascii.Error.
        except (TypeError, binascii.Error):
            raise CreationError("Invalid symbol in hex initialiser.")
        self._setbytes_unsafe(data, length*4, 0)

    def _readhex(self, length, start):
        """Read bits and interpret as a hex string."""
        if length % 4 != 0:
            raise InterpretError("Cannot convert to hex unambiguously - "
                                 "not multiple of 4 bits.")
        if length == 0:
            return ''
        # This monstrosity is the only thing I could get to work for both 2.6 and 3.1.
        # TODO: Optimize
        s = str(binascii.hexlify(self[start:start+length].tobytes()).decode('utf-8'))
        if (length // 4) % 2:
            # We've got one nibble too many, so cut it off.
            return '0x' + s[:-1]
        else:
            return '0x' + s

    def _gethex(self):
        """Return the hexadecimal representation as a string prefixed with '0x'.

        Raises an InterpretError if the bitstring's length is not a multiple of 4.

        """
        return self._readhex(self.len, 0)

    def _setbytepos(self, bytepos):
        """Move to absolute byte-aligned position in stream."""
        self._setbitpos(bytepos*8)

    def _getbytepos(self):
        """Return the current position in the stream in bytes. Must be byte aligned."""
        if self._pos % 8 != 0:
            raise ByteAlignError("Not byte aligned in _getbytepos().")
        return self._pos // 8

    def _setbitpos(self, pos):
        """Move to absolute postion bit in bitstream."""
        if pos < 0:
            raise ValueError("Bit position cannot be negative.")
        if pos > self.len:
            raise ValueError("Cannot seek past the end of the data.")
        self._pos = pos

    def _getbitpos(self):
        """Return the current position in the stream in bits."""
        return self._pos

    def _getoffset(self):
        return self._datastore.offset

    def _getlength(self):
        """Return the length of the bitstring in bits."""
        return self._datastore.bitlength

    def _ensureinmemory(self):
        """Ensure the data is held in memory, not in a file."""
        assert self._filebased == False
        self._setbytes_unsafe(self._datastore.getbyteslice(0, self._datastore.bytelength), self.len,
                              self._offset)

    @classmethod
    def _converttobitstring(cls, bs, offset=0, cache={}):
        """Convert bs to a bitstring and return it.

        offset gives the suggested bit offset of first significant
        bit, to optimise append etc.
        """
        try:
            return cache[(bs, offset)]
        except KeyError:
            if isinstance(bs, cBits):
                return bs
            if isinstance(bs, basestring):
                b = cBits()
                try:
                    _, tokens = tokenparser(bs)
                except ValueError:  # TODO: was 'as e'
                    raise CreationError # TODO: was (*e.args)
                for token in tokens:
                    b._append(cBits._init_with_token(*token))
                b._datastore.setoffset(offset)
                assert b._assertsanity()
                cache[(bs, offset)] = b
                return b
        except TypeError:
            # Unhashable type
            pass
        return cls(bs)

    def _copy(self):
        """Create and return a new copy of the Bits (always in memory)."""
        s_copy = self.__class__()
        # The copy doesn't keep the same bit position.
        s_copy._pos = 0
        s_copy._setbytes_unsafe(self._datastore.getbyteslice(0, self._datastore.bytelength),
                                self.len, self._offset)
        return s_copy

    def _slice(self, start, end=None):
        """Used internally to get a slice, without error checking."""
        if end is None:
            # Single bit, return True or False
            return self._datastore.getbit(start)
        return self._readbits(end - start, start)

    def _readtoken(self, name, length):
        """Reads a token from the bitstring and returns the result."""
        if length is not None and int(length) > self.length - self._pos:
            raise ReadError("Reading off the end of the data.")
        try:
            val = name_to_read[name](self, length, self._pos)
            self._pos += length
            return val
        except KeyError:
            raise ValueError("Can't parse token {0}:{1}".format(name, length))
        except TypeError:
            # This is for the 'ue' and 'se' tokens. They will advance the pos.
            val = name_to_read[name](self)
            return val

    def _append(self, bs):
        """Append a bitstring to the current bitstring."""
        try:
            self._datastore.appendarray(bs._datastore)
        except NotImplementedError:
            self._datastore.appendarray(bs._datastore)

    def _prepend(self, bs):
        """Prepend a bitstring to the current bitstring."""
        try:
            self._datastore.prependarray(bs._datastore)
        except NotImplementedError:
            self._datastore.prependarray(bs._datastore)
        self._pos += bs.len

    def _truncatestart(self, bits):
        """Truncate bits from the start of the bitstring."""
        assert 0 <= bits <= self.len
        if bits == 0:
            return
        if bits == self.len:
            self._clear()
            return
        bytepos, offset = divmod(self._offset + bits, 8)
        self._pos = max(0, self._pos - bits)
        self._setbytes_unsafe(self._datastore.getbyteslice(bytepos, self._datastore.bytelength), self.len - bits, offset)
        assert self._assertsanity()

    def _truncateend(self, bits):
        """Truncate bits from the end of the bitstring."""
        assert 0 <= bits <= self.len
        if bits == 0:
            return
        if bits == self.len:
            self._clear()
            return
        newlength_in_bytes = (self._offset + self.len - bits + 7) // 8
        # Ensure that the position is still valid
        self._pos = max(0, min(self._pos, self.len - bits))
        self._setbytes_unsafe(self._datastore.getbyteslice(0, newlength_in_bytes), self.len - bits,
                       self._offset)
        assert self._assertsanity()

    def _insert(self, bs, pos):
        """Insert bs at pos."""
        assert 0 <= pos <= self.len
        if pos > self.len // 2:
            # Inserting nearer end, so cut off end.
            end = self._slice(pos, self.len)
            self._truncateend(self.len - pos)
            self._append(bs)
            self._append(end)
        else:
            # Inserting nearer start, so cut off start.
            start = self._slice(0, pos)
            self._truncatestart(pos)
            self._prepend(bs)
            self._prepend(start)
        self._pos = pos + bs.len
        assert self._assertsanity()

    def _overwrite(self, bs, pos):
        """Overwrite with bs at pos."""
        assert 0 <= pos < self.len
        bitposafter = pos + bs.len
        if bs is self:
            # Just overwriting with self, so do nothing.
            assert pos == 0
            return
        firstbytepos = (self._offset + pos) // 8
        lastbytepos = (self._offset + pos + bs.len - 1) // 8
        bytepos, bitoffset = divmod(self._offset + pos, 8)
        if firstbytepos == lastbytepos:
            mask = ((1 << bs.len) - 1) << (8 - bs.len - bitoffset)
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) & (~mask))
            bs._datastore.setoffset(bitoffset)
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) | (bs._datastore.getbyte(0) & mask))
        else:
            # Do first byte
            mask = (1 << (8 - bitoffset)) - 1
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) & (~mask))
            bs._datastore.setoffset(bitoffset)
            self._datastore.setbyte(bytepos, self._datastore.getbyte(bytepos) | (bs._datastore.getbyte(0) & mask))
            # Now do all the full bytes
            self._datastore.setbyteslice(firstbytepos + 1, lastbytepos, bs._datastore.getbyteslice(1, lastbytepos - firstbytepos))
            # and finally the last byte
            bitsleft = (self._offset + pos + bs.len) % 8
            if bitsleft == 0:
                bitsleft = 8
            mask = (1 << (8 - bitsleft)) - 1
            self._datastore.setbyte(lastbytepos, self._datastore.getbyte(lastbytepos) & mask)
            self._datastore.setbyte(lastbytepos, self._datastore.getbyte(lastbytepos) | (bs._datastore.getbyte(bs._datastore.bytelength - 1) & ~mask))
        self._pos = bitposafter
        assert self._assertsanity()

    def _delete(self, bits, pos):
        """Delete bits at pos."""
        assert 0 <= pos <= self.len
        assert pos + bits <= self.len
        if pos == 0:
            # Cutting bits off at the start.
            self._truncatestart(bits)
            return
        if pos + bits == self.len:
            # Cutting bits off at the end.
            self._truncateend(bits)
            return
        if pos > self.len - pos - bits:
            # More bits before cut point than after it, so do bit shifting
            # on the final bits.
            end = self._slice(pos + bits, self.len)
            assert self.len - pos > 0
            self._truncateend(self.len - pos)
            self._pos = self.len
            self._append(end)
            return
        # More bits after the cut point than before it.
        start = self._slice(0, pos)
        self._truncatestart(pos + bits)
        self._pos = 0
        self._prepend(start)
        return

    def _reversebytes(self, start, end):
        """Reverse bytes in-place."""
        # Make the start occur on a byte boundary
        # TODO: We could be cleverer here to avoid changing the offset.
        newoffset = 8 - (start % 8)
        if newoffset == 8:
            newoffset = 0
        self._datastore.setoffset(newoffset)
        # Now just reverse the byte data
        toreverse = bytearray(self._datastore.getbyteslice((newoffset + start)//8, (newoffset + end)//8))
        toreverse.reverse()
        self._datastore.setbyteslice((newoffset + start)//8, (newoffset + end)//8, toreverse)

    def _set(self, pos):
        """Set bit at pos to 1."""
        assert 0 <= pos < self.len
        self._datastore.setbit(pos)

    def _unset(self, pos):
        """Set bit at pos to 0."""
        assert 0 <= pos < self.len
        self._datastore.unsetbit(pos)
        
    def _invert(self, pos):
        """Flip bit at pos 1<->0."""
        assert 0 <= pos < self.len
        self._datastore.invertbit(pos)

    def _invert_all(self):
        """Invert every bit."""
        set = self._datastore.setbyte
        get = self._datastore.getbyte
        for p in xrange(self._datastore.bytelength):
            set(p, 256 + ~get(p))
            
    def _ilshift(self, n):
        """Shift bits by n to the left in place. Return self."""
        assert 0 < n <= self.len
        self._append(cBits(n))
        self._truncatestart(n)
        return self

    def _irshift(self, n):
        """Shift bits by n to the right in place. Return self."""
        assert 0 < n <= self.len
        self._prepend(cBits(n))
        self._truncateend(n)       
        return self

    def _imul(self, n):
        """Concatenate n copies of self in place. Return self."""
        assert n >= 0
        if n == 0:
            self._clear()
            return self
        m = 1
        old_len = self.len
        while m*2 < n:
            self._append(self)
            m *= 2
        self._append(self[0:(n-m)*old_len])
        return self

    def _inplace_logical_helper(self, bs, f):
        """Helper function containing most of the __ior__, __iand__, __ixor__ code."""
        # Give the two BitStrings the same offset
        if bs._offset != self._offset:
            if self._offset == 0:
                bs._datastore.setoffset(0)
            else:
                self._datastore.setoffset(bs._offset)
        assert self._offset == bs._offset
        a = self._datastore
        b = bs._datastore
        assert a.bytelength == b.bytelength
        for i in xrange(a.bytelength):
            a.setbyte(i, f(a.getbyte(i), b.getbyte(i)))
        return self

    def _ior(self, bs):
        return self._inplace_logical_helper(bs, operator.ior)

    def _iand(self, bs):
        return self._inplace_logical_helper(bs, operator.iand)

    def _ixor(self, bs):
        return self._inplace_logical_helper(bs, operator.xor)

    def _readbits(self, length, start):
        """Read some bits from the bitstring and return newly constructed bitstring."""
        if length is None:
            return self[start] # TODO: Don't range check
        startbyte, newoffset = divmod(start + self._offset, 8)
        endbyte = (start + self._offset + length - 1) // 8
        bs = self.__class__(bytes=self._datastore.getbyteslice(startbyte, endbyte + 1),
                            length=length, offset=newoffset)
        return bs

    def _validate_slice(self, start, end):
        """Validate start and end and return them as positive bit positions."""
        if start is None:
            start = 0
        elif start < 0:
            start += self.len
        if end is None:
            end = self.len
        elif end < 0:
            end += self.len
        if not 0 <= end <= self.len:
            raise ValueError("end is not a valid position in the bitstring.")
        if not 0 <= start <= self.len:
            raise ValueError("start is not a valid position in the bitstring.")
        if end < start:
            raise ValueError("end must not be less than start.")
        return start, end

    def unpack(self, fmt, **kwargs):
        """Interpret the whole bitstring using fmt and return list.

        fmt - One or more strings with comma separated tokens describing
              how to interpret the bits in the bitstring.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        Raises ValueError if the format is not understood. If not enough bits
        are available then all bits to the end of the bitstring will be used.

        See the docstring for 'read' for token examples.

        """
        bitposbefore = self._pos
        self._pos = 0
        return_values = self.readlist(fmt, **kwargs)
        self._pos = bitposbefore
        return return_values

    def read(self, fmt):
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
                        'bits:5'    : 5 bits as a bitstring
                        'bytes:10'  : 10 bytes as a bytes object
                        'bool'      : 1 bit as a bool

        fmt may also be an integer, which will be treated like the 'bits' token.

        The position in the bitstring is advanced to after the read items.

        Raises ReadError if not enough bits are available.
        Raises ValueError if the format is not understood.

        """
        if isinstance(fmt, (int, long)):
            if fmt < 0:
                raise ValueError("Cannot read negative amount.")
            if fmt > self.len - self._pos:
                raise ReadError("Cannot read {0} bits, only {1} available.",
                                fmt, self.len - self._pos)
            bs = self._readbits(fmt, self._pos)
            self._pos += fmt
            return bs
        p = self._pos
        _, token = tokenparser(fmt)
        if len(token) != 1:
            self._pos = p
            raise ValueError("Format string should be a single token, not {0} "
                             "tokens - use readlist() instead.".format(len(token)))
        name, length, _ = token[0]
        if length is None:
            length = self.len - self.pos
        return self._readtoken(name, length)

    def readlist(self, fmt, **kwargs):
        """Interpret next bits according to format string(s) and return list.

        fmt -- A single string or list of strings with comma separated tokens
               describing how to interpret the next bits in the bitstring. Items
               can also be integers, for reading new bitstring of the given length.
        kwargs -- A dictionary or keyword-value pairs - the keywords used in the
                  format string will be replaced with their given value.

        The position in the bitstring is advanced to after the read items.

        Raises ReadError is not enough bits are available.
        Raises ValueError if the format is not understood.

        See the docstring for 'read' for token examples.

        >>> h, b1, b2 = s.readlist('hex:20, bin:5, bin:3')
        >>> i, bs1, bs2 = s.readlist(['uint:12', 10, 10])

        """
        tokens = []
        stretchy_token = None
        if isinstance(fmt, basestring):
            fmt = [fmt]
        # Not very optimal this, but replace integers with 'bits' tokens
        # TODO: optimise
        for i, f in enumerate(fmt):
            if isinstance(f, (int, long)):
                fmt[i] = "bits:{0}".format(f)
        for f_item in fmt:
            stretchy, tkns = tokenparser(f_item, tuple(sorted(kwargs.keys())))
            if stretchy:
                if stretchy_token:
                    raise Error("It's not possible to have more than one 'filler' token.")
                stretchy_token = stretchy
            tokens.extend(tkns)
        if not stretchy_token:
            lst = []
            for name, length, _ in tokens:
                if length in kwargs:
                    length = kwargs[length]
                if name in kwargs and length is None:
                    # Using default 'uint' - the name is really the length.
                    lst.append(self._readtoken('uint', kwargs[name]))
                    continue
                lst.append(self._readtoken(name, length))
            return lst
        stretchy_token = False
        bits_after_stretchy_token = 0
        for token in tokens:
            name, length, _ = token
            if length in kwargs:
                length = kwargs[length]
            if name in kwargs and length is None:
                # Default 'uint'.
                length = kwargs[name]
            if stretchy_token:
                if name in ('se', 'ue'):
                    raise Error("It's not possible to parse a variable"
                                "length token after a 'filler' token.")
                else:
                    bits_after_stretchy_token += length
            if length is None and name not in ('se', 'ue'):
                if stretchy_token:
                    raise Error("It's not possible to have more than "
                                "one 'filler' token.")
                stretchy_token = token
        bits_left = self.len - self._pos
        return_values = []
        for token in tokens:
            name, length, _ = token
            if token is stretchy_token:
                # Set length to the remaining bits
                length = max(bits_left - bits_after_stretchy_token, 0)
            if length in kwargs:
                length = kwargs[length]
            if name in kwargs and length is None:
                # Default 'uint'
                length = kwargs[name]
            if length is not None:
                bits_left -= length
            return_values.append(self._readtoken(name, length))
        return return_values

    def peek(self, fmt):
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

    def peeklist(self, fmt, **kwargs):
        """Interpret next bits according to format string(s) and return list.

        fmt -- One or more strings with comma separated tokens describing
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

    def find(self, bs, start=None, end=None, bytealigned=False):
        """Find first occurence of substring bs.
        
        Returns a single item tuple with the bit position if found, or an
        empty tuple if not found. The bit position (pos property) will
        also be set to the start of the substring if it is found.
        
        bs -- The bitstring to find.
        start -- The bit position to start the search. Defaults to 0.
        end -- The bit position one past the last bit to search.
               Defaults to self.len.
        bytealigned -- If True the bitstring will only be
                       found on byte boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > self.len or
        if end < start.
        
        >>> Bits('0xc3e').find('0b1111')
        (6,)

        """
        bs = self._converttobitstring(bs)
        if not bs.len:
            raise ValueError("Cannot find an empty bitstring.")
        start, end = self._validate_slice(start, end)
        # If everything's byte aligned (and whole-byte) use the quick algorithm.
        if bytealigned and len(bs) % 8 == 0 and self._datastore.offset == 0:
            # Extract data bytes from bitstring to be found.
            d = bs.bytes
            oldpos = self._pos
            self._pos = start
            self.bytealign()
            bytepos = self._pos // 8
            found = False
            p = bytepos
            finalpos = end // 8
            increment = max(1024, len(d)*10)
            buffersize = increment + len(d)
            while p < finalpos:
                # Read in file or from memory in overlapping chunks and search the chunks.
                buf = bytearray(self._datastore.getbyteslice(p, min(p + buffersize, finalpos)))
                pos = buf.find(d)
                if pos != -1:
                    found = True
                    p += pos
                    break
                p += increment
            if not found:
                self._pos = oldpos
                return ()
            self._pos = p*8
            return (p*8,)
        else:
            oldpos = self._pos
            targetbin = bs._getbin()[2:]
            found = False
            p = start
            # We grab overlapping chunks of the binary representation and
            # do an ordinary string search within that.
            increment = max(16384, bs.len*10)
            buffersize = increment + bs.len
            while p < end:
                buf = self[p:min(p+buffersize, end)]._getbin()[2:]
                pos = buf.find(targetbin)
                if pos != -1:
                    # if bytealigned then we only accept byte aligned positions.
                    if not bytealigned or (p + pos) % 8 == 0:
                        found = True
                        p += pos
                        break
                    if bytealigned:
                        # Advance to just beyond the non-byte-aligned match and try again...
                        p += pos + 1
                        continue
                p += increment
            if not found:
                self._pos = oldpos
                return ()
            self._pos = p
            return (p,)

    def rfind(self, bs, start=None, end=None, bytealigned=False):
        """Find final occurence of substring bs.
        
        Returns a single item tuple with the bit position if found, or an
        empty tuple if not found. The bit position (pos property) will
        also be set to the start of the substring if it is found.

        bs -- The bitstring to find.
        start -- The bit position to end the reverse search. Defaults to 0.
        end -- The bit position one past the first bit to reverse search.
               Defaults to self.len.
        bytealigned -- If True the bitstring will only be found on byte
                       boundaries.

        Raises ValueError if bs is empty, if start < 0, if end > self.len or
        if end < start.

        """
        bs = self._converttobitstring(bs)
        start, end = self._validate_slice(start, end)
        if not bs.len:
            raise ValueError("Cannot find an empty bitstring.")
        # Search chunks starting near the end and then moving back
        # until we find bs.
        increment = max(8192, bs.len*80)
        buffersize = min(increment + bs.len, end - start)
        pos = max(start, end - buffersize)
        while(True):
            found = list(self.findall(bs, start=pos, end=pos + buffersize,
                                      bytealigned=bytealigned))
            if not found:
                if pos == start:
                    return ()
                pos = max(start, pos - increment)
                continue
            self._pos = found[-1]
            return (found[-1],)

    def bytealign(self):
        """Align to next byte and return number of skipped bits.

        Raises ValueError if the end of the bitstring is reached before
        aligning to the next byte.

        """
        skipped = (8 - (self._pos % 8)) % 8
        self.pos += self._offset + skipped
        assert self._assertsanity()
        return skipped

    def join(self, sequence):
        """Return concatenation of bitstrings joined by self.

        sequence -- A sequence of bitstrings.

        """
        s = self.__class__()
        i = iter(sequence)
        try:
            s._append(self._converttobitstring(next(i)))
            while(True):
                n = next(i)
                s._append(self)
                s._append(self._converttobitstring(n))
        except StopIteration:
            pass
        return s

    def tobytes(self):
        """Return the bitstring as bytes, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        if self._filebased:
            if self._offset == 0:
                d = self._datastore.rawbytes
            else:
                s = cBits(bytes=self._datastore.rawbytes, offset=self._offset)
                s._datastore.setoffset(0)
                d = self._datastore.rawbytes
        else:
            self._datastore.setoffset(0)
            d = self._datastore.rawbytes
        # Need to ensure that unused bits at end are set to zero
        unusedbits = 8 - self.len % 8
        if unusedbits != 8:
            # This is horrible. Shouldn't have to copy the string here!
            t1 = d[:self._datastore.bytelength - 1]
            t1.append(d[self._datastore.bytelength - 1] & (255 << unusedbits))
            return bytes(t1)
        return bytes(d)

    def tofile(self, f):
        """Write the bitstring to a file object, padding with zero bits if needed.

        Up to seven zero bits will be added at the end to byte align.

        """
        # If the bitstring is file based then we don't want to read it all
        # in to memory.
        chunksize = 1024*1024 # 1 MB chunks
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
            if bits_in_final_byte == 0:
                bits_in_final_byte = 8
            f.write(self[-bits_in_final_byte:].tobytes())
        else:
            # Really quite inefficient...
            a = 0
            p = self[a:a + chunksize*8]
            while p.len == chunksize*8:
                f.write(p.bytes)
                a += chunksize*8
                p = self[a:a + chunksize*8]
            f.write(p.tobytes())

    def startswith(self, prefix, start=None, end=None):
        """Return whether the current bitstring starts with prefix.

        prefix -- The bitstring to search for.
        start -- The bit position to start from. Defaults to 0.
        end -- The bit position to end at. Defaults to self.len.

        """
        prefix = self._converttobitstring(prefix)
        start, end = self._validate_slice(start, end)
        if end < start + prefix.len:
            return False
        end = start + prefix.len
        return self[start:end] == prefix

    def endswith(self, suffix, start=None, end=None):
        """Return whether the current bitstring ends with suffix.

        suffix -- The bitstring to search for.
        start -- The bit position to start from. Defaults to 0.
        end -- The bit position to end at. Defaults to self.len.

        """
        suffix = self._converttobitstring(suffix)
        start, end = self._validate_slice(start, end)
        if start + suffix.len > end:
            return False
        start = end - suffix.len
        return self[start:end] == suffix

    def all(self, value, pos=None):
        """Return True if one or many bits are all set to value.

        value -- If value is True then checks for bits set to 1, otherwise
                 checks for bits set to 0.
        pos -- An iterable of bit positions. Negative numbers are treated in
               the same way as slice indices. Defaults to the whole bitstring.

        """
        value = bool(value)
        length = self.len
        if pos is None:
            pos = xrange(self.len)
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError("Bit position {0} out of range.".format(p))
            if not self._datastore.getbit(p) is value:
                return False
        return True

    def any(self, value, pos=None):
        """Return True if any of one or many bits are set to value.

        value -- If value is True then checks for bits set to 1, otherwise
                 checks for bits set to 0.
        pos -- An iterable of bit positions. Negative numbers are treated in
               the same way as slice indices. Defaults to the whole bitstring.

        """
        value = bool(value)
        length = self.len
        if pos is None:
            pos = xrange(self.len)
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError("Bit position {0} out of range.".format(p))
            if self._datastore.getbit(p) is value:
                return True
        return False
    
    def count(self, value):
        """Return count of total number of either zero or one bits.
        
        value -- If True then bits set to 1 are counted, otherwise bits set
                 to 0 are counted.
                 
        >>> Bits('0xef').count(1)
        7
        
        """
        if not self.len:
            return 0
        
        count = bin(self._getuint()).count('1')
        return count if value else self.len - count
        
        # count the number of 1s (from which it's easy to work out the 0s).
        # Don't count the final byte yet.
        # TODO: Replace xrange (could fail with 32-bit Python 2.x).
        count = sum([BIT_COUNT[self._datastore.getbyte(i)] for i in xrange(self._datastore.bytelength - 1)])
        # adjust for bits at start that aren't part of the bitstring
        if self._offset:
            count -= BIT_COUNT[self._datastore.getbyte(0) >> (8 - self._offset)]
        # and count the last 1 - 8 bits at the end.
        endbits = self._datastore.bytelength*8 - (self._offset + self.len)
        count += BIT_COUNT[self._datastore.getbyte(self._datastore.bytelength - 1) >> endbits]
        return count if value else self.len - count

    # Create native-endian functions as aliases depending on the byteorder
    if byteorder == 'little':
        _setfloatne = _setfloatle
        _readfloatne = _readfloatle
        _getfloatne = _getfloatle
        _setuintne = _setuintle
        _readuintne = _readuintle
        _getuintne = _getuintle
        _setintne = _setintle
        _readintne = _readintle
        _getintne = _getintle
    else:
        _setfloatne = _setfloat
        _readfloatne = _readfloat
        _getfloatne = _getfloat
        _setuintne = _setuintbe
        _readuintne = _readuintbe
        _getuintne = _getuintbe
        _setintne = _setintbe
        _readintne = _readintbe
        _getintne = _getintbe

    _offset = property(_getoffset)

    len    = property(_getlength,
                      doc="""The length of the bitstring in bits. Read only.
                      """)
    length = property(_getlength,
                      doc="""The length of the bitstring in bits. Read only.
                      """)
    bool   = property(_getbool,
                      doc="""The bitstring as a bool (True or False)."""
                      )
    hex    = property(_gethex,
                      doc="""The bitstring as a hexadecimal string. Read only.

                      Will be prefixed with '0x' and including any leading zeros.

                      """)
    bin    = property(_getbin,
                      doc="""The bitstring as a binary string. Read only.

                      Will be prefixed with '0b' and including any leading zeros.

                      """)
    oct    = property(_getoct,
                      doc="""The bitstring as an octal string. Read only.

                      Will be prefixed with '0o' and including any leading zeros.

                      """)
    bytes  = property(_getbytes,
                      doc="""The bitstring as a bytes object. Read only.
                      """)
    int    = property(_getint,
                      doc="""The bitstring as a two's complement signed int. Read only.
                      """)
    uint   = property(_getuint,
                      doc="""The bitstring as a two's complement unsigned int. Read only.
                      """)
    float  = property(_getfloat,
                      doc="""The bitstring as a floating point number. Read only.
                      """)
    intbe  = property(_getintbe,
                      doc="""The bitstring as a two's complement big-endian signed int. Read only.
                      """)
    uintbe = property(_getuintbe,
                      doc="""The bitstring as a two's complement big-endian unsigned int. Read only.
                      """)
    floatbe= property(_getfloat,
                      doc="""The bitstring as a big-endian floating point number. Read only.
                      """)
    intle  = property(_getintle,
                      doc="""The bitstring as a two's complement little-endian signed int. Read only.
                      """)
    uintle = property(_getuintle,
                      doc="""The bitstring as a two's complement little-endian unsigned int. Read only.
                      """)
    floatle= property(_getfloatle,
                      doc="""The bitstring as a little-endian floating point number. Read only.
                      """)
    intne  = property(_getintne,
                      doc="""The bitstring as a two's complement native-endian signed int. Read only.
                      """)
    uintne = property(_getuintne,
                      doc="""The bitstring as a two's complement native-endian unsigned int. Read only.
                      """)
    floatne= property(_getfloatne,
                      doc="""The bitstring as a native-endian floating point number. Read only.
                      """)
    ue     = property(_getue,
                      doc="""The bitstring as an unsigned exponential-Golomb code. Read only.
                      """)
    se     = property(_getse,
                      doc="""The bitstring as a signed exponential-Golomb code. Read only.
                      """)
    pos    = property(_getbitpos, _setbitpos,
                      doc="""The position in the bitstring in bits. Read and write.
                      """)
    bitpos = property(_getbitpos, _setbitpos,
                      doc="""The position in the bitstring in bits. Read and write.
                      """)
    bytepos= property(_getbytepos, _setbytepos,
                      doc="""The position in the bitstring in bytes. Read and write.
                      """)

# Dictionary that maps token names to the function that reads them.
name_to_read = {'uint':    cBits._readuint,
                'uintle':  cBits._readuintle,
                'uintbe':  cBits._readuintbe,
                'uintne':  cBits._readuintne,
                'int':     cBits._readint,
                'intle':   cBits._readintle,
                'intbe':   cBits._readintbe,
                'intne':   cBits._readintne,
                'float':   cBits._readfloat,
                'floatbe': cBits._readfloat, # floatbe is a synonym for float
                'floatle': cBits._readfloatle,
                'floatne': cBits._readfloatne,
                'hex':     cBits._readhex,
                'oct':     cBits._readoct,
                'bin':     cBits._readbin,
                'bits':    cBits._readbits,
                'bytes':   cBits._readbytes,
                'ue':      cBits._readue,
                'se':      cBits._readse,
                'bool':    cBits._readbool,
                }

# Dictionaries for mapping init keywords with init functions.
init_with_length_and_offset = {'bytes':    cBits._setbytes_safe,
                               'filename': cBits._setfile,
                              }

init_with_length_only = {'uint':    cBits._setuint,
                         'int':     cBits._setint,
                         'float':   cBits._setfloat,
                         'uintbe':  cBits._setuintbe,
                         'intbe':   cBits._setintbe,
                         'floatbe': cBits._setfloat,
                         'uintle':  cBits._setuintle,
                         'intle':   cBits._setintle,
                         'floatle': cBits._setfloatle,
                         'uintne':  cBits._setuintne,
                         'intne':   cBits._setintne,
                         'floatne': cBits._setfloatne,
                         }

init_without_length_or_offset = {'bin': cBits._setbin_safe,
                                 'hex': cBits._sethex,
                                 'oct': cBits._setoct,
                                 'ue':  cBits._setue,
                                 'se':  cBits._setse,
                                 'bool':cBits._setbool,
                                 }

One = cBits(bytes=b'\x80', length=1)
Zero = cBits(bytes=b'\x00', length=1)