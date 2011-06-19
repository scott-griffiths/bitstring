
from cbits import *
import bitstring


def findall(self, bs, start=None, end=None, count=None, bytealigned=None):
    """Find all occurrences of bs. Return generator of bit positions.

    bs -- The bitstring to find.
    start -- The bit position to start the search. Defaults to 0.
    end -- The bit position one past the last bit to search.
           Defaults to self.len.
    count -- The maximum number of occurrences to find.
    bytealigned -- If True the bitstring will only be found on
                   byte boundaries.

    Raises ValueError if bs is empty, if start < 0, if end > self.len or
    if end < start.

    Note that all occurrences of bs are found, even if they overlap.

    """
    if count is not None and count < 0:
        raise ValueError("In findall, count must be >= 0.")
    bs = ConstBitArray(bs)
    start, end = self._validate_slice(start, end)
    if bytealigned is None:
        bytealigned = bitstring.bytealigned
    c = 0
    while True:
        p = self.find(bs, start, end, bytealigned)
        if not p:
            break
        if count is not None and c >= count:
            return
        c += 1
        yield p[0]
        if bytealigned:
            start = p[0] + 8
        else:
            start = p[0] + 1
        if start >= end:
            break
    return

def cut(self, bits, start=None, end=None, count=None):
    """Return bitstring generator by cutting into bits sized chunks.

    bits -- The size in bits of the bitstring chunks to generate.
    start -- The bit position to start the first cut. Defaults to 0.
    end -- The bit position one past the last bit to use in the cut.
           Defaults to self.len.
    count -- If specified then at most count items are generated.
             Default is to cut as many times as possible.

    """
    start, end = self._validate_slice(start, end)
    if count is not None and count < 0:
        raise ValueError("Cannot cut - count must be >= 0.")
    if bits <= 0:
        raise ValueError("Cannot cut - bits must be >= 0.")
    c = 0
    while count is None or c < count:
        c += 1
        nextchunk = self._slice(start, min(start + bits, end))
        if nextchunk.len != bits:
            return
        assert nextchunk._assertsanity()
        yield nextchunk
        start += bits
    return

def split(self, delimiter, start=None, end=None, count=None,
          bytealigned=None):
    """Return bitstring generator by splittling using a delimiter.

    The first item returned is the initial bitstring before the delimiter,
    which may be an empty bitstring.

    delimiter -- The bitstring used as the divider.
    start -- The bit position to start the split. Defaults to 0.
    end -- The bit position one past the last bit to use in the split.
           Defaults to self.len.
    count -- If specified then at most count items are generated.
             Default is to split as many times as possible.
    bytealigned -- If True splits will only occur on byte boundaries.

    Raises ValueError if the delimiter is empty.

    """
    delimiter = ConstBitArray(delimiter)
    if not delimiter.len:
        raise ValueError("split delimiter cannot be empty.")
    start, end = self._validate_slice(start, end)
    if bytealigned is None:
        bytealigned = bitstring.bytealigned
    if count is not None and count < 0:
        raise ValueError("Cannot split - count must be >= 0.")
    if count == 0:
        return
    # Use the base class find as we don't want to ever alter _pos.
    found = ConstBitArray.find(self, delimiter, start, end, bytealigned)
    if not found:
        # Initial bits are the whole bitstring being searched
        yield self._slice(start, end)
        return
    # yield the bytes before the first occurrence of the delimiter, even if empty
    yield self[start:found[0]]
    startpos = pos = found[0]
    c = 1
    while count is None or c < count:
        pos += delimiter.len
        found = ConstBitArray.find(self, delimiter, pos, end, bytealigned)
        if not found:
            # No more occurrences, so return the rest of the bitstring
            yield self[startpos:end]
            return
        c += 1
        yield self[startpos:found[0]]
        startpos = pos = found[0]
    # Have generated count bitstrings, so time to quit.
    return

ConstBitArray.findall = findall
ConstBitArray.split = split
ConstBitArray.cut = cut