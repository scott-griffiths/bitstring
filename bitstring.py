#!/usr/bin/env python
# bitstring class for bit-wise data manipulation.

license = """
The MIT License

Copyright (c) 2006-2008 Scott Griffiths

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
import logging as log



# Using a lookup string is a horrible way of converting from an integer to
# a single byte, but if you can think of a better way...
byte_lookup = '\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'\
              '\x10\x11\x12\x13\x14\x15\x16\x17\x18\x19\x1a\x1b\x1c\x1d\x1e\x1f'\
              '\x20\x21\x22\x23\x24\x25\x26\x27\x28\x29\x2a\x2b\x2c\x2d\x2e\x2f'\
              '\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x3a\x3b\x3c\x3d\x3e\x3f'\
              '\x40\x41\x42\x43\x44\x45\x46\x47\x48\x49\x4a\x4b\x4c\x4d\x4e\x4f'\
              '\x50\x51\x52\x53\x54\x55\x56\x57\x58\x59\x5a\x5b\x5c\x5d\x5e\x5f'\
              '\x60\x61\x62\x63\x64\x65\x66\x67\x68\x69\x6a\x6b\x6c\x6d\x6e\x6f'\
              '\x70\x71\x72\x73\x74\x75\x76\x77\x78\x79\x7a\x7b\x7c\x7d\x7e\x7f'\
              '\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f'\
              '\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f'\
              '\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf'\
              '\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf'\
              '\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf'\
              '\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf'\
              '\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef'\
              '\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff'

def single_byte_from_hex_string(h):
    """Return a byte equal to the input hex string."""
    try:
        int(h, 16)
    except ValueError:
        raise Error("Can't convert hex string to a single byte")
    if len(h) > 2:
        raise Error("Hex string can't be more than one byte in size")
    if len(h) == 2:
        return byte_lookup[int(h, 16)]    
    elif len(h) == 1:
        return byte_lookup[int(h, 16)<<4]

def single_byte_from_hex_string_unsafe(h):
    """Return a byte equal to the input 2 character hex string. No parameter checking done."""
    return byte_lookup[int(h, 16)]

def hex_string_from_single_byte(b):
    """Return a two character hex string from a single byte value."""
    v = ord(b)
    if v > 15:
        return hex(v)[2:]
    elif v > 0:
        return '0'+hex(v)[2:]
    else:
        return '00'

def removewhitespace(s):
    """Return string with all whitespace removed."""
    return string.join(s.split(), '')

    
class Error(Exception):
    pass

class FileArray(object):
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
        raise Error("FileArray.copy() not allowed")
    
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
            return MemArray(self.source.read(1))
        # A slice
        if key.step is not None:
            raise Error("step not supported for slicing BitStrings")
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
            return MemArray(self.source.read(stop-start))
        else:
            return MemArray('')
    
    def tostring(self):
        raise NotImplementedError
    

class MemArray(object):
    """A class that wraps the array.array functionality."""
    
    def __init__(self, data):
        self._data = array.array('B', data)
    
    def __len__(self):
        # Doesn't work for > 4GB.
        raise NotImplementedError
    
    def length(self):
        return len(self._data)
    
    def __copy__(self):
        return MemArray(self._data)
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
       data : raw data as a string (not in general printable!)
       bin : binary string representation, e.g. '00101110'
       hex : hexadecimal string representation, e.g. '0x2e'
       offset : bit offset to the data (0 - 7). The first offset bits are ignored.
       
       e.g.
       a = BitString(hex='0x123456', offset=4, length=8)
       a.hex # equal to '0x23'
        
    """
    
    def __init__(self, data = None, length = None, offset = 0, filename = None, hex = None,
                 bin = None, uint = None, int = None,  ue = None, se = None):
        """Contains a numerical string with length in bits with an offset bit count."""
        if not 0 <= offset < 8:
            raise Error("offset must be between 0 and 7")
        
        self._offset = offset
        self._pos = 0
        self._length = 0
        self._file = None
        if length is not None and length < 0:
            raise Error("length cannot be negative")
        
        initialisers = [data, filename, hex, bin, int, uint, ue, se]
        if initialisers.count(None) < len(initialisers) - 1:
            raise Error("You must only specify one initialiser when initialising the BitString")
        
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
            if length is not None:
                raise Error("A length cannot be specified for a ue initialiser")
            self._setue(ue)
        elif se is not None:
            if length is not None:
                raise Error("A length cannot be specified for a se initialiser")
            self._setse(se)
        elif filename is not None:
            self._setfile(filename, length)
        elif length is not None:
            # initialise to zeros
            data = '\x00'*((length+7)/8)
            self._setdata(data, length)
        else:
            assert(length is None and initialisers.count(None) == len(initialisers))
            self._setdata('', length)
        self._assertSanity()

    def _fillBuffer(self):
        """Fill up the byte buffer from the file source."""
        
    def _setfile(self, filename, lengthinbits):
        assert(not lengthinbits or lengthinbits%8 == 0) # TODO raise exception
        self._data = FileArray(filename, lengthinbits)
        # Note that len(self._data) will raise OverflowError if > 4GB. Python bug?
        self._length = self._data.length()*8
            
        

    def _assertSanity(self):
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
        """Set the data."""
        self._data = MemArray(data)
        if length is None:
            # Use to the end of the data
            self._length = self._data.length()*8 - self._offset
        else:
            self._length = length
            if self._length+self._offset < self._data.length()*8:
                # strip unused bytes from the end
                self._data = MemArray(self._data[:(self._length+self._offset+7)/8])
            if self._length+self._offset > self._data.length()*8:
                raise Error("Not enough data present. Need %d bits, have %d." % \
                                     (self._length+self._offset, self._data.length()*8))
        self._setunusedbitstozero()
        self._assertSanity()
            
    def _getdata(self):
        """Return the data as an ordinary string."""
        return self._data.tostring()

    def _getbytepos(self):
        """Return the position in the stream as a byte offset."""
        p = self._getbitpos()
        if p%8 != 0:
            raise Error("Not byte aligned in _getbytepos()")
        return p/8

    def _getbitpos(self):
        """Return position in stream as a bit position."""
        assert(0 <= self._pos <= self._length)
        return self._pos
    
    def _getlength(self):
        """Return the length of the BitString in bits."""
        assert(self._length == 0 or 0 <= self._pos <= self._length)
        return self._length
    
    def empty(self):
        """Return True if the BitString has no data."""
        return self._length == 0

    def readbits(self, bits):
        """Return new BitString of length bits and advance position."""
        if bits < 0:
            raise Error("Cannot read negative amount")
        if self._pos+bits > self._length:
            raise Error("Reading off the end of the stream")
        newoffset = (self._pos+self._offset)%8
        startbyte = (self._pos+self._offset)/8
        endbyte = (self._pos+self._offset+bits-1)/8
        self._pos += bits
        self._assertSanity()
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

    # TODO: Is the needed now? can't we just do bitPos += bits
    def advancebits(self, bits):
        """Advance position by bits."""
        if bits < 0:
            raise Error("Cannot advance by a negative amount")
        self.bitpos = self._pos + bits

    def retreatbits(self, bits):
        """Retreat position by bits."""
        if bits < 0:
            raise Error("Cannot retreat by a negative amount")
        self.bitpos = self._pos - bits

    def advancebytes(self, bytes):
        """Advance position by bytes. Does not byte align."""
        if bytes < 0:
            raise Error("Cannot advance by a negative amount")
        self.bitpos = self._pos + bytes*8

    def retreatbytes(self, bytes):
        """Retreat position by bytes."""
        if bytes < 0:
            raise Error("Cannot retreat by a negative amount")
        self.bitpos = self._pos - bytes*8

    def _setbytepos(self, bytepos):
        """Move to absolute byte-aligned position in stream."""
        self._setbitpos(bytepos*8)

    def _setbitpos(self, bitpos):
        """Move to absolute postion bit in bitstream."""
        if bitpos < 0:
            raise Error("Bit position cannot be negative")
        if bitpos >= self._length:
            raise Error("Cannot seek past the end of the data")
        self._pos = bitpos

    def findbytes(self, d):
        """Seek to start of next occurence of byte-aligned string. Return True if string is found."""
        oldpos = self._pos
        try:
            self.bytealign()
        except Error:
            self._pos = oldpos
            return False
        try:
            p = self._data.tostring().find(d, self._pos/8)
        except NotImplementedError:
            pass # TODO!
        if p == -1:
            self._pos = oldpos
            return False
        self.bytepos = p
        #self._assertSanity()
        return True
    
    def find(self, s):
        """Seek to start of next occurence of byte-aligned BitString. Return True is string is found."""
        if s._length % 8 != 0:
            raise Error("Can only use find for whole-byte BitStrings.")
        s.offset = 0
        return self.findbytes(s.data)

    def bytealign(self):
        """Align to next byte and return number of skipped bits."""
        skipped = (8 - (self._pos%8))%8
        self.bitpos = self._pos + skipped
        #self._assertSanity()
        return skipped

    def _getuint(self):
        """Return data as an unsigned int."""
        if self._data.length() == 0:
            raise Error("Empty BitString cannot be interpreted as a uint")
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
        if length is None:
            length = self._length
        if length is None:
            raise Error("A length must be specified with a uint initialiser")
        if uint >= (1 << length) or length == 0:
            raise Error("uint cannot be contained using BitString of that length")
        if uint < 0:
            raise Error("uint cannot be initialsed to a negative number")     
        
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
        if length is None:
            length = self._length
        if length is None:
            raise Error("A length must be specified with an int initialiser")
        if length == 0 or int >=  (1 << (length - 1)) or int < -(1 << (length - 1)):
            raise Error("int cannot be contained using BitString of that length")   
        if int < 0:
            # the twos complement thing to get the equivalent +ive number
            int = (-int-1)^((1 << length) - 1)
        self._setuint(int, length)
    
    def _getue(self):
        """Return interpretation of next bits in stream as an unsigned Exponential Goulomb of the type used in H.264.
           Advances position to after read code."""
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
        if i < 0:
            raise Error("Cannot use negative initialiser for unsigned Exponential Goulomb.")
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
        """Return interpretation as a signed Exponential Goulomb of the type used in H.264."""
        codenum = self.ue
        m = (codenum + 1)/2
        if codenum % 2 == 0:
            return -m
        else:
            return m
    
    def _setse(self, i):
        if i > 0:
            u = (i*2)-1
        else:
            u = -2*i
        self._setue(u)

    def _gethex(self):
        """Return interpretation as a hexidecimal string."""
        if self._length%4 != 0:
            raise Error("Cannot convert to hex unambiguously - not multiple of 4 bits")
        if self._length == 0:
            return ''
        self._setoffset(0)
        s = self._data.tostring()
        hexstrings = [hex_string_from_single_byte(i) for i in s]
        if (self._length/4)%2 == 1:
            # only a nibble left at the end
            hexstrings[-1] = hexstrings[-1][0]
        s = '0x'+''.join(hexstrings)
        return s
    
    def _sethexsafe(self, hexstring, length=None):
        """Reset the BitString to have the value given in hexstring."""
        # remove whitespace
        hexstring = removewhitespace(hexstring)
            # remove leading 0x if present
        if len(hexstring) > 2 and hexstring[0:2] in ['0x','0X']:
            hexstring = hexstring[2:]
        if length is None:
            length = len(hexstring)*4 - self._offset
        if length < 0 or length + self._offset > len(hexstring)*4:
            raise Error("Invalid length %d, offset %d for hexstring %s" % (length, self._offset, hexstring))    
        hexstring = hexstring[0:(length + self._offset + 3)/4]
        self._length = length
        if self._length == 0:
            self._data = MemArray('')
            return
        datastring = ""
        # First do the whole bytes
        for i in range(len(hexstring)/2):
            try:
                int(hexstring[i*2:i*2+2], 16)
            except ValueError:
                raise Error("Cannot convert to hexadecimal")
            datastring += single_byte_from_hex_string(hexstring[i*2:i*2+2])
        # then any remaining nibble
        if len(hexstring)%2 == 1:
            try:
                int(hexstring[-1],16)
            except ValueError:
                raise Error("Cannot convert last digit to hexadecimal")
            datastring += single_byte_from_hex_string(hexstring[-1])
        self._data = MemArray(datastring)
        self._setunusedbitstozero()
        self._assertSanity()
        
    def _sethexunsafe(self, hexstring, length=None):
        """Reset the BitString to have the value given in hexstring.
           Does not do parameter checking. Use _sethexsafe() unless you are sure of the input."""
        if length is None:
            length = len(hexstring)*4 - self._offset   
        self._length = length
        if self._length == 0:
            self._data = MemArray('')
            return
        datastring = ""
        # First do the whole bytes
        for i in xrange(len(hexstring)/2):
            datastring += single_byte_from_hex_string_unsafe(hexstring[i*2:i*2+2])
        # then any remaining nibble
        if len(hexstring)%2 == 1:
            datastring += single_byte_from_hex_string(hexstring[-1])
        self._data = MemArray(datastring)
        self._setunusedbitstozero()
        self._assertSanity()
        
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
        binstring = removewhitespace(binstring)
        if length is None:
            length = len(binstring)
        if length < 0 or length > len(binstring):
            raise Error("Invalid length of binary string")
        # Truncate the bin_string if needed
        binstring = binstring[0:length]
        self._length = length
        self._offset = 0
        if self._length == 0:
            self._data = MemArray('')
            return
        # pad with zeros up to byte boundary if needed
        boundary = ((self._length + 7)/8)*8
        if len(binstring) < boundary:
            binstring += '0'*(boundary - self._length)
        try:
            bytes = [int(binstring[x:x+8], 2) for x in range(0, len(binstring), 8)]
        except ValueError:
            raise Error("Invalid character in binstring")
        self._data = MemArray(bytes)
        self._setunusedbitstozero()
        self._assertSanity()

    def truncateend(self, bits):
        """Truncate bits from the end of the BitString."""
        if bits < 0 or bits > self._length:
            raise Error("Truncation length of %d bits not possible. Length = %d"%(bits,self._length))
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
        s._assertSanity()
        return s    
    
    def truncatestart(self, bits):
        """Truncate bits from the start of the BitString."""
        if bits < 0 or bits > self._length:
            raise Error("Truncation length of %d not possible. Length = %d" % (bits, self._length))
        s = BitString()
        if bits == 0:
            return BitString(data=self._data, offset=self._offset, length=self._length)
        if bits == self._length:
            return BitString() # empty as everything's been truncated
        s._offset = self._offset + bits
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
        s._assertSanity()
        return s
    
    def slice(self, startbit, endbit):
        """Return a slice of the BitString: [startbit, endbit)."""
        if endbit < startbit:
            raise bs.BitStreamError("Slice: endbit must not be less than startbit")
        s = self.truncateend(self._length - endbit).truncatestart(startbit)
        assert(s.length == endbit - startbit)
        s._assertSanity()
        return s
    
    def insert(self, bs, insertpos = None):
        """Insert a BitString into the current BitString at insertPos and return new BitString."""
        if bs.empty():
            return copy.copy(self)
        if insertpos is None:
            insertpos = self._pos
        if insertpos < 0 or insertpos > self._length:
            raise Error("Invalid insertpos")
        end = self.truncatestart(insertpos)
        start = self.truncateend(self._length - insertpos)
        s = start.append(bs).append(end)
        s._assertSanity()
        return s

    def overwrite(self, bs, pos = None):
        """Overwrite the section of the current BitString at pos with new data and return new BitString."""
        if bs.empty():
            return copy.copy(self)
        if pos is None:
            pos = self._pos
        if pos < 0 or pos + bs._length > self._length:
            raise Error("Overwrite exceeds boundary of BitString")
        # This is of course horribly inefficient...
        s = self.truncateend(self._length - pos) + bs
        s += self.truncatestart(pos + bs._length)
        s._pos = self._pos + bs._length
        return s
    
    def deletebits(self, bitstodelete):
        """Delete bits from the current position and return new BitString."""
        if bitstodelete < 0:
            raise Error("Can't delete a negative number of bits")
        if bitstodelete + self._pos > self.length:
            raise Error("Can't delete past the end of the BitString")
        return self[0:self._pos]+self[self._pos+bitstodelete:]

    def __copy__(self):
        """Return a new copy of the BitString."""
        s_copy = BitString()
        s_copy._offset = self._offset
        s_copy._pos = self._pos
        s_copy._length = self._length
        if self._file is not None:
            raise Error("Cannot copy file based BitStrings.")
        s_copy._data = copy.copy(self._data)
        return s_copy

    def append(self, s2):
        """Return a BitString with the new BitString appended."""
        s1 = copy.copy(self)
        if s2.empty():
            return s1      
        bits_in_final_byte = (s1._offset + s1._length)%8
        s2.offset = bits_in_final_byte
        if bits_in_final_byte != 0:
            # first do the byte with the join
            s1._data[-1] = (s1._data[-1] | s2._data[0])
        else:
            s1._data.append(s2._data[0])
        s1._data.extend(s2._data[1:s2._data.length()])
        s1._length += s2._length
        #s1._assertSanity()
        return s1
    
    def _setoffset(self, offset):
        """Realign BitString with offset to first bit."""
        if offset == self._offset:
            return
        if not 0 <= offset < 8:
            raise Error("Can only align to an offset from 0 to 7")
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
                self._data = MemArray(self._data[:-1])
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
        #self._assertSanity()

    def _getoffset(self):
        """Return current offset."""
        return self._offset
    
    def __add__(self, s):
        """Concatenate BitStrings."""
        return self.append(s)
    
    def __iadd__(self, s):
        """Do the += thing."""
        self = self + s
        return self
    
    def __getitem__(self, key):
        """Return a slice of the BitString. Stepping is not supported."""
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
            raise Error("step not supported for slicing BitStrings")
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
        """Return a generator of BitStrings by splittling into substring starting with a byte aligned delimiter.
        The first item returned is the initial bytes before the delimiter, which may be empty."""
        if len(delimiter) == 0:
            raise Error("split delimiter cannot be null.")
        if len(delimiter)%8 != 0:
            raise Error("split delimiter must be whole number of bytes.")
        oldpos = self._pos
        self._pos = 0
        found = self.find(delimiter)
        if not found:
            # Initial bits are the whole BitString
            self._pos = oldpos
            yield copy.copy(self)
            return
        if self._pos != 0:
            yield self[0:self._pos]
        startpos = self._pos
        while found:
            self._pos += len(delimiter)
            found = self.find(delimiter)
            if not found:
                self._pos = oldpos
                yield self[startpos:]
                return
            yield self[startpos:self._pos]
            startpos = self._pos
            
    
    def __len__(self):
        return self._length

    length = property(_getlength, doc="the length of the BitString in bits")
    offset = property(_getoffset, _setoffset, doc="the offset of the BitString relative to being byte aligned")
    hex    = property(_gethex, _sethexsafe, doc="the BitString as a hexidecimal string (including leading zeros)")
    bin    = property(_getbin, _setbin, doc="the BitString as a binary string (including leading zeros)")
    data   = property(_getdata, _setdata, doc="the BitString as a ordinary string")
    int    = property(_getint, _setint, doc="the BitString as a two's complement signed int")
    uint   = property(_getuint, _setuint, doc="the BitString as an unsigned int")
    ue     = property(_getue, _setue, doc="the BitString as an unsigned Exponential Goulomb")
    se     = property(_getse, _setse, doc="the BitString as a signed Exponential Goulomb")
    bitpos = property(_getbitpos, _setbitpos, doc="the position in the BitString in bits")
    bytepos= property(_getbytepos, _setbytepos, doc="the position in the BitString in bytes")

     
def join(bitstrings):
    """Return the concatenation of the BitStrings in a list"""
    s = BitString(length = sum([s.length for s in bitstrings]))
    bits, offset, pos = 0, 0, 0
    for bs in bitstrings:
        bs.offset = offset
        for i in xrange(bs._data.length()):
            s._data[pos] |= bs._data[i]
            pos += 1
        offset = (offset + bs.length)%8
        bits += bs.length
        pos = bits / 8        
    return s
    