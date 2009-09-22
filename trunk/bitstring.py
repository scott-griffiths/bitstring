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

__version__ = "1.0.0"

__author__ = "Scott Griffiths"

import array
import copy
import string
import os
import struct
import re
import sys
import itertools

# Maximum number of digits to use in __str__ and __repr__.
_maxchars = 250

os.SEEK_SET = 0 # For backward compatibility with Python 2.4

def _single_byte_from_hex_string(h):
    """Return a byte equal to the input hex string."""
    try:
        i = int(h, 16)
        if i < 0:
            raise ValueError
    except ValueError:
        raise ValueError("Can't convert hex string to a single byte")
    if len(h) > 2:
        raise ValueError("Hex string can't be more than one byte in size")
    if len(h) == 2:
        return struct.pack('B', i)  
    elif len(h) == 1:
        return struct.pack('B', i<<4)

def _tidyupinputstring(s):
    """Return string made lowercase and with all whitespace removed."""
    s = string.join(s.split(), '').lower()
    return s
    
def _init_with_token(name, token_length, value):
    if token_length is not None:
        token_length = int(token_length)
    name = name.lower()
    if token_length == 0:
        return BitString()
    if name in ('0x', 'hex'):
        b = BitString(hex=value)
    elif name in ('0b', 'bin'):
        b = BitString(bin=value)
    elif name in ('0o', 'oct'):
        b = BitString(oct=value)
    elif name == 'se':
        b = BitString(se=int(value))
    elif name == 'ue':
        b = BitString(ue=int(value))
    elif name == 'uint':
        b = BitString(uint=int(value), length=token_length)
    elif name == 'int':
        b = BitString(int=int(value), length=token_length)
    elif name == 'uintbe':
        b = BitString(uintbe=int(value), length=token_length)
    elif name == 'intbe':
        b = BitString(intbe=int(value), length=token_length)
    elif name == 'uintle':
        b = BitString(uintle=int(value), length=token_length)
    elif name == 'intle':
        b = BitString(intle=int(value), length=token_length)
    elif name == 'uintne':
        b = BitString(uintne=int(value), length=token_length)
    elif name == 'intne':
        b = BitString(intne=int(value), length=token_length)
    elif name == 'bits':
        b = BitString(value)
    elif name == 'bytes':
        b = BitString(value)
        if b.length % 8 != 0:
            raise ValueError("'bytes' token must be given a whole byte value (bytes=%s)." % value)
    else:
        raise ValueError("Can't parse token name %s." % name)
    if token_length is not None and b.length != token_length:
        raise ValueError("Token with length %d packed with value of length %d (%s:%d=%s)." %
                         (token_length, b.length, name, token_length, value))
    return b


_init_names = ('uint', 'int', 'ue', 'se', 'hex', 'oct', 'bin', 'bits',
               'bytes', 'uintbe', 'intbe', 'uintle', 'intle', 'uintne', 'intne')

_init_names_ored = '|'.join(_init_names)
_tokenre = re.compile(r'^(?P<name>' + _init_names_ored + r')((:(?P<len1>[^=]+))|(:?(?P<len2>[\d]+)))?(=(?P<value>.*))?$', re.IGNORECASE)
_keyre = re.compile(r'^(?P<name>[^:=]+)$')

# Hex, oct or binary literals
_literalre = re.compile(r'^(?P<name>0(x|o|b))(?P<value>.+)', re.IGNORECASE)

# An endianness indicator followed by one or more struct.pack codes
_structpackre = re.compile(r'^(?P<endian><|>|@)(?P<format>(?:\d*[bBhHlLqQ])+)$')

# A number followed by a single character struct.pack code
_structsplitre = re.compile(r'\d*[bBhHlLqQ]')

# These replicate the struct.pack codes
# Big-endian
_replacements_be = {'b': 'intbe:8',  'B': 'uintbe:8',
                    'h': 'intbe:16', 'H': 'uintbe:16',
                    'l': 'intbe:32', 'L': 'uintbe:32',
                    'q': 'intbe:64', 'Q': 'uintbe:64'}
# Little-endian
_replacements_le = {'b': 'intle:8',  'B': 'uintle:8',
                    'h': 'intle:16', 'H': 'uintle:16',
                    'l': 'intle:32', 'L': 'uintle:32',
                    'q': 'intle:64', 'Q': 'uintle:64'}

def _tokenparser(format, keys=None):
    """Divide the format string into tokens and parse them.
    
    Return list of [initialiser, length, value]
    initialiser is one of: hex, oct, bin, uint, int, se, ue, 0x, 0o, 0b
    length is None if not known, as is value.
    
    If the token is in the keyword dictionary (keys) then it counts as a
    special case and isn't messed with.
    
    tokens must be of the form: initialiser[:][length][=value]
    
    """
    # Split tokens be ',' and remove whitespace
    tokens = (string.join(f.split(), '') for f in format.split(','))
    return_values = []
    new_tokens = []
    for token in tokens:
        # See if it's a struct-like format
        m = _structpackre.match(token)
        if m:
            # Split the format string into a list of 'q', '4h' etc.
            formatlist = re.findall(_structsplitre, m.group('format'))
            # Now deal with mulitplicative factors, 4h -> hhhh etc.
            format = []
            for f in formatlist:
                if len(f) != 1:
                    format.append(f[-1]*int(f[:-1]))
                else:
                    format.append(f)
            format = ''.join(format)
            endian = m.group('endian')
            if endian == '@':
                # Native endianness
                if sys.byteorder == 'little':
                    endian = '<'
                else:
                    assert sys.byteorder == 'big'
                    endian = '>'
            if endian == '<':
                new_tokens.append(_replacements_le[c] for c in format)
            else:
                assert endian == '>'
                new_tokens.append(_replacements_be[c] for c in format)
        else:
            new_tokens.append([token])

    for token in itertools.chain.from_iterable(new_tokens):
        if keys and token in keys:
            # Don't bother parsing it, it's part of a keyword argument
            return_values.append([token, None, None])
            continue
        value = length = None
        if token == '':
            continue
        # Match literal tokens of the form 0x... 0o... and 0b...
        m = _literalre.match(token)
        if m:
            name = m.group('name')
            value = m.group('value')
            return_values.append([name, length, value])
            continue
        # Match everything else!
        m = _tokenre.match(token)
        if m:
            name = m.group('name')
            if m.group('len1'):
                length = m.group('len1')
            if m.group('len2'):
                length = m.group('len2')
            if length and name == 'bytes':
                # Make the length unit bits, not bytes
                length = str(int(length)*8)
            if m.group('value'):
                value = m.group('value')
            return_values.append([name, length, value])
            continue
        # Try it as a key in a dictionary
        m = _keyre.match(token)
        if m:
            name = m.group('name')
            return_values.append([token, None, None])
            continue
        raise ValueError("Don't understand token '%s'." % token)
    return return_values
    
# Not pretty, but a byte to bitstring lookup really speeds things up.
_byte2bits = ('00000000', '00000001', '00000010', '00000011', '00000100', '00000101', '00000110', '00000111',
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
              '11111000', '11111001', '11111010', '11111011', '11111100', '11111101', '11111110', '11111111')

_oct2bits = ('000', '001', '010', '011', '100', '101', '110', '111')

class BitStringError(Exception):
    """For errors in the bitstring module."""

class _Array(object):
    
    def __init__(self):
        raise NotImplementedError
    
    def __copy__(self):
        raise NotImplementedError
    
    def __getitem__(self, key):
        """Return a slice of the raw bytes."""
        raise NotImplementedError

    def __setitem__(self, key, item):
        """Set a slice of the raw bytes."""
        raise NotImplementedError
    
    def appendbytes(self, data):
        """Append raw byte data."""
        raise NotImplementedError

    def appendarray(self, array):
        """Append another array to this one."""
        raise NotImplementedError
    
    def prependarray(self, array):
        """Prepend another array to this one."""
        raise NotImplementedError

    
class _FileArray(_Array):
    """A class that mimics the array.array type but gets data from a file object."""
    
    def __init__(self, source, bitlength, offset, byteoffset):
        # byteoffset - bytes to ignore at start of file
        # bitoffset - bits (0-7) to ignore after the byteoffset
        filelength = os.path.getsize(source.name)
        self.source = source
        if bitlength is None:
            self.bytelength = filelength - byteoffset
            bitlength = self.bytelength*8 - offset
        else:
            self.bytelength = (bitlength + offset + 7) // 8
        if self.bytelength > filelength - byteoffset:
            raise ValueError("File is not long enough for specified BitString length and offset.")
        self.byteoffset = byteoffset
        self.bitlength = bitlength
        self.offset = offset
    
    def __getitem__(self, key):
        try:
            # A slice
            start = self.byteoffset
            assert start >= 0
            if key.start is not None:
                start += key.start
            stop = self.bytelength + self.byteoffset
            if key.stop is not None:
                stop += key.stop - self.bytelength
            assert stop >= 0
            if start < stop:
                self.source.seek(start, os.SEEK_SET)
                return array.array('B', self.source.read(stop-start))
            else:
                return ''
        except AttributeError:
            # single element
            if key < 0:
                key += self.bytelength
            if key >= self.bytelength:
                raise IndexError
            key += self.byteoffset
            self.source.seek(key, os.SEEK_SET)
            return ord(self.source.read(1))


