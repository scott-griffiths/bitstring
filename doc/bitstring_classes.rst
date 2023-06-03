
****************
Introduction
****************

.. module:: bitstring
.. moduleauthor:: Scott Griffiths <dr.scottgriffiths@gmail.com>

The bitstring module provides four classes, :class:`Bits`, :class:`BitArray`, :class:`ConstBitStream` and :class:`BitStream` which are containers for binary data.

:class:`Bits` is the simplest, and represents an immutable sequence of bits. :class:`BitArray` adds various methods that modify the contents. These classes are intended to loosely mirror the ``bytes`` and ``bytearray`` types in Python. The :class:`BitStream` and :class:`ConstBitStream` classes have additional methods to treat the bits as a file or stream.

If you need to change the contents of a bitstring after creation then you must use either the :class:`BitArray` or :class:`BitStream` classes. If you need to use bitstrings as keys in a dictionary or members of a set then you must use either a :class:`Bits` or a :class:`ConstBitStream`. In this documentation the generic term 'bitstring' is used to refer to an object of any of these classes.

Note that for the bitstream classes the bit position within the bitstream (the position from which reads occur) can change without affecting the equality operation. This means that the :attr:`~ConstBitStream.pos` and :attr:`~ConstBitStream.bytepos` properties can change even for a :class:`ConstBitStream` object.


.. _auto_init:

The auto initialiser
^^^^^^^^^^^^^^^^^^^^

The first parameter when creating a bitstring is called ``auto`` and can be a variety of types.
If it is a string then that string will be parsed into tokens to construct the binary data:


* Starting with ``'0x'`` or ``'hex='`` implies hexadecimal. e.g. ``'0x013ff'``, ``'hex=013ff'``

* Starting with ``'0o'`` or ``'oct='`` implies octal. e.g. ``'0o755'``, ``'oct=755'``

* Starting with ``'0b'`` or ``'bin='`` implies binary. e.g. ``'0b0011010'``, ``'bin=0011010'``

* Starting with ``'int'`` or ``'uint'`` followed by a length in bits and ``'='`` gives base-2 integers. e.g. ``'uint8=255'``, ``'int4=-7'``

* To get big, little and native-endian whole-byte integers append ``'be'``, ``'le'`` or ``'ne'`` respectively to the ``'uint'`` or ``'int'`` identifier. e.g. ``'uintle32=1'``, ``'intne16=-23'``

* For floating point numbers use ``'float'`` followed by the length in bits and ``'='`` and the number. The default is big-endian, but you can also append ``'be'``, ``'le'`` or ``'ne'`` as with integers. e.g. ``'float64=0.2'``, ``'floatle32=-0.3e12'``

* Starting with ``'ue='``, ``'uie='``, ``'se='`` or ``'sie='`` implies an exponential-Golomb coded integer. e.g. ``'ue=12'``, ``'sie=-4'``

Multiples tokens can be joined by separating them with commas, so for example ``'uint4=4, 0b1, se=-1'`` represents the concatenation of three elements.

Parentheses and multiplicative factors can also be used, for example ``'2*(0b10, 0xf)'`` is equivalent to ``'0b10, 0xf, 0b10, 0xf'``.
The multiplying factor must come before the thing it is being used to repeat.

The ``auto`` parameter also accepts other types:

* A list or tuple, whose elements will be evaluated as booleans (imagine calling ``bool()`` on each item) and the bits set to ``1`` for ``True`` items and ``0`` for ``False`` items.
* A positive integer, used to create a bitstring of that many zero bits.
* A file object, presumably opened in read-binary mode, from which the bitstring will be formed.
* A ``bytearray`` or ``bytes`` object.
* An ``array`` object from the built-in ``array`` module. This is used after being converted to it's constituent byte data via its ``tobytes`` method.
* A ``bitarray`` or ``frozenbitarray`` object from the 3rd party ``bitarray`` package.



Class properties
^^^^^^^^^^^^^^^^

Bitstrings use a wide range of properties for getting and setting different interpretations on the binary data, as well as accessing bit lengths and positions. For the mutable :class:`BitStream` and :class:`BitArray` objects the properties are all read and write (with the exception of the :attr:`~Bits.len`), whereas for immutable objects the only write enabled properties are for the position in the bitstream (:attr:`~ConstBitStream.pos`/:attr:`~ConstBitStream.bitpos` and :attr:`~ConstBitStream.bytepos`).


