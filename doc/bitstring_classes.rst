.. module:: bitstring
.. moduleauthor:: Scott Griffiths <scott@griffiths.name>


The bitstring module
--------------------

The bitstring module provides two classes, :class:`BitString` and :class:`Bits`. These share many methods as :class:`Bits` is the base class for :class:`BitString`. The distinction between them is that :class:`Bits` represents an immutable sequence of bits whereas :class:`BitString` objects support many methods that modify their contents.

If you need to change the contents of a bitstring after creation then you must use the :class:`BitString` class. If you need to use bitstrings as keys in a dictionary or members of a set then you must use the :class:`Bits` class (:class:`Bits` are hashable). Otherwise you can use whichever you prefer, but note that :class:`Bits` objects can potentially be more efficent than :class:`BitString` objects. In this section the generic term 'bitstring' means either a :class:`Bits` or a :class:`BitString` object.

Note that the bit position within the bitstring (the position from which reads occur) can change without affecting the equality operation. This means that the :attr:`~Bits.pos` and :attr:`~Bits.bytepos` properties can change even for a :class:`Bits` object.

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

* Starting with ``ue=`` or ``se=`` implies an exponential-Golomb coded integer. e.g. ``ue=12``, ``se=-4``

Multiples tokens can be joined by separating them with commas, so for example ``se=4, 0b1, se=-1`` represents the concatenation of three elements.

Parentheses and multiplicative factors can also be used, for example ``2*(0b10, 0xf)`` is equivalent to ``0b10, 0xf, 0b10, 0xf``. The multiplying factor must come before the thing it is being used to repeat.

The ``auto`` parameter also accepts other types:

* A list or tuple, whose elements will be evaluated as booleans (imagine calling ``bool()`` on each item) and the bits set to ``1`` for ``True`` items and ``0`` for ``False`` items.
* A positive integer, used to create a bitstring of that many zero bits.
* A file object, presumably opened in read-binary mode, from which the bitstring will be formed.
* A ``bytearray`` object.
* In Python 3 only, a ``bytes`` object. Note this won't work for Python 2 as ``bytes`` is just a synonym for ``str``.



Compact format strings
^^^^^^^^^^^^^^^^^^^^^^

For the :meth:`~Bits.read`, :meth:`~Bits.unpack`, :meth:`~Bits.peek` methods and :func:`pack` function you can use compact format strings similar to those used in the :mod:`struct` and :mod:`array` modules. These start with an endian identifier: ``>`` for big-endian, ``<`` for little-endian or ``@`` for native-endian. This must be followed by at least one of these codes:

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

Bitstrings use a wide range of properties for getting and setting different interpretations on the binary data, as well as accessing bit lengths and positions. For the mutable :class:`BitString` objects the properties are all read and write (with the exception of the :attr:`~Bits.length`), whereas for immutable :class:`Bits` objects the only write enabled properties are for the position in the bitstring (:attr:`~Bits.pos`/:attr:`~Bits.bitpos` and :attr:`~Bits.bytepos`).


