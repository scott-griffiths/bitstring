.. currentmodule:: bitstring

BitStream
=========

.. class:: BitStream(auto: BitsType | int | None, /, length: int | None = None, offset: int | None = None, pos: int = 0, **kwargs)

    Both the :class:`BitArray` and the :class:`ConstBitStream` classes are base classes for :class:`BitStream` and so all of their methods are also available for :class:`BitStream` objects. The initialiser is the same as for :class:`ConstBitStream`.

    A :class:`BitStream` is a mutable container of bits with methods and properties that allow it to be parsed as a stream of bits. There are no additional methods or properties in this class - see its base classes (:class:`Bits`, :class:`BitArray` and :class:`ConstBitStream`) for details.


The ``pos`` will also used as a default for the :meth:`BitArray.overwrite` and :meth:`BitArray.insert` methods.

The bit position is modified by methods that read bits, as described in :attr:`~ConstBitStream.pos`, but for the mutable ``BitStream`` it is also modified by other methods:

* If a methods extends the bitstring (``+=``, ``append``) the ``pos`` will move to the end of the bitstring.
* If a method otherwise changes the length of the bitstring (``prepend``, ``insert``, sometimes ``replace``) the ``pos`` becomes invalid and will be reset to ``0``.

