#!/usr/bin/env python
# BitString class for bit-wise data manipulation.

license = """
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

import array
import copy
import string
import os
import struct


def _single_byte_from_hex_string(h):
    """Return a byte equal to the input hex string."""
    try:
        i = int(h, 16)
    except ValueError:
        raise BitStringError("Can't convert hex string to a single byte")
    if len(h) > 2:
        raise BitStringError("Hex string can't be more than one byte in size")
    if len(h) == 2:
        return struct.pack('B', i)  
    elif len(h) == 1:
        return struct.pack('B', i<<4)

def _single_byte_from_hex_string_unsafe(h):
    """Return a byte equal to the input 2 character hex string. No parameter checking done."""
    return struct.pack('B', int(h, 16))

def _hex_string_from_single_byte(b):
    """Return a two character hex string from a single byte value."""
    v = ord(b)
    if v > 15:
        return hex(v)[2:]
    elif v > 0:
        return '0'+hex(v)[2:]
    else:
        return '00'

def _removewhitespace(s):
    """Return string with all whitespace removed."""
    return string.join(s.split(), '')


class BitStringError(Exception):
    """Base class for errors in the bitstring module."""


class _FileArray(object):
    """A class that mimics the array.array type but gets data from a file object."""
    
    def __init__(self, filename, lengthinbits):
        filelength = os.path.getsize(filename)
        self.source = file(filename, 'rb')
        if lengthinbits is None:
            length = filelength
        else:
            length = lengthinbits/8
        self._length = length # length in bytes
    
    def __len__(self):
        # This fails for > 4GB, so better to explictly disallow it!
        raise NotImplementedError
    
    def length(self):
        return self._length
    
    def __copy__(self):
        raise BitStringError("_FileArray.copy() not allowed")
    
    def __getitem__(self, key):
        try:
            key.start
        except AttributeError:
            # single element
            if key >= self._length or key < -self._length:
                raise IndexError
            if key < 0:
                key = self._length + key
            self.source.seek(key, os.SEEK_SET)
            return _MemArray(self.source.read(1))
        # A slice
        if key.step is not None:
            raise BitStringError("step not supported for slicing BitStrings")
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
            self.source.seek(start, os.SEEK_SET)
            return _MemArray(self.source.read(stop-start))
        else:
            return _MemArray('')
    
    def tostring(self):
        self.source.seek(0, os.SEEK_SET)
        return self.source.read()
    

class _MemArray(object):
    """A class that wraps the array.array functionality."""
    
    def __init__(self, data):
        self._data = array.array('B', data)
    
    def __len__(self):
        # Doesn't work for > 4GB.
        raise NotImplementedError
    
    def length(self):
        return len(self._data)
    
    def __copy__(self):
        return _MemArray(self._data)
        #return copy.copy(self.data)
    
    def __getitem__(self, key):
        return self._data.__getitem__(key)

    def __setitem__(self, key, item):
        self._data.__setitem__(key, item)

    def append(self, data):
        self._data.append(data)
        
    def extend(self, data):
        self._data.extend(data)
        
    def tostring(self):
        return self._data.tostring()

class BitString(object):
    """A class for general bit-wise manipulations and interpretations.
    
       length : length of the string in bits
       offset : bit offset to the data (0 - 7). The first offset bits are ignored.
       
       Initialise the BitString with one (and only one) of:
       data : raw data as a string, for example read from binary file
       bin : binary string representation, e.g. '00101110'
       hex : hexadecimal string representation, e.g. '0x2e'
       uint : unsigned integer
       int : signed integer
       se : signed Exponential-Golomb
       ue : unsigned Exponential-Golomb
       filename : Note this option is experimental and only partially supported
       
       e.g.
       a = BitString(hex='0x123456', offset=4, length=8)
       a.hex # equal to '0x23'
        
    """
    
    def __init__(self, data = None, length = None, offset = 0, filename = None, hex = None,
                 bin = None, uint = None, int = None,  ue = None, se = None):
        """Contains a numerical string with length in bits with an offset bit count."""
        if not 0 <= offset < 8:
            raise BitStringError("Offset must be between 0 and 7")
        
        self._offset = offset
        self._pos = 0
        self._length = 0
        self._file = None
        if length is not None and length < 0:
            raise BitStringError("Length cannot be negative")
        
        initialisers = [data, filename, hex, bin, int, uint, ue, se]
        if initialisers.count(None) < len(initialisers) - 1:
            raise BitStringError("You must only specify one initialiser when initialising the BitString")
        if (se is not None or ue is not None) and length is not None:
            raise BitStringError("A length cannot be specified for an Exponential-Golomb initialiser")
            
        if hex is not None:
            self._sethexsafe(hex, length)
        elif bin is not None:
            self._setbin(bin, length)
        elif data is not None:
            self._setdata(data, length)
        elif uint is not None:
            self._setuint(uint, length)
        elif int is not None:
            self._setint(int, length)
        elif ue is not None:
            self._setue(ue)
        elif se is not None:
            self._setse(se)
        elif filename is not None:
            self._setfile(filename, length)
        elif length is not None:
            # initialise to zeros
            data = '\x00'*((length+7)/8)
            self._setdata(data, length)
        else:
            assert(length is None and initialisers.count(None) == len(initialisers))
            self._setdata('')
        self._assertsanity()
        
    def _setfile(self, filename, lengthinbits):
        "Use file as source of bits. Experimental code, not fully working yet."
        assert(not lengthinbits or lengthinbits%8 == 0) # TODO raise exception
        self._data = _FileArray(filename, lengthinbits)
        # Note that len(self._data) will raise OverflowError if > 4GB. Python bug?
        self._length = self._data.length()*8

    def _assertsanity(self):
        """Check internal self consistency as a debugging aid."""
        assert(self._length >= 0)
        assert(0 <= self._offset < 8)
        if self._length == 0:
            assert(self._data.length() == 0)
            assert(self._pos == 0)
        else:
            assert(self._pos <= self._length)
        assert((self._length + self._offset +7)/8 == self._data.length())
        if self._offset > 0:
            # initial unused bits should always be set to zero
            assert((self._data[0] >> (8-self._offset)) == 0)
        bitsinfinalbyte = (self._offset + self._length)%8
        if bitsinfinalbyte > 0:
            # final unused bits should always be set to zero
            assert(self._data[-1] & ((1 << (8-bitsinfinalbyte)) - 1) == 0)
            
    def _setunusedbitstozero(self):
        """Set non data bits in first and last byte to zero."""
        # set unused bits in first byte to zero
        if self._offset > 0:
            self._data[0] &= (255 >> self._offset)
        # set unused bits at the end of the last byte to zero
        bits_used_in_final_byte = (self._offset + self._length)%8
        if bits_used_in_final_byte > 0:
            self._data[-1] &= 255 ^ (255 >> bits_used_in_final_byte)        
        
    def _setdata(self, data, length = None):
        """Set the data from a string."""
        self._data = _MemArray(data)
        if length is None:
            # Use to the end of the data
            self._length = self._data.length()*8 - self._offset
        else:
            self._length = length
            if self._length+self._offset < self._data.length()*8:
                # strip unused bytes from the end
                self._data = _MemArray(self._data[:(self._length+self._offset+7)/8])
            if self._length+self._offset > self._data.length()*8:
                raise BitStringError("Not enough data present. Need %d bits, have %d." % \
                                     (self._length+self._offset, self._data.length()*8))
        self._setunusedbitstozero()
        self._assertsanity()
            
    def _getdata(self):
        """Return the data as an ordinary string."""
        return self._data.tostring()

    def _getbytepos(self):
        """Return the current position in the stream in bytes. Must be byte aligned."""
        p = self._getbitpos()
        if p%8 != 0:
            raise BitStringError("Not byte aligned in _getbytepos()")
        return p/8

    def _getbitpos(self):
        """Return the current position in the stream in bits."""
        assert(0 <= self._pos <= self._length)
        return self._pos
    
    def _getlength(self):
        """Return the length of the BitString in bits."""
        assert(self._length == 0 or 0 <= self._pos <= self._length)
        return self._length
    
    def empty(self):
        """Return True only if the BitString is empty."""
        return self._length == 0

    def readbits(self, bits):
        """Return new BitString of length bits and advance position."""
        if bits < 0:
            raise BitStringError("Cannot read negative amount")
        if self._pos+bits > self._length:
            raise BitStringError("Reading off the end of the stream")
        newoffset = (self._pos+self._offset)%8
        startbyte = (self._pos+self._offset)/8
        endbyte = (self._pos+self._offset+bits-1)/8
        self._pos += bits
        self._assertsanity()
        return BitString(data = self._data[startbyte:endbyte+1], length = bits,
                         offset = newoffset) 

    def readbytes(self, bytes):
        """Return new BitString of length bytes and advances position. Does not byte align."""
        return self.readbits(bytes*8)
    
    def readbit(self):
        """Return BitString of length 1 and advances position."""
        return self.readbits(1)
    
    def readbyte(self):
        """Return BitString of length 8 bits and advances position. Does not byte align."""
        return self.readbits(8)

    def advancebits(self, bits):
        """Advance position by bits."""
        if bits < 0:
            raise BitStringError("Cannot advance by a negative amount")
        self.bitpos = self._pos + bits

    def retreatbits(self, bits):
        """Retreat position by bits."""
        if bits < 0:
            raise BitStringError("Cannot retreat by a negative amount")
        self._setbitpos(self._pos - bits)

    def advancebytes(self, bytes):
        """Advance position by bytes. Does not byte align."""
        if bytes < 0:
            raise BitStringError("Cannot advance by a negative amount")
        self._setbitpos(self._pos + bytes*8)

    def retreatbytes(self, bytes):
        """Retreat position by bytes."""
        if bytes < 0:
            raise BitStringError("Cannot retreat by a negative amount")
        self._setbitpos(self._pos - bytes*8)

    def _setbytepos(self, bytepos):
        """Move to absolute byte-aligned position in stream."""
        self._setbitpos(bytepos*8)

    def _setbitpos(self, bitpos):
        """Move to absolute postion bit in bitstream."""
        if bitpos < 0:
            raise BitStringError("Bit position cannot be negative")
        if bitpos >= self._length:
            raise BitStringError("Cannot seek past the end of the data")
        self._pos = bitpos

    def find(self, s):
        """Seek to start of next occurence of BitString. Return True if BitString is found."""
        if s._length == 0:
            raise BitStringError("Can't find empty string.")
        oldpos = self._pos
        targetbin = s.bin
        found = False
        for p in xrange(oldpos, self._length - s._length + 1):
            if self[p:p+s._length].bin == targetbin:
                found = True
                break
        if not found:
            self._pos = oldpos
            return False
        self._pos = p
        return True

    def findbytealigned(self, d):
        """Seek to start of next occurence of byte-aligned string or BitString. Return True if string is found."""
        # If we are passed in a BitString then convert it to raw data.
        if isinstance(d, BitString):
            if d._length % 8 != 0:
                raise BitStringError("Can only use find for whole-byte BitStrings.")
            d._setoffset(0)
            d = d.data
        if len(d) == 0:
            raise BitStringError("Can't find empty string.")
        self._setoffset(0)
        oldpos = self._pos
        try:
            self.bytealign()
        except BitStringError:
            self._pos = oldpos
            return False
        bytepos = self._pos/8
        found = False
        p = bytepos
        finalpos = self._length/8 - len(d) + 1
        while p < finalpos:
            if self[p*8:(p+len(d))*8].data == d:
                found = True
                break
            p += 1
        if not found:
            self._pos = oldpos
            return False
        self._setbytepos(p)
        self._assertsanity()
        return True

    def bytealign(self):
        """Align to next byte and return number of skipped bits."""
        skipped = (8 - ((self._pos)%8))%8
        self._setbitpos(self._pos + self._offset + skipped)
        self._assertsanity()
        return skipped

    def _getuint(self):
        """Return data as an unsigned int."""
        if self._data.length() == 0:
            raise BitStringError("An empty BitString cannot be interpreted as an unsigned integer")
        if self._data.length() == 1:
            mask = ((1<<self._length)-1)<<(8-self._length-self._offset)
            val = self._data[0] & mask
            val >>= 8 - self._offset - self._length
            return val
        firstbits = 8 - self._offset
        mask = (1<<firstbits) - 1
        val = self._data[0] & mask
        for j in xrange(1, self._data.length()-1):
            val <<= 8
            val += self._data[j]
        lastbyte = self._data[-1:][0]
        bitsleft = (self._offset + self._length)%8
        if bitsleft == 0:
            bitsleft = 8
        val <<= bitsleft
        mask = 255 - ((1<<(8-bitsleft))-1)
        val += (lastbyte&mask)>>(8-bitsleft)
        return val
    
    def _setuint(self, uint, length=None):
        """Reset the BitString to have given unsigned int interpretation."""
        if length is None and self._length != 0:
            length = self._length
        if length is None:
            raise BitStringError("A length must be specified with a uint initialiser")
        if uint >= (1 << length) or length == 0:
            raise BitStringError("uint cannot be contained using BitString of that length")
        if uint < 0:
            raise BitStringError("uint cannot be initialsed by a negative number")     
        
        hexstring = hex(uint)[2:]
        if hexstring[-1] == 'L':
            hexstring = hexstring[:-1]
        hexlengthneeded = (length+3)/4
        leadingzeros = hexlengthneeded - len(hexstring)
        if leadingzeros > 0:
            hexstring = '0'*leadingzeros + hexstring
        self._sethexunsafe(hexstring)
        self._offset = (4*hexlengthneeded) - length
        self._length = length
        
    def _getint(self):
        """Return data as a two's complement signed int."""
        ui = self.uint
        if ui < (1 << (self._length - 1)):
            # Top bit not set, must be positive
            return ui
        tmp = (~(ui-1)) & ((1 << self._length)-1)
        return -tmp
    
    def _setint(self, int, length=None):
        """Reset the BitString to have given signed int interpretation."""
        if length is None and self._length != 0:
            length = self._length
        if length is None:
            raise BitStringError("A length must be specified with an int initialiser")
        if length == 0 or int >=  (1 << (length - 1)) or int < -(1 << (length - 1)):
            raise BitStringError("int cannot be contained using BitString of that length")   
        if int < 0:
            # the twos complement thing to get the equivalent +ive number
            int = (-int-1)^((1 << length) - 1)
        self._setuint(int, length)
    
    def _getue(self):
        """Return interpretation of next bits in stream as an unsigned Exponential-Golomb of the type used in H.264.
           Advances position to after the read code."""
        leadingzerobits = -1
        b = 0
        while b == 0:
            b = self.readbits(1).uint
            leadingzerobits += 1
        codenum = (1 << leadingzerobits) - 1
        if leadingzerobits > 0:
            codenum += self.readbits(leadingzerobits).uint
        return codenum

    def _setue(self, i):
        """Initialise BitString with unsigned Exponential-Golomb code for i."""
        if i < 0:
            raise BitStringError("Cannot use negative initialiser for unsigned Exponential-Golomb.")
        if i == 0:
            self._setbin('1')
            return
        tmp = i + 1
        leadingzeros = -1
        while tmp > 0:
            tmp >>= 1
            leadingzeros += 1
        remainingpart = i + 1 - (1 << leadingzeros)
        binstring = '0'*leadingzeros + '1' + BitString(uint = remainingpart, length = leadingzeros).bin
        self._setbin(binstring)
    
    def _getse(self):
        """Return interpretation as a signed Exponential-Golomb of the type used in H.264.
           Advances position to after the read code."""
        codenum = self.ue
        m = (codenum + 1)/2
        if codenum % 2 == 0:
            return -m
        else:
            return m
    
    def _setse(self, i):
        """Initialise BitString with signed Exponential-Golomb code for i."""
        if i > 0:
            u = (i*2)-1
        else:
            u = -2*i
        self._setue(u)

    def _gethex(self):
        """Return interpretation as a hexidecimal string."""
        if self._length%4 != 0:
            raise BitStringError("Cannot convert to hex unambiguously - not multiple of 4 bits")
        if self._length == 0:
            return ''
        self._setoffset(0)
        s = self._data.tostring()
        hexstrings = [_hex_string_from_single_byte(i) for i in s]
        if (self._length/4)%2 == 1:
            # only a nibble left at the end
            hexstrings[-1] = hexstrings[-1][0]
        s = '0x'+''.join(hexstrings)
        return s
    
    def _sethexsafe(self, hexstring, length=None):
        """Reset the BitString to have the value given in hexstring."""
        hexstring = _removewhitespace(hexstring)
        # remove leading 0x if present
        if len(hexstring) > 2 and hexstring[0:2] in ['0x','0X']:
            hexstring = hexstring[2:]
        if length is None:
            length = len(hexstring)*4 - self._offset
        if length < 0 or length + self._offset > len(hexstring)*4:
            raise BitStringError("Invalid length %d, offset %d for hexstring %s" % (length, self._offset, hexstring))    
        hexstring = hexstring[0:(length + self._offset + 3)/4]
        self._length = length
        if self._length == 0:
            self._data = _MemArray('')
            return
        datastring = ""
        # First do the whole bytes
        for i in range(len(hexstring)/2):
            try:
                int(hexstring[i*2:i*2+2], 16)
            except ValueError:
                raise BitStringError("Cannot convert to hexadecimal")
            datastring += _single_byte_from_hex_string(hexstring[i*2:i*2+2])
        # then any remaining nibble
        if len(hexstring)%2 == 1:
            try:
                int(hexstring[-1],16)
            except ValueError:
                raise BitStringError("Cannot convert last digit to hexadecimal")
            datastring += _single_byte_from_hex_string(hexstring[-1])
        self._data = _MemArray(datastring)
        self._setunusedbitstozero()
        self._assertsanity()
        
    def _sethexunsafe(self, hexstring, length=None):
        """Reset the BitString to have the value given in hexstring.
           Does not do parameter checking. Use _sethexsafe() unless you are sure of the input."""
        if length is None:
            length = len(hexstring)*4 - self._offset   
        self._length = length
        if self._length == 0:
            self._data = _MemArray('')
            return
        datastring = ""
        # First do the whole bytes
        for i in xrange(len(hexstring)/2):
            datastring += _single_byte_from_hex_string_unsafe(hexstring[i*2:i*2+2])
        # then any remaining nibble
        if len(hexstring)%2 == 1:
            datastring += _single_byte_from_hex_string(hexstring[-1])
        self._data = _MemArray(datastring)
        self._setunusedbitstozero()
        self._assertsanity()
        
    def _getbin(self):
        """Return interpretation as a binary string."""
        c = []
        if self._length != 0:
            # Horribly inefficient!
            i = self.uint
            for x in xrange(self._length):
                c.append('1' if i%2 == 1 else '0')
                i /= 2
        c.reverse()
        return ''.join(c)
    
    def _setbin(self, binstring, length=None):
        """Reset the BitString to the value given in binstring."""
        binstring = _removewhitespace(binstring)
        if length is None:
            length = len(binstring)
        if length < 0 or length > len(binstring):
            raise BitStringError("Invalid length of binary string")
        # Truncate the bin_string if needed
        binstring = binstring[0:length]
        self._length = length
        self._offset = 0
        if self._length == 0:
            self._data = _MemArray('')
            return
        # pad with zeros up to byte boundary if needed
        boundary = ((self._length + 7)/8)*8
        if len(binstring) < boundary:
            binstring += '0'*(boundary - self._length)
        try:
            bytes = [int(binstring[x:x+8], 2) for x in range(0, len(binstring), 8)]
        except ValueError:
            raise BitStringError("Invalid character in binstring")
        self._data = _MemArray(bytes)
        self._setunusedbitstozero()
        self._assertsanity()

    def truncateend(self, bits):
        """Truncate bits from the end of the BitString. Return new BitString."""
        if bits < 0 or bits > self._length:
            raise BitStringError("Truncation length of %d bits not possible. Length = %d"%(bits,self._length))
        s = BitString()
        if bits == 0:
            return BitString(data=self._data, offset=self._offset, length=self._length)
        if bits == self._length:
            return BitString() # empty as everything's been truncated
        new_length_in_bytes = (self._offset + self._length - bits + 7)/8
        s._setdata(self._data[:new_length_in_bytes])
        s._length = self._length - bits
        s._offset = self._offset
        s._setunusedbitstozero()
        # Ensure that the position is still valid
        s._pos = min(self._pos, s._length-1)
        s._assertsanity()
        return s    
    
    def truncatestart(self, bits):
        """Truncate bits from the start of the BitString. Return new BitString."""
        if bits < 0 or bits > self._length:
            raise BitStringError("Truncation length of %d not possible. Length = %d" % (bits, self._length))
        s = BitString()
        if bits == 0:
            return BitString(data=self._data, offset=self._offset, length=self._length)
        if bits == self._length:
            return BitString() # empty as everything's been truncated
        s._offset += bits
        truncatedbytes = s._offset/8
        s._offset %= 8
        # strip whole bytes from the start
        s._setdata(self._data[truncatedbytes:])
        # Adjust the position and length, and clip to start if needed
        s._length = self._length - bits
        s._pos = self._pos - bits
        if s._pos < 0:
            s._pos = 0
        s._setunusedbitstozero()
        s._assertsanity()
        return s
    
    def slice(self, startbit, endbit):
        """Return a slice of the BitString: [startbit, endbit)."""
        if endbit < startbit:
            raise bs.BitStreamError("Slice: endbit must not be less than startbit")
        if startbit < 0 or endbit > self._length:
            raise BitStringError("slice not in range")
        s = BitString()
        s._offset = (self._offset + startbit)%8
        startbyte = startbit/8
        new_length_in_bytes = (endbit - startbit + s._offset + 7)/8
        s._setdata(self._data[startbyte:startbyte+new_length_in_bytes])
        s._length = endbit - startbit
        s._pos = self._pos - startbit
        s._pos = max(s._pos, 0)
        s._pos = min(s._pos, s._length-1)
        s._setunusedbitstozero()
        s._assertsanity()
        return s
    
    def insert(self, bs, bitpos=None):
        """Insert a BitString into the current BitString at insertpos and return new BitString."""
        if bs.empty():
            return copy.copy(self)
        if bitpos is None:
            bitpos = self._pos
        if bitpos < 0 or bitpos > self._length:
            raise BitStringError("Invalid insertpos")
        end = self.truncatestart(bitpos)
        start = self.truncateend(self._length - bitpos)
        s = start.append(bs).append(end)
        s._assertsanity()
        return s

    def overwrite(self, bs, bitpos=None):
        """Overwrite the section of the current BitString at pos with new data and return new BitString."""
        if bs.empty():
            return copy.copy(self)
        if bitpos is None:
            bitpos = self._pos
        if bitpos < 0 or bitpos + bs._length > self._length:
            raise BitStringError("Overwrite exceeds boundary of BitString")
        # This is of course horribly inefficient...
        s = self.truncateend(self._length - bitpos) + bs
        s += self.truncatestart(bitpos + bs._length)
        s._pos = self._pos + bs._length
        return s
    
    def deletebits(self, bits, bitpos=None):
        """Delete number of bits from the BitString at deletpos and return new BitString."""
        if bitpos is None:
            bitpos = self._pos
        if bits < 0:
            raise BitStringError("Can't delete a negative number of bits")
        if bits + bitpos > self.length:
            raise BitStringError("Can't delete past the end of the BitString")
        return self[0:bitpos]+self[bitpos+bits:]

    def __copy__(self):
        """Return a new copy of the BitString."""
        s_copy = BitString()
        s_copy._offset = self._offset
        s_copy._pos = self._pos
        s_copy._length = self._length
        if self._file is not None:
            raise BitStringError("Cannot copy file based BitStrings.")
        s_copy._data = copy.copy(self._data)
        return s_copy

    def append(self, bs):
        """Return a BitString with the new BitString appended."""
        s1 = copy.copy(self)
        if bs.empty():
            return s1      
        bits_in_final_byte = (s1._offset + s1._length)%8
        bs._setoffset(bits_in_final_byte)
        if bits_in_final_byte != 0:
            # first do the byte with the join
            s1._data[-1] = (s1._data[-1] | bs._data[0])
        else:
            s1._data.append(bs._data[0])
        s1._data.extend(bs._data[1:bs._data.length()])
        s1._length += bs._length
        s1._assertsanity()
        return s1
    
    def _setoffset(self, offset):
        """Realign BitString with offset to first bit."""
        if offset == self._offset:
            return
        if not 0 <= offset < 8:
            raise BitStringError("Can only align to an offset from 0 to 7")
        assert(0 <= self._offset < 8)
        if offset < self._offset:
            # We need to shift everything left
            shiftleft = self._offset - offset
            # First deal with everything except for the final byte
            for x in range(self._data.length() - 1):
                self._data[x] = ((self._data[x] << shiftleft)&255) + (self._data[x+1] >> (8 - shiftleft))
            # if we've shifted all of the data in the last byte then we need to truncate by 1
            bits_in_last_byte = (self._offset + self._length)%8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte <= shiftleft:
                self._data = _MemArray(self._data[:-1])
            # otherwise just shift the last byte
            else:
                self._data[-1] = (self._data[-1]<<shiftleft)&255
        else: # offset > self._offset
            shiftright = offset - self._offset
            # Give some overflow room for the last byte
            if (self._offset + self._length + shiftright + 7)/8 > (self._offset + self._length + 7)/8:
                self._data.append(0)
            for x in range(self._data.length()-1, 0, -1):
                self._data[x] = ((self._data[x-1] << (8 - shiftright))&255) + (self._data[x] >> shiftright)
            self._data[0] = self._data[0] >> shiftright
        self._offset = offset
        self._assertsanity()

    def _getoffset(self):
        """Return current offset."""
        return self._offset
    
    def __add__(self, s):
        """Concatenate BitStrings and return new BitString."""
        return self.append(s)
    
    def __iadd__(self, s):
        """Do the += thing."""
        self = self + s
        return self
    
    def __getitem__(self, key):
        """Return a slice of the BitString. Indices are in bits and stepping is not supported."""
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
            raise BitStringError("step not supported for slicing BitStrings")
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
        
    def split(self, delimiter):
        """Return a generator of BitStrings by splittling into substrings starting with a byte aligned delimiter.
        The first item returned is the initial bytes before the delimiter, which may be empty."""
        if len(delimiter) == 0:
            raise BitStringError("split delimiter cannot be null.")
        if len(delimiter)%8 != 0:
            raise BitStringError("split delimiter must be whole number of bytes.")
        oldpos = self._pos
        self._pos = 0
        found = self.findbytealigned(delimiter)
        if not found:
            # Initial bits are the whole BitString
            self._pos = oldpos
            yield copy.copy(self)
            return
        # yield the bytes before the first occurence of the delimiter, even if empty
        yield self[0:self._pos]
        startpos = self._pos
        while found:
            self._pos += len(delimiter)
            found = self.findbytealigned(delimiter)
            if not found:
                self._pos = oldpos
                yield self[startpos:]
                return
            yield self[startpos:self._pos]
            startpos = self._pos
            
    
    def __len__(self):
        return self._getlength()

    length = property(_getlength, doc="the length of the BitString in bits")
    offset = property(_getoffset, doc="the offset of the BitString relative to being byte aligned")
    hex    = property(_gethex, _sethexsafe, doc="the BitString as a hexidecimal string (including leading zeros)")
    bin    = property(_getbin, _setbin, doc="the BitString as a binary string (including leading zeros)")
    data   = property(_getdata, _setdata, doc="the BitString as a ordinary string")
    int    = property(_getint, _setint, doc="the BitString as a two's complement signed int")
    uint   = property(_getuint, _setuint, doc="the BitString as an unsigned int")
    ue     = property(_getue, _setue, doc="the BitString as an unsigned Exponential-Golomb")
    se     = property(_getse, _setse, doc="the BitString as a signed Exponential-Golomb")
    bitpos = property(_getbitpos, _setbitpos, doc="the position in the BitString in bits")
    bytepos= property(_getbytepos, _setbytepos, doc="the position in the BitString in bytes")

     
def join(bitstringlist):
    """Return the concatenation of the BitStrings in a list"""
    s = BitString(length = sum([s.length for s in bitstringlist]))
    bits, offset, pos = 0, 0, 0
    for bs in bitstringlist:
        bs._setoffset(offset)
        for i in xrange(bs._data.length()):
            s._data[pos] |= bs._data[i]
            pos += 1
        offset = (offset + bs.length)%8
        bits += bs.length
        pos = bits / 8        
    return s
    