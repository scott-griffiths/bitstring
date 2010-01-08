

Deprecated methods
------------------
These methods were all present in the 1.0 release, but have now been deprecated to simplify the API as they have trivial alternatives and offer no extra functionality.

It is likely that they will be removed in version 2.0 so their use is discouraged.

.. method:: Bits.advancebit()

    Advances position by 1 bit.

    Equivalent to ``s.pos += 1``. 

.. method:: Bits.advancebits(bits)

   Advances position by ``bits`` bits.

   Equivalent to ``s.pos += bits``.

.. method:: Bits.advancebyte()

   Advances position by 8 bits.

   Equivalent to ``s.pos += 8``.

.. method:: Bits.advancebytes(bytes)

   Advances position by ``8*bytes`` bits.

   Equivalent to ``s.pos += 8*bytes``.

.. method:: BitString.delete(bits[, pos])

   Removes ``bits`` bits from the :class:`BitString` at position ``pos``. 

   Equivalent to ``del s[pos:pos+bits]``.
    
.. method:: Bits.retreatbit()

   Retreats position by 1 bit.

   Equivalent to ``s.pos -= 1``. 

.. method:: Bits.retreatbits(bits)

   Retreats position by ``bits`` bits.

   Equivalent to ``s.pos -= bits``. 

.. method:: Bits.retreatbyte()

   Retreats position by 8 bits.

   Equivalent to ``s.pos -= 8``.

.. method:: Bits.retreatbytes(bytes)

   Retreats position by ``bytes*8`` bits.

   Equivalent to ``s.pos -= 8*bytes``.

.. method:: Bits.seek(pos)

   Moves the current position to ``pos``.

   Equivalent to ``s.pos = pos``. 

.. method:: Bits.seekbyte(bytepos)

   Moves the current position to ``bytepos``.

   Equivalent to ``s.bytepos = bytepos``, or ``s.pos = bytepos*8``. 

.. method:: Bits.slice([start, end, step])

   Returns the :class:`BitString` slice ``s[start*step : end*step]``.
 
   It's use is equivalent to using the slice notation ``s[start:end:step]``; see :meth:`__getitem__` for examples.

.. method:: Bits.tell()

   Returns the current bit position.

   Equivalent to using the :attr:`pos` property as a getter.

.. method:: Bits.tellbyte()

   Returns the current byte position.

   Equivalent to using the :attr:`bytepos` property as a getter.

.. method:: BitString.truncateend(bits)

   Remove the last ``bits`` bits from the end of the :class:`BitString`.

   Equivalent to ``del s[-bits:]``.

.. method:: BitString.truncatestart(bits)

   Remove the first ``bits`` bits from the start of the :class:`BitString`.

   Equivalent to ``del s[:bits]``.

