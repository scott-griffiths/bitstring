#!/usr/bin/env python

import copy
import os

class BaseArray(object):
    """Array types should implement the methods given here."""

    __slots__ = ()

    def __init__(self, data, bitlength=0, offset=0):
        raise NotImplementedError

    def getbit(self, pos):
        """Return the bit at pos (True or False)."""
        raise NotImplementedError

    def getbyte(self, pos):
        """Return the integer value of the byte stored at pos."""
        raise NotImplementedError

    def getbyteslice(self, start, end):
        """Return a byte slice"""
        raise NotImplementedError

    def __copy__(self):
        raise NotImplementedError

    def setoffset(self, newoffset):
        raise NotImplementedError

    def appendarray(self, array):
        raise NotImplementedError

    def prependarray(self, array):
        raise NotImplementedError

# Need to just take a reference to the data that is passed in - don't copy it.
# Then need to make sure what's passed in isn't unneccesarily large!
# The offset can then be > 8 (no need to % it).
# Might need to add a byteoffset / bitoffset pair.
# Then change getbit, getbyte etc.
# Then a bytearrayview can be created as just a ByteArray - using same underlying bytes.


class ByteArray(BaseArray):
    """Stores raw bytes together with a bit offset and length."""

    __slots__ = ('offset', '_rawarray', 'bitlength')

    def __init__(self, data, bitlength=0, offset=0):
        assert isinstance(data, bytearray)
        self._rawarray = data[:]
        self.offset = offset
        self.bitlength = bitlength
        assert (self.bitlength + self.offset + 7) // 8 == len(self._rawarray), "bitlength:{0}, offset:{1}, bytelength:{2}".format(self.bitlength, self.offset, len(self._rawarray))

    def __copy__(self):
        return ByteArray(self._rawarray, self.bitlength, self.offset)

    def getbit(self, pos):
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        return bool(self._rawarray[byte] & (128 >> bit))

    def getbyte(self, pos):
        return self._rawarray[pos]

    def getbyteslice(self, start, end):
        c = self._rawarray[start:end]
        return c

    def setbit(self, pos):
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        self._rawarray[byte] |= (128 >> bit)

    def unsetbit(self, pos):
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        self._rawarray[byte] &= ~(128 >> bit)
        
    def invertbit(self, pos):
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        self._rawarray[byte] ^= (128 >> bit)

    def setbyte(self, pos, value):
        self._rawarray[pos] = value

    def setbyteslice(self, start, end, value):
        self._rawarray[start:end] = value

    def appendarray(self, array):
        """Join another array on to the end of this one."""
        if array.bitlength == 0:
            return
        # Set new array offset to the number of bits in the final byte of current array.
        array = offsetcopy(array, (self.offset + self.bitlength) % 8)
        if array.offset != 0:
            # first do the byte with the join.
            joinval = (self._rawarray.pop() & (255 ^ (255 >> array.offset)) | (array.getbyte(0) & (255 >> array.offset)))
            self._rawarray.append(joinval)
            self._rawarray.extend(array._rawarray[1:])
        else:
            self._rawarray.extend(array._rawarray)
        self.bitlength += array.bitlength

    def prependarray(self, array):
        """Join another array on to the start of this one."""
        if array.bitlength == 0:
            return
        # Set the offset of copy of array so that it's final byte
        # ends in a position that matches the offset of self,
        # then join self on to the end of it.
        array = offsetcopy(array, (self.offset - array.bitlength) % 8)
        assert (array.offset + array.bitlength) % 8 == self.offset
        if self.offset != 0:
            # first do the byte with the join.
            array.setbyte(-1, (array.getbyte(-1) & (255 ^ (255 >> self.offset)) | \
                                   (self._rawarray[0] & (255 >> self.offset))))
            array._rawarray.extend(self._rawarray[1 : self.bytelength])
        else:
            array._rawarray.extend(self._rawarray[0 : self.bytelength])
        self._rawarray = array._rawarray
        self.offset = array.offset
        self.bitlength += array.bitlength

    @property
    def bytelength(self):
        return len(self._rawarray)

    @property
    def rawbytes(self):
        return self._rawarray


class FileArray(BaseArray):
    """A class that mimics bytearray but gets data from a file object."""

    __slots__ = ('source', 'bytelength', 'bitlength', 'byteoffset', 'offset')

    def __init__(self, source, bitlength, offset):
        # byteoffset - bytes to ignore at start of file
        # bitoffset - bits (0-7) to ignore after the byteoffset
        byteoffset, bitoffset = divmod(offset, 8)
        filelength = os.path.getsize(source.name)
        self.source = source
        if bitlength is None:
            self.bytelength = filelength - byteoffset
            bitlength = self.bytelength*8 - bitoffset
        else:
            self.bytelength = (bitlength + bitoffset + 7) // 8
        if self.bytelength > filelength - byteoffset:
            from bitstring import CreationError
            raise CreationError("File is not long enough for specified "
                                "bitstring length and offset.")
        self.byteoffset = byteoffset
        self.bitlength = bitlength
        self.offset = bitoffset

    def __copy__(self):
        # Asking for a copy of a FileArray gets you a MemArray. After all,
        # why would you want a copy if you didn't want to modify it?
        return ByteArray(self.rawbytes, self.bitlength, self.offset)

    def getbyte(self, pos):
        if pos < 0:
            pos += self.bytelength
        pos += self.byteoffset
        self.source.seek(pos, os.SEEK_SET)
        return ord(self.source.read(1))

    def getbit(self, pos):
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        byte += self.byteoffset
        self.source.seek(byte, os.SEEK_SET)
        return bool(ord(self.source.read(1)) & (128 >> bit))

    def getbyteslice(self, start, end):
        if start < end:
            self.source.seek(start + self.byteoffset, os.SEEK_SET)
            return bytearray(self.source.read(end - start))
        else:
            return bytearray()

    @property
    def rawbytes(self):
        return bytearray(self.getbyteslice(0, self.bytelength))
        
        
def offsetcopy(s, newoffset):
    """Return a copy of s with the newoffset. Is allowed to return s
    as an optimisation if newoffset==s.offset and s is immutable."""
    if newoffset == s.offset or s.bitlength == 0:
        return copy.copy(s)
    else:
        assert 0 <= newoffset < 8
        newdata = []
        d = s._rawarray
        if newoffset < s.offset:
            # We need to shift everything left
            shiftleft = s.offset - newoffset
            # First deal with everything except for the final byte
            for x in range(s.bytelength - 1):
                newdata.append(((d[x] << shiftleft) & 0xff) + \
                                     (d[x + 1] >> (8 - shiftleft)))
            bits_in_last_byte = (s.offset + s.bitlength) % 8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte > shiftleft:
                newdata.append((d[-1] << shiftleft) & 0xff)
        else: # newoffset > s._offset
            shiftright = newoffset - s.offset
            newdata.append(s.getbyte(0) >> shiftright)
            for x in range(1, s.bytelength):
                newdata.append(((d[x-1] << (8 - shiftright)) & 0xff) + \
                                     (d[x] >> shiftright))
            bits_in_last_byte = (s.offset + s.bitlength) % 8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte + shiftright > 8:
                newdata.append((d[-1] << (8 - shiftright)) & 0xff)
        new_s = ByteArray(bytearray(newdata), s.bitlength, newoffset)
        assert new_s.offset == newoffset
        assert (new_s.offset + new_s.bitlength + 7) // 8 == new_s.bytelength
        return new_s
    
