.. currentmodule:: bitstring

.. note::
    The Array class is new in version 4.1 of bitstring, and is considered a 'beta' feature for now.
    There may be some small changes in future point releases and it hasn't been tested as well as the rest of the library.

    This documentation may also be a bit 'beta'.


Array Class
===========

.. class:: Array(fmt: str[, initializer[, trailing_bits]])

    Create a new ``Array`` whose elements are set by the ``fmt`` string.
    This can be any format which has a fixed length.
    See :ref:`format_tokens` and :ref:`compact_format` for details on allowed format strings, noting that only formats with well defined bit lengths are allowed.

    The ``Array`` class is a way to efficiently store data that has a single type with a set length.
    The ``bitstring.Array`` type is meant as a more flexible version of the standard ``array.array``, and can be used the same way. ::

        import array
        import bitstring

        x = array.array('f', [1.0, 2.0, 3.14])
        y = bitstring.Array('=f', [1.0, 2.0, 3.14])

        assert x.tobytes() == y.tobytes()

    This example packs three 32-bit floats into objects using both libraries.
    The only difference is the explicit native endianness for the format string of the bitstring version.
    The bitstring Array's advantage lies in the way that any fixed-length bitstring format can be used instead of just the dozen or so typecodes supported by the ``array`` module.

    For example ``'uint4'``, ``'bfloat'`` or ``'hex12'`` can be used, and the endianness of multi-byte formats can be properly specified.

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

        a[1:4]  # Array('uint4', [5, 5, 3])
        b[0]    # -56.0
        c[-1]   # 120

        a[0] = 2
        b.extend([0.0, -1.5])

    Conversion between ``Array`` types can be done by creating a new one with the new format from the elements of the other one.
    If elements of the old array don't fit or don't make sense in the new array then the relevant exceptions will be raised. ::

        >>> x = Array('float64', [89.3, 1e34, -0.00000001, 34])
        >>> y = Array('float16', x.tolist())
        >>> y
        Array('float16', [89.3125, inf, -0.0, 34.0])
        >>> y = Array('float8_143', y.tolist())
        >>> y
        Array('float8_143', [88.0, 240.0, 0.0, 32.0])
        >>> Array('uint8', y.tolist())
        Array('uint8', [88, 240, 0, 32])
        >>> Array('uint7', y.tolist())
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



    The ``fmt`` string can be a type code such as ``'>H'`` or ``'=d'`` but it can also be a string defining any format which has a fixed-length in bits, for example ``'int12'``, ``'bfloat'``, ``'bytes5'`` or ``'bool'``.

    Note that the typecodes must include an endianness character to give the byte ordering.
    This is more like the ``struct`` module typecodes, and is different to the ``array.array`` typecodes which are always native-endian.

    The correspondence between the big-endian type codes and bitstring format codes is given in the table below.

    =========   ===================
    Type code   bitstring format
    =========   ===================
    ``'>b'``     ``'int8'``
    ``'>B'``     ``'uint8'``
    ``'>h'``     ``'int16'``
    ``'>H'``     ``'uint16'``
    ``'>l'``     ``'int32'``
    ``'>L'``     ``'uint32'``
    ``'>q'``     ``'int64'``
    ``'>Q'``     ``'uint64'``
    ``'>e'``     ``'float16'``
    ``'>f'``     ``'float32'``
    ``'>d'``     ``'float64'``
    =========   ===================

    The endianness character can be ``'>'`` for big-endian, ``'<'`` for little-endian or ``'='`` for native-endian (``'@'`` can also be used for native-endian).
    In the bitstring formats the default is big-endian, but you can specify little or native endian using ``'le'`` or ``'ne'`` modifiers, for example:

    ============  =============================
    Type code     bitstring format
    ============  =============================
    ``'>H'``      ``'uint16'`` / ``'uintbe16'``
    ``'=H'``      ``'uintne16'``
    ``'<H'``      ``'uintle16'``
    ============  =============================


    Note that:

    * The ``array`` module's native endianness means that different packed binary data will be created on different types of machines.
      Users may find that behaviour unexpected which is why endianness must be explicitly given as in the rest of the bitstring module.

    * The ``'u'`` type code from the ``array`` module isn't supported as its length is platform dependent.

    * The ``'e'`` type code isn't one of the ``array`` supported types, but it is used in the ``struct`` module and we support it here.

    * The ``'b'`` and ``'B'`` type codes need to be preceded by an endianness character even though it makes no difference which one you use as they are only 1 byte long.


