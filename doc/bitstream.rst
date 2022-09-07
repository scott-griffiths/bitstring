.. currentmodule:: bitstring

BitStream Class
===============

.. class:: BitStream([auto, length, offset, pos, **kwargs])

    Both the :class:`BitArray` and the :class:`ConstBitStream` classes are base classes for :class:`BitStream` and so all of their methods are also available for :class:`BitStream` objects. The initialiser is the same as for :class:`ConstBitStream`.

    A :class:`BitStream` is a mutable container of bits with methods and properties that allow it to be parsed as a stream of bits. There are no additional methods or properties in this class - see its base classes (:class:`Bits`, :class:`BitArray` and :class:`ConstBitStream`) for details.

