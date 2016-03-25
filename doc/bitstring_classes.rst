.. module:: bitstring
.. moduleauthor:: Scott Griffiths <dr.scottgriffiths@gmail.com>


The bitstring module
--------------------

The bitstring module provides four classes, :class:`Bits`, :class:`BitArray`, :class:`ConstBitStream` and :class:`BitStream`. :class:`Bits` is the simplest, and represents an immutable sequence of bits, while :class:`BitArray` adds various methods that modify the contents (these classes are intended to loosely mirror ``bytes`` and ``bytearray`` in Python 3). The 'Stream' classes have additional methods to treat the bits as a file or stream.

If you need to change the contents of a bitstring after creation then you must use either the :class:`BitArray` or :class:`BitStream` classes. If you need to use bitstrings as keys in a dictionary or members of a set then you must use either a :class:`Bits` or a :class:`ConstBitStream`. In this section the generic term 'bitstring' is used to refer to an object of any of these classes.

Note that for the bitstream classes the bit position within the bitstream (the position from which reads occur) can change without affecting the equality operation. This means that the :attr:`~ConstBitStream.pos` and :attr:`~ConstBitStream.bytepos` properties can change even for a :class:`ConstBitStream` object.

The public methods, special methods and properties of both classes are detailed in this section.

.. _auto_init:

The auto initialiser
^^^^^^^^^^^^^^^^^^^^

Note that in places where a bitstring can be used as a parameter, any other valid input to the ``auto`` initialiser can also be used. This means that the parameter can also be a format string which consists of tokens:

* Starting with ``hex=``, or simply starting with ``0x`` implies hexadecimal. e.g. ``0x013ff``, ``hex=013ff``

* Starting with ``oct=``, or simply starting with ``0o`` implies octal. e.g. ``0o755``, ``oct=755``

* Starting with ``bin=``, or simply starting with ``0b`` implies binary. e.g. ``0b0011010``, ``bin=0011010``

* Starting with ``int:`` or ``uint:`` followed by a length in bits and ``=`` gives base-2 integers. e.g. ``uint:8=255``, ``int:4=-7``

* To get big, little and native-endian whole-byte integers append ``be``, ``le`` or ``ne`` respectively to the ``uint`` or ``int`` identifier. e.g. ``uintle:32=1``, ``intne:16=-23``

* For floating point numbers use ``float:`` followed by the length in bits and ``=`` and the number. The default is big-endian, but you can also append ``be``, ``le`` or ``ne`` as with integers. e.g. ``float:64=0.2``, ``floatle:32=-0.3e12``

* Starting with ``ue=``, ``uie=``, ``se=`` or ``sie=`` implies an exponential-Golomb coded integer. e.g. ``ue=12``, ``sie=-4``

Multiples tokens can be joined by separating them with commas, so for example ``se=4, 0b1, se=-1`` represents the concatenation of three elements.

Parentheses and multiplicative factors can also be used, for example ``2*(0b10, 0xf)`` is equivalent to ``0b10, 0xf, 0b10, 0xf``. The multiplying factor must come before the thing it is being used to repeat.

The ``auto`` parameter also accepts other types:

* A list or tuple, whose elements will be evaluated as booleans (imagine calling ``bool()`` on each item) and the bits set to ``1`` for ``True`` items and ``0`` for ``False`` items.
* A positive integer, used to create a bitstring of that many zero bits.
* A file object, presumably opened in read-binary mode, from which the bitstring will be formed.
* A ``bytearray`` object.
* An ``array`` object. This is used after being converted to it's constituent byte data via its ``tostring`` method.
* In Python 3 only, a ``bytes`` object. Note this won't work for Python 2.7 as ``bytes`` is just a synonym for ``str``.



Compact format strings
^^^^^^^^^^^^^^^^^^^^^^

For the :meth:`~ConstBitStream.read`, :meth:`~Bits.unpack`, :meth:`~ConstBitStream.peek` methods and :func:`pack` function you can use compact format strings similar to those used in the :mod:`struct` and :mod:`array` modules. These start with an endian identifier: ``>`` for big-endian, ``<`` for little-endian or ``@`` for native-endian. This must be followed by at least one of these codes:

+------+------------------------------------+
|Code  |      Interpretation                |
+======+====================================+
|``b`` |      8 bit signed integer          |
+------+------------------------------------+
|``B`` |      8 bit unsigned integer        |
+------+------------------------------------+
|``h`` |      16 bit signed integer         |
+------+------------------------------------+
|``H`` |      16 bit unsigned integer	    |
+------+------------------------------------+
|``l`` |      32 bit signed integer         |
+------+------------------------------------+
|``L`` |      32 bit unsigned integer	    |
+------+------------------------------------+
|``q`` |      64 bit signed integer         |
+------+------------------------------------+
|``Q`` |      64 bit unsigned integer       |
+------+------------------------------------+
|``f`` |      32 bit floating point number  |
+------+------------------------------------+
|``d`` |      64 bit floating point number  |
+------+------------------------------------+

For more detail see :ref:`compact_format`.


Class properties
^^^^^^^^^^^^^^^^

Bitstrings use a wide range of properties for getting and setting different interpretations on the binary data, as well as accessing bit lengths and positions. For the mutable :class:`BitStream` and :class:`BitArray` objects the properties are all read and write (with the exception of the :attr:`~Bits.len`), whereas for immutable objects the only write enabled properties are for the position in the bitstream (:attr:`~ConstBitStream.pos`/:attr:`~ConstBitStream.bitpos` and :attr:`~ConstBitStream.bytepos`).


