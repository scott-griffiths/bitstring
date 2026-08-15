.. currentmodule:: bitstring

Dtypes
======

A data type (or 'dtype') concept is used in the bitstring module to encapsulate how to pack, unpack and present different bit interpretations.
The properties described above are all examples of dtypes.

.. class:: Dtype(token: str | Dtype, /, length: int | None = None)

Dtypes are immutable and cannot be changed after creation.

The first parameter is a format token string that can optionally include a length. For example ``'ue'``, ``'i'`` or ``'f16'``.

If the first parameter doesn't include a length and one is appropriate, the `length` parameter can be used to specify the length of the dtype.

An existing :class:`Dtype` can be given as the first parameter instead of a token string. Without a `length` this returns
the same object, and with one it returns a new :class:`Dtype` of the same type with that length. The length is validated
as it would be for a token string, so ``Dtype(Dtype('u8'), 16)`` gives ``Dtype('u', 16)`` but ``Dtype(Dtype('bool'), 8)``
raises a :exc:`ValueError`. ::

    >>> Dtype(Dtype('u8'), 16)
    Dtype('u', 16)

In most situations the token string can be used instead of `Dtype` object when it is needed, and the `Dtype` will be constructed automatically,
which is why the `Dtype` object is rarely used directly in this documentation.
It can however be advantageous to to create `Dtype` objects directly for efficiency reasons, or for using dtypes programmatically.

.. note::
    The `scale` parameter was removed in version 5.0. See :ref:`Exotic floats` for how to apply a scaling factor to MX format data.

----

Methods
-------

.. method:: Dtype.pack(value: Any, /) -> Bits

Pack a value into a bitstring.
The *value* parameter should be of a type appropriate to the dtype.

    >>> d = Dtype('u10')
    >>> d.pack(85)  # Equivalent to: Bits(u10=85)
    Bits('0b0001010101')


.. method:: Dtype.unpack(b: BitsType, /) -> Any

Unpack a bitstring to find its value. The *b* parameter should be a bitstring of the appropriate length, or an object that can be converted to a bitstring.

    >>> d = Dtype('u10')
    >>> d.unpack('0b0001010101')  # Equivalent to: Bits('0b0001010101').u10
    85

----

Properties
----------

All properties are read-only.

.. attribute:: Dtype.bitlength
    :type: int | None

The number of bits needed to represent a single instance of the data type.
Will be set to ``None`` for variable length dtypes.

.. attribute:: Dtype.is_signed
    :type: bool

If True then the data type represents a signed quantity.

.. attribute:: Dtype.length
    :type: int | None

The length of the data type. This is in bits for every dtype except ``bytes``, which counts bytes,
so ``Dtype('bytes4').length`` is 4 while its :attr:`~Dtype.bitlength` is 32.
Use :attr:`~Dtype.bitlength` when you need a length that is always in bits.
Will be set to ``None`` for variable length dtypes.

.. attribute:: Dtype.name
    :type: str

A string giving the name of the data type.

.. attribute:: Dtype.return_type
    :type: type

The type of the value returned by the `unpack` method, such as ``int``, ``float`` or ``str``.

.. attribute:: Dtype.variable_length
    :type: bool

If True then the length of the data type depends on the data being interpreted, and must not be specified.
