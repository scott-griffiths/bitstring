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


.. class:: Array(fmt, [initializer])

    Create a new ``Array`` whose elements are set by the ``fmt`` string.
    The ``fmt`` string can be a typecode such as ``'H'`` or ``'d'`` but it can also be a string defining any fixed-length bitstring.

    For example ``'uint4'``, ``'bfloat'``, ``'bits7'``, ``'hex12'`` or even compound formats such as ``'2*uint12, bin3'`` can be used.

    Each element in the ``Array`` must then be something that makes sense for the ``fmt``.
    Some examples will help illustrate::

        from bitstring import Array

        a = Array('uint4', [0, 5, 5, 3, 2])   # Each int is stored in 4 bits
        b = Array('float8_152', [-56.0, 0.123, 99.6])   # Floats stored in 8 bits each
        c = Array('2*int7', [[-3, 15], [0, 0], [99, 120]])  # Each element is a pair of 7 bit signed integers!

Methods
-------

.. method:: Array.count(value)

    Returns the number of elements set to *value*.
