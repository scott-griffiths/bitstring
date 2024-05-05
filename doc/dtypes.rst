.. currentmodule:: bitstring

Dtypes
======

A data type (or 'dtype') concept is used in the bitstring module to encapsulate how to create, parse and present different bit interpretations.
The properties described above are all examples of dtypes.

.. class:: Dtype(token: str | Dtype, /, length: int | None = None, scale: int | float | None = None)

Dtypes are immutable and cannot be changed after creation.

The first parameter is a format token string that can optionally include a length. For example ``'ue'``, ``'int'`` or ``'float16'``.

If the first parameter doesn't include a length and one is appropriate, the `length` parameter can be used to specify the length of the dtype.

The `scale` parameter can be used to specify a multiplicative scaling factor for the interpretation of the data.
This is primarily intended for use with floating point formats of 8 bits or less, but can be used on other types.

In most situations the token string can be used instead of `Dtype` object when it is needed, and the `Dtype` will be constructed automatically,
which is why the `Dtype` object is rarely used directly in this documentation.
It can however be advantageous to to create `Dtype` objects directly for efficiency reasons, or for using dtypes programmatically.

If you need to use the `scale` parameter then there is no way to specify this in the format token string, so you must directly use a `Dtype` object.

----

Methods
-------

.. method:: Dtype.build(value: Any, /) -> Bits

Create a bitstring from a value.
The *value* parameter should be of a type appropriate to the dtype.

    >>> d = Dtype('u10')
    >>> d.build(85)  # Equivalent to: Bits(u10=85)
    Bits('0b0001010101')


.. method:: Dtype.parse(b: BitsType, /) -> Any

Parse a bitstring to find its value. The *b* parameter should be a bitstring of the appropriate length, or an object that can be converted to a bitstring.

    >>> d = Dtype('u10')
    >>> d.parse('0b0001010101')  # Equivalent to: Bits('0b0001010101').u10
    85

----

Properties
----------

All properties are read-only.

.. attribute:: Dtype.bitlength
    :type: int | None

The number of bits needed to represent a single instance of the data type.
Will be set to ``None`` for variable length dtypes.

.. attribute:: Dtype.bits_per_item
    :type: int

The number of bits for each unit of length. Usually 1, but equals 8 for `bytes` type.

.. attribute:: Dtype.get_fn
    :type: Callable

A function to get the value of the data type.

.. attribute:: Dtype.is_signed
    :type: bool

If True then the data type represents a signed quantity.

.. attribute:: Dtype.length
    :type: int | None

The length of the data type in units of `bits_per_item`.
Will be set to ``None`` for variable length dtypes.

.. attribute:: Dtype.name
    :type: str

A string giving the name of the data type.

.. attribute:: Dtype.read_fn
    :type: Callable

A function to read the value of the data type.

.. attribute:: Dtype.return_type
    :type: type

The type of the value returned by the `parse` method, such as ``int``, ``float`` or ``str``.

.. attribute:: Dtype.scale
    :type: int | float | None

The multiplicative scale applied when interpreting the data.

.. attribute:: Dtype.set_fn
    :type: Callable

A function to set the value of the data type.

.. attribute:: Dtype.variable_length
    :type: bool

If True then the length of the data type depends on the data being interpreted, and must not be specified.