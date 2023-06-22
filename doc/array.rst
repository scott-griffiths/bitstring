.. currentmodule:: bitstring

.. warning::
    The Array class is a work in progress and has not been released even in beta form.
    I sometimes like to write the documentation first, then the tests, then the code.
    So these are plans, not reality!


Array Class
===========

The ``Array`` class is a way to efficiently store data that has a single type with a set length.
The ``bitstring.Array`` type is meant as a more flexible version of the standard ``array.array``, and can be used the same way. ::

    import array
    import bitstring

    x = array.array('d', [1.0, 2.0, 3.14])
    y = bitstring.Array('d', [1.0, 2.0, 3.14])

    assert x.tobytes() == y.tobytes()

So far, so pointless! Its flexibility lies in the way that any fixed-length bitstring format can be used instead of just the dozen or so typecodes supported by the ``array`` module.

For example ``'uint4'``, ``'bfloat'``, ``'bits7'``, ``'hex12'`` or even compound formats such as ``'2*uint12, bin3'`` can be used.

Each element in the ``Array`` must then be something that makes sense for the ``fmt``.
Some examples will help illustrate::

    from bitstring import Array

    # Each unsigned int is stored in 4 bits
    a = Array('uint4', [0, 5, 5, 3, 2])

    # Convert and store floats in 8 bits each
    b = Array('float8_152', [-56.0, 0.123, 99.6])

    # Each element is a pair of 7 bit signed integers!
    c = Array('2*int7', [[-3, 15], [0, 0], [99, 120]])

You can then access and modify the ``Array`` with the usual notation::

    a[1:5]  # Array('uint4', [5, 5, 3])
    b[0]  # -56.0
    c[-1]  # [99, 120]

    a[0] = 2
    b.extend([0.0, -1.5])

Conversion between ``Array`` types can be done by creating a new one with the new format.
If elements of the old array don't fit or don't make sense in the new array then the relevant exceptions will be raised. ::

    >>> x = Array('float64', [89.3, 1e34, -0.00000001, 34])
    >>> y = Array('float16', x)
    >>> y
    Array('float16', [89.3125, inf, -0.0, 34.0])
    >>> y = Array('float8_143', y)
    >>> y
    Array('float8_143', [88.0, 240.0, 0.0, 32.0])
    >>> Array('uint8', y)
    Array('uint8', [88, 240, 0, 32])
    >>> Array('uint7', y)
    bitstring.CreationError: 240 is too large an unsigned integer for a bitstring of length 7. The allowed range is [0, 127].

You can also reinterpret the data by changing the ``fmt`` property directly.
This will not copy any data but will cause the current data to be shown differently. ::

    >>> x = Array('int16', [-5, 100, -4])
    >>> x
    Array('int16', [-5, 100, -4])
    >>> x.fmt = 'int8'
    >>> x
    Array('int8', [-1, -5, 0, 100, -1, -4])



The data for the array is stored internally as a ``BitArray`` object.
It can be directly accessed  using the ``data`` property.
You can manipulate the internal data directly using all of the methods available for the ``BitArray`` class.

The ``Array`` object also has a ``final`` read-only data member, which consists of the end bits of the ``data`` ``BitArray`` that are left over when the ``Array`` is interpreted using ``fmt``.
Typically ``final`` will be an empty ``BitArray`` but if you change the length of the ``data`` or change the ``fmt`` specification there may be some bits left over.

Some methods, such as ``append`` and ``extend`` will raise an exception if used when ``final`` is not empty, as it not clear how these should behave in this case.





.. class:: Array(fmt, [initializer], [final])

    Create a new ``Array`` whose elements are set by the ``fmt`` string.
    The ``fmt`` string can be a typecode such as ``'H'`` or ``'d'`` but it can also be a string defining any fixed-length bitstring.



    The `fmt` can either be a single interpretation or multiple.
    Getting and setting elements of the ``Array`` need to take this into account.
    The single interpretation case is straightforward::

        x = Array('float32', some_byte_data)
        if x[0] == 0.0:
            x[0] = -1.0

    For multiple interpreations each element of the ``Array`` represents multiple objects, so a list or tuple is needed to get and set::

        x = Array('2*float16', some_byte_data)
        if x[0] == (0.0, 0.0):
            x[0] = (0.0, 1005.0)

    Note that you can use the ``'pad'`` token to ignore some bits, and this will cause ``None`` to be returned::

        x = Array('uint4, pad4, uint8', some_byte_data)
        a, b, c = x[5]
        assert b is None



Methods
-------

.. method:: Array.count(value)

    Returns the number of elements set to *value*.

.. method:: Array.frombytes(b)

    Appends elements from `b`, which can be any initializer for ``Bits`` as long as it's a multiple of the bit length of the array's elements.

Properties
----------

.. attribute:: data

    The bit data of the ``Array``, as a ``BitArray``. Read and write, but note that if you want to continue to use it as an ``Array`` it should always be left with a length that is a multiple of its ``itemsize``.

.. attribute:: fmt

    The format string used to initialise the ``Array`` type. Read-only.

.. attribute:: itemsize

    The size in bits of each item in the ``Array``. Read-only.

    If each element of the ``Array`` is a single item the ``itemsize`` will be a single ``int``.
    If the ``fmt`` specifies more than one item the ``itemsize`` will be a list of ``int`` values.

    Note that this gives a value in bits, unlike the equivalent in the ``array`` module which gives a value in bytes. ::

        >>> a = Array('int8')
        >>> b = Array('bool, pad3, uint4')
        >>> a.itemsize
        8
        >>> b.itemsize
        [1, 3, 4]