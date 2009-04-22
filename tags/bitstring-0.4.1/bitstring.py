#!/usr/bin/env python
"""
Module for bit-wise data manipulation.
http://python-bitstring.googlecode.com
"""

__licence__ = """
The MIT License

Copyright (c) 2006-2009 Scott Griffiths (scott@griffiths.name)

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

__version__ = "0.4.1"

import array
import copy
import string
import os
import struct

# Maximum number of digits to use in __str__ and __repr__.
_maxchars = 250

os.SEEK_SET = 0 # For backward compatibility with Python 2.4

def _single_byte_from_hex_string(h):
    """Return a byte equal to the input hex string."""
    try:
        i = int(h, 16)
    except ValueError:
        raise ValueError("Can't convert hex string to a single byte")
    if len(h) > 2:
        raise ValueError("Hex string can't be more than one byte in size")
    if len(h) == 2:
        return struct.pack('B', i)  
    elif len(h) == 1:
        return struct.pack('B', i<<4)

def _single_byte_from_hex_string_unsafe(h):
    """Return a byte equal to the input 2 character hex string. No parameter checking done."""
    return struct.pack('B', int(h, 16))

def _hex_string_from_single_byte(b):
    """Return a two character hex string from a single byte value."""
    v = b
    if v > 15:
        return hex(v)[2:]
    elif v > 0:
        return '0' + hex(v)[2:]
    else:
        return '00'

def _tidyupinputstring(s):
    """Return string made lowercase and with all whitespace removed."""
    return ''.join(s.split()).lower()

# Not pretty, but a byte to bitstring lookup really speeds things up.
_byte2bits = ['00000000', '00000001', '00000010', '00000011', '00000100', '00000101', '00000110', '00000111',
              '00001000', '00001001', '00001010', '00001011', '00001100', '00001101', '00001110', '00001111',
              '00010000', '00010001', '00010010', '00010011', '00010100', '00010101', '00010110', '00010111',
              '00011000', '00011001', '00011010', '00011011', '00011100', '00011101', '00011110', '00011111',
              '00100000', '00100001', '00100010', '00100011', '00100100', '00100101', '00100110', '00100111',
              '00101000', '00101001', '00101010', '00101011', '00101100', '00101101', '00101110', '00101111',
              '00110000', '00110001', '00110010', '00110011', '00110100', '00110101', '00110110', '00110111',
              '00111000', '00111001', '00111010', '00111011', '00111100', '00111101', '00111110', '00111111',
              '01000000', '01000001', '01000010', '01000011', '01000100', '01000101', '01000110', '01000111',
              '01001000', '01001001', '01001010', '01001011', '01001100', '01001101', '01001110', '01001111',
              '01010000', '01010001', '01010010', '01010011', '01010100', '01010101', '01010110', '01010111',
              '01011000', '01011001', '01011010', '01011011', '01011100', '01011101', '01011110', '01011111',
              '01100000', '01100001', '01100010', '01100011', '01100100', '01100101', '01100110', '01100111',
              '01101000', '01101001', '01101010', '01101011', '01101100', '01101101', '01101110', '01101111',
              '01110000', '01110001', '01110010', '01110011', '01110100', '01110101', '01110110', '01110111',
              '01111000', '01111001', '01111010', '01111011', '01111100', '01111101', '01111110', '01111111',
              '10000000', '10000001', '10000010', '10000011', '10000100', '10000101', '10000110', '10000111',
              '10001000', '10001001', '10001010', '10001011', '10001100', '10001101', '10001110', '10001111',
              '10010000', '10010001', '10010010', '10010011', '10010100', '10010101', '10010110', '10010111',
              '10011000', '10011001', '10011010', '10011011', '10011100', '10011101', '10011110', '10011111',
              '10100000', '10100001', '10100010', '10100011', '10100100', '10100101', '10100110', '10100111',
              '10101000', '10101001', '10101010', '10101011', '10101100', '10101101', '10101110', '10101111',
              '10110000', '10110001', '10110010', '10110011', '10110100', '10110101', '10110110', '10110111',
              '10111000', '10111001', '10111010', '10111011', '10111100', '10111101', '10111110', '10111111',
              '11000000', '11000001', '11000010', '11000011', '11000100', '11000101', '11000110', '11000111',
              '11001000', '11001001', '11001010', '11001011', '11001100', '11001101', '11001110', '11001111',
              '11010000', '11010001', '11010010', '11010011', '11010100', '11010101', '11010110', '11010111',
              '11011000', '11011001', '11011010', '11011011', '11011100', '11011101', '11011110', '11011111',
              '11100000', '11100001', '11100010', '11100011', '11100100', '11100101', '11100110', '11100111',
              '11101000', '11101001', '11101010', '11101011', '11101100', '11101101', '11101110', '11101111',
              '11110000', '11110001', '11110010', '11110011', '11110100', '11110101', '11110110', '11110111',
              '11111000', '11111001', '11111010', '11111011', '11111100', '11111101', '11111110', '11111111']


class BitStringError(Exception):
    """For errors in the bitstring module."""

class _FileArray(object):
    """A class that mimics the array.array type but gets data from a file object."""
    
    def __init__(self, filename, lengthinbits, offset, byteoffset):
        filelength = os.path.getsize(filename)
        self.source = open(filename, 'rb')
        if byteoffset is None:
            byteoffset = 0
        if lengthinbits is None:
            length = filelength - byteoffset
        else:
            length = (lengthinbits + offset + 7)//8
        if length > filelength - byteoffset:
            raise ValueError("File is not long enough for specified BitString length and offset.")
        self._length = length # length in bytes
        self.byteoffset = byteoffset
    
    def __len__(self):
        # This fails for > 4GB, so better to explictly disallow it!
        raise NotImplementedError

    def __copy__(self):
        raise BitStringError("_FileArray.copy() not allowed.")
    
    def __getitem__(self, key):
        try:
            key.start
        except AttributeError:
            # single element
            key += self.byteoffset
            if key >= self._length or key < -self._length:
                raise IndexError
            if key < 0:
                key = self._length + key
            self.source.seek(key, os.SEEK_SET)
            return ord(self.source.read(1))
        # A slice
        if key.step is not None:
            raise BitStringError("Step not supported for slicing BitStrings.")
        if key.start is None:
            start = self.byteoffset
        elif key.start < 0:
            start = self._length + key.start + self.byteoffset
        else:
            start = key.start + self.byteoffset
        if key.stop is None:
            stop = self._length + self.byteoffset
        elif key.stop < 0:
            stop = self._length + key.stop + self.byteoffset
        else:
            stop = key.stop + self.byteoffset
        if start < stop:
            self.source.seek(start, os.SEEK_SET)
            return array.array('B', self.source.read(stop-start))
        else:
            return ''

    def extend(self, data):
        raise NotImplementedError
    
    def append(self, data):
        raise NotImplementedError
    
    def length(self):
        return self._length
    
    def tostring(self):
        self.source.seek(0, os.SEEK_SET)
        return self.source.read(self._length)
    

class _MemArray(object):
    """A class that wraps the array.array functionality."""
    
    def __init__(self, data):
        self._data = array.array('B', data)
    
    def __len__(self):
        # Doesn't work for > 4GB.
        raise NotImplementedError

    def __copy__(self):
        return _MemArray(self._data)
    
    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __setitem__(self, key, item):
        self._data.__setitem__(key, item)
    
    def length(self):
        return len(self._data)
    
    def append(self, data):
        self._data.append(data)

    def extend(self, data):
        self._data.extend(data)

    def tostring(self):
        return self._data.tostring()


class BitString(object):
    """A class for general bit-wise manipulations and interpretations."""
    
    def __init__(self, auto=None, length=None, offset=0, data=None,
                 filename=None, hex=None, bin=None, oct=None,
                 uint=None, int=None, ue=None, se=None):
        """
        Initialise the BitString with one (and only one) of:
        auto -- string starting with '0x', '0o' or '0b' to be interpreted as
                hexadecimal, octal or binary respectively, or another BitString.
        data -- raw data as a string, for example read from binary file.
        bin -- binary string representation, e.g. '0b001010'.
        hex -- hexadecimal string representation, e.g. '0x2ef'
        oct -- octal string representation, e.g. '0o777'.
        uint -- an unsigned integer (length must be supplied).
        int -- a signed integer (length must be supplied).
        se -- a signed exponential-Golomb code.
        ue -- an unsigned exponential-Golomb code.
        filename -- a file which will be opened in binary read-only mode.
    
        Other keyword arguments:
        length -- length of the BitString in bits, if needed and appropriate.
        offset -- bit offset to the data. These offset bits are
                  ignored and this is mainly intended for use when
                  initialising using 'data'.
       
        e.g.
        a = BitString('0x123ab560')
        b = BitString(filename="movie.ts")
        c = BitString(int=10, length=6)
            
        """
        self._pos = 0
        self._length = 0
        self._file = None
        self._offset = 0
        if length is not None and length < 0:
            raise ValueError("length cannot be negative.")
        
        initialisers = [auto, data, filename, hex, bin, oct, int, uint, ue, se]
        initfuncs = [self._setauto, self._setdata, self._setfile,
                     self._sethex, self._setbin, self._setoct,
                     self._setint, self._setuint, self._setue, self._setse]
        assert len(initialisers) == len(initfuncs)
        if initialisers.count(None) < len(initialisers) - 1:
            raise BitStringError("You must only specify one initialiser when initialising the BitString.")
        if (se is not None or ue is not None) and length is not None:
            raise BitStringError("A length cannot be specified for an exponential-Golomb initialiser.")
        if (int or uint or ue or se) and offset != 0:
            raise BitStringError("offset cannot be specified when initialising from an integer.")
        if offset < 0:
            raise ValueError("offset must be >= 0.")
        if initialisers.count(None) == len(initialisers):
            # No initialisers, so initialise with nothing or zero bits
            if length is not None:
                data = b'\x00'*((length + 7)//8)
                self._setdata(data, length)
            else:
                self._setdata('')
        else:
            init = [(d, func) for (d, func) in zip(initialisers, initfuncs) if d is not None]
            assert len(init) == 1
            (d, func) = init[0]
            if d == filename:
                byteoffset, self._offset = divmod(offset, 8)
                func(d, length, byteoffset)
            else:
                self._offset = offset
                if length is not None:
                    func(d, length)
                else:
                    func(d)
        assert self._assertsanity()

    def __index__(self):
        return self._getuint()

    def __copy__(self):
        """Return a new copy of the BitString."""
        s_copy = BitString()
        s_copy._offset = self._offset
        s_copy._pos = self._pos
        s_copy._length = self._length
        if self._file is not None:
            raise BitStringError("Cannot copy file based BitStrings.")
        s_copy._datastore = copy.copy(self._datastore)
        return s_copy

    def __add__(self, bs):
        """Concatenate BitStrings and return new BitString.
        
        bs -- the BitString (or string for 'auto' initialiser) to append.
        
        """
        return self.__copy__().append(bs)

    def __iadd__(self, bs):
        """Append bs to current BitString. Return self.
        
        bs -- the BitString (or string for 'auto' initialiser) to append.
        
        """
        return self.append(bs)
    
    def __radd__(self, bs):
        """Append current BitString to bs and return new BitString.
        
        bs -- the string for the 'auto' initialiser that will be appended to.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        return bs.__add__(self)

    def __setitem__(self, key, value):
        """Set item or range to new value.
        
        Indices are in bits.
        Stepping is not supported and use will raise a BitStringError.
        
        """
        if isinstance(value, str):
            value = BitString(value)
        if not isinstance(value, BitString):
            raise TypeError("BitString or string expected. Got %s." % type(value))
        try:
            key.start
        except AttributeError:
            # single element
            if key >= self._length or key < -self._length:
                raise IndexError
            oldpos = self._pos
            if key < 0:
                key = self._length + key
            self._pos = key
            if value._length == 1:
                self.overwrite(value)
            else:
                self.deletebits(1)
                self.insert(value)
            self._pos = oldpos
            return
        # A slice
        if key.step is not None:
            raise BitStringError("step not supported for slicing BitStrings.")
        if key.start is None:
            start = 0
        elif key.start < 0:
            start = self._length + key.start
        else:
            start = key.start
        if key.stop is None:
            stop = self._length
        elif key.stop < 0:
            stop = self._length + key.stop
        else:
            stop = key.stop
        oldpos = self._pos
        self._pos = start
        if start >= stop:
            raise IndexError
        if (stop - start) == value._length:
            self.overwrite(value)
        else:
            self.deletebits(stop - start)
            self.insert(value)
        return
    
    def __getitem__(self, key):
        """Return a new BitString representing a slice of the current BitString.
        
        Indices are in bits.
        Stepping is not supported and use will raise a BitStringError.
        
        """
        try:
            key.start
        except AttributeError:
            # single element
            if key >= self._length or key < -self._length:
                raise IndexError
            oldpos = self._pos
            if key < 0:
                key = self._length + key
            self._pos = key
            s = self.readbit()
            self._pos = oldpos
            return s
        # A slice
        if key.step is not None:
            raise BitStringError("step not supported for slicing BitStrings.")
        if key.start is None:
            start = 0
        elif key.start < 0:
            start = self._length + key.start
        else:
            start = key.start
        if key.stop is None:
            stop = self._length
        elif key.stop < 0:
            stop = self._length + key.stop
        else:
            stop = key.stop
        if start < stop:
            return self.slice(start, stop)
        else:
            return BitString()

    def __delitem__(self, key):
        """Delete item or range.
        
        Indices are in bits.
        Stepping is not supported and use will raise a BitStringError.
        
        """
        self.__setitem__(key, BitString())

    def __len__(self):
        """Return the length of the BitString in bits."""
        return self._getlength()

    def __str__(self):
        """Return approximate string representation of BitString for printing.
        
        If exact hex representation is available it will be used, otherwise oct,
        otherwise bin. Long strings will be truncated with '...'.
        
        """
        length = self._length
        if length == 0:
            return ''
        if length > _maxchars*4:
            # Too long for hex. Truncate...
            return self.slice(0, _maxchars*4)._gethex() + '...'
        if length % 4 == 0:
            # Fine to use hex.
            return self._gethex()
        if length % 3 == 0 and length // 3 <= _maxchars:
            # Fine to use oct.
            return self._getoct()
        if length <= _maxchars:
            # Fine to use bin.
            return self._getbin()
        # Can't return exact string, so pad and use hex.
        padding = 4 - (length % 4)
        if padding == 4:
            padding = 0
        return (self + '0b0'*padding)._gethex()

    def __repr__(self):
        """Return representation that could be used to recreate the BitString.
        
        If the returned string is too long it will be truncated. See __str__().
        
        """
        length = self._length
        if isinstance(self._datastore, _FileArray):
            offsetstring = ''
            if self._datastore.byteoffset or self._offset:
                offsetstring = ", offset=%d" % (self._datastore.byteoffset * 8 + self._offset)
            lengthstring = ", length=%d" % length
            return "bitstring.BitString(filename='%s'%s%s)" % (self._datastore.source.name,
                                                               lengthstring,
                                                               offsetstring)
        else:
            s = self.__str__()
            lengthstring = ''
            if s[-3:] == '...' or (s[:2] == '0x' and length % 4 != 0):
                lengthstring = ", length=%d" % length
            return "bitstring.BitString('%s'%s)" % (s, lengthstring)
            
    def __eq__(self, bs):
        """Return True if two BitStrings have the same binary representation.
        
        Can also be used with a string for the 'auto' initialiser.
        e.g.
            a = BitString('0b11110000')
            assert a == '0xf0'
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if not isinstance(bs, BitString):
            return False
        if self._length != bs._length:
            return False
        # This could be made faster by exiting with False as early as possible.
        bs._setoffset(self._offset)
        if self._getdata() != bs._getdata():
            return False
        else:
            return True
        
    def __ne__(self, bs):
        """Return False if two BitStrings have the same binary representation.
        
        Can also be used with a string for the 'auto' initialiser.
        e.g.
            a = BitString('0b111')
            assert a != '0b1111'
        
        """
        return not self.__eq__(bs)
    
    def __hex__(self):
        """Return the hexadecimal representation as a string prefixed with '0x'.
        
        Raises a ValueError if the BitString's length is not a multiple of 4.
        
        """
        return self._gethex()
    
    def __oct__(self):
        """Return the octal representation as a string prefixed with '0o'.
        
        Raises a ValueError if the BitString's length is not a multiple of 3.
        
        """
        return self._getoct()

    def __invert__(self):
        """Return BitString with every bit inverted.
        
        Raises BitStringError if the BitString is empty.
        
        """
        if self.empty():
            raise BitStringError("Cannot invert empty BitString.")
        s = BitString(int=~(self._getint()), length=self._length)
        return s

    def __lshift__(self, n):
        """Return BitString with bits shifted by n to the left.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if self.empty():
            raise ValueError("Cannot shift an empty BitString.")
        s = self[n:].append(BitString(length = min(n, self._length)))
        return s
    
    def __ilshift__(self, n):
        """Shift bits by n to the left in place. Return self.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        self._setbin(self.__lshift__(n)._getbin())
        return self

    def __rshift__(self, n):
        """Return BitString with bits shifted by n to the right.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if self.empty():
            raise ValueError("Cannot shift an empty BitString.")
        s = BitString(length = min(n, self._length)).append(self[:-n])
        return s
    
    def __irshift__(self, n):
        """Shift bits by n to the right in place. Return self.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        self._setbin(self.__rshift__(n)._getbin())
        return self
    
    def __mul__(self, n):
        """Return BitString consisting of n concatenations of self.
        
        Called for expression of the form 'a = b*3'.
        n -- The number of concatenations. Must be >= 0.
        
        """
        if not isinstance(n, int):
            raise TypeError("Can only multiply a BitString by an int, but %s was provided." % type(n))
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        if n == 0:
            return BitString()
        s = BitString(self)
        for i in range(n - 1):
            s.append(self)
        return s

    def __rmul__(self, n):
        """Return BitString consisting of n concatenations of self.
        
        Called for expressions of the form 'a = 3*b'.
        n -- The number of concatenations. Must be >= 0.
        
        """
        return self.__mul__(n)
    
    def __imul__(self, n):
        """Concatenate n copies of self in place. Return self.
        
        Called for expressions of the form 'a *= 3'.
        n -- The number of concatenations. Must be >= 0.
        
        """
        if not isinstance(n, int):
            raise TypeError("Can only multiply a BitString by an int, but %s was provided." % type(n))
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        if n == 0:
            self._setdata('')
            return self
        s = BitString(self)
        for i in range(n - 1):
            self.append(s)
        return self

    def __and__(self, bs):
        """Bit-wise 'and' between two BitStrings. Returns new BitString.
        
        bs -- The BitString (or string for 'auto' initialiser) to & with.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if self._length != bs._length:
            raise ValueError('BitStrings must have the same length for & operator.')
        return BitString(uint=self._getuint() & bs._getuint(), length=self._length)
    
    def __rand__(self, bs):
        """Bit-wise 'and' between a string and a BitString. Returns new BitString.
        
        bs -- the string for the 'auto' initialiser to use.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        return self.__and__(bs)
        
    def __or__(self, bs):
        """Bit-wise 'or' between two BitStrings. Returns new BitString.
        
        bs -- The BitString (or string for 'auto' initialiser) to | with.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if self._length != bs._length:
            raise ValueError('BitStrings must have the same length for | operator.')
        return BitString(uint=self._getuint() | bs._getuint(), length=self._length)

    def __ror__(self, bs):
        """Bit-wise 'or' between a string and a BitString. Returns new BitString.
        
        bs -- the string for the 'auto' initialiser to use.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        return self.__or__(bs)

    def __xor__(self, bs):
        """Bit-wise 'xor' between two BitStrings. Returns new BitString.
        
        bs -- The BitString (or string for 'auto' initialiser) to ^ with.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if self._length != bs._length:
            raise ValueError('BitStrings must have the same length for ^ operator.')
        return BitString(uint=self._getuint() ^ bs._getuint(), length=self._length)
    
    def __rxor__(self, bs):
        """Bit-wise 'xor' between a string and a BitString. Returns new BitString.
        
        bs -- the string for the 'auto' initialiser to use.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        return self.__xor__(bs)

    def __contains__(self, bs):
        """Return whether bs is contained in the current BitString.
        
        bs -- The BitString (or string for 'auto' initialiser) to search for.
        
        """
        oldpos = self._pos
        found = self.find(bs, bytealigned=False)
        self._pos = oldpos
        return found

    def _assertsanity(self):
        """Check internal self consistency as a debugging aid."""
        assert self._length >= 0
        assert 0 <= self._offset < 8
        if self._length == 0:
            assert self._datastore.length() == 0
            assert self._pos == 0
        else:
            assert self._pos <= self._length
        assert (self._length + self._offset + 7) // 8 == self._datastore.length()
        return True
    
    def _setauto(self, s, length = None):
        """Set BitString from another BitString, or a binary, octal or hexadecimal string."""
        if isinstance(s, BitString):
            self.__init__(data=s._getdata(), length=s._length, offset=s._offset)
            return
        s = _tidyupinputstring(s)
        if not s:
            self._setdata('')
            return
        if s.startswith('0x'):
            s = s.replace('0x', '')
            self._sethex(s, length)
            return
        if s.startswith('0b'):
            s = s.replace('0b', '')
            self._setbin(s, length)
            return
        if s.startswith('0o'):
            s = s.replace('0o', '')
            self._setoct(s, length)
            return
        raise ValueError("String '%s' cannot be interpreted as hexadecimal, binary or octal. "
                             "It must start with '0x', '0b' or '0o'." % s)

    def _setfile(self, filename, lengthinbits=None, byteoffset=None):
        "Use file as source of bits."
        self._datastore = _FileArray(filename, lengthinbits,
                                     self._offset, byteoffset)
        if lengthinbits:
            self._length = lengthinbits
        else:
            self._length = self._datastore.length()*8 - self._offset

    def _setdata(self, data, length = None):
        """Set the data from a string."""
        if length is None:
            # Use to the end of the data
            self._datastore = _MemArray(data[self._offset // 8:])
            self._length = self._datastore.length()*8 - self._offset
        else:
            self._length = length
            if self._length + self._offset > len(data)*8:
                raise ValueError("Not enough data present. Need %d bits, have %d." % \
                                     (self._length+self._offset, len(data)*8))
            if self._length == 0:
                self._datastore = _MemArray('')
            else:
                self._datastore = _MemArray(data[self._offset // 8:(self._length + self._offset + 7) // 8])
        self._offset %= 8

    def _getdata(self):
        """Return the data as an ordinary string."""
        self._ensureinmemory()
        self._setoffset(0)
        d = self._datastore.tostring()
        # Need to ensure that unused bits at end are set to zero
        unusedbits = 8 - self._length % 8
        if unusedbits != 8:
            # This is horrible. Mustn't copy the string here!
            return d[:-1] + bytes([d[-1] & (255 << unusedbits)])
        return d

    def _setuint(self, uint, length=None):
        """Reset the BitString to have given unsigned int interpretation."""
        if length is None and self._length != 0:
            length = self._length
        if length is None or length == 0:
            raise ValueError("A non-zero length must be specified with a uint initialiser.")
        if uint >= (1 << length):
            raise ValueError("uint cannot be contained using BitString of that length.")
        if uint < 0:
            raise ValueError("uint cannot be initialsed by a negative number.")     
        hexstring = hex(uint)[2:]
        if hexstring[-1] == 'L':
            hexstring = hexstring[:-1]
        hexlengthneeded = (length + 3) // 4
        leadingzeros = hexlengthneeded - len(hexstring)
        if leadingzeros > 0:
            hexstring = '0'*leadingzeros + hexstring
        self._sethex(hexstring)
        self._offset = (4*hexlengthneeded) - length
        self._length = length

    def _getuint(self):
        """Return data as an unsigned int."""
        if self.empty():
            raise ValueError("An empty BitString cannot be interpreted as an unsigned integer")
        if self._datastore.length() == 1:
            mask = ((1 << self._length) - 1) << (8 - self._length-self._offset)
            val = self._datastore[0] & mask
            val >>= 8 - self._offset - self._length
            return val
        # Take the bits in the first byte and shift them to their final position
        firstbits = 8 - self._offset
        mask = (1<<firstbits) - 1
        shift = self._length - firstbits
        val = (self._datastore[0] & mask) << shift
        # For the middle of the data we use struct.unpack to do the conversion
        # as it's more efficient. This loop only gets invoked if the BitString's
        # data is more than 10 bytes.
        j = 1
        structsize = struct.calcsize('Q')
        end = self._datastore.length() - 1
        while j + structsize < end:
            shift -= 8*structsize
            # Convert next 8 bytes to an int, then shift it to proper place
            # and add it
            val += (struct.unpack('>Q', self._datastore[j:j+structsize])[0] << shift)
            j += structsize
        # Do the remaining bytes, except for the final one
        while j < end:
            shift -= 8
            val += (self._datastore[j] << shift)
            j += 1
        # And the very final byte
        assert shift <= 8
        bitsleft = (self._offset + self._length) % 8
        if bitsleft == 0:
            bitsleft = 8
        lastbyte = self._datastore[-1]
        mask = 255 - ((1 << (8 - bitsleft)) - 1)
        val += (lastbyte & mask) >> (8 - bitsleft)
        return val

    def _setint(self, int, length=None):
        """Reset the BitString to have given signed int interpretation."""
        if length is None and self._length != 0:
            length = self._length
        if length is None or length == 0:
            raise ValueError("A non-zero length must be specified with an int initialiser.")
        if int >=  (1 << (length - 1)) or int < -(1 << (length - 1)):
            raise ValueError("int cannot be contained using BitString of that length.")   
        if int < 0:
            # the twos complement thing to get the equivalent +ive number
            int = (-int - 1)^((1 << length) - 1)
        self._setuint(int, length)

    def _getint(self):
        """Return data as a two's complement signed int."""
        ui = self._getuint()
        if ui < (1 << (self._length - 1)):
            # Top bit not set - must be positive
            return ui
        tmp = (~(ui - 1)) & ((1 << self._length) - 1)
        return -tmp

    def _setue(self, i):
        """Initialise BitString with unsigned exponential-Golomb code for integer i.
        
        Raises ValueError if i < 0.
        
        """
        if i < 0:
            raise ValueError("Cannot use negative initialiser for unsigned exponential-Golomb.")
        if i == 0:
            self._setbin('1')
            return
        tmp = i + 1
        leadingzeros = -1
        while tmp > 0:
            tmp >>= 1
            leadingzeros += 1
        remainingpart = i + 1 - (1 << leadingzeros)
        binstring = '0'*leadingzeros + '1' + BitString(uint = remainingpart,
                                                       length = leadingzeros).bin[2:]
        self._setbin(binstring)

    def _getue(self):
        """Return data as unsigned exponential-Golomb code.
        
        Raises BitStringError if BitString is not a single exponential-Golomb code.
        
        """
        oldpos = self._pos
        self._pos = 0
        try:
            value = self.readue()
            if self._pos != self._length:
                raise BitStringError
        except BitStringError:
            self._pos = oldpos
            raise BitStringError("BitString is not a single exponential-Golomb code.")
        self._pos = oldpos
        return value
    
    def _setse(self, i):
        """Initialise BitString with signed exponential-Golomb code for integer i."""
        if i > 0:
            u = (i*2) - 1
        else:
            u = -2*i
        self._setue(u)

    def _getse(self):
        """Return data as signed exponential-Golomb code.
        
        Raises BitStringError if BitString is not a single exponential-Golomb code.
                
        """
        oldpos= self._pos
        self._pos = 0
        try:
            value = self.readse()
            if value is None or self._pos != self._length:
                raise BitStringError
        except BitStringError:
            self._pos = oldpos
            raise BitStringError("BitString is not a single exponential-Golomb code.")
        self._pos = oldpos
        return value
    
    def _setbin(self, binstring, length=None):
        """Reset the BitString to the value given in binstring."""
        binstring = _tidyupinputstring(binstring)
        # remove any 0b if present
        binstring = binstring.replace('0b', '')
        if length is None:
            length = len(binstring) - self._offset
        if length < 0 or length > (len(binstring) - self._offset):
            raise ValueError("Invalid length of binary string.")
        # Truncate the bin_string if needed
        binstring = binstring[self._offset:length + self._offset]
        self._length = length
        self._offset = 0
        if self._length == 0:
            self._datastore = _MemArray('')
            return
        # pad with zeros up to byte boundary if needed
        boundary = ((self._length + 7) // 8) * 8
        if len(binstring) < boundary:
            binstring += '0'*(boundary - self._length)
        try:
            bytes = [int(binstring[x:x + 8], 2) for x in range(0, len(binstring), 8)]
        except ValueError:
            raise ValueError("Invalid character in bin initialiser.")
        self._datastore = _MemArray(bytes)

    def _getbin(self):
        """Return interpretation as a binary string."""
        if self._length == 0:
            return ''
        c = [_byte2bits[x] for x in self._datastore]
        return '0b' + ''.join(c)[self._offset:self._offset + self._length]

    def _setoct(self, octstring, length=None):
        """Reset the BitString to have the value given in octstring."""
        octstring = _tidyupinputstring(octstring)
        # remove any 0o if present
        octstring = octstring.replace('0o', '')
        if length is None:
            length = len(octstring)*3 - self._offset
        if length < 0 or length + self._offset > len(octstring)*3:
            raise ValueError("Invalid length %s, offset %d for oct initialiser %s" % (length, self._offset, octstring))
        octstring = octstring[self._offset // 3:(length + self._offset + 2) // 3]
        self._offset %= 3
        self._length = length
        if self._length == 0:
            self._datastore = _MemArray('')
            return
        binlookup = ['000', '001', '010', '011', '100', '101', '110', '111']
        binlist = []
        for i in octstring:
            try:
                if not 0 <= int(i) < 8:
                    raise ValueError
                binlist.append(binlookup[int(i)])
            except ValueError:
                raise ValueError("Invalid symbol '%s' in oct initialiser." % i)
        self._setbin(''.join(binlist))

    def _getoct(self):
        """Return interpretation as an octal string."""
        if self._length%3 != 0:
            raise ValueError("Cannot convert to octal unambiguously - not multiple of 3 bits.")
        if self._length == 0:
            return ''
        oldbitpos = self._pos
        self._setbitpos(0)
        octlist = ['0o']
        for i in range(self._length//3):
            octlist.append(str(self.readbits(3).uint))
        self._pos = oldbitpos
        return ''.join(octlist)
    
    def _sethex(self, hexstring, length=None):
        """Reset the BitString to have the value given in hexstring."""
        hexstring = _tidyupinputstring(hexstring)
        # remove any 0x if present
        hexstring = hexstring.replace('0x', '')
        if length is None:
            length = len(hexstring)*4 - self._offset
        if length < 0 or length + self._offset > len(hexstring)*4:
            raise ValueError("Invalid length %d, offset %d for hexstring 0x%s." % (length, self._offset, hexstring))
        
        hexstring = hexstring[self._offset // 4:(length + self._offset + 3) // 4]
        self._offset %= 4
        self._length = length
        if self._length == 0:
            self._datastore = _MemArray('')
            return
        hexlist = []
        # First do the whole bytes
        for i in range(len(hexstring)//2):
            try:
                j = int(hexstring[i*2:i*2 + 2], 16) 
                if not 0 <= j < 256:
                    raise ValueError
                hexlist.append(_single_byte_from_hex_string(hexstring[i*2:i*2 + 2]))
            except ValueError:
                raise ValueError("Invalid symbol in hex initialiser.")
        # then any remaining nibble
        if len(hexstring) % 2 == 1:
            try:
                j = int(hexstring[-1], 16)
                if not 0 <= j < 16:
                    raise ValueError
                hexlist.append(_single_byte_from_hex_string(hexstring[-1]))
            except ValueError:
                raise ValueError("Invalid symbol in hex initialiser.")
        self._datastore = _MemArray(b''.join(hexlist))

    def _gethex(self):
        """Return the hexadecimal representation as a string prefixed with '0x'.
        
        Raises a ValueError if the BitString's length is not a multiple of 4.
        
        """        
        if self._length % 4 != 0:
            raise ValueError("Cannot convert to hex unambiguously - not multiple of 4 bits.")
        if self._length == 0:
            return ''
        self._ensureinmemory()
        self._setoffset(0)
        s = self._datastore.tostring()
        hexstrings = [_hex_string_from_single_byte(i) for i in s]
        if (self._length // 4) % 2 == 1:
            # only a nibble left at the end
            hexstrings[-1] = hexstrings[-1][0]
        s = '0x'+''.join(hexstrings)
        return s  

    def _setbytepos(self, bytepos):
        """Move to absolute byte-aligned position in stream."""
        self._setbitpos(bytepos*8)

    def _getbytepos(self):
        """Return the current position in the stream in bytes. Must be byte aligned."""
        p = self._getbitpos()
        if p % 8 != 0:
            raise BitStringError("Not byte aligned in _getbytepos().")
        return p // 8

    def _setbitpos(self, bitpos):
        """Move to absolute postion bit in bitstream."""
        if bitpos < 0:
            raise ValueError("Bit position cannot be negative.")
        if bitpos > self._length:
            raise ValueError("Cannot seek past the end of the data.")
        self._pos = bitpos

    def _getbitpos(self):
        """Return the current position in the stream in bits."""
        assert 0 <= self._pos <= self._length
        return self._pos

    def _setoffset(self, offset):
        """Realign BitString with offset to first bit."""
        if offset == self._offset:
            return
        if not 0 <= offset < 8:
            raise ValueError("Can only align to an offset from 0 to 7.")
        if offset < self._offset:
            # We need to shift everything left
            shiftleft = self._offset - offset
            # First deal with everything except for the final byte
            for x in range(self._datastore.length() - 1):
                self._datastore[x] = ((self._datastore[x] << shiftleft) & 255) + \
                                     (self._datastore[x + 1] >> (8 - shiftleft))
            # if we've shifted all of the data in the last byte then we need to truncate by 1
            bits_in_last_byte = (self._offset + self._length) % 8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte <= shiftleft:
                self._datastore = _MemArray(self._datastore[:-1])
            # otherwise just shift the last byte
            else:
                self._datastore[-1] = (self._datastore[-1] << shiftleft) & 255
        else: # offset > self._offset
            shiftright = offset - self._offset
            # Give some overflow room for the last byte
            if (self._offset + self._length + shiftright + 7)//8 > (self._offset + self._length + 7)//8:
                self._datastore.append(0)
            for x in range(self._datastore.length()-1, 0, -1):
                self._datastore[x] = ((self._datastore[x-1] << (8 - shiftright)) & 255) + \
                                     (self._datastore[x] >> shiftright)
            self._datastore[0] = self._datastore[0] >> shiftright
        self._offset = offset

    def _getlength(self):
        """Return the length of the BitString in bits."""
        assert self._length == 0 or 0 <= self._pos <= self._length
        return self._length
    
    def _ensureinmemory(self):
        """Ensure the data is held in memory, not in a file."""
        if isinstance(self._datastore, _FileArray):
            self._datastore = _MemArray(self._datastore[:])
    
    def empty(self):
        """Return True if the BitString is empty (has zero length)."""
        return self._length == 0
    
    def readbit(self):
        """Return next bit in BitString as new BitString and advance position.
        
        Returns empty BitString if bitpos is at the end of the BitString.
        
        """
        return self.readbits(1)

    def readbits(self, bits):
        """Return next bits in BitString as a new BitString and advance position.
        
        bits -- The number of bits to read.
        
        If not enough bits are available then all will be returned.
        
        Raises ValueError if bits < 0.
        
        """
        if bits < 0:
            raise ValueError("Cannot read negative amount.")
        if self._pos+bits > self._length:
            bits = self._length - self._pos
        startbyte, newoffset = divmod(self._pos + self._offset, 8)
        endbyte = (self._pos + self._offset + bits - 1) // 8
        self._pos += bits
        assert self._assertsanity()
        return BitString(data=self._datastore[startbyte:endbyte + 1],
                         length=bits, offset=newoffset) 
    
    def readbyte(self):
        """Return next byte as a new BitString and advance position.
        
        Does not byte align.
        
        If not enough bits are available then all will be returned.
        
        """
        return self.readbits(8)

    def readbytes(self, bytes):
        """Return next bytes as a new BitString and advance position.
        
        Does not byte align.
        
        bytes -- The number of bytes to read.
        
        If not enough bits are available then all will be returned.
        
        """
        return self.readbits(bytes*8)

    def readue(self):
        """Return interpretation of next bits as unsigned exponential-Golomb code.
           
        Advances position to after the read code.
        
        Raises BitStringError if the end of the BitString is encountered while
        reading the code.
        
        """
        oldpos = self._pos
        foundone = self.find('0b1', False, self._pos)
        if not foundone:
            self._pos = self._length
            raise BitStringError("Read off end of BitString trying to read code.")
        leadingzeros = self._pos - oldpos
        codenum = (1 << leadingzeros) - 1
        if leadingzeros > 0:
            restofcode = self.readbits(leadingzeros + 1)
            if restofcode._length != leadingzeros + 1:
                raise BitStringError("Read off end of BitString trying to read code.")
            codenum += restofcode[1:].uint
        else:
            assert codenum == 0
            self._pos += 1
        return codenum

    def readse(self):
        """Return interpretation of next bits as a signed exponential-Golomb code.
        
        Advances position to after the read code.
        
        Raises BitStringError if the end of the BitString is encountered while
        reading the code.
        
        """
        codenum = self.readue()
        m = (codenum + 1)//2
        if codenum % 2 == 0:
            return -m
        else:
            return m

    def peekbit(self):
        """Return next bit as a new BitString without advancing position.
        
        Returns empty BitString if bitpos is at the end of the BitString.
        
        """
        return self.peekbits(1)

    def peekbits(self, bits):
        """Return next bits as a new BitString without advancing position.
        
        bits -- The number of bits to read. Must be >= 0.
        
        If not enough bits are available then all will be returned.
        
        """
        bitpos = self._pos
        s = self.readbits(bits)
        self._pos = bitpos
        return s
    
    def peekbyte(self):
        """Return next byte as a new BitString without advancing position.
        
        If not enough bits are available then all will be returned.
        
        """
        return self.peekbits(8)

    def peekbytes(self, bytes):
        """Return next bytes as a new BitString without advancing position.
        
        bytes -- The number of bytes to read. Must be >= 0.
        
        If not enough bits are available then all will be returned.
        
        """
        return self.peekbits(bytes*8)

    def advancebit(self):
        """Advance position by one bit.
        
        Raises ValueError if bitpos is past the last bit in the BitString.
        
        """
        self._setbitpos(self._pos + 1)

    def advancebits(self, bits):
        """Advance position by bits.
        
        bits -- Number of bits to increment bitpos by. Must be >= 0.
        
        Raises ValueError if bits is negative or if bitpos goes past the end
        of the BitString.
        
        """
        if bits < 0:
            raise ValueError("Cannot advance by a negative amount.")
        self._setbitpos(self._pos + bits)

    def advancebyte(self):
        """Advance position by one byte. Does not byte align.
        
        Raises ValueError if there is less than one byte from bitpos to
        the end of the BitString.
        
        """
        self._setbitpos(self._pos + 8)

    def advancebytes(self, bytes):
        """Advance position by bytes. Does not byte align.
        
        bytes -- Number of bytes to increment bitpos by. Must be >= 0.
        
        Raises ValueError if there are not enough bytes from bitpos to
        the end of the BitString.
        
        """
        if bytes < 0:
            raise ValueError("Cannot advance by a negative amount.")
        self._setbitpos(self._pos + bytes*8)

    def retreatbit(self):
        """Retreat position by one bit.
        
        Raises ValueError if bitpos is already at the start of the BitString.
        
        """
        self._setbitpos(self._pos - 1)
 
    def retreatbits(self, bits):
        """Retreat position by bits.
        
        bits -- Number of bits to decrement bitpos by. Must be >= 0.
        
        Raises ValueError if bits negative or if bitpos goes past the start
        of the BitString.
        
        """
        if bits < 0:
            raise ValueError("Cannot retreat by a negative amount.")
        self._setbitpos(self._pos - bits)

    def retreatbyte(self):
        """Retreat position by one byte. Does not byte align.
        
        Raises ValueError if bitpos is less than 8.
        
        """
        self._setbitpos(self._pos - 8)

    def retreatbytes(self, bytes):
        """Retreat position by bytes. Does not byte align.
        
        bytes -- Number of bytes to decrement bitpos by. Must be >= 0.
        
        Raises ValueError if bytes negative or if bitpos goes past the start
        of the BitString.
        
        """
        if bytes < 0:
            raise ValueError("Cannot retreat by a negative amount.")
        self._setbitpos(self._pos - bytes*8)

    def seekbit(self, bitpos):
        """Seek to absolute bit position bitpos.
        
        Raises ValueError if bitpos < 0 or bitpos > self.length.
        
        """
        self._setbitpos(bitpos)
    
    def seekbyte(self, bytepos):
        """Seek to absolute byte position bytepos.
        
        Raises ValueError if bytepos < 0 or bytepos*8 > self.length.
        
        """
        self._setbytepos(bytepos)
    
    def tellbit(self):
        """Return current position in the BitString in bits (bitpos)."""
        return self._getbitpos()
    
    def tellbyte(self):
        """Return current position in the BitString in bytes (bytepos).
        
        Raises BitStringError if position is not byte-aligned.
        
        """
        return self._getbytepos()

    def find(self, bs, bytealigned=True, startbit=None, endbit=None):
        """Seek to start of next occurence of bs. Return True if string is found.
        
        bs -- The BitString (or string for 'auto' initialiser) to find.
        bytealigned -- If True (the default) the BitString will only be
                       found on byte boundaries.
        startbit -- The bit position to start the search.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to search.
                  Defaults to len(self).
        
        Raises ValueError if bs is empty, if startbit < 0,
        if endbit > len(self) or if endbit < startbit.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if bs.empty():
            raise ValueError("Cannot find an empty BitString.")
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self._length
        if startbit < 0:
            raise ValueError("Cannot find - startbit must be >= 0.")
        if endbit > self._length:
            raise ValueError("Cannot find - endbit is past the end of the BitString.")
        if endbit < startbit:
            raise ValueError("endbit must not be less than startbit.")
        if bytealigned and len(bs) % 8 == 0:
            # Extract data bytes from BitString to be found.
            bs._setoffset(0)
            d = bs._getdata()
            self._setoffset(0)
            oldpos = self._pos
            self._pos = startbit
            try:
                self.bytealign()
            except BitStringError:
                # Not even enough bits left to byte-align.
                self._pos = oldpos
                return False
            bytepos = self._pos // 8
            found = False
            p = bytepos
            finalpos = endbit // 8
            increment = max(1024, len(d)*10)
            buffersize = increment + len(d)
            while p < finalpos:
                # Read in file or from memory in overlapping chunks and search the chunks.
                buffer = self._datastore[p:min(p + buffersize, finalpos)].tostring()
                pos = buffer.find(d)
                if pos != -1:
                    found = True
                    p += pos
                    break
                p += increment
            if not found:
                self._pos = oldpos
                return False
            self._setbytepos(p)
            assert self._assertsanity()
            return True
        else:
            oldpos = self._pos
            targetbin = bs._getbin()[2:]
            found = False
            p = startbit
            # We grab overlapping chunks of the binary representation and
            # do an ordinary string search within that.
            increment = max(16384, bs._length*10)
            buffersize = increment + bs._length
            while p < endbit:
                buffer = self[p:min(p+buffersize, endbit)]._getbin()[2:]
                pos = buffer.find(targetbin)
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
                return False
            self._pos = p
            return True

    def findall(self, bs, bytealigned=True, startbit=None, endbit=None):
        """Find all occurences of bs. Return list of bit positions.
        
        bs -- The BitString (or string for 'auto' initialiser) to find.
        bytealigned -- If True (the default) the BitString will only be
                       found on byte boundaries.
        startbit -- The bit position to start the search.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to search.
                  Defaults to len(self).
        
        Raises ValueError if bs is empty, if startbit < 0,
        if endbit > len(self) or if endbit < startbit.
        
        Note that all occurences of bs are found, even if they overlap.
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self._length
        # Can rely on find() for parameter checking
        foundpositions = []
        while self.find(bs, bytealigned=bytealigned, startbit=startbit,
                        endbit=endbit):
            foundpositions.append(self._pos)
            if bytealigned:
                startbit = self._pos + 8
            else:
                startbit = self._pos + 1
            if startbit >= endbit:
                break
        return foundpositions
    
    def rfind(self, bs, bytealigned=True, startbit=None, endbit=None):
        """Seek backwards to start of previous occurence of bs.
        
        Return True if string is found.
        
        bs -- The BitString (or string for 'auto' initialiser) to find.
        bytealigned -- If True (the default) the BitString will only be
                       found on byte boundaries.
        startbit -- The bit position to end the reverse search.
                    Defaults to 0.
        endbit -- The bit position one past the first bit to reverse search.
                  Defaults to len(self).
        
        Raises ValueError if bs is empty, if startbit < 0,
        if endbit > len(self) or if endbit < startbit.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if bs.empty():
            raise ValueError("Cannot find an empty BitString.")
        # Obviously finding all isn't very efficient, and this needs to be rewritten.
        positions = self.findall(bs, bytealigned=bytealigned,
                                 startbit=startbit, endbit=endbit)
        if not positions:
            return False
        self._pos = positions[-1]
        return True
    
    def replace(self, old, new, bytealigned=True, startbit=None, endbit=None, count=None):
        """Replace all occurrences of old with new in place.
        
        Returns number of replacements made.
        
        old -- The BitString (or string for 'auto' initialiser) to replace
        new -- The replacement BitString (or string for 'auto' initialiser).
        bytealigned -- If True (the default) replacements will only be made
                       on byte boundaries.
        startbit -- Any occurences that start before starbit will not
                    be replaced. Defaults to 0.
        endbit -- Any occurences that finish after endbit will not
                  be replaced. Defaults to len(self)
        count -- The maximum number of replacements to make.
        
        Raises ValueError if old is empty or if startbit or endbit are
        out of range.
        
        """        
        if isinstance(old, str):
            old = BitString(old)
        if isinstance(new, str):
            new = BitString(new)
        if old.empty():
            raise ValueError("Empty BitString cannot be replaced.")
        newpos = self._pos
        sections = self.split(old, bytealigned=bytealigned,
                              startbit=startbit, endbit=endbit, maxsplit=count)
        lengths = [s.length for s in sections]
        if len(lengths) == 1:
            self._pos = newpos
            return 0 # no replacements done
        positions = [lengths[0]]
        for l in lengths[1:-1]:
            # Next position is the previous one plus the length of the next section.
            positions.append(positions[-1] + l)
        # We have all the positions that need replacements. We do them
        # in reverse order so that they won't move around as we replace.
        positions.reverse()
        for p in positions:
            self[p:p + old.length] = new
        if old.length != new.length:
            # Need to calculate new bitpos
            diff = new.length - old.length
            for p in positions:
                if p >= newpos:
                    continue
                if p + old.length <= newpos:
                    newpos += diff
                else:
                    newpos = p
        self._pos = newpos
        assert self._assertsanity()
        return len(lengths) - 1

    def bytealign(self):
        """Align to next byte and return number of skipped bits.
        
        Raises ValueError if the end of the BitString is reached before
        aligning to the next byte.
        
        """
        skipped = (8 - (self._pos % 8)) % 8
        self._setbitpos(self._pos + self._offset + skipped)
        assert self._assertsanity()
        return skipped

    def truncatestart(self, bits):
        """Truncate bits from the start of the BitString. Return new BitString.
        
        bits -- Number of bits to remove from start of the BitString.
        
        Raises ValueError if bits < 0 or bits > self.length.
        
        """
        if bits < 0 or bits > self._length:
            raise ValueError("Truncation length of %d not possible. Length = %d." % (bits, self._length))
        if bits == self._length:
            self._offset = 0
            self._setdata('')
            return self
        self._offset = (self._offset + bits) % 8
        self._setdata(self._datastore[bits//8:], length=self._length - bits)
        self._pos = max(0, self._pos - bits)
        assert self._assertsanity()
        return self

    def truncateend(self, bits):
        """Truncate bits from the end of the BitString. Return new BitString.
        
        bits -- Number of bits to remove from end of the BitString.
        
        Raises ValueError if bits < 0 or bits > self.length.
        
        """
        if bits < 0 or bits > self._length:
            raise ValueError("Truncation length of %d bits not possible. Length = %d." % (bits, self._length))
        if bits == self._length:
            self._offset = 0
            self._setdata('')
            return self
        new_length_in_bytes = (self._offset + self._length - bits + 7) // 8
        # Ensure that the position is still valid
        self._pos = max(0, min(self._pos, self._length - bits))
        self._setdata(self._datastore[:new_length_in_bytes], length=self._length - bits)
        assert self._assertsanity()
        return self
    
    def slice(self, startbit, endbit):
        """Return a new BitString which is the slice [startbit, endbit).
        
        startbit -- Position of first bit in the new BitString.
        endbit -- One past the position of the last bit in the new BitString.
        
        Raises ValueError if endbit < startbit, if startbit < 0 or
        endbit > self.length.
        
        """
        if endbit < startbit:
            raise ValueError("Cannot slice - endbit is less than startbit.")
        if endbit == startbit:
            return BitString()
        if startbit < 0:
            raise ValueError("Cannot slice - startbit is less than zero.")
        if endbit > self._length:
            raise ValueError("Cannot slice - endbit is past the end of the BitString.")
        startbyte, newoffset = divmod(startbit + self._offset, 8)
        endbyte = (endbit + self._offset - 1) // 8
        return BitString(data=self._datastore[startbyte:endbyte + 1],
                         length=endbit - startbit,
                         offset=newoffset)
    
    def insert(self, bs, bitpos=None):
        """Insert bs at current position, or bitpos if supplied. Return self.
        
        bs -- The BitString (or string for 'auto' initialiser) to insert.
        bitpos -- The bit position to insert the BitString.
        
        Raises ValueError if bitpos < 0 or bitpos > self.length.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if bs.empty():
            return self
        if bs is self:
            bs = self.__copy__()
        if bitpos is None:
            bitpos = self._pos
        if bitpos < 0 or bitpos > self._length:
            raise ValueError("Invalid insert position.")
        end = self.slice(bitpos, self._length)
        self.truncateend(self._length - bitpos)
        self.append(bs)
        self.append(end)
        assert self._assertsanity()
        return self

    def overwrite(self, bs, bitpos=None):
        """Overwrite with bs at current position, or bitpos if given. Return self.
        
        bs -- The BitString (or string for 'auto' initialiser) to
              overwrite with.
        bitpos -- The bit position to begin overwriting from.
        
        Raises ValueError if bitpos < 0 or bitpos + len(bs) > self.length
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if bs.empty():
            return self
        if bs is self:
            bs = self.__copy__()        
        if bitpos is None:
            bitpos = self._pos
        if bitpos < 0 or bitpos + bs._length > self._length:
            raise ValueError("Overwrite exceeds boundary of BitString.")
        end = self.slice(bitpos+bs._length, self._length)
        self.truncateend(self._length - bitpos)
        self.append(bs)
        self.append(end)
        self._pos = bitpos + bs._length
        assert self._assertsanity()
        return self
    
    def deletebits(self, bits, bitpos=None):
        """Delete bits at current position, or bitpos if supplied. Return self.
        
        bits -- Number of bits to delete.
        bitpos -- Bit position to delete from (default is self.bitpos).
        
        Raises ValueError if bits < 0 or if you try to delete past the
        end of the BitString.
        
        """
        if bitpos is None:
            bitpos = self._pos
        if bits < 0:
            raise ValueError("Cannott delete a negative number of bits.")
        if bits + bitpos > self.length:
            raise ValueError("Cannot delete past the end of the BitString.")
        end = self.slice(bitpos+bits, self._length)
        self.truncateend(self._length - bitpos)
        self.append(end)
        return self
    
    def deletebytes(self, bytes, bytepos=None):
        """Delete bytes at current position, or bytepos if supplied. Return self.
        
        bytes -- Number of bytes to delete.
        bytepos -- Byte position to delete from (default is self.bytepos)
        
        Raises BitStringError if bytepos not specified and current position
        is not byte aligned.
        Raises ValueError if bytes < 0 or if you try to delete past the
        end of the BitString.
        
        """
        if bytepos is None and self._pos % 8 != 0:
            raise BitStringError("Must be byte-aligned for deletebytes().")
        if bytepos is None:
            bytepos = self._pos//8
        return self.deletebits(bytes*8, bytepos*8)

    def append(self, bs):
        """Append a BitString to the current BitString. Return self.
        
        bs -- The BitString (or string for 'auto' initialiser) to append.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if bs.empty():
            return self
        # Can't modify file, so ensure it's read into memory
        self._ensureinmemory()
        if bs is self:
            bs = self.__copy__()
        bits_in_final_byte = (self._offset + self._length)%8
        bs._setoffset(bits_in_final_byte)
        if bits_in_final_byte != 0:
            # first do the byte with the join.
            self._datastore[-1] = (self._datastore[-1] & (255 ^ (255 >> bits_in_final_byte)) | \
                                   (bs._datastore[0] & (255 >> bs._offset)))
        else:
            self._datastore.append(bs._datastore[0])
        self._datastore.extend(bs._datastore[1:bs._datastore.length()])
        self._length += bs._length
        assert self._assertsanity()
        return self
    
    def prepend(self, bs):
        """Prepend a BitString to the current BitString. Return self.
        
        bs -- The BitString (or string for 'auto' initialiser) to prepend.
        
        """
        if isinstance(bs, str):
            bs = BitString(bs)
        if bs.empty():
            return self
        # Can't modify file so ensure it's read into memory
        self._ensureinmemory()
        if bs is self:
            bs = self.__copy__()
        bits_in_final_byte = (bs._offset + bs._length)%8
        end = self.__copy__()
        end._setoffset(bits_in_final_byte)
        bitpos = self._pos
        self._pos = 0
        self._setdata(bs._getdata(), length=bs._length)
        if bits_in_final_byte != 0:
            self._datastore[-1] = (self._datastore[-1] | end._datastore[0])
        elif not end.empty():
            self._datastore.append(end._datastore[0])
        self._datastore.extend(end._datastore[1:end._datastore.length()])
        self._length += end._length
        self._pos = bitpos + bs._length
        assert self._assertsanity()
        return self
    
    def reversebits(self):
        """Reverse all bits in-place. Return self.
        
        Using on an empty BitString will have no effect.
        
        """
        self._setbin(self._getbin()[:1:-1])
        return self
    
    def split(self, delimiter, bytealigned=True, startbit=None,
              endbit=None, maxsplit=None):
        """Return BitString generator by splittling using a delimiter.
        
        The first item returned is the initial BitString before the delimiter,
        which may be an empty BitString.
        
        delimiter -- The BitString (or string for 'auto' initialiser) used as
                     the divider.
        bytealigned -- If True (the default) splits will only occur on byte
                       boundaries.
        startbit -- The bit position to start the split.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to use in the split.
                  Defaults to len(self).
        maxsplit -- If specified then at most maxsplit splits are done.
                    Default is to split as many times as possible.
        
        Raises ValueError if the delimiter empty or if bytealigned is True
        and the delimiter is not a whole number of bytes.
        
        """
        if isinstance(delimiter, str):
            delimiter = BitString(delimiter)
        if delimiter.empty():
            raise ValueError("split delimiter cannot be empty.")
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self._length
        if startbit < 0:
            raise ValueError("Cannot split - startbit must be >= 0.")
        if endbit > self._length:
            raise ValueError("Cannot split - endbit is past the end of the BitString.")
        if endbit < startbit:
            raise ValueError("endbit must not be less than startbit.")
        splits = 0
        oldpos = self._pos
        self._pos = startbit
        found = self.find(delimiter, bytealigned=bytealigned,
                          startbit=startbit, endbit=endbit)
        if not found or maxsplit == 0:
            # Initial bits are the whole BitString being searched
            self._pos = oldpos
            yield self.slice(startbit, endbit)
            return
        # yield the bytes before the first occurence of the delimiter, even if empty
        yield self[startbit:self._pos]
        startpos = self._pos
        while found:
            self._pos += delimiter._length
            found = self.find(delimiter, bytealigned=bytealigned,
                              startbit=self._pos, endbit=endbit)
            if not found:
                # No more occurences, so return the rest of the BitString
                self._pos = oldpos
                yield self[startpos:endbit]
                return
            if maxsplit is not None:
                splits += 1
                if splits == maxsplit:
                    # Done all the splits we need to, return the rest of the BitString
                    self._pos = oldpos
                    yield self[startpos:]
                    return
            yield self[startpos:self._pos]
            startpos = self._pos

    length = property(_getlength,
                      doc="""The length of the BitString in bits. Read only.
                      """)
    hex    = property(_gethex, _sethex,
                      doc="""The BitString as a hexadecimal string. Read and write.
                      
                      When read will be prefixed with '0x' and including any leading zeros.
                      
                      """)
    bin    = property(_getbin, _setbin,
                      doc="""The BitString as a binary string. Read and write.
                      
                      When read will be prefixed with '0b' and including any leading zeros.
                      
                      """)
    oct    = property(_getoct, _setoct,
                      doc="""The BitString as an octal string. Read and write.
                      
                      When read will be prefixed with '0o' and including any leading zeros.
                      
                      """)
    data   = property(_getdata, _setdata,
                      doc="""The BitString as a ordinary string. Read and write.
                      
                      When used to read will add up to seven zero bits to the end of the
                      BitString to byte align.
                      
                      """)
    int    = property(_getint, _setint,
                      doc="""The BitString as a two's complement signed int. Read and write.
                      """)
    uint   = property(_getuint, _setuint,
                      doc="""The BitString as a two's complement unsigned int. Read and write.
                      """)
    ue     = property(_getue, _setue,
                      doc="""The BitString as an unsigned exponential-Golomb code. Read and write.
                      """)
    se     = property(_getse, _setse,
                      doc="""The BitString as a signed exponential-Golomb code. Read and write.
                      """)
    bitpos = property(_getbitpos, _setbitpos,
                      doc="""The position in the BitString in bits. Read and write.
                      """)
    bytepos= property(_getbytepos, _setbytepos,
                      doc="""The position in the BitString in bytes. Read and write.
                      """)
    

def join(bitstringlist):
    """Return the concatenation of the BitStrings in a list.
    
    bitstringlist -- Can contain BitStrings, or strings to be used by the 'auto'
                     initialiser.
    
    >>> a = join(['0x0001ee', BitString(int=13, length=100), '0b0111')
    
    """
    s = BitString()
    for bs in bitstringlist:
        s.append(bs)
    return s


if __name__=='__main__':
    print("Running bitstring module unit tests:")
    try:
        import test_bitstring
        test_bitstring.unittest.main(test_bitstring)
    except ImportError:
        print("Error: cannot find test_bitstring.py")
    