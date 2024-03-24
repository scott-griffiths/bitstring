.. currentmodule:: bitstring

Interpreting Bitstrings
=======================

Bitstrings don't know or care how they were created; they are just collections of bits. This means that you are quite free to interpret them in any way that makes sense.

Several Python properties are used to create interpretations for the bitstring. These properties call private functions which will calculate and return the appropriate interpretation. These don’t change the bitstring in any way and it remains just a collection of bits. If you use the property again then the calculation will be repeated.

Note that these properties can potentially be very expensive in terms of both computation and memory requirements. For example if you have initialised a bitstring from a 10 GiB file object and ask for its binary string representation then that string will be around 80 GiB in size!

If you're in an interactive session then the pretty-print method :meth:`~Bits.pp` can be useful as it will only convert the bitstring one chunk at a time for display.


Short Interpretations
---------------------

Many of the more commonly used interpretations have single letter equivalents. The ``hex``, ``bin``, ``oct``, ``int``, ``uint`` and ``float`` properties can be shortened to ``h``, ``b``, ``o``, ``i``, ``u`` and ``f`` respectively. Properties can have bit lengths appended to them to make properties such as ``f64``, ``u32`` or ``floatle32``.

When used as a getter these just add an extra check on the bitstring's length - if the bitstring is not the stated length then an :exc:`InterpretError` is raised. When used as a setter they define the new length of the bitstring. ::

    s = BitArray()  # Empty bitstring
    s.f32 = 101.5   # New length is 32 bits, representing a float


Properties
----------

For the properties described below we will use these::

    >>> a = BitArray('0x123')
    >>> b = BitArray('0b111')


bin / b
^^^^^^^

The most fundamental interpretation is perhaps as a binary string (a ‘bitstring’). The :attr:`~Bits.bin` property returns a string of the binary representation of the bitstring. All bitstrings can use this property and it is used to test equality between bitstrings. ::

    >>> a.bin
    '000100100011'
    >>> b.b
    '111'

Note that the initial zeros are significant; for bitstrings the zeros are just as important as the ones!

hex / h
^^^^^^^

For whole-byte bitstrings the most natural interpretation is often as hexadecimal, with each byte represented by two hex digits.

If the bitstring does not have a length that is a multiple of four bits then an :exc:`InterpretError` exception will be raised. This is done in preference to truncating or padding the value, which could hide errors in user code. ::

    >>> a.hex
    '123'
    >>> b.h
    ValueError: Cannot convert to hex unambiguously - not multiple of 4 bits.

oct / o
^^^^^^^

For an octal interpretation use the :attr:`~Bits.oct` property.

If the bitstring does not have a length that is a multiple of three then an :exc:`InterpretError` exception will be raised. ::

    >>> a.oct
    '0443'
    >>> b.o
    '7'
    >>> (b + '0b0').oct
    ValueError: Cannot convert to octal unambiguously - not multiple of 3 bits.

uint / u / uintbe / uintle / uintne
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To interpret the bitstring as a binary (base-2) bit-wise big-endian unsigned integer (i.e. a non-negative integer) use the :attr:`~Bits.uint` property.

    >>> a.uint
    283
    >>> b.u
    7

For byte-wise big-endian, little-endian and native-endian interpretations use :attr:`~Bits.uintbe`, :attr:`~Bits.uintle` and :attr:`~Bits.uintne` respectively. These will raise a :exc:`ValueError` if the bitstring is not a whole number of bytes long. ::

    >>> s = BitArray('0x000001')
    >>> s.uint     # bit-wise big-endian 
    1
    >>> s.uintbe   # byte-wise big-endian
    1
    >>> s.uintle   # byte-wise little-endian
    65536
    >>> s.uintne   # byte-wise native-endian (will be 1 on a big-endian platform!)
    65536
 
int / i / intbe / intle / intne
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a two's complement interpretation as a base-2 signed integer use the :attr:`~Bits.int` property. If the first bit of the bitstring is zero then the :attr:`~Bits.int` and :attr:`~Bits.uint` interpretations will be equal, otherwise the :attr:`~Bits.int` will represent a negative number. ::

    >>> a.int
    283
    >>> b.i
    -1

For byte-wise big, little and native endian signed integer interpretations use :attr:`~Bits.intbe`, :attr:`~Bits.intle` and :attr:`~Bits.intne` respectively. These work in the same manner as their unsigned counterparts described above.