Methods
-------

    .. note::
        Some methods that are available for ``array.array`` objects are deliberately omitted in this interface as they don't really add much.
        In particular, some omissions and their suggested replacements are:

        ``a.fromlist(alist)`` → ``a.extend(alist)``

        ``a.frombytes(s)`` → ``a.data.extend(s)``


    .. method:: Array.append(x: float | int | str | bytes) -> None

        Add a new element with value `x` to the end of the Array.
        The type of `x` should be appropriate for the type of the Array.

        Raises a ``ValueError`` if the Array's bit length is not a multiple of its format length (see :attr:`~Array.trailing_bits`).

    .. method:: Array.byteswap() -> None

        Change the byte endianness of each element.

        Raises a ``ValueError`` if the format is not an integer number of bytes long. ::

            >>> a = Array('uint32', [100, 1, 999])
            >>> a.byteswap()
            >>> a
            Array('uint32', [1677721600, 16777216, 3875733504])
            >>> a.fmt = 'uintle32'
            >>> a
            Array('uintle32', [100, 1, 999])

    .. method:: Array.count(value: float | int | str | bytes) -> int

        Returns the number of elements set to *value*. ::

            >>> a = Array('hex4')
            >>> a.data += '0xdeadbeef'
            >>> a
            Array('hex4', ['d', 'e', 'a', 'd', 'b', 'e', 'e', 'f'])
            >>> a.count('e')
            3

    .. method:: Array.extend(iterable: Iterable | Array) -> None

        Extend the Array by constructing new elements from the values in a list or other iterable.

        The `iterable` can be another ``Array`` or an ``array.array``, but only if the format is the same. ::

            >>> a = Array('int5', [-5, 0, 10])
            >>> a.extend([3, 2, 1])
            >>> a.extend(a[0:3] // 5)
            >>> a
            Array('int5', [-5, 0, 10, 3, 2, 1, -1, 0, 2])

    .. method:: Array.fromfile(f: BinaryIO, n: int | None) -> None

        Append items read from a file object.

    .. method:: Array.insert(i: int, x: float | int | str | bytes) -> None

        Insert an item at a given position. ::

            >>> a = Array('float8_152', [-10, -5, -0.5, 5, 10])
            >>> a.insert(3, 0.5)
            >>> a
            Array('float8_152', [-10.0, -5.0, -0.5, 0.5, 5.0, 10.0])


    .. method:: Array.pop(i: int | None) -> float | int | str | bytes

        Remove and return the item at position i.

        If a position isn't specified the final item is returned and removed. ::

            >>> Array('bytes3', [b'ABC', b'DEF', b'ZZZ'])
            >>> a.pop(0)
            b'ABC'
            >>> a.pop()
            b'ZZZ'
            >>> a.pop()
            b'DEF'


    .. method:: Array.pp(fmt: str | None, width: int, sep: str, show_offset: bool, stream: TextIO) -> None

        Pretty print the Array.

    .. method:: Array.reverse() -> None

        Reverse the order of all items in the Array. ::

            >>> a = Array('>L', [100, 200, 300])
            >>> a.reverse()
            >>> a
            Array('>L', [300, 200, 100])

    .. method:: Array.tobytes() -> bytes

        Return Array data as bytes object, padding with zero bits at the end if needed. ::

            >>> a = Array('i4', [3, -6, 2, -3, 2, -7])
            >>> a.tobytes()
            b':-)'

    .. method:: Array.tofile(f: BinaryIO) -> None

        Write Array data to a file, padding with zero bits at the end if needed.

    .. method:: Array.tolist() -> List[float | int | str | bytes]

        Return Array items as a list.

        Each packed element of the Array is converted to an ordinary Python object such as a ``float`` or an ``int`` depending on the Array's format, and returned in a Python list.

        This can be helpful if you want to use an Array to create a new Array with a different format. ::

            >>> a = Array('float16', b'some_long_byte_data?')
            >>> a
            Array('float16', [15224.0, 5524.0, 475.0, 7608.0, 1887.0, 828.5, 18000.0, 473.0, 698.0, 671.5])
            >>> b = Array('float8_152', a.tolist())
            >>> b
            Array('float8_152', [14336.0, 5120.0, 448.0, 7168.0, 1792.0, 768.0, 16384.0, 448.0, 640.0, 640.0])
            >>> b.tobytes()
            b'wqcskfxcee'


Special Methods
---------------

    .. method:: Array.__len__(self) -> int

        ``len(a)``

        Return the number of elements in the Array. ::

            >>> a = Array('uint20', [1, 2, 3])
            >>> len(a)
            3
            >>> a.fmt = 'uint1'
            >>> len(a)
            60


    .. method:: Array.__eq__(self, other) -> bool

        ``a1 == a2``

        Equality test - `other` can be either another bitstring Array or an ``array``.
        To be equal the formats must be equivalent and the underlying bit data must be the same. ::

            >>> a = Array('u8', [1, 2, 3, 2, 1])
            >>> a[0:3] == a[-1:-4:-1]
            True

        To compare only the values contained in the Array, extract them using :meth:`~Array.tolist` first.

    .. method:: Array.__ne__(self, other) -> bool

        ``a1 != a2``


    .. method:: Array.__getitem__(self, key: int | slice) -> float | int | str | bytes | Array

        ``a[i]``

        ``a[start:end:step]``

    .. method:: Array.__add__(other: int | float) -> Array

        ``a + x``


    .. method:: Array.__sub__(self, other: int | float) -> Array

        ``a - x``

    .. method:: Array.__mul__(self, other: int | float) -> Array

        ``a * x``

    .. method:: Array.__truediv__(self, other: int | float) -> Array

        ``a / x``

    .. method:: Array.__floordiv__(self, other: int | float) -> Array

        ``a // x``

    .. method:: Array.__rshift__(self, other: int) -> Array

        ``a >> i``

    .. method:: Array.__lshift__(self, other: int) -> Array

        ``a << i``

    .. method:: Array.__and__(self, other: Bits) -> Array

        ``a & bs``

    .. method:: Array.__or__(self, other: Bits) -> Array

        ``a | bs``

    .. method:: Array.__xor__(self, other: Bits) -> Array

        ``a ^ bs``

    .. method:: Array.__setitem__(self, key: int | slice, value) -> None

        ``a[i] = x``

        ``a[start:end:step] = x``

    .. method:: Array.__delitem__(self, key: int | slice) -> None

        ``del a[i]``

        ``del[start:end:step]``

    .. method:: Array.__iadd__(self, other: int | float) -> None

        In-place version of :meth:`+ <Array.__add__>`. ::

            >>> a += 3


    .. method:: Array.__isub__(self, other: int | float) -> None

        In-place version of :meth:`- <Array.__sub__>`. ::

            >>> a -= 9.4


    .. method:: Array.__imul__(self, other: int | float) -> None

        In-place version of :meth:`* <Array.__mul__>`. ::

            >>> a *= 2

    .. method:: Array.__itruediv__(self, other: int | float) -> None

        In-place version of :meth:`/ <Array.__truediv__>`. ::

            >>> a /= 5.1

    .. method:: Array.__ifloordiv__(self, other: int | float) -> None

        In-place version of :meth:`// <Array.__floordiv__>`. ::

            >>> a //= 8


    .. method:: Array.__irshift__(self, other: int) -> None

        In-place version of :meth:`>> <Array.__rshift__>`. ::

            >>> a >>= 1

    .. method:: Array.__ilshift__(self, other: int) -> None

        In-place version of :meth:`\<\< <Array.__lshift__>`. ::

            >>> a <<= 2


    .. method:: Array.__iand__(self, other: Bits) -> None

        In-place version of :meth:`& <Array.__and__>`. ::

            >>> a &= '0b1110'

    .. method:: Array.__ior__(self, other: Bits) -> None

        In-place version of :meth:`| <Array.__or__>`. ::

            >>> a |= '0x7fff'

    .. method:: Array.__ixor__(self, other: Bits) -> None

        In-place version of :meth:`^ <Array.__xor__>`. ::

            >>> a ^= bytearray([56, 23])


Properties
----------

    .. attribute:: Array.data

        The bit data of the ``Array``, as a ``BitArray``. Read and write, and can be freely manipulated with all of ``BitArray`` methods.

        Note that some ``Array`` methods such as ``append`` and ``extend`` require the  ``data`` to have a length that is a multiple of the ``Array``'s ``itemsize``.

    .. attribute:: Array.fmt

        The format string used to initialise the ``Array`` type. Read and write.

        Changing the format for an already formed ``Array`` will cause all of the bit data to be reinterpreted and can change the length of the ``Array``.
        However, changing the format won't change the underlying bit data in any way.

        Note that some ``Array`` methods such as ``append`` and ``extend`` require the bit data to have a length that is a multiple of the ``Array``'s ``itemsize``.

    .. attribute:: Array.itemsize

        The size *in bits* of each item in the ``Array``. Read-only.

        Note that this gives a value in bits, unlike the equivalent in the ``array`` module which gives a value in bytes. ::

            >>> a = Array('>h')
            >>> b = Array('bool')
            >>> a.itemsize
            16
            >>> b.itemsize
            1

    .. attribute:: Array.trailing_bits

        A ``BitArray`` object equal to the end of the ``data`` that is not a multiple of the ``itemsize``. Read only.

        This will typically be an empty ``BitArray``, but if an the ``fmt`` or the ``data`` of an ``Array`` object has been altered after its creation then there may be left-over bits at the end of the data.

        Note that any methods that append items to the ``Array`` will fail with a ``ValueError`` if there are any trailing bits.