class _MemArray(_Array):
    """Stores raw bytes together with a bit offset and length."""
    
    def __init__(self, data, bitlength, offset):
        self._rawarray = array.array('B', data[offset // 8: (offset + bitlength + 7)//8])
        self.offset = offset % 8
        self.bitlength = bitlength
        assert (self.bitlength + self.offset + 7)//8 == len(self._rawarray)

    def __copy__(self):
        return _MemArray(self._rawarray, self.bitlength, self.offset)
    
    def __getitem__(self, key):
        return self._rawarray.__getitem__(key)

    def __setitem__(self, key, item):
        self._rawarray.__setitem__(key, item)
    
    def _getbytelength(self):
        return len(self._rawarray)
    
    def appendbytes(self, data):
        try:
            self._rawarray.extend(data)
        except TypeError:
            self._rawarray.append(data)
    
    def setoffset(self, newoffset):
        """Realign BitString with new offset to first bit."""
        if newoffset == self.offset:
            return
        if not 0 <= newoffset < 8:
            raise ValueError("Can only align to an offset from 0 to 7.")
        if newoffset < self.offset:
            # We need to shift everything left
            shiftleft = self.offset - newoffset
            # First deal with everything except for the final byte
            for x in xrange(self.bytelength - 1):
                self[x] = ((self[x] << shiftleft) & 255) + \
                                     (self[x + 1] >> (8 - shiftleft))
            # if we've shifted all of the data in the last byte then we need to truncate by 1
            bits_in_last_byte = (self.offset + self.bitlength) % 8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte <= shiftleft:
                # Remove the last byte
                self._rawarray.pop()
            # otherwise just shift the last byte
            else:
                self[-1] = (self[-1] << shiftleft) & 255
        else: # offset > self._offset
            shiftright = newoffset - self.offset
            # Give some overflow room for the last byte
            b = self.offset + self.bitlength + 7
            if (b + shiftright) // 8 > b // 8:
                self.appendbytes(0)
            for x in xrange(self.bytelength - 1, 0, -1):
                self[x] = ((self[x-1] << (8 - shiftright)) & 255) + \
                                     (self[x] >> shiftright)
            self[0] = self[0] >> shiftright
        self.offset = newoffset
    
    def appendarray(self, array):
        """Join another array on to the end of this one."""
        if array.bitlength == 0:
            return
        bits_in_final_byte = (self.offset + self.bitlength) % 8
        array.setoffset(bits_in_final_byte)
        if array.offset != 0:
            # first do the byte with the join.
            self[-1] = (self[-1] & (255 ^ (255 >> array.offset)) | \
                                   (array[0] & (255 >> array.offset)))
            self.appendbytes(array[1 : array.bytelength])
        else:
            self.appendbytes(array[0 : array.bytelength])
        self.bitlength += array.bitlength

    def prependarray(self, array):
        """Join another array on to the start of this one."""
        if array.bitlength == 0:
            return
        # Set the offset of copy of array so that it's final byte
        # ends in a position that matches the offset of self,
        # then join self on to the end of it.
        array = copy.copy(array)
        array.setoffset((self.offset - array.bitlength) % 8)
        assert (array.offset + array.bitlength) % 8 == self.offset
        if self.offset != 0:
            # first do the byte with the join.
            array[-1] = (array[-1] & (255 ^ (255 >> self.offset)) | \
                                   (self._rawarray[0] & (255 >> self.offset)))
            array.appendbytes(self._rawarray[1 : self.bytelength])
        else:
            array.appendbytes(self._rawarray[0 : self.bytelength])
        self._rawarray = array._rawarray
        self.offset = array.offset
        self.bitlength += array.bitlength

    def _getrawbytes(self):
        return self._rawarray.tostring()
        
    bytelength = property(_getbytelength)
    
    rawbytes = property(_getrawbytes)


class _CatArray(_Array):
    
    def __init__(self, array):
        self.arraylist = [array]
        
    def appendarray(self, array):
        #self.arraylist.append(array)
        self.arraylist[0].appendarray(array.arraylist[0])
    
    def prependarray(self, array):
        #self.arraylist.insert(0, array)
        self.arraylist[0].prependarray(array.arraylist[0])
        
    def __getitem__(self, key):
        self.flatten()
        return self.arraylist[0].__getitem__(key)
    
    def __setitem__(self, key, value):
        self.flatten()
        self.arraylist[0].__setitem__(key, value)
    
    def _getrawbytes(self):
        self.flatten()
        return self.arraylist[0].rawbytes
    
    def __copy__(self):
        return _CatArray(copy.copy(self.arraylist[0]))
    
    def setoffset(self, newoffset):
        self.arraylist[0].setoffset(newoffset)
    
    def _getoffset(self):
        return self.arraylist[0].offset
    
    def _getbitlength(self):
        return sum(a.bitlength for a in self.arraylist)
    
    def _getbytelength(self):
        return (self.bitlength + self.offset + 7) // 8
    
    def flatten(self):
        """Concatenate the arraylist items down to a single item."""
        a = self.arraylist[0]
        for b in self.arraylist[1:]:
            a.appendarray(b)
        self.arraylist = [a]
    
    rawbytes = property(_getrawbytes)
    offset = property(_getoffset)
    bitlength = property(_getbitlength)
    bytelength = property(_getbytelength)
    

class BitString(object):
    """A class for general bit-wise manipulations and interpretations."""

    def __init__(self, auto=None, length=None, offset=0, data=None,
                 filename=None, hex=None, bin=None, oct=None, uint=None,
                 int=None, uintbe=None, intbe=None, uintle=None, intle=None,
                 uintne=None, intne=None, ue=None, se=None):
        """
        Initialise the BitString with one (and only one) of:
        auto -- string of comma separated tokens, a list or tuple to be 
                interpreted as booleans, a file object or another BitString.
        data -- raw data as a string, for example read from a binary file.
        bin -- binary string representation, e.g. '0b001010'.
        hex -- hexadecimal string representation, e.g. '0x2ef'
        oct -- octal string representation, e.g. '0o777'.
        uint -- an unsigned integer (length must be supplied).
        int -- a signed integer (length must be supplied).
        uintbe -- an unsigned big-endian whole byte integer.
        intbe -- a signed big-endian whole byte integer.
        uintle -- an unsigned little-endian whole byte integer.
        intle -- a signed little-endian whole byte integer.
        uintne -- an unsigned native-endian whole byte integer.
        intne -- a signed native-endian whole byte integer.
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
        self._file = None
        self._mutable = True
        if length is not None and length < 0:
            raise ValueError("BitString length cannot be negative.")
        
        initialisers = [auto, data, filename, hex, bin, oct, int, uint, ue, se,
                        intbe, uintbe, intle, uintle, intne, uintne]
        if initialisers.count(None) == len(initialisers):
            # No initialisers, so initialise with nothing or zero bits
            if length is not None:
                data = '\x00' * ((length + 7) // 8)
                self._setdata(data, 0, length)
            else:
                self._setdata('', 0)
            return
        initfuncs = (self._setauto, self._setdata, self._setfile,
                     self._sethex, self._setbin, self._setoct,
                     self._setint, self._setuint, self._setue, self._setse,
                     self._setintbe, self._setuintbe, self._setintle,
                     self._setuintle, self._setintne, self._setuintne)
        assert len(initialisers) == len(initfuncs)
        if initialisers.count(None) < len(initialisers) - 1:
            raise BitStringError("You must only specify one initialiser when initialising the BitString.")
        if (se is not None or ue is not None) and length is not None:
            raise BitStringError("A length cannot be specified for an exponential-Golomb initialiser.")
        if (int or uint or intbe or uintbe or intle or uintle or intne or uintne or ue or se) and offset != 0:
            raise BitStringError("offset cannot be specified when initialising from an integer.")
        if offset < 0:
            raise ValueError("offset must be >= 0.")
        init = [(d, func) for (d, func) in zip(initialisers, initfuncs) if d is not None]
        assert len(init) == 1
        (d, func) = init[0]
        if d == filename:
            byteoffset, offset = divmod(offset, 8)
            func(d, offset, length, byteoffset)
        elif d in (se, ue):
            func(d)
        elif d in (int, uint, intbe, uintbe, intle, uintle, intne, uintne):
            func(d, length)
        else:
            func(d, offset, length)
        assert self._assertsanity()
        
    def __copy__(self):
        """Return a new copy of the BitString."""
        s_copy = BitString()
        s_copy._pos = self._pos
        if isinstance(self._datastore, _FileArray):
            # Let them both point to the same (invariant) file.
            # If either gets modified then at that point they'll be read into memory.
            s_copy._datastore = self._datastore
        else:
            s_copy._datastore = copy.copy(self._datastore)
        return s_copy

    def __add__(self, bs):
        """Concatenate BitStrings and return new BitString.
        
        bs -- the BitString to append.
        
        """
        s = self.__copy__()
        s.append(bs)
        s.bitpos = 0
        return s

    def __iadd__(self, bs):
        """Append bs to current BitString. Return self.
        
        bs -- the BitString to append.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use += on immutable BitString.")
        self.append(bs)
        return self
    
    def __radd__(self, bs):
        """Append current BitString to bs and return new BitString.
        
        bs -- the string for the 'auto' initialiser that will be appended to.
        
        """
        bs = self._converttobitstring(bs)
        return bs.__add__(self)

    def __setitem__(self, key, value):
        """Set item or range to new value.
        
        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.
        
        If the length of the BitString is changed then bitpos will be moved
        to after the inserted section, otherwise it will remain unchanged.
        
        >>> s = BitString('0xff')
        >>> s[0:1:4] = '0xe'
        >>> print s
        '0xef'
        >>> s[4:4] = '0x00'
        >>> print s
        '0xe00f'
        
        """
        if not self._mutable:
            raise TypeError("Cannot use __setitem__ on immutable BitString.")
        try:
            value = self._converttobitstring(value)
        except TypeError:
            if not isinstance(value, int):
                raise TypeError("BitString, int or string expected. Got %s." % type(value))
        try:
            # A slice
            start, step = 0, 1
            if key.step is not None:
                step = key.step
            if step == 0:
                stop = 0
            else:
                # default stop needs to be a multiple of step
                if key.stop is not None:
                    stop = self.length - (self.length % abs(step))
                else:
                    stop = self.length
            if key.start is not None:
                start = key.start * abs(step)
                if key.start < 0:
                    start += stop
                if start < 0:
                    start = 0
            if key.stop is not None:
                stop = key.stop * abs(step)
                if key.stop < 0:
                    stop += self.length - (self.length % abs(step))
            # Adjust start and stop if we're stepping backwards
            if step < 0:
                if key.start is None:
                    start = self.length + step
                if key.stop is None:
                    stop = step
                start, stop = stop - step, start - step
            if start > stop:
                if step == 1:
                    # The standard behaviour for lists is to just insert at the
                    # start position if stop < start and step == 1.
                    stop = start
                else:
                    # We have a step which takes us in the wrong direction,
                    # and will never get from start to stop.
                    raise ValueError("Attempt to assign to badly defined extended slice.")
            if isinstance(value, int):
                if value >= 0:
                    value = BitString(uint=value, length=stop - start)
                else:
                    value = BitString(int=value, length=stop - start)
            if (stop - start) == value.length:
                # This is an overwrite, so we retain the bitpos
                bitposafter = self._pos
                if step >= 0:
                    self.overwrite(value, start)
                else:
                    self.overwrite(value.__getitem__(slice(None, None, step)), start)
                self._pos = bitposafter
            else:
                self.deletebits(stop - start, start)
                if step >= 0:
                    self.insert(value, start)
                else:
                    self.insert(value.__getitem__(slice(None, None, step)), start)
                # bitpos is now after the inserted piece.
            return
        except AttributeError:
            # single element
            if isinstance(value, int):
                if value >= 0:
                    value = BitString(uint=value, length=1)
                else:
                    value = BitString(int=value, length=1)
            if key < 0:
                key += self.length
            if not 0 <= key < self.length:
                raise IndexError("Slice index out of range.")
            if value.length == 1:
                # This is an overwrite, so we retain the bitpos
                bitposafter = self._pos
                self.overwrite(value, key)
                self._pos = bitposafter
            else:
                self.deletebits(1, key)
                self.insert(value, key)
            return
    
    def __getitem__(self, key):
        """Return a new BitString representing a slice of the current BitString.
        
        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.
        
        >>> print BitString('0b00110')[1:4]
        '0b011'
        >>> print BitString('0x00112233')[1:3:8]
        '0x1122'
        
        """
        try:
            start, step = 0, 1
            if key.step is not None:
                step = key.step
            if step != 0:
                stop = self.length - (self.length % abs(step))
            else:
                stop = 0
            if key.start is not None:
                start = key.start * abs(step)
                if key.start < 0:
                    start += stop
            if key.stop is not None:
                stop = key.stop * abs(step)
                if key.stop < 0:
                    stop += self.length - (self.length % abs(step))
            start = max(start, 0)
            stop = min(stop, self.length - self.length % abs(step))
            # Adjust start and stop if we're stepping backwards
            if step < 0:
                # This compensates for negative indices being inclusive of the
                # final index rather than the first.
                if key.start is not None and key.start < 0:
                    start += step
                if key.stop is not None and key.stop < 0:
                    stop += step
                
                if key.start is None:
                    start = self.length - (self.length % abs(step)) + step
                if key.stop is None:
                    stop = step
                start, stop = stop - step, start - step
            if start < stop:
                if step >= 0:
                    return self._slice(start, stop)
                else:
                    # Negative step, so reverse the BitString in chunks of step.
                    bsl = [self._slice(x, x - step) for x in xrange(start, stop, -step)]
                    bsl.reverse()
                    return BitString().join(bsl)                    
            else:
                return BitString()
        except AttributeError:
            # single element
            if key < 0:
                key += self.length
            if not 0 <= key < self.length:
                raise IndexError("Slice index out of range.")
            return self._slice(key, key + 1)

    def __delitem__(self, key):
        """Delete item or range.
        
        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.
        
        After deletion bitpos will be moved to the deleted slice's position.
        
        >>> a = BitString('0x001122')
        >>> del a[1:2:8]
        >>> print a
        0x0022
        
        """
        if not self._mutable:
            raise TypeError("Cannot use __delitem__ on immutable BitString.")
        self.__setitem__(key, BitString())

    def __len__(self):
        """Return the length of the BitString in bits."""
        return self._getlength()

    def __str__(self):
        """Return approximate string representation of BitString for printing.
        
        Short strings will be given wholly in hexadecimal or binary. Longer
        strings may be part hexadecimal and part binary. Very long strings will
        be truncated with '...'.
        
        """
        length = self.length
        if length == 0:
            return ''
        if length > _maxchars*4:
            # Too long for hex. Truncate...
            return self[:_maxchars:4].hex + '...'
        # If it's quite short and we can't do hex then use bin
        if length < 32 and length % 4 != 0:
            return self.bin
        # First we do as much as we can in hex
        s = self[::4].hex
        if length % 4 != 0:
            # Add on 1, 2 or 3 bits at the end
            if s:
                s = s + ', '
            s = s + self[-(length % 4):].bin
        return s

    def __repr__(self):
        """Return representation that could be used to recreate the BitString.
        
        If the returned string is too long it will be truncated. See __str__().
        
        """
        length = self.length
        if isinstance(self._datastore, _FileArray):
            offsetstring = ''
            if self._datastore.byteoffset or self._offset:
                offsetstring = ", offset=%d" % (self._datastore.byteoffset * 8 + self._offset)
            lengthstring = ", length=%d" % length
            return "BitString(filename='%s'%s%s)" % (self._datastore.source.name,
                                                     lengthstring, offsetstring)
        else:
            s = self.__str__()
            lengthstring = ''
            if s[-3:] == '...':
                lengthstring = ", length=%d" % length
            return "BitString('%s'%s)" % (s, lengthstring)
            
    def __eq__(self, bs):
        """Return True if two BitStrings have the same binary representation.
        
        Can also be used with a string for the 'auto' initialiser.

        >>> BitString('0b1110') == '0xe'
        True
        
        """
        try:
            bs = self._converttobitstring(bs)
        except TypeError:
            return False
        if self.length != bs.length:
            return False
        # This could be made faster by exiting with False as early as possible.
        if self.tostring() != bs.tostring():
            return False
        else:
            return True
        
    def __ne__(self, bs):
        """Return False if two BitStrings have the same binary representation.
        
        Can also be used with a string for the 'auto' initialiser.
        
        >>> BitString('0b111') == '0x7'
        False
        
        """
        return not self.__eq__(bs)

    def __invert__(self):
        """Return BitString with every bit inverted.
        
        Raises BitStringError if the BitString is empty.
        
        """
        if self.empty():
            raise BitStringError("Cannot invert empty BitString.")
        s = BitString(int=~(self.int), length=self.length)
        return s

    def __lshift__(self, n):
        """Return BitString with bits shifted by n to the left.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if self.empty():
            raise ValueError("Cannot shift an empty BitString.")
        s = self[n:]
        s.append(BitString(length=min(n, self.length)))
        return s
    
    def __ilshift__(self, n):
        """Shift bits by n to the left in place. Return self.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use <<= on immutable BitString.")
        self.bin = self.__lshift__(n).bin
        return self

    def __rshift__(self, n):
        """Return BitString with bits shifted by n to the right.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if self.empty():
            raise ValueError("Cannot shift an empty BitString.")
        s = BitString(length=min(n, self.length))
        s.append(self[:-n])
        return s
    
    def __irshift__(self, n):
        """Shift bits by n to the right in place. Return self.
        
        n -- the number of bits to shift. Must be >= 0.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use >>= on immutable BitString.")
        self.bin = self.__rshift__(n).bin
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
        for i in xrange(n - 1):
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
        if not self._mutable:
            raise TypeError("Cannot use *= on immutable BitString.")
        if not isinstance(n, int):
            raise TypeError("Can only multiply a BitString by an int, but %s was provided." % type(n))
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        if n == 0:
            self._clear()
            return self
        s = BitString(self)
        for i in xrange(n - 1):
            self.append(s)
        return self

    def __and__(self, bs):
        """Bit-wise 'and' between two BitStrings. Returns new BitString.
        
        bs -- The BitString (or string for 'auto' initialiser) to & with.
        
        Raises ValueError if the two BitStrings have differing lengths.
        
        """
        bs = self._converttobitstring(bs)
        if self.length != bs.length:
            raise ValueError('BitStrings must have the same length for & operator.')
        return BitString(uint=self.uint & bs.uint, length=self.length)
    
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
        bs = self._converttobitstring(bs)
        if self.length != bs.length:
            raise ValueError('BitStrings must have the same length for | operator.')
        return BitString(uint=self.uint | bs.uint, length=self.length)

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
        bs = self._converttobitstring(bs)
        if self.length != bs.length:
            raise ValueError('BitStrings must have the same length for ^ operator.')
        return BitString(uint=self.uint ^ bs.uint, length=self.length)
    
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
        assert self.length >= 0
        assert 0 <= self._offset < 8
        if self.length == 0:
            assert self._datastore.bytelength == 0
            assert self._pos == 0
        else:
            assert 0 <= self._pos <= self.length
        assert (self.length + self._offset + 7) // 8 == self._datastore.bytelength
        return True

    def _clear(self):
        """Reset the BitString to an empty state."""
        self.data = ''
        self._pos = 0
    
    def _setauto(self, s, offset, length):
        """Set BitString from a BitString, file, list, tuple or string."""
        if isinstance(s, BitString):
            if length is None:
                length = s.length - offset
            if isinstance(s._datastore, _FileArray):
                byteoffset, bitoffset = divmod(s._datastore.offset + \
                                               s._datastore.byteoffset*8  + \
                                               offset, 8)
                self._datastore = _FileArray(s._datastore.source, length, bitoffset,
                                             byteoffset)
            else:
                self._setdata(s._datastore.rawbytes, s._offset + offset, length)
            return
        if isinstance(s, (list, tuple)):
            # Evaluate each item as True or False and set bits to 1 or 0.
            self._setbin(''.join([str(int(bool(x))) for x in s]), offset, length)
            return
        if isinstance(s, file):
            byteoffset, bitoffset = divmod(offset, 8)
            self._datastore = _FileArray(s, length, bitoffset, byteoffset)
            return
        if not isinstance(s, str):
            raise TypeError("Cannot initialise BitString from %s." % type(s))
        
        self._setdata('', 0)        
        tokens = _tokenparser(s)
        for token in tokens:
            self.append(_init_with_token(*token))

        # Finally we honour the offset and length
        self.truncatestart(offset)
        if length is not None:
            self.truncateend(self.length - length)
        
    def _setfile(self, filename, offset, lengthinbits=None, byteoffset=None):
        "Use file as source of bits."
        source = open(filename, 'rb')
        self._datastore = _FileArray(source, lengthinbits,
                                     offset, byteoffset)

    def _setdata(self, data, offset=0, length=None):
        """Set the data from a string."""
        if length is None:
            # Use to the end of the data
            length = (len(data) - (offset // 8)) * 8 - offset
            self._datastore = _CatArray(_MemArray(data, length, offset))
        else:
            if length + offset > len(data)*8:
                raise ValueError("Not enough data present. Need %d bits, have %d." % \
                                     (length + offset, len(data)*8))
            if length == 0:
                self._datastore = _CatArray(_MemArray('', 0, 0))
            else:
                self._datastore = _CatArray(_MemArray(data, length, offset))

    def _getdata(self):
        """Return the data as an ordinary string."""
        if self.length % 8 != 0:
            raise ValueError("Cannot convert to string unambiguously - not multiple of 8 bits.")
        return self.tostring()

    def _setuint(self, uint, length=None):
        """Reset the BitString to have given unsigned int interpretation."""
        if length is None and hasattr(self, "_datastore") and self.length != 0:
            length = self.length
        if length is None or length == 0:
            raise ValueError("A non-zero length must be specified with a uint initialiser.")
        if uint >= (1 << length):
            raise ValueError("uint %d is too large for a BitString of length %d." % (uint, length))  
        if uint < 0:
            raise ValueError("uint cannot be initialsed by a negative number.")     
        hexstring = hex(uint)[2:]
        if hexstring[-1] == 'L':
            hexstring = hexstring[:-1]
        hexlengthneeded = (length + 3) // 4
        leadingzeros = hexlengthneeded - len(hexstring)
        if leadingzeros > 0:
            hexstring = '0'*leadingzeros + hexstring
        offset = (4*hexlengthneeded) - length
        self._sethex(hexstring, offset)
        
    def _getuint(self):
        """Return data as an unsigned int."""
        if self.empty():
            raise ValueError("An empty BitString cannot be interpreted as an integer.")
        # Special case if the datastore is only one byte long.
        if self._datastore.bytelength == 1:
            mask = ((1 << self.length) - 1) << (8 - self.length - self._offset)
            val = self._datastore[0] & mask
            val >>= 8 - self._offset - self.length
            return val
        # Take the bits in the first byte and shift them to their final position
        firstbits = 8 - self._offset
        mask = (1 << firstbits) - 1
        shift = self.length - firstbits
        val = (self._datastore[0] & mask) << shift
        # For the middle of the data we use struct.unpack to do the conversion
        # as it's more efficient. This loop only gets invoked if the BitString's
        # data is more than 10 bytes.
        j = 1
        structsize = struct.calcsize('Q')
        end = self._datastore.bytelength - 1
        while j + structsize < end:
            shift -= 8*structsize
            # Convert next 8 bytes to an int, then shift it to proper place
            # and add it
            d = self._datastore[j:j + structsize].tostring()
            val += (struct.unpack('>Q', d)[0] << shift)
            j += structsize
        # Do the remaining bytes, except for the final one
        while j < end:
            shift -= 8
            val += (self._datastore[j] << shift)
            j += 1
        # And the very final byte
        assert shift <= 8
        bitsleft = (self._offset + self.length) % 8
        if bitsleft == 0:
            bitsleft = 8
        lastbyte = self._datastore[-1]
        mask = 255 - ((1 << (8 - bitsleft)) - 1)
        val += (lastbyte & mask) >> (8 - bitsleft)
        return val

    def _setint(self, int, length=None):
        """Reset the BitString to have given signed int interpretation."""
        # TODO: This next line is pretty hacky. Either rewrite or comment.
        if length is None and hasattr(self, "_datastore") and self.length != 0:
            length = self.length
        if length is None or length == 0:
            raise ValueError("A non-zero length must be specified with an int initialiser.")
        if int >=  (1 << (length - 1)) or int < -(1 << (length - 1)):
            raise ValueError("int %d is too large for a BitString of length %d." % (int, length))   
        if int < 0:
            # the two's complement thing to get the equivalent +ive number
            int = (-int - 1)^((1 << length) - 1)
        self._setuint(int, length)

    def _getint(self):
        """Return data as a two's complement signed int."""
        ui = self.uint
        if ui < (1 << (self.length - 1)):
            # Top bit not set - must be positive
            return ui
        tmp = (~(ui - 1)) & ((1 << self.length) - 1)
        return -tmp

    def _setuintbe(self, uint, length=None):
        if length is not None and length % 8 != 0:
            raise ValueError("Big-endian integers must be whole-byte. Length = %d bits." % length)
        self._setuint(uint, length)
    
    def _getuintbe(self):
        if self.length % 8 != 0:
            raise ValueError("Big-endian integers must be whole-byte. Length = %d bits." % self.length)
        return self._getuint()
    
    def _setintbe(self, int, length=None):
        if length is not None and length % 8 != 0:
            raise ValueError("Big-endian integers must be whole-byte. Length = %d bits." % length)
        self._setint(int, length)
    
    def _getintbe(self):
        if self.length % 8 != 0:
            raise ValueError("Big-endian integers must be whole-byte. Length = %d bits." % self.length)
        return self._getint()
     
    def _setuintle(self, uint, length=None):
        if length is not None and length % 8 != 0:
            raise ValueError("Little-endian integers must be whole-byte. Length = %d bits." % length)
        self._setuint(uint, length)
        self.reversebytes()
    
    def _getuintle(self):
        if self.length % 8 != 0:
            raise ValueError("Little-endian integers must be whole-byte. Length = %d bits." % self.length)
        return self[::-8]._getuint()
    
    def _setintle(self, int, length=None):
        if length is not None and length % 8 != 0:
            raise ValueError("Little-endian integers must be whole-byte. Length = %d bits." % length)
        self._setint(int, length)
        self.reversebytes()
    
    def _getintle(self):
        if self.length % 8 != 0:
            raise ValueError("Little-endian integers must be whole-byte. Length = %d bits." % self.length)
        return self[::-8]._getint()
        
    def _setintne(self, int, length=None):
        if sys.byteorder == 'little':
            self._setintle(int, length)
        else:
            self._setintbe(int, length)
    
    def _getintne(self):
        if sys.byteorder == 'little':
            return self._getintle()
        else:
            return self._getintbe()

    def _setuintne(self, uint, length=None):
        if sys.byteorder == 'little':
            self._setuintle(uint, length)
        else:
            self._setuintbe(uint, length)
    
    def _getuintne(self):
        if sys.byteorder == 'little':
            return self._getuintle()
        else:
            return self._getuintbe()
        
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
        self.bin = binstring

    def _getue(self):
        """Return data as unsigned exponential-Golomb code.
        
        Raises BitStringError if BitString is not a single exponential-Golomb code.
        
        """
        oldpos = self._pos
        self._pos = 0
        try:
            value = self._readue()
            if self._pos != self.length:
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
        self.ue = u

    def _getse(self):
        """Return data as signed exponential-Golomb code.
        
        Raises BitStringError if BitString is not a single exponential-Golomb code.
                
        """
        oldpos= self._pos
        self._pos = 0
        try:
            value = self._readse()
            if value is None or self._pos != self.length:
                raise BitStringError
        except BitStringError:
            self._pos = oldpos
            raise BitStringError("BitString is not a single exponential-Golomb code.")
        self._pos = oldpos
        return value
    
    def _setbin(self, binstring, offset=0, length=None):
        """Reset the BitString to the value given in binstring."""
        binstring = _tidyupinputstring(binstring)
        # remove any 0b if present
        binstring = binstring.replace('0b', '')
        if length is None:
            length = length or len(binstring) - offset
        if length < 0 or length > (len(binstring) - offset):
            raise ValueError("Invalid length of binary string. String %s, length %d, offset %d." % (binstring, length, offset))
        if length == 0:
            self._clear()
            return
        # Truncate the bin_string if needed
        binstring = binstring[offset:length + offset]
        # pad with zeros up to byte boundary if needed
        boundary = ((length + 7) // 8) * 8
        if len(binstring) < boundary:
            padded_binstring = binstring + '0'*(boundary - length)
        else:
            padded_binstring = binstring
        try:
            bytes = [int(padded_binstring[x:x + 8], 2) for x in xrange(0, len(padded_binstring), 8)]
        except ValueError:
            raise ValueError("Invalid character in bin initialiser %s." % binstring)
        self._datastore = _CatArray(_MemArray(bytes, length, 0))

    def _getbin(self):
        """Return interpretation as a binary string."""
        if self.length == 0:
            return ''
        # Use lookup table to convert each byte to string of 8 bits.
        c = (_byte2bits[x] for x in self._datastore)
        return '0b' + ''.join(c)[self._offset:self._offset + self.length]

    def _setoct(self, octstring, offset=0, length=None):
        """Reset the BitString to have the value given in octstring."""
        octstring = _tidyupinputstring(octstring)
        # remove any 0o if present
        octstring = octstring.replace('0o', '')
        if length is None:
            length = len(octstring)*3 - offset
        if length < 0 or length + offset > len(octstring) * 3:
            raise ValueError("Invalid length %s, offset %d for oct initialiser %s" % (length, offset, octstring))
        if length == 0:
            self._clear()
            return
        octstring = octstring[offset // 3:(length + offset + 2) // 3]
        offset %= 3
        binlist = []
        for i in octstring:
            try:
                if not 0 <= int(i) < 8:
                    raise ValueError
                binlist.append(_oct2bits[int(i)])
            except ValueError:
                raise ValueError("Invalid symbol '%s' in oct initialiser." % i)
        self._setbin(''.join(binlist), offset=offset, length=length)

    def _getoct(self):
        """Return interpretation as an octal string."""
        if self.length % 3 != 0:
            raise ValueError("Cannot convert to octal unambiguously - not multiple of 3 bits.")
        if self.length == 0:
            return ''
        oldbitpos = self._pos
        self._pos = 0
        octlist = ['0o']
        # TODO: This is very slow.
        for i in xrange(self.length // 3):
            octlist.append(str(self.readbits(3).uint))
        self._pos = oldbitpos
        return ''.join(octlist)
    
    def _sethex(self, hexstring, offset=0, length=None):
        """Reset the BitString to have the value given in hexstring."""
        hexstring = _tidyupinputstring(hexstring)
        # remove any 0x if present
        hexstring = hexstring.replace('0x', '')
        if length is None:
            length = len(hexstring)*4 - offset
        if length < 0 or length + offset > len(hexstring)*4:
            raise ValueError("Invalid length %d, offset %d for hexstring 0x%s." % (length, offset, hexstring))
        if length == 0:
            self._clear()
            return
        hexstring = hexstring[offset // 4:(length + offset + 3) // 4]
        offset %= 4
        hexlist = []
        # First do the whole bytes
        for i in xrange(len(hexstring) // 2):
            try:
                j = int(hexstring[i*2:i*2 + 2], 16) 
                hexlist.append(_single_byte_from_hex_string(hexstring[i*2:i*2 + 2]))
            except ValueError:
                raise ValueError("Invalid symbol in hex initialiser.")
        # then any remaining nibble
        if len(hexstring) % 2 == 1:
            try:
                j = int(hexstring[-1], 16)
                hexlist.append(_single_byte_from_hex_string(hexstring[-1]))
            except ValueError:
                raise ValueError("Invalid symbol in hex initialiser.")
        self._datastore = _CatArray(_MemArray(''.join(hexlist), length, offset))

    def _gethex(self):
        """Return the hexadecimal representation as a string prefixed with '0x'.
        
        Raises a ValueError if the BitString's length is not a multiple of 4.
        
        """        
        if self.length % 4 != 0:
            raise ValueError("Cannot convert to hex unambiguously - not multiple of 4 bits.")
        if self.length == 0:
            return ''
        s = '0x' + self.tostring().encode('hex')
        if (self.length // 4) % 2 == 1:
            return s[:-1]
        else:
            return s

    def _setbytepos(self, bytepos):
        """Move to absolute byte-aligned position in stream."""
        self._setbitpos(bytepos*8)

    def _getbytepos(self):
        """Return the current position in the stream in bytes. Must be byte aligned."""
        if self._pos % 8 != 0:
            raise BitStringError("Not byte aligned in _getbytepos().")
        return self._pos // 8

    def _setbitpos(self, bitpos):
        """Move to absolute postion bit in bitstream."""
        if bitpos < 0:
            raise ValueError("Bit position cannot be negative.")
        if bitpos > self.length:
            raise ValueError("Cannot seek past the end of the data.")
        self._pos = bitpos

    def _getbitpos(self):
        """Return the current position in the stream in bits."""
        return self._pos
    
    def _getoffset(self):
        return self._datastore.offset

    def _getlength(self):
        """Return the length of the BitString in bits."""
        return self._datastore.bitlength
    
    def _ensureinmemory(self):
        """Ensure the data is held in memory, not in a file."""
        if isinstance(self._datastore, _FileArray):
            self._datastore = _CatArray(_MemArray(self._datastore[:],
                                                  self.length, self._offset))
    
    def _converttobitstring(self, bs):
        """Attemp to convert bs to a BitString and return it."""
        if isinstance(bs, BitString):
            return bs
        if isinstance(bs, (str, list, tuple)):
            return BitString(bs)
        raise TypeError("Cannot initialise BitString from %s." % type(bs))

    def _slice(self, startbit, endbit):
        """Used internally to get a slice, without error checking."""
        if endbit == startbit:
            return BitString()
        startbyte, newoffset = divmod(startbit + self._offset, 8)
        endbyte = (endbit + self._offset - 1) // 8
        return BitString(data=self._datastore[startbyte:endbyte + 1],
                         length=endbit - startbit,
                         offset=newoffset)

    def _readue(self):
        """Return interpretation of next bits as unsigned exponential-Golomb code.
           
        Advances position to after the read code.
        
        Raises BitStringError if the end of the BitString is encountered while
        reading the code.
        
        """
        oldpos = self._pos
        foundone = self.find('0b1', self._pos)
        if not foundone:
            self._pos = self.length
            raise BitStringError("Read off end of BitString trying to read code.")
        leadingzeros = self._pos - oldpos
        codenum = (1 << leadingzeros) - 1
        if leadingzeros > 0:
            restofcode = self.readbits(leadingzeros + 1)
            if restofcode.length != leadingzeros + 1:
                raise BitStringError("Read off end of BitString trying to read code.")
            codenum += restofcode[1:].uint
        else:
            assert codenum == 0
            self._pos += 1
        return codenum

    def _readse(self):
        """Return interpretation of next bits as a signed exponential-Golomb code.
        
        Advances position to after the read code.
        
        Raises BitStringError if the end of the BitString is encountered while
        reading the code.
        
        """
        codenum = self._readue()
        m = (codenum + 1) // 2
        if codenum % 2 == 0:
            return -m
        else:
            return m

    def _readtoken(self, name, length, value):
        """Reads a token from the BitString and returns the result."""
        if length is not None:
            length = int(length)
        name = name.lower()
        if name in ('uint', 'int', 'intbe', 'uintbe', 'intle', 'uintle',
                    'intne', 'uintne', 'hex', 'oct', 'bin'):
            return getattr(self.readbits(length), name)
        if name in ('bits', 'bytes'):
            return self.readbits(length)
        if name == 'ue':
            return self._readue()
        if name == 'se':
            return self._readse()
        else:
            raise ValueError("Can't parse token %s:%d" % (name, length))
        
    def empty(self):
        """Return True if the BitString is empty (has zero length)."""
        return self.length == 0
    
    def unpack(self, *format):
        """Interpret the whole BitString using format and return result.
        
        format - One or more strings with comma separated tokens describing
                 how to interpret the bits in the BitString.
        
        If only one token is present then a single object is returned,
        otherwise a list is returned.
        
        Raises ValueError if the format is not understood.
        
        See the docstring for 'read' for more information.
        
        """
        bitposbefore = self._pos
        self._pos = 0
        return_values = self.read(*format)
        self._pos = bitposbefore
        return return_values

    def read(self, *format):
        """Interpret next bits according to format string(s) and return result.
        
        format -- One or more strings with comma separated tokens describing
                  how to interpret the next bits in the BitString.
                
        If only one token is present then a single object is returned,
        otherwise a list is returned.
        
        The position in the BitString is advanced to after the read items.
        
        Raises ValueError if the format is not understood.
        
        Token examples: 'int:12'  : 12 bits as a signed integer
                        'uint:8'  : 8 bits as an unsigned integer
                        'hex:80'  : 80 bits as a hex string
                        'oct:9'   : 9 bits as an octal string
                        'bin:1'   : single bit binary string
                        'ue'      : next bits as unsigned exp-Golomb code
                        'se'      : next bits as signed exp-Golomb code
                        'bits:5'  : 5 bits as a BitString object
                        'bytes:3' : 3 bytes as a BitString object
                
        >>> h, b1, b2 = s.read('hex:20, bin:5, bin:3')
        >>> i, bs1, bs2 = s.read('uint:12', 'bits:10', 'bits:10')
        
        """
        tokens = []
        for f_item in format:
            tokens.extend(_tokenparser(f_item))

        # Scan tokens to see if one has no length
        bits_after_stretchy_token = 0
        stretchy_token = None
        for token in tokens:
            if token[1] is not None:
                token[1] = int(token[1])
            name, length, value = token
            if stretchy_token:
                if name in ('se', 'ue'):
                    raise BitStringError("It's not possible to parse a variable length token after a 'filler' token.")
                else:
                    bits_after_stretchy_token += length
            if length is None and value is None and name not in ('se', 'ue'):
                if stretchy_token:
                    raise BitStringError("It's not possible to have more than one 'filler' token.")
                stretchy_token = token
                
        bits_left = self.length - self.bitpos
        return_values = []
        for token in tokens:
            if token is stretchy_token:
                # Set length to the remaining bits
                token[1] = max(bits_left - bits_after_stretchy_token, 0)
            if token[1] is not None:
                bits_left -= token[1]
            return_values.append(self._readtoken(*token))            
        if len(return_values) == 1:
            return return_values[0]
        return return_values
    
    def readbit(self):
        """Return next bit in BitString as new BitString and advance position.
        
        Returns empty BitString if bitpos is at the end of the BitString.
        
        """
        return self.readbits(1)

    def readbits(self, *bits):
        """Return next bits in BitString as new BitString(s) and advance position.
        
        bits -- The number of bits to read. If more than one bit length is
                given a list of BitStrings will be returned.
        
        If not enough bits are available then all remaining will be returned.
        
        Raises ValueError if bits < 0.
        
        """
        return_values = []
        for b in bits:
            if b < 0:
                raise ValueError("Cannot read negative amount.")
            b = min(b, self.length - self._pos)
            startbyte, newoffset = divmod(self._pos + self._offset, 8)
            endbyte = (self._pos + self._offset + b - 1) // 8
            self._pos += b
            bs = BitString(data=self._datastore[startbyte:endbyte + 1],
                           length=b, offset=newoffset)
            return_values.append(bs)
        if len(return_values) == 1:
            return return_values[0]
        return return_values
    
    def readbyte(self):
        """Return next byte as a new BitString and advance position.
        
        Does not byte align.
        
        If not enough bits are available then all will be returned.
        
        """
        return self.readbits(8)

    def readbytes(self, *bytes):
        """Return next bytes as new BitString(s) and advance position.
        
        bytes -- The number of bytes to read. If more than one byte length is
                 given a list of BitStrings will be returned.
        
        Does not byte align.
        If not enough bits are available then all remaining will be returned.
        
        """
        return self.readbits(*[b*8 for b in bytes])
    
    def peek(self, *format):
        """Interpret next bits according to format string(s) and return result.
        
        format -- One or more strings with comma separated tokens describing
                  how to interpret the next bits in the BitString.
                  
        If only one token is present then a single object is returned,
        otherwise a list is returned.
        The position in the BitString is not changed.
        
        See the docstring for 'read' for more information.
        
        """
        bitpos = self._pos
        return_values = self.read(*format)
        self._pos = bitpos
        return return_values

    def peekbit(self):
        """Return next bit as a new BitString without advancing position.
        
        Returns empty BitString if bitpos is at the end of the BitString.
        
        """
        return self.peekbits(1)

    def peekbits(self, *bits):
        """Return next bits as new BitString(s) without advancing position.
        
        bits -- The number of bits to read. If more than one bit length is
                given a list of BitStrings will be returned.
        
        If not enough bits are available then all remaining will be returned.
        
        Raises ValueError if bits < 0.
        
        """
        bitpos = self._pos
        s = self.readbits(*bits)
        self._pos = bitpos
        return s
    
    def peekbyte(self):
        """Return next byte as a new BitString without advancing position.
        
        If not enough bits are available then all will be returned.
        
        """
        return self.peekbits(8)

    def peekbytes(self, *bytes):
        """Return next bytes as new BitString(s) without advancing position.
        
        bytes -- The number of bytes to read. If more than one byte length is
                 given a list of BitStrings will be returned.
                     
        If not enough bits are available then all remaining will be returned.
        
        """
        return self.peekbits(*[b*8 for b in bytes])

    def advancebit(self):
        """Advance position by one bit.
        
        Raises ValueError if bitpos is past the last bit in the BitString.
        
        """
        self.bitpos += 1

    def advancebits(self, bits):
        """Advance position by bits.
        
        bits -- Number of bits to increment bitpos by. Must be >= 0.
        
        Raises ValueError if bits is negative or if bitpos goes past the end
        of the BitString.
        
        """
        if bits < 0:
            raise ValueError("Cannot advance by a negative amount.")
        self.bitpos += bits

    def advancebyte(self):
        """Advance position by one byte. Does not byte align.
        
        Raises ValueError if there is less than one byte from bitpos to
        the end of the BitString.
        
        """
        self.bitpos += 8

    def advancebytes(self, bytes):
        """Advance position by bytes. Does not byte align.
        
        bytes -- Number of bytes to increment bitpos by. Must be >= 0.
        
        Raises ValueError if there are not enough bytes from bitpos to
        the end of the BitString.
        
        """
        if bytes < 0:
            raise ValueError("Cannot advance by a negative amount.")
        self.bitpos += bytes*8

    def retreatbit(self):
        """Retreat position by one bit.
        
        Raises ValueError if bitpos is already at the start of the BitString.
        
        """
        self.bitpos -= 1
 
    def retreatbits(self, bits):
        """Retreat position by bits.
        
        bits -- Number of bits to decrement bitpos by. Must be >= 0.
        
        Raises ValueError if bits negative or if bitpos goes past the start
        of the BitString.
        
        """
        if bits < 0:
            raise ValueError("Cannot retreat by a negative amount.")
        self.bitpos -= bits

    def retreatbyte(self):
        """Retreat position by one byte. Does not byte align.
        
        Raises ValueError if bitpos is less than 8.
        
        """
        self.bitpos -= 8

    def retreatbytes(self, bytes):
        """Retreat position by bytes. Does not byte align.
        
        bytes -- Number of bytes to decrement bitpos by. Must be >= 0.
        
        Raises ValueError if bytes negative or if bitpos goes past the start
        of the BitString.
        
        """
        if bytes < 0:
            raise ValueError("Cannot retreat by a negative amount.")
        self.bitpos -= bytes*8

    def seekbit(self, bitpos):
        """Seek to absolute bit position bitpos.
        
        Raises ValueError if bitpos < 0 or bitpos > self.length.
        
        """
        self.bitpos = bitpos
    
    def seekbyte(self, bytepos):
        """Seek to absolute byte position bytepos.
        
        Raises ValueError if bytepos < 0 or bytepos*8 > self.length.
        
        """
        self.bytepos = bytepos
    
    def tellbit(self):
        """Return current position in the BitString in bits (bitpos)."""
        return self.bitpos
    
    def tellbyte(self):
        """Return current position in the BitString in bytes (bytepos).
        
        Raises BitStringError if position is not byte-aligned.
        
        """
        return self.bytepos

    def find(self, bs, startbit=None, endbit=None, bytealigned=False):
        """Seek to start of next occurence of bs. Return True if string is found.
        
        bs -- The BitString to find.
        startbit -- The bit position to start the search.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to search.
                  Defaults to self.length.
        bytealigned -- If True the BitString will only be
                       found on byte boundaries.
        
        Raises ValueError if bs is empty, if startbit < 0,
        if endbit > self.length or if endbit < startbit.
        
        """
        bs = self._converttobitstring(bs)
        if bs.empty():
            raise ValueError("Cannot find an empty BitString.")
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        if startbit < 0:
            raise ValueError("Cannot find - startbit must be >= 0.")
        if endbit > self.length:
            raise ValueError("Cannot find - endbit is past the end of the BitString.")
        if endbit < startbit:
            raise ValueError("endbit must not be less than startbit.")
        # If everything's byte aligned (and whole-byte) then use the quick algorithm.
        if bytealigned and len(bs) % 8 == 0 and self._datastore.offset == 0:
            # Extract data bytes from BitString to be found.
            d = bs.data
            oldpos = self._pos
            self._pos = startbit
            self.bytealign()
            bytepos = self._pos // 8
            found = False
            p = bytepos
            finalpos = endbit // 8
            increment = max(1024, len(d)*10)
            buffersize = increment + len(d)
            while p < finalpos:
                # Read in file or from memory in overlapping chunks and search the chunks.
                buf = self._datastore[p:min(p + buffersize, finalpos)].tostring()
                pos = buf.find(d)
                if pos != -1:
                    found = True
                    p += pos
                    break
                p += increment
            if not found:
                self._pos = oldpos
                return False
            self.bytepos = p
            return True
        else:
            oldpos = self._pos
            targetbin = bs._getbin()[2:]
            found = False
            p = startbit
            # We grab overlapping chunks of the binary representation and
            # do an ordinary string search within that.
            increment = max(16384, bs.length*10)
            buffersize = increment + bs.length
            while p < endbit:
                buf = self[p:min(p+buffersize, endbit)]._getbin()[2:]
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
                return False
            self._pos = p
            return True

    def findall(self, bs, startbit=None, endbit=None, count=None,
                bytealigned=False):
        """Find all occurences of bs. Return generator of bit positions.
        
        bs -- The BitString to find.
        startbit -- The bit position to start the search.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to search.
                  Defaults to self.length.
        count -- The maximum number of occurences to find.
        bytealigned -- If True the BitString will only be found on
                       byte boundaries.
        
        Raises ValueError if bs is empty, if startbit < 0,
        if endbit > self.length or if endbit < startbit.
        
        Note that all occurences of bs are found, even if they overlap.
        
        """
        if count is not None and count < 0:
            raise ValueError("In findall, count must be >= 0.")
        bs = self._converttobitstring(bs)
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        c = 0
        # Can rely on find() for parameter checking
        while self.find(bs, startbit, endbit, bytealigned):
            if count is not None and c >= count:
                return
            c += 1
            yield self._pos
            if bytealigned:
                startbit = self._pos + 8
            else:
                startbit = self._pos + 1
            if startbit >= endbit:
                break
        return
    
    def rfind(self, bs, startbit=None, endbit=None, bytealigned=False):
        """Seek backwards to start of previous occurence of bs.
        
        Return True if string is found.
        
        bs -- The BitString to find.
        startbit -- The bit position to end the reverse search.
                    Defaults to 0.
        endbit -- The bit position one past the first bit to reverse search.
                  Defaults to self.length.
        bytealigned -- If True the BitString will only be found on byte 
                       boundaries.
        
        Raises ValueError if bs is empty, if startbit < 0,
        if endbit > self.length or if endbit < startbit.
        
        """
        bs = self._converttobitstring(bs)
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        if bs.empty():
            raise ValueError("Cannot find an empty BitString.")
        # Search chunks starting near the end and then moving back
        # until we find bs.
        increment = max(8192, bs.length*80)
        buffersize = min(increment + bs.length, endbit - startbit)
        pos = max(startbit, endbit - buffersize)
        while(True):
            found = list(self.findall(bs, startbit=pos, endbit=pos + buffersize,
                                      bytealigned=bytealigned))
            if not found:
                if pos == startbit:
                    return False
                pos = max(startbit, pos - increment)
                continue
            self._pos = found[-1]
            return True
    
    def replace(self, old, new, startbit=None, endbit=None, count=None,
                bytealigned=False):
        """Replace all occurrences of old with new in place.
        
        Returns number of replacements made.
        
        old -- The BitString to replace.
        new -- The replacement BitString.
        startbit -- Any occurences that start before starbit will not
                    be replaced. Defaults to 0.
        endbit -- Any occurences that finish after endbit will not
                  be replaced. Defaults to self.length.
        count -- The maximum number of replacements to make. Defaults to
                 replace all occurences.
        bytealigned -- If True replacements will only be made on byte
                       boundaries.
        
        Raises ValueError if old is empty or if startbit or endbit are
        out of range.
        
        """        
        if not self._mutable:
            raise TypeError("Cannot use replace on immutable BitString.")
        old = self._converttobitstring(old)
        new = self._converttobitstring(new)
        if old.empty():
            raise ValueError("Empty BitString cannot be replaced.")
        newpos = self._pos
        # Adjust count for use in split()
        if count is not None:
            count += 1
        sections = self.split(old, startbit, endbit, count, bytealigned)
        lengths = [s.length for s in sections]
        if len(lengths) == 1:
            # Didn't find anything to replace.
            self._pos = newpos
            return 0 # no replacements done
        if new is self:
            # Prevent self assignment woes
            new = copy.copy(self)
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
        self.bitpos = self._pos + self._offset + skipped
        assert self._assertsanity()
        return skipped

    def truncatestart(self, bits):
        """Truncate bits from the start of the BitString.
        
        bits -- Number of bits to remove from start of the BitString.
        
        Raises ValueError if bits < 0 or bits > self.length.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use truncatestart on immutable BitString.")
        if bits == 0:
            return self
        if bits < 0 or bits > self.length:
            raise ValueError("Truncation length of %d not possible. Length = %d."
                             % (bits, self.length))
        if bits == self.length:
            self._clear()
            return self
        offset = (self._offset + bits) % 8
        self._setdata(self._datastore[bits // 8:], offset, length=self.length - bits)
        self._pos = max(0, self._pos - bits)
        assert self._assertsanity()
        return

    def truncateend(self, bits):
        """Truncate bits from the end of the BitString.
        
        bits -- Number of bits to remove from end of the BitString.
        
        Raises ValueError if bits < 0 or bits > self.length.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use truncateend on immutable BitString.")
        if bits == 0:
            return self
        if bits < 0 or bits > self.length:
            raise ValueError("Truncation length of %d bits not possible. Length = %d."
                             % (bits, self.length))
        if bits == self.length:
            self._clear()
            return self
        newlength_in_bytes = (self._offset + self.length - bits + 7) // 8
        # Ensure that the position is still valid
        self._pos = max(0, min(self._pos, self.length - bits))
        self._setdata(self._datastore[:newlength_in_bytes], offset=self._offset,
                      length=self.length - bits)
        assert self._assertsanity()
        return
    
    def slice(self, startbit=None, endbit=None, step=None):
        """Return a new BitString which is the slice [startbit:endbit:step].
        
        startbit -- Position of first bit in the new BitString. Defaults to 0.
        endbit -- One past the position of the last bit in the new BitString.
                  Defaults to self.length.
        step -- Multiplicative factor for startbit and endbit. Defaults to 1.
        
        Has the same semantics as __getitem__.
        
        """
        return self.__getitem__(slice(startbit, endbit, step))
    
    def insert(self, bs, bitpos=None):
        """Insert bs at current position, or bitpos if supplied.
        
        bs -- The BitString to insert.
        bitpos -- The bit position to insert the BitString
                  Defaults to self.bitpos.
        
        After insertion self.bitpos will be immediately after the inserted bits.
        Raises ValueError if bitpos < 0 or bitpos > self.length.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use insert on immutable BitString.")
        bs = self._converttobitstring(bs)
        if bs.empty():
            return self
        if bs is self:
            bs = self.__copy__()
        if bitpos is None:
            bitpos = self._pos
        if bitpos < 0 or bitpos > self.length:
            raise ValueError("Invalid insert position.")            
        end = self._slice(bitpos, self.length)
        self.truncateend(self.length - bitpos)
        self.append(bs)
        self.append(end)
        self._pos = bitpos + bs.length
        assert self._assertsanity()
        return

    def overwrite(self, bs, bitpos=None):
        """Overwrite with bs at current position, or bitpos if given.
        
        bs -- The BitString to overwrite with.
        bitpos -- The bit position to begin overwriting from.
                  Defaults to self.bitpos.
                  
        After overwriting self.bitpos will be immediately after the new bits.
        Raises ValueError if bitpos < 0 or bitpos + bs.length > self.length
        
        """
        if not self._mutable:
            raise TypeError("Cannot use overwrite on immutable BitString.")
        bs = self._converttobitstring(bs)
        if bs.empty():
            return self
        if bs is self:
            bs = self.__copy__()
        if bitpos is None:
            bitpos = self._pos
        bitposafter = bitpos + bs.length
        if bitpos < 0 or bitpos + bs.length > self.length:
            raise ValueError("Overwrite exceeds boundary of BitString.")
        self._ensureinmemory()
        bs._ensureinmemory()
        
        firstbytepos = (self._offset + bitpos) // 8
        lastbytepos = (self._offset + bitpos + bs.length - 1) // 8
        bytepos, bitoffset = divmod(self._offset + bitpos, 8)
        if firstbytepos == lastbytepos:    
            mask = ((1 << bs.length) - 1) << (8 - bs.length - bitoffset)
            self._datastore[bytepos] &= ~mask
            bs._datastore.setoffset(bitoffset)
            self._datastore[bytepos] |= bs._datastore[0] & mask   
        else:
            # Do first byte
            mask = (1 << (8 - bitoffset)) - 1
            self._datastore[bytepos] &= ~mask
            bs._datastore.setoffset(bitoffset)
            self._datastore[bytepos] |= bs._datastore[0] & mask
            # Now do all the full bytes
            self._datastore[firstbytepos + 1:lastbytepos] = bs._datastore[1:lastbytepos - firstbytepos]
            # and finally the last byte
            bitsleft = (self._offset + bitpos + bs.length) % 8
            if bitsleft == 0:
                bitsleft = 8
            mask = (1 << (8 - bitsleft)) - 1
            self._datastore[lastbytepos] &= mask
            self._datastore[lastbytepos] |= bs._datastore[-1] & ~mask
        self._pos = bitposafter
        assert self._assertsanity()
        return
    
    def deletebits(self, bits, bitpos=None):
        """Delete bits at current position, or bitpos if given.
        
        bits -- Number of bits to delete.
        bitpos -- Bit position to delete from.
                  Defaults to self.bitpos.
        
        Raises ValueError if bits < 0.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use deletebits on immutable BitString.")
        if bitpos is None:
            bitpos = self._pos
        if bits < 0:
            raise ValueError("Cannot delete a negative number of bits.")
        # If too many bits then delete to the end.
        bits = min(bits, self.length - bitpos)
        end = self._slice(bitpos + bits, self.length)
        self.truncateend(max(self.length - bitpos, 0))
        self.append(end)
        return
    
    def deletebytes(self, bytes, bytepos=None):
        """Delete bytes at current position, or bytepos if given.
        
        bytes -- Number of bytes to delete.
        bytepos -- Byte position to delete from.
                   Defaults to self.bytepos.
        
        Raises BitStringError if bytepos not specified and current position
        is not byte aligned.
        Raises ValueError if bytes < 0.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use deletebytes on immutable BitString.")
        if bytepos is None and self._pos % 8 != 0:
            raise BitStringError("Must be byte-aligned for deletebytes().")
        if bytepos is None:
            bytepos = self._pos // 8
        self.deletebits(bytes*8, bytepos*8)
        return
    
    def append(self, bs):
        """Append a BitString to the current BitString.
        
        bs -- The BitString to append.
        
        """
        if not self._mutable:
            raise TypeError("Cannot append to an immutable BitString.")
        bs = self._converttobitstring(bs)
        if bs.empty():
            return self
        # Can't modify file, so ensure it's read into memory
        self._ensureinmemory()
        bs._ensureinmemory()
        if bs is self:
            bs = self.__copy__()
        self._datastore.appendarray(bs._datastore)
        return
        
    def prepend(self, bs):
        """Prepend a BitString to the current BitString.
        
        bs -- The BitString to prepend.
        
        """
        if not self._mutable:
            raise TypeError("Cannot prepend to an immutable BitString.")
        bs = self._converttobitstring(bs)
        if bs.empty():
            return self
        # Can't modify file so ensure it's read into memory
        self._ensureinmemory()
        bs._ensureinmemory()
        if bs is self:
            bs = self.__copy__()
        self._datastore.prependarray(bs._datastore)
        self.bitpos += bs.length
        return

    def reversebits(self, startbit=None, endbit=None):
        """Reverse bits in-place.
        
        startbit -- Position of first bit to reverse.
                    Defaults to 0.
        endbit -- One past the position of the last bit to reverse.
                  Defaults to self.length.
        
        Using on an empty BitString will have no effect.
        
        Raises ValueError if startbit < 0, endbit > self.length or
        endbit < startbit.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use reversebits on immutable BitString.")
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        if startbit < 0:
            raise ValueError("startbit must be >= 0 in reversebits().")
        if endbit > self.length:
            raise ValueError("endbit must be <= self.length in reversebits().")
        if endbit < startbit:
            raise ValueError("endbit must be >= startbit in reversebits().")
        # TODO: This could be made much more efficient...
        self[startbit:endbit] = BitString(bin=self[startbit:endbit].bin[:1:-1])
        return
    
    def reversebytes(self, startbit=None, endbit=None):
        """Reverse bytes in-place.
        
        startbit -- Position of first bit to reverse.
                    Defaults to 0.
        endbit -- One past the position of the last bit to reverse.
                  Defaults to self.length.
        
        Raises BitStringError if endbit - startbit is not a whole number of
        bytes long.
        
        """
        if not self._mutable:
            raise TypeError("Cannot use reversebytes on immutable BitString.")
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        if startbit < 0:
            raise ValueError("startbit must be >= 0 in reversebytes().")
        if endbit > self.length:
            raise ValueError("endbit must be <= self.length in reversebytes().")
        if endbit < startbit:
            raise ValueError("endbit must be >= startbit in reversebytes().")
        if (endbit - startbit) % 8 != 0:
            raise BitStringError("Can only use reversebytes on whole-byte BitStrings.")
        # TODO: This could be made much more efficient...
        self[startbit:endbit] = BitString(data=self[startbit:endbit].data[::-1])
        return
    
    def cut(self, bits, startbit=None, endbit=None, count=None):
        """Return BitString generator by cutting into bits sized chunks.
        
        bits -- The size in bits of the BitString chunks to generate.
        startbit -- The bit position to start the first cut.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to use in the cut.
                  Defaults to self.length.
        count -- If specified then at most count items are generated.
                 Default is to cut as many times as possible.
        
        """
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        if startbit < 0:
            raise ValueError("Cannot cut - startbit must be >= 0.")
        if endbit > self.length:
            raise ValueError("Cannot cut - endbit is past the end of the BitString.")
        if endbit < startbit:
            raise ValueError("endbit must not be less than startbit.")
        if count is not None and count < 0:
            raise ValueError("Cannot cut - count must be >= 0.")
        if bits <= 0:
            raise ValueError("Cannot cut - bits must be >= 0.")
        c = 0
        while count is None or c < count:
            c += 1
            nextchunk = self._slice(startbit, min(startbit + bits, endbit))
            if nextchunk.length != bits:
                return
            assert nextchunk._assertsanity()
            yield nextchunk
            startbit += bits
        return
 
    def split(self, delimiter, startbit=None, endbit=None, count=None,
              bytealigned=False):
        """Return BitString generator by splittling using a delimiter.
        
        The first item returned is the initial BitString before the delimiter,
        which may be an empty BitString.
        
        delimiter -- The BitString used as the divider.
        startbit -- The bit position to start the split.
                    Defaults to 0.
        endbit -- The bit position one past the last bit to use in the split.
                  Defaults to self.length.
        count -- If specified then at most count items are generated.
                 Default is to split as many times as possible.
        bytealigned -- If True splits will only occur on byte boundaries.
        
        Raises ValueError if the delimiter is empty.
        
        """  
        delimiter = self._converttobitstring(delimiter)
        if delimiter.empty():
            raise ValueError("split delimiter cannot be empty.")
        if startbit is None:
            startbit = 0
        if endbit is None:
            endbit = self.length
        if startbit < 0:
            raise ValueError("Cannot split - startbit must be >= 0.")
        if endbit > self.length:
            raise ValueError("Cannot split - endbit is past the end of the BitString.")
        if endbit < startbit:
            raise ValueError("endbit must not be less than startbit.")
        if count is not None and count < 0:
            raise ValueError("Cannot split - count must be >= 0.")
        oldpos = self._pos
        self._pos = startbit
        if count == 0:
            return
        found = self.find(delimiter, startbit, endbit, bytealigned)
        if not found:
            # Initial bits are the whole BitString being searched
            self._pos = oldpos
            yield self._slice(startbit, endbit)
            return
        # yield the bytes before the first occurence of the delimiter, even if empty
        yield self[startbit:self._pos]
        startpos = self._pos
        c = 1
        while count is None or c < count:
            self._pos += delimiter.length
            found = self.find(delimiter, self._pos, endbit, bytealigned)
            if not found:
                # No more occurences, so return the rest of the BitString
                self._pos = oldpos
                yield self[startpos:endbit]
                return
            c += 1
            yield self[startpos:self._pos]
            startpos = self._pos
        # Have generated count BitStrings, so time to quit.
        self._pos = oldpos
        return

    def join(self, bitstringlist):
        """Return the BitStrings in a list joined by self.
        
        bitstringlist -- A list of BitStrings.
        
        """
        s = BitString()
        if bitstringlist:
            for bs in bitstringlist[:-1]:
                s.append(bs)
                s.append(self)
            s.append(bitstringlist[-1])
        return s

    def tostring(self):
        """Return the BitString as a string, padding with zero bits if needed.
        
        Up to seven zero bits will be added at the end to byte align.
        
        """
        self._ensureinmemory()
        self._datastore.setoffset(0)
        d = self._datastore.rawbytes
        # Need to ensure that unused bits at end are set to zero
        unusedbits = 8 - self.length % 8
        if unusedbits != 8:
            # This is horrible. Shouldn't have to copy the string here!
            return d[:-1] + chr(ord(d[-1]) & (255 << unusedbits))
        return d

    def tofile(self, f):
        """Write the BitString to a file object, padding with zero bits if needed.
        
        Up to seven zero bits will be added at the end to byte align.
        
        """
        # If the BitString is file based then we don't want to read it all
        # in to memory.
        chunksize = 1024*1024 # 1 MB chunks
        if self._offset == 0:
            # TODO: Shouldn't this just use array.tofile() if available ???
            a = 0
            bytelen = self._datastore.bytelength
            p = self._datastore[a:min(a + chunksize, bytelen - 1)]
            while len(p) == chunksize:
                f.write(p)
                a += chunksize
                p = self._datastore[a:min(a + chunksize, bytelen - 1)]
            f.write(p)
            # Now the final byte, ensuring that unused bits at end are set to 0.
            unusedbits = 8 - self.length % 8
            f.write(chr(self._datastore[-1] & (255 << unusedbits)))
        else:
            # Really quite inefficient...
            a = 0
            p = self[a:a + chunksize*8]
            while p.length == chunksize*8:
                f.write(p.data)
                a += chunksize*8
                p = self[a:a + chunksize*8]
            f.write(p.tostring())

    _offset = property(_getoffset)

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
    intbe  = property(_getintbe, _setintbe,
                      doc="""The BitString as a two's complement big-endian signed int. Read and write.
                      """)
    uintbe = property(_getuintbe, _setuintbe,
                      doc="""The BitString as a two's complement big-endian unsigned int. Read and write.
                      """)
    intle  = property(_getintle, _setintle,
                      doc="""The BitString as a two's complement little-endian signed int. Read and write.
                      """)
    uintle = property(_getuintle, _setuintle,
                      doc="""The BitString as a two's complement little-endian unsigned int. Read and write.
                      """)
    intne  = property(_getintne, _setintne,
                      doc="""The BitString as a two's complement native-endian signed int. Read and write.
                      """)
    uintne = property(_getuintne, _setuintne,
                      doc="""The BitString as a two's complement native-endian unsigned int. Read and write.
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
    
def pack(format, *values, **kwargs):
    """Pack the values according to the format string and return a new BitString.

    format -- A string with comma separated tokens describing how to create the
              next bits in the BitString.
    values -- Zero or more values to pack according to the format.
    kwargs -- A dictionary or keyword-value pairs - the keywords used in the
              format string will be replaced with their given value.
                
    Token examples: 'int:12'    : 12 bits as a signed integer
                    'uint:8'    : 8 bits as an unsigned integer
                    'intbe:16'  : 2 bytes as big-endian signed integer
                    'uintbe:16' : 2 bytes as big-endian unsigned integer
                    'intle:32'  : 4 bytes as little-endian signed integer
                    'uintle:64' : 8 bytes as little-endian unsigned integer
                    'intne:24'  : 3 bytes as native-endian signed integer
                    'uintne:64' : 8 bytes as native-endian unsigned integer
                    'hex:8'     : 8 bits as a hex string
                    'oct:9'     : 9 bits as an octal string
                    'bin:1'     : single bit binary string
                    'ue'        : next bits as unsigned exp-Golomb code
                    'se'        : next bits as signed exp-Golomb code
                    'bits:5'    : 5 bits as a BitString object
                    'bytes:3'   : 3 bytes as a BitString object

    >>> s = pack('uint:12, bits', 100, '0xffe')
    >>> t = pack('bits, bin:3', s, '111')
    >>> u = pack('uint:8=a, uint:8=b, uint:55=a', a=6, b=44)
    
    """
    tokens = _tokenparser(format, kwargs.keys())
    new_values = []
    # This is a bit clumsy...
    for v in values:
        if isinstance(v, int):
            new_values.append(str(v))
        else:
            new_values.append(v)
    value_iter = iter(new_values)
    s = BitString()
    try:
        for name, length, value in tokens:
            # If the value is in the kwd dictionary then it takes precedence.
            if value in kwargs:
                value = str(kwargs[value])
            # If the length is in the kwd dictionary then use that too.
            if length in kwargs:
                length = str(kwargs[length])
            # Also if we just have a dictionary name then we want to use it
            if name in kwargs and length is None and value is None:
                s.append(str(kwargs[name]))
                continue
            if length is not None:
                length = int(length)
            if value is None:
                # Take the next value from the ones provided
                value = value_iter.next()
            s.append(_init_with_token(name, length, value))
    except StopIteration:
        raise ValueError("Not enough parameters present to pack according to the "
                         "format. %d values are needed." % len(tokens))
    try:
        value_iter.next()
    except StopIteration:
        # Good, we've used up all the *values.
        return s
    raise ValueError("Too many parameters present to pack according to the format.")


if __name__=='__main__':
    print "Running bitstring module unit tests:"
    try:
        import test_bitstring
        test_bitstring.unittest.main(test_bitstring)
    except ImportError:
        print "Error: cannot find test_bitstring.py"

 