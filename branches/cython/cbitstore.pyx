#!/usr/bin/env python

import copy
import os


cdef class ByteArray:
    """Stores raw bytes together with a bit offset and length."""

    cpdef public int offset, bitlength
    cpdef public object _rawarray

    def __init__(self, data, int bitlength=0, int offset=0):
        self._rawarray = bytearray(data[offset // 8:(offset + bitlength + 7) // 8])
        self.offset = offset % 8
        self.bitlength = bitlength
        assert (self.bitlength + self.offset + 7) // 8 == len(self._rawarray), "bitlength:{0}, offset:{1}, bytelength:{2}".format(self.bitlength, self.offset, len(self._rawarray))

    def __copy__(self):
        return ByteArray(self._rawarray, self.bitlength, self.offset)

    def getbit(self, int pos):
        assert 0 <= pos < self.bitlength
        cdef int byte, bit
        byte, bit = divmod(self.offset + pos, 8)
        return bool(self._rawarray[byte] & (128 >> bit))

    def getbyte(self, int pos):
        return self._rawarray[pos]

    def getbyteslice(self, int start, int end):
        c = self._rawarray[start:end]
        # We convert to bytes because struct.unpack can't handle a bytearray (in Python 2.6 only).
        # Probably a struct module bug. We could return a buffer object here though, but I don't
        # think that it would be faster.
        return bytes(c)

    def setbit(self, int pos):
        assert 0 <= pos < self.bitlength
        cdef int byte, bit
        byte, bit = divmod(self.offset + pos, 8)
        self._rawarray[byte] |= (128 >> bit)

    def unsetbit(self, int pos):
        assert 0 <= pos < self.bitlength
        cdef int byte, bit
        byte, bit = divmod(self.offset + pos, 8)
        self._rawarray[byte] &= ~(128 >> bit)
        
    def invertbit(self, int pos):
        assert 0 <= pos < self.bitlength
        cdef int byte, bit
        byte, bit = divmod(self.offset + pos, 8)
        self._rawarray[byte] ^= (128 >> bit)

    def setbyte(self, int pos, int value):
        self._rawarray[pos] = value

    def setbyteslice(self, int start, int end, value):
        self._rawarray[start:end] = value

    def setoffset(self, int newoffset):
        """Realign BitString with new offset to first bit."""
        cdef int shiftleft, bits_in_last_byte, shiftright, x
        if newoffset != self.offset:
            assert 0 <= newoffset < 8
            data = self._rawarray
            if newoffset < self.offset:
                # We need to shift everything left
                shiftleft = self.offset - newoffset
                # First deal with everything except for the final byte
                for x in range(self.bytelength - 1):
                    data[x] = ((data[x] << shiftleft) & 255) + \
                                         (data[x + 1] >> (8 - shiftleft))
                # if we've shifted all of the data in the last byte then we need
                # to truncate by 1
                bits_in_last_byte = (self.offset + self.bitlength) % 8
                if bits_in_last_byte == 0:
                    bits_in_last_byte = 8
                if bits_in_last_byte <= shiftleft:
                    # Remove the last byte
                    data.pop()
                # otherwise just shift the last byte
                else:
                    data[-1] = (data[-1] << shiftleft) & 255
            else: # offset > self._offset
                shiftright = newoffset - self.offset
                # Give some overflow room for the last byte
                b = self.offset + self.bitlength + 7
                if (b + shiftright) // 8 > b // 8:
                    self._rawarray.append(0)
                for x in range(self.bytelength - 1, 0, -1):
                    data[x] = ((data[x-1] << (8 - shiftright)) & 255) + \
                                         (data[x] >> shiftright)
                data[0] >>= shiftright
            self.offset = newoffset

    def appendarray(self, ByteArray array):
        """Join another array on to the end of this one."""
        cdef int joinval
        # TODO: The copy here and in prepend array is needed in case array is self
        # or if array is a FileArray. The logic needs looking at to see when it can
        # be skipped.
        array = copy.copy(array)
        # Set new array offset to the number of bits in the final byte of current array.
        array.setoffset((self.offset + self.bitlength) % 8)
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
        # Set the offset of copy of array so that it's final byte
        # ends in a position that matches the offset of self,
        # then join self on to the end of it.
        array = copy.copy(array)
        array.setoffset((self.offset - array.bitlength) % 8)
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


class FileArray(object):
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
            return self.source.read(end - start)
        else:
            return b''

    @property
    def rawbytes(self):
        return bytearray(self.getbyteslice(0, self.bytelength))
        
