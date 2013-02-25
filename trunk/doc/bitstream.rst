.. currentmodule:: bitstring

The BitStream class
-------------------

.. class:: BitStream([auto, length, offset, **kwargs])

    Both the :class:`BitArray` and the :class:`ConstBitStream` classes are base classes for :class:`BitStream` and so all of their methods are also available for :class:`BitStream` objects. The initialiser is also the same as for :class:`Bits` and so won't be repeated here.

    A :class:`BitStream` is a mutable container of bits with methods and properties that allow it to be parsed as a stream of bits. There are no additional methods or properties in this class - see its base classes (:class:`Bits`, :class:`BitArray` and :class:`ConstBitStream`) for details.

