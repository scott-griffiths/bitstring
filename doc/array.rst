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

For example ``'uint4'``, ``'bfloat'`` or ``'hex12'`` can be used.

Each element in the ``Array`` must then be something that makes sense for the ``fmt``.
Some examples will help illustrate::

    from bitstring import Array

    # Each unsigned int is stored in 4 bits
    a = Array('uint4', [0, 5, 5, 3, 2])

    # Convert and store floats in 8 bits each
    b = Array('float8_152', [-56.0, 0.123, 99.6])

    # Each element is a  7 bit signed integer
    c = Array('int7', [-3, 0, 120])

You can then access and modify the ``Array`` with the usual notation::

    a[1:5]  # Array('uint4', [5, 5, 3])
    b[0]  # -56.0
    c[-1]  # 120

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
It can be directly accessed using the ``data`` property.
You can freely manipulate the internal data using all of the methods available for the ``BitArray`` class.

The ``Array`` object also has a ``trailing_bits`` read-only data member, which consists of the end bits of the ``data`` ``BitArray`` that are left over when the ``Array`` is interpreted using ``fmt``.
Typically ``trailing_bits`` will be an empty ``BitArray`` but if you change the length of the ``data`` or change the ``fmt`` specification there may be some bits left over.

Some methods, such as ``append`` and ``extend`` will raise an exception if used when ``trailing_bits`` is not empty, as it not clear how these should behave in this case. You can however still use ``insert`` which will always leave the ``trailing_bits`` unchanged.


.. class:: Array(fmt, [initializer], [trailing_bits])

    Create a new ``Array`` whose elements are set by the ``fmt`` string.
    This can be any format which has a well defined and fixed length in bits.

    The ``fmt`` string can be a type code such as ``'H'`` or ``'d'`` but it can also be a string defining any format which has a fixed-length in bits.

    The correspondence between type codes and bitstring format codes is given in the table below.

    =========   ===================
    Type code   bitstring format
    =========   ===================
    ``'b'``     ``'int8'``
    ``'B'``     ``'uint8'``
    ``'h'``     ``'intne16'``
    ``'H'``     ``'uintne16'``
    ``'l'``     ``'intne32'``
    ``'L'``     ``'uintne32'``
    ``'q'``     ``'intne64'``
    ``'Q'``     ``'uintne64'``
    ``'e'``     ``'floatne16'``
    ``'f'``     ``'floatne32'``
    ``'d'``     ``'floatne64'``
    =========   ===================

    .. note::
        To keep compatibility with the ``array`` module the multi-byte formats all have native endianness.

        The ``'u'`` type code from the ``array`` module isn't supported as its length is platform dependent.

        The ``'e'`` type code isn't one of the ``array`` supported types, but it is used in the ``struct`` module and we support it here.


Properties
----------

.. attribute:: data

    The bit data of the ``Array``, as a ``BitArray``. Read and write, and can be freely manipulated with all of ``BitArray`` methods.

    Note that some ``Array`` methods such as ``append`` and ``extend`` require the  ``data`` to have a length that is a multiple of the ``Array``'s ``itemsize``.

.. attribute:: fmt

    The format string used to initialise the ``Array`` type. Read and write.

    Changing the format for an already formed ``Array`` will cause all of the bit data to be reinterpreted and can change the length of the ``Array``.

    Note that some ``Array`` methods such as ``append`` and ``extend`` require the bit data to have a length that is a multiple of the ``Array``'s ``itemsize``.

.. attribute:: itemsize

    The size in bits of each item in the ``Array``. Read-only.

    Note that this gives a value in bits, unlike the equivalent in the ``array`` module which gives a value in bytes. ::

        >>> a = Array('h')
        >>> b = Array('bool')
        >>> a.itemsize
        16
        >>> b.itemsize
        1

.. attribute:: trailing_bits

    A ``BitArray`` object that returns the end of the ``data`` that is not a multiple of the ``itemsize``. Read only.

    This will typically be an empty ``BitArray``, but if an the ``fmt`` or the ``data`` of an ``Array`` object has been altered after its creation then there may be left-over bits at the end of the data.

    Note that any methods that append items to the ``Array`` will fail with a ``ValueError`` if there are any trailing bits.


Methods
-------


.. method:: ~Array.append(x)

.. method:: ~Array.byteswap()

.. method:: ~Array.count(value)

    Returns the number of elements set to *value*.

.. method:: ~Array.extend(initializer)

.. method:: ~Array.frombytes(b)

.. method:: ~Array.fromfile(f, n)

.. method:: ~Array.fromlist(list_)

.. method:: ~Array.insert(i, x)

.. method:: ~Array.pop([i])

.. method:: ~Array.reverse()

.. method:: ~Array.tobytes()

.. method:: ~Array.tofile()

.. method:: ~Array.tolist()

