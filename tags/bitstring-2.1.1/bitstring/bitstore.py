#!/usr/bin/env python
"""
This modules is used by the Bits and BitString classes and does not form
part of the public interface. Please do not use this module directly as
it is largely undocumented and could change without warning.
"""

import copy
import os
import mmap
from bitstring.errors import CreationError


class MmapByteArray(object):
    """Looks like a bytearray, but from an mmap."""

    __slots__ = ('filemap', 'filelength', 'source')

    def __init__(self, source):
        self.source = source
        self.filelength = os.path.getsize(source.name)
        self.filemap = mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ)

    def __getitem__(self, key):
        try:
            start = key.start
            return bytearray(self.filemap.__getitem__(key))
        except AttributeError:
            try:
                return ord(self.filemap[key])
            except TypeError:
                # for Python 3
                return self.filemap[key]

    def __len__(self):
        return self.filelength


class ConstByteArray(object):
    """Stores raw bytes together with a bit offset and length."""

    __slots__ = ('offset', '_rawarray', 'bitlength')

    def __init__(self, data, bitlength=None, offset=None):
        self._rawarray = data
        if offset is None:
            offset = 0
        if bitlength is None:
            bitlength = 8*len(data) - offset
        self.offset = offset
        self.bitlength = bitlength
        
# TODO: It should be possible to remove this method...
    def __copy__(self):
        return ByteArray(self._rawarray[:], self.bitlength, self.offset)

    def getbit(self, pos):
        assert 0 <= pos < self.bitlength
        byte, bit = divmod(self.offset + pos, 8)
        return bool(self._rawarray[byte] & (128 >> bit))

    def getbyte(self, pos):
        return self._rawarray[pos + self.byteoffset]

    def getbyteslice(self, start, end):
        c = self._rawarray[start + self.byteoffset:end + self.byteoffset]
        return c

    @property
    def bytelength(self):
        if self.bitlength == 0:
            return 0
        sb = self.offset // 8
        eb = (self.offset + self.bitlength - 1) // 8
        if eb == -1:
            return 1 # ? Empty bitstring still has one byte of data?
        return eb - sb + 1

    @property
    def byteoffset(self):
        return self.offset // 8

    @property
    def rawbytes(self):
        return self._rawarray


class ByteArray(ConstByteArray):

    __slots__ = ()

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
        self._rawarray[pos + self.byteoffset] = value

    def setbyteslice(self, start, end, value):
        self._rawarray[start + self.byteoffset:end + self.byteoffset] = value

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


def slice(ba, bitlength, offset):
    """Return a new ByteArray created as a slice of ba."""
    try:
        return ByteArray(ba._rawarray, bitlength, ba.offset + offset)
    except AttributeError:
        return FileArray(ba.source, bitlength, 8*ba.byteoffset + ba.offset + offset)

def offsetcopy(s, newoffset):
    """Return a copy of s with the newoffset."""
    assert 0 <= newoffset < 8
    if s.bitlength == 0:
        return copy.copy(s)
    else:
        if newoffset == s.offset % 8:
            return ByteArray(s.getbyteslice(0, s.bytelength), s.bitlength, newoffset)

        assert 0 <= newoffset < 8
        newdata = []
        d = s._rawarray
        assert newoffset != s.offset % 8
        if newoffset < s.offset % 8:
            # We need to shift everything left
            shiftleft = s.offset % 8 - newoffset
            # First deal with everything except for the final byte
            for x in range(s.byteoffset, s.byteoffset + s.bytelength - 1):
                newdata.append(((d[x] << shiftleft) & 0xff) + \
                                     (d[x + 1] >> (8 - shiftleft)))
            bits_in_last_byte = (s.offset + s.bitlength) % 8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte > shiftleft:
                newdata.append((d[s.byteoffset + s.bytelength - 1] << shiftleft) & 0xff)
        else: # newoffset > s._offset % 8
            shiftright = newoffset - s.offset % 8
            newdata.append(s.getbyte(0) >> shiftright)
            for x in range(1, s.bytelength):
                newdata.append(((d[x-1] << (8 - shiftright)) & 0xff) + \
                                     (d[x] >> shiftright))
            bits_in_last_byte = (s.offset + s.bitlength) % 8
            if bits_in_last_byte == 0:
                bits_in_last_byte = 8
            if bits_in_last_byte + shiftright > 8:
                newdata.append((d[s.byteoffset + s.bytelength - 1] << (8 - shiftright)) & 0xff)
        new_s = ByteArray(bytearray(newdata), s.bitlength, newoffset)
        assert new_s.offset == newoffset
        return new_s

def equal(a, b):
    """Return True if a == b."""

    a_bitlength = a.bitlength
    b_bitlength = b.bitlength
    if a_bitlength != b_bitlength:
        return False
    if a_bitlength == 0:
        return True
    # Make 'a' the one with the smaller offset
    if (a.offset % 8) > (b.offset % 8):
        a, b = b, a
    a_bitoff = a.offset % 8
    b_bitoff = b.offset % 8
    a_byteoffset = a.byteoffset
    b_byteoffset = b.byteoffset
    a_bytelength = a.bytelength
    b_bytelength = b.bytelength

    da = a._rawarray
    db = b._rawarray

    # If they are pointing to the same data, they must be equal
    if da is db and a.offset == b.offset:
        return True

    if a_bitoff == b_bitoff:
        bits_spare_in_last_byte = 8 - (a_bitoff + a_bitlength) % 8
        if bits_spare_in_last_byte == 8:
            bits_spare_in_last_byte = 0
        # Special case for a, b contained in a single byte
        if a_bytelength == 1:
            a_val = ((da[a_byteoffset] << a_bitoff) & 0xff) >> (8 - a_bitlength)
            b_val = ((db[b_byteoffset] << b_bitoff) & 0xff) >> (8 - b_bitlength)
            return a_val == b_val
        # Otherwise check first byte
        if da[a_byteoffset] & (0xff >> a_bitoff) != db[b_byteoffset] & (0xff >> b_bitoff):
            return False
        # then everything up to the last
        b_a_offset = b_byteoffset - a_byteoffset
        for x in range(1 + a_byteoffset, a_byteoffset + a_bytelength - 1):
            if da[x] != db[b_a_offset + x]:
                return False
        # and finally the last byte
        if da[a_byteoffset + a_bytelength - 1] >> bits_spare_in_last_byte != db[b_byteoffset + b_bytelength - 1] >> bits_spare_in_last_byte:
            return False
        return True

    # This is how much we need to shift a to the right to compare with b:
    shift = b_bitoff - a_bitoff
    # Special case for b only one byte long
    if b_bytelength == 1:
        assert a_bytelength == 1
        a_val = ((da[a_byteoffset] << a_bitoff) & 0xff) >> (8 - a_bitlength)
        b_val = ((db[b_byteoffset] << b_bitoff) & 0xff) >> (8 - b_bitlength)
        return a_val == b_val
    # Special case for a only one byte long
    if a_bytelength == 1:
        assert b_bytelength == 2
        a_val = ((da[a_byteoffset] << a_bitoff) & 0xff) >> (8 - a_bitlength)
        b_val = db[b_byteoffset] << 8
        b_val += db[b_byteoffset + 1]
        b_val <<= b_bitoff
        b_val &= 0xffff
        b_val >>= 16 - b_bitlength
        return a_val == b_val

    # Compare first byte of b with bits from first byte of a
    if (da[a_byteoffset] & (0xff >> a_bitoff)) >> shift != db[b_byteoffset] & (0xff >> b_bitoff):
        return False
    # Now compare every full byte of b with bits from 2 bytes of a
    for x in range(1, b_bytelength - 1):
        # Construct byte from 2 bytes in a to compare to byte in b
        b_val = db[b_byteoffset + x]
        a_val = da[a_byteoffset + x - 1] << 8
        a_val += da[a_byteoffset + x]
        a_val >>= shift
        a_val &= 0xff
        if a_val != b_val:
            return False

    # Now check bits in final byte of b
    final_b_bits = (b.offset + b_bitlength) % 8
    if final_b_bits == 0:
        final_b_bits = 8
    b_val = db[b_byteoffset + b_bytelength - 1] >> (8 - final_b_bits)
    final_a_bits = (a.offset + a_bitlength) % 8
    if final_a_bits == 0:
        final_a_bits = 8
    if b.bytelength > a_bytelength:
        assert b_bytelength == a_bytelength + 1
        a_val = da[a_byteoffset + a_bytelength - 1] >> (8 - final_a_bits)
        a_val &= 0xff >> (8 - final_b_bits)
        return a_val == b_val
    assert a_bytelength == b_bytelength
    a_val = da[a_byteoffset + a_bytelength - 2] << 8
    a_val += da[a_byteoffset + a_bytelength - 1]
    a_val >>= (8 - final_a_bits)
    a_val &= 0xff >> (8 - final_b_bits)
    return a_val == b_val


