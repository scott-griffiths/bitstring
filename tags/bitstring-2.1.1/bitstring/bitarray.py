#!/usr/bin/env python

import re
import collections
import copy
import numbers
import bitstring.constbitarray as constbitarray
from bitstring.bitstore import ByteArray
from bitstring.errors import Error

cba = constbitarray.ConstBitArray

# Hack for Python 3
try:
    xrange
except NameError:
    xrange = range
    basestring = str

class BitArray(constbitarray.ConstBitArray):

    """A container holding a mutable sequence of bits.

    Subclass of the immutable ConstBitArray class. Inherits all of its
    methods (except __hash__) and adds mutating methods.

    Mutating methods:

    append() -- Append a bitstring.
    byteswap() -- Change byte endianness in-place.
    insert() -- Insert a bitstring.
    invert() -- Flip bit(s) between one and zero.
    overwrite() -- Overwrite a section with a new bitstring.
    prepend() -- Prepend a bitstring.
    replace() -- Replace occurences of one bitstring with another.
    reverse() -- Reverse bits in-place.
    rol() -- Rotate bits to the left.
    ror() -- Rotate bits to the right.
    set() -- Set bit(s) to 1 or 0.

    Methods inherited from ConstBitArray:

    all() -- Check if all specified bits are set to 1 or 0.
    any() -- Check if any of specified bits are set to 1 or 0.
    count() -- Count the number of bits set to 1 or 0.
    cut() -- Create generator of constant sized chunks.
    endswith() -- Return whether the bitstring ends with a sub-string.
    find() -- Find a sub-bitstring in the current bitstring.
    findall() -- Find all occurences of a sub-bitstring in the current bitstring.
    join() -- Join bitstrings together using current bitstring.
    rfind() -- Seek backwards to find a sub-bitstring.
    split() -- Create generator of chunks split by a delimiter.
    startswith() -- Return whether the bitstring starts with a sub-bitstring.
    tobytes() -- Return bitstring as bytes, padding if needed.
    tofile() -- Write bitstring to file, padding if needed.
    unpack() -- Interpret bits using format string.

    Special methods:

    Mutating operators are available: [], <<=, >>=, *=, &=, |= and ^=
    in addition to the inherited [], ==, !=, +, *, ~, <<, >>, &, | and ^.

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

    # As BitArray objects are mutable, we shouldn't allow them to be hashed.
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
        # For mutable BitArrays we always read in files to memory:
        if not isinstance(self._datastore, ByteArray):
            self._ensureinmemory()

    def __iadd__(self, bs):
        """Append bs to current bitstring. Return self.

        bs -- the bitstring to append.

        """
        self.append(bs)
        return self

    def __setitem__(self, key, value):
        """Set item or range to new value.

        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.

        If the length of the bitstring is changed then pos will be moved
        to after the inserted section, otherwise it will remain unchanged.

        >>> s = BitArray('0xff')
        >>> s[0:1:4] = '0xe'
        >>> print s
        '0xef'
        >>> s[4:4] = '0x00'
        >>> print s
        '0xe00f'

        """
        try:
            # A slice
            start, step = 0, 1
            if key.step is not None:
                step = key.step
        except AttributeError:
            # single element
            if key < 0:
                key += self.len
            if not 0 <= key < self.len:
                raise IndexError("Slice index out of range.")
            if isinstance(value, numbers.Integral):
                if value == 0:
                    self._unset(key)
                    return
                if value in (1, -1):
                    self._set(key)
                    return
                raise ValueError("Cannot set a single bit with integer {0}.".format(value))
            value = self._converttobitstring(value)
            if value.len == 1:
                # TODO: this can't be optimal
                if value[0]:
                    self._set(key)
                else:
                    self._unset(key)
            else:
                self._delete(1, key)
                self._insert(value, key)
            return
        else:
            # If value is an integer then we want to set the slice to that
            # value rather than initialise a new bitstring of that length.
            if not isinstance(value, numbers.Integral):
                try:
                    value = self._converttobitstring(value)
                except TypeError:
                    raise TypeError("Bitstring, integer or string expected. "
                                    "Got {0}.".format(type(value)))
            if step == 0:
                stop = 0
            else:
                # default stop needs to be a multiple of step
                stop = self.len
                if key.stop is not None:
                    stop -= (self.len % abs(step))
            if key.start is not None:
                start = key.start * abs(step)
                if key.start < 0:
                    start += stop
                if start < 0:
                    start = 0
            if key.stop is not None:
                stop = key.stop * abs(step)
                if key.stop < 0:
                    stop += self.len - (self.len % abs(step))
            # Adjust start and stop if we're stepping backwards
            if step < 0:
                if key.start is None:
                    start = self.len + step
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
                    raise ValueError("Attempt to assign to badly defined "
                                     "extended slice.")
            if isinstance(value, numbers.Integral):
                if value >= 0:
                    value = self.__class__(uint=value, length=stop - start)
                else:
                    value = self.__class__(int=value, length=stop - start)
            stop = min(stop, self.len)
            start = max(start, 0)
            start = min(start, stop)
            if (stop - start) == value.len:
                if value.len == 0:
                    return
                if step >= 0:
                    self._overwrite(value, start)
                else:
                    self._overwrite(value.__getitem__(slice(None, None, step)), start)
            else:
                # TODO: A delete then insert is wasteful - it could do unneeded shifts.
                # Could be either overwrite + insert or overwrite + delete.
                self._delete(stop - start, start)
                if step >= 0:
                    self._insert(value, start)
                else:
                    self._insert(value.__getitem__(slice(None, None, step)), start)
                # pos is now after the inserted piece.
            return


    def __delitem__(self, key):
        """Delete item or range.

        Indices are in units of the step parameter (default 1 bit).
        Stepping is used to specify the number of bits in each item.

        >>> a = BitArray('0x001122')
        >>> del a[1:2:8]
        >>> print a
        0x0022

        """
        try:
            # A slice
            start = 0
            step = key.step if key.step is not None else 1
        except AttributeError:
            # single element
            if key < 0:
                key += self.len
            if not 0 <= key < self.len:
                raise IndexError("Slice index out of range.")
            self._delete(1, key)
            return
        else:
            if step == 0:
                stop = 0
            else:
                # default stop needs to be a multiple of step
                stop = self.len
                if key.stop is not None:
                    stop -= self.len % abs(step)
            if key.start is not None:
                start = key.start * abs(step)
                if key.start < 0:
                    start += stop
                if start < 0:
                    start = 0
            if key.stop is not None:
                stop = key.stop * abs(step)
                if key.stop < 0:
                    stop += self.len - (self.len % abs(step))
            # Adjust start and stop if we're stepping backwards
            if step < 0:
                if key.start is None:
                    start = self.len + step
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
                    raise ValueError("Attempt to delete badly defined "
                                     "extended slice.")
            stop = min(stop, self.len)
            start = max(start, 0)
            start = min(start, stop)
            self._delete(stop - start, start)
            return


    def __ilshift__(self, n):
        """Shift bits by n to the left in place. Return self.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        if n == 0:
            return self
        n = min(n, self.len)
        return self._ilshift(n)

    def __irshift__(self, n):
        """Shift bits by n to the right in place. Return self.

        n -- the number of bits to shift. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot shift by a negative amount.")
        if not self.len:
            raise ValueError("Cannot shift an empty bitstring.")
        if n == 0:
            return self
        n = min(n, self.len)
        return self._irshift(n)

    def __imul__(self, n):
        """Concatenate n copies of self in place. Return self.

        Called for expressions of the form 'a *= 3'.
        n -- The number of concatenations. Must be >= 0.

        """
        if n < 0:
            raise ValueError("Cannot multiply by a negative integer.")
        return self._imul(n)

    def __ior__(self, bs):
        bs = self._converttobitstring(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length "
                             "for |= operator.")
        return self._ior(bs)

    def __iand__(self, bs):
        bs = self._converttobitstring(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length "
                             "for &= operator.")
        return self._iand(bs)

    def __ixor__(self, bs):
        bs = self._converttobitstring(bs)
        if self.len != bs.len:
            raise ValueError("Bitstrings must have the same length "
                             "for ^= operator.")
        return self._ixor(bs)

    def _reverse(self):
        """Reverse all bits in-place."""
        # Reverse the contents of each byte
        n = [constbitarray.BYTE_REVERSAL_DICT[b] for b in self._datastore.rawbytes]
        # Then reverse the order of the bytes
        n.reverse()
        # The new offset is the number of bits that were unused at the end.
        newoffset = 8 - (self._offset + self.len) % 8
        if newoffset == 8:
            newoffset = 0
        self._setbytes_unsafe(bytearray().join(n), self.length, newoffset)

    def replace(self, old, new, start=None, end=None, count=None,
                bytealigned=False):
        """Replace all occurrences of old with new in place.

        Returns number of replacements made.

        old -- The bitstring to replace.
        new -- The replacement bitstring.
        start -- Any occurences that start before this will not be replaced.
                 Defaults to 0.
        end -- Any occurences that finish after this will not be replaced.
               Defaults to self.len.
        count -- The maximum number of replacements to make. Defaults to
                 replace all occurences.
        bytealigned -- If True replacements will only be made on byte
                       boundaries.

        Raises ValueError if old is empty or if start or end are
        out of range.

        """
        old = self._converttobitstring(old)
        new = self._converttobitstring(new)
        if not old.len:
            raise ValueError("Empty bitstring cannot be replaced.")
        start, end = self._validate_slice(start, end)
        # Adjust count for use in split()
        if count is not None:
            count += 1
        sections = self.split(old, start, end, count, bytealigned)
        lengths = [s.len for s in sections]
        if len(lengths) == 1:
            # Didn't find anything to replace.
            return 0 # no replacements done
        if new is self:
            # Prevent self assignment woes
            new = copy.copy(self)
        positions = [lengths[0] + start]
        for l in lengths[1:-1]:
            # Next position is the previous one plus the length of the next section.
            positions.append(positions[-1] + l)
        # We have all the positions that need replacements. We do them
        # in reverse order so that they won't move around as we replace.
        positions.reverse()
        try:
            # Need to calculate new pos, if this is a bitstream
            newpos = self._pos
            for p in positions:
                self[p:p + old.len] = new
            if old.len != new.len:
                diff = new.len - old.len
                for p in positions:
                    if p >= newpos:
                        continue
                    if p + old.len <= newpos:
                        newpos += diff
                    else:
                        newpos = p
            self._pos = newpos
        except AttributeError:
            for p in positions:
                self[p:p + old.len] = new
        assert self._assertsanity()
        return len(lengths) - 1

    def insert(self, bs, pos=None):
        """Insert bs at bit position pos.

        bs -- The bitstring to insert.
        pos -- The bit position to insert at.

        Raises ValueError if pos < 0 or pos > self.len.

        """
        bs = self._converttobitstring(bs)
        if not bs.len:
            return self
        if bs is self:
            bs = self.__copy__()
        if pos is None:
            try:
                pos = self._pos
            except AttributeError:
                raise TypeError("insert require a bit position for this type.")
        if pos < 0:
            pos += self.len
        if not 0 <= pos <= self.len:
            raise ValueError("Invalid insert position.")
        self._insert(bs, pos)

    def overwrite(self, bs, pos=None):
        """Overwrite with bs at bit position pos.

        bs -- The bitstring to overwrite with.
        pos -- The bit position to begin overwriting from.

        Raises ValueError if pos < 0 or pos + bs.len > self.len

        """
        bs = self._converttobitstring(bs)
        if not bs.len:
            return
        if pos is None:
            try:
                pos = self._pos
            except AttributeError:
                raise TypeError("overwrite require a bit position for this type.")
        if pos < 0:
            pos += self.len
        if pos < 0 or pos + bs.len > self.len:
            raise ValueError("Overwrite exceeds boundary of bitstring.")
        self._overwrite(bs, pos)
        try:
            self._pos = pos + bs.len
        except AttributeError:
            pass

    def append(self, bs):
        """Append a bitstring to the current bitstring.

        bs -- The bitstring to append.

        """
        # The offset is a hint to make bs easily appendable.
        bs = self._converttobitstring(bs, offset=(self.len + self._offset) % 8)
        self._append(bs)

    def prepend(self, bs):
        """Prepend a bitstring to the current bitstring.

        bs -- The bitstring to prepend.

        """
        bs = self._converttobitstring(bs)
        self._prepend(bs)

    def reverse(self, start=None, end=None):
        """Reverse bits in-place.

        start -- Position of first bit to reverse. Defaults to 0.
        end -- One past the position of the last bit to reverse.
               Defaults to self.len.

        Using on an empty bitstring will have no effect.

        Raises ValueError if start < 0, end > self.len or end < start.

        """
        start, end = self._validate_slice(start, end)
        if start == 0 and end == self.len:
            self._reverse()
            return
        s = self[start:end]
        s._reverse()
        self[start:end] = s

    def set(self, value, pos=None):
        """Set one or many bits to 1 or 0.

        value -- If True bits are set to 1, otherwise they are set to 0.
        pos -- Either a single bit position or an iterable of bit positions.
               Negative numbers are treated in the same way as slice indices.
               Defaults to the entire bitstring.

        Raises IndexError if pos < -self.len or pos >= self.len.

        """
        f = self._set if value else self._unset
        if pos is None:
            pos = xrange(self.len)
        try:
            length = self.len
            for p in pos:
                if p < 0:
                    p += length
                if not 0 <= p < length:
                    raise IndexError("Bit position {0} out of range.".format(p))
                f(p)
        except TypeError:
            # Single pos
            if pos < 0:
                pos += self.len
            if not 0 <= pos < length:
                raise IndexError("Bit position {0} out of range.".format(pos))
            f(pos)

    def invert(self, pos=None):
        """Invert one or many bits from 0 to 1 or vice versa.

        pos -- Either a single bit position or an iterable of bit positions.
               Negative numbers are treated in the same way as slice indices.

        Raises IndexError if pos < -self.len or pos >= self.len.

        """
        if pos is None:
            self._invert_all()
            return
        if not isinstance(pos, collections.Iterable):
            pos = (pos,)
        length = self.len
        for p in pos:
            if p < 0:
                p += length
            if not 0 <= p < length:
                raise IndexError("Bit position {0} out of range.".format(p))
            self._invert(p)

    def ror(self, bits, start=None, end=None):
        """Rotate bits to the right in-place.

        bits -- The number of bits to rotate by.
        start -- Start of slice to rotate. Defaults to 0.
        end -- End of slice to rotate. Defaults to self.len.

        Raises ValueError if bits < 0.

        """
        if self.len == 0:
            raise Error("Cannot rotate an empty bitstring.")
        if bits < 0:
            raise ValueError("Cannot rotate right by negative amount.")
        start, end = self._validate_slice(start, end)
        bits %= (end - start)
        if bits == 0:
            return
        rhs = self[end - bits:end]
        del self[end - bits:end]
        self.insert(rhs, start)

    def rol(self, bits, start=None, end=None):
        """Rotate bits to the left in-place.

        bits -- The number of bits to rotate by.
        start -- Start of slice to rotate. Defaults to 0.
        end -- End of slice to rotate. Defaults to self.len.

        Raises ValueError if bits < 0.

        """
        if self.len == 0:
            raise Error("Cannot rotate an empty bitstring.")
        if bits < 0:
            raise ValueError("Cannot rotate left by negative amount.")
        start, end = self._validate_slice(start, end)
        bits %= (end - start)
        if bits == 0:
            return
        lhs = self[start:start + bits]
        del self[start:start + bits]
        self.insert(lhs, end - bits)

    def byteswap(self, fmt=None, start=None, end=None, repeat=True):
        """Change the endianness in-place. Return number of repeats of fmt done.

        fmt -- A compact structure string, an integer number of bytes or
               an iterable of integers. Defaults to 0, which byte reverses the
               whole bitstring.
        start -- Start bit position, defaults to 0.
        end -- End bit position, defaults to self.len.
        repeat -- If True (the default) the byte swapping pattern is repeated
                  as much as possible.

        """
        start, end = self._validate_slice(start, end)
        if fmt is None or fmt == 0:
            # reverse all of the whole bytes.
            bytesizes = [(end - start) // 8]
        elif isinstance(fmt, numbers.Integral):
            if fmt < 0:
                raise ValueError("Improper byte length {0}.".format(fmt))
            bytesizes = [fmt]
        elif isinstance(fmt, basestring):
            m = constbitarray.STRUCT_PACK_RE.match(fmt)
            if not m:
                raise ValueError("Cannot parse format string {0}.".format(fmt))
            # Split the format string into a list of 'q', '4h' etc.
            formatlist = re.findall(constbitarray.STRUCT_SPLIT_RE, m.group('fmt'))
            # Now deal with multiplicative factors, 4h -> hhhh etc.
            bytesizes = []
            for f in formatlist:
                if len(f) == 1:
                    bytesizes.append(constbitarray.PACK_CODE_SIZE[f])
                else:
                    bytesizes.extend([constbitarray.PACK_CODE_SIZE[f[-1]]]*int(f[:-1]))
        elif isinstance(fmt, collections.Iterable):
            bytesizes = fmt
            for bytesize in bytesizes:
                if not isinstance(bytesize, numbers.Integral) or bytesize < 0:
                    raise ValueError("Improper byte length {0}.".format(bytesize))
        else:
            raise ValueError("Format must be an integer, string or iterable.")

        repeats = 0
        totalbitsize = 8*sum(bytesizes)
        if not totalbitsize:
            return 0
        if repeat:
            # Try to repeat up to the end of the bitstring.
            finalbit = end
        else:
            # Just try one (set of) byteswap(s).
            finalbit = start + totalbitsize
        for patternend in xrange(start + totalbitsize, finalbit + 1, totalbitsize):
            bytestart = patternend - totalbitsize
            for bytesize in bytesizes:
                byteend = bytestart + bytesize*8
                self._reversebytes(bytestart, byteend)
                bytestart += bytesize*8
            repeats += 1
        return repeats


    int    = property(cba._getint, cba._setint,
                      doc="""The bitstring as a two's complement signed int. Read and write.
                      """)
    uint   = property(cba._getuint, cba._setuint,
                      doc="""The bitstring as a two's complement unsigned int. Read and write.
                      """)
    float  = property(cba._getfloat, cba._setfloat,
                      doc="""The bitstring as a floating point number. Read and write.
                      """)
    intbe  = property(cba._getintbe, cba._setintbe,
                      doc="""The bitstring as a two's complement big-endian signed int. Read and write.
                      """)
    uintbe = property(cba._getuintbe, cba._setuintbe,
                      doc="""The bitstring as a two's complement big-endian unsigned int. Read and write.
                      """)
    floatbe= property(cba._getfloat, cba._setfloat,
                      doc="""The bitstring as a big-endian floating point number. Read and write.
                      """)
    intle  = property(cba._getintle, cba._setintle,
                      doc="""The bitstring as a two's complement little-endian signed int. Read and write.
                      """)
    uintle = property(cba._getuintle, cba._setuintle,
                      doc="""The bitstring as a two's complement little-endian unsigned int. Read and write.
                      """)
    floatle= property(cba._getfloatle, cba._setfloatle,
                      doc="""The bitstring as a little-endian floating point number. Read and write.
                      """)
    intne  = property(cba._getintne, cba._setintne,
                      doc="""The bitstring as a two's complement native-endian signed int. Read and write.
                      """)
    uintne = property(cba._getuintne, cba._setuintne,
                      doc="""The bitstring as a two's complement native-endian unsigned int. Read and write.
                      """)
    floatne= property(cba._getfloatne, cba._setfloatne,
                      doc="""The bitstring as a native-endian floating point number. Read and write.
                      """)
    ue     = property(cba._getue, cba._setue,
                      doc="""The bitstring as an unsigned exponential-Golomb code. Read and write.
                      """)
    se     = property(cba._getse, cba._setse,
                      doc="""The bitstring as a signed exponential-Golomb code. Read and write.
                      """)
    hex    = property(cba._gethex, cba._sethex,
                      doc="""The bitstring as a hexadecimal string. Read and write.

                      When read will be prefixed with '0x' and including any leading zeros.

                      """)
    bin    = property(cba._getbin, cba._setbin_safe,
                      doc="""The bitstring as a binary string. Read and write.

                      When read will be prefixed with '0b' and including any leading zeros.

                      """)
    oct    = property(cba._getoct, cba._setoct,
                      doc="""The bitstring as an octal string. Read and write.

                      When read will be prefixed with '0o' and including any leading zeros.

                      """)
    bool   = property(cba._getbool, cba._setbool,
                      doc="""The bitstring as a bool (True or False). Read and write."""
                      )
    bytes  = property(cba._getbytes, cba._setbytes_safe,
                      doc="""The bitstring as a ordinary string. Read and write.
                      """)