float / f / floatbe / floatle / floatne
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For a floating point interpretation use the :attr:`~Bits.float` property. This uses the IEEE 754 floating point representation and will only work if the bitstring is 16, 32 or 64 bits long.

Different endiannesses are provided via :attr:`~Bits.floatle` and :attr:`~Bits.floatne`. Note that as floating point interpretations are only valid on whole-byte bitstrings there is no difference between the bit-wise big-endian :attr:`~Bits.float` and the byte-wise big-endian :attr:`~Bits.floatbe`.

Note also that standard floating point numbers in Python are stored in 64 bits, so use this size if you wish to avoid rounding errors.

bfloat / bfloatbe / bfloatle / bfloatne
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is a specialised 16-bit floating point format that is essentially a truncated version of the 32-bit IEEE float. It is used mainly in machine learning. As only one length is permitted it doesn't need to be specified on creation or interpretation.

See :ref:`Exotic floats` for more information.

p4binary / p3binary
^^^^^^^^^^^^^^^^^^^^^^^

Specialised 8-bit floating point formats. See :ref:`Exotic floats` for more information.

bytes
^^^^^

A common need is to retrieve the raw bytes from a bitstring for further processing or for writing to a file. For this use the :py:attr:`~Bits.bytes` interpretation, which returns a ``bytes`` object.

If the length of the bitstring isn't a multiple of eight then a :exc:`ValueError` will be raised. This is because there isn't an unequivocal representation as ``bytes``. You may prefer to use the method :meth:`~Bits.tobytes` as this will be pad with between one and seven zero bits up to a byte boundary if necessary. ::

    >>> open('somefile', 'wb').write(a.tobytes())
    >>> open('anotherfile', 'wb').write(('0x0'+a).bytes)
    >>> a1 = BitArray(filename='somefile')
    >>> a1.hex
    '1230'
    >>> a2 = BitArray(filename='anotherfile')
    >>> a2.hex
    '0123'

Note that the :meth:`~Bits.tobytes` method automatically padded with four zero bits at the end, whereas for the other example we explicitly padded at the start to byte align before using the :attr:`~Bits.bytes` property.

ue
^^

The :attr:`~Bits.ue` property interprets the bitstring as a single unsigned exponential-Golomb code and returns an integer. If the bitstring is not exactly one code then an :exc:`InterpretError` is raised instead. If you instead wish to read the next bits in the stream and interpret them as a code use the read function or unpack with a ``ue`` format string. See :ref:`exp-golomb` for a short explanation of this type of integer representation. ::

    >>> s = BitStream(ue=12)
    >>> s.bin
    '0001101'
    >>> s.append('ue=3')
    >>> print(s.unpack('2*ue'))
    [12, 3]

se
^^

The :attr:`~Bits.se` property does much the same as ``ue`` and the provisos there all apply. The obvious difference is that it interprets the bitstring as a signed exponential-Golomb rather than unsigned - see :ref:`exp-golomb` for more information. ::

    >>> s = BitStream('0x164b')
    >>> s.se
    InterpretError: Bitstring is not a single exponential-Golomb code.
    >>> while s.pos < len(s):
    ...     print(s.read('se'))
    -5
    2
    0
    -1
 


uie / sie
^^^^^^^^^

A slightly different type, interleaved exponential-Golomb codes are also supported. The principles are the same as with ``ue`` and ``se`` - see :ref:`exp-golomb` for detail of the differences.


Dtypes
======

A data type (or 'dtype') concept is used in the bitstring module to encapsulate how to create, parse and present different bit interpretations.
The properties described above are all examples of dtypes.

.. class:: Dtype(token: str | Dtype, /, length: int | None = None, scale: int | float | None = None)

Dtypes are immutable and cannot be changed after creation.

The first parameter is a format token string that can optionally include a length. For example ``'ue'``, ``'int'`` or ``'float16'``.

If the first parameter doesn't include a length and one is appropriate, the `length` parameter can be used to specify the length of the dtype.

The `scale` parameter can be used to specify a multiplicative scaling factor for the interpretation of the data.
This is primarily inteded for use with floating point formats of 8 bits or less, but can be used on other types.

In most situations the token string can be used instead of `Dtype` object when it is needed, and the `Dtype` will be constructed automatically,
which is why the `Dtype` object is rarely used directly in this documentation.

It can however be advantageous to to create `Dtype` objects directly for efficiency reasons, or for using dtypes programmatically.

If you need to use the `scale` parameter then there is no way to specify this in the format token string, so you must directly use a `Dtype` object.


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