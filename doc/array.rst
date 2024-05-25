.. currentmodule:: bitstring


Array
=====

.. class:: Array(dtype: str | Dtype, initializer: Iterable | int | Array | array.array | Bits | bytes | bytearray | memoryview | BinaryIO | None = None, trailing_bits: BitsType | None = None)

    Create a new ``Array`` whose elements are set by the `dtype` (data-type) string or :class:`Dtype`.
    This can be any format which has a fixed length.
    See :ref:`format_tokens` and :ref:`compact_format` for details on allowed dtype strings, noting that only formats with well defined bit lengths are allowed.

    The `inititalizer` will typically be an iterable such as a list, but can also be many other things including an open binary file, a bytes or bytearray object, another ``bitstring.Array`` or an ``array.array``.
    It can also be an integer, in which case the ``Array`` will be zero-initialised with that many items. ::

        >>> bitstring.Array('i4', 8)
        Array('int4', [0, 0, 0, 0, 0, 0, 0, 0])

    The `trailing_bits` typically isn't used in construction, and specifies bits left over after interpreting the stored binary data according to the data type `dtype`.


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

For example ``'uint4'``, ``'bfloat'`` or ``'hex12'`` can be used, and the endianness of multi-byte dtypes can be properly specified.

Each element in the ``Array`` must then be something that makes sense for the ``dtype``.
Some examples will help illustrate::

    from bitstring import Array

    # Each unsigned int is stored in 4 bits
    a = Array('uint4', [0, 5, 5, 3, 2])

    # Convert and store floats in 8 bits each
    b = Array('p3binary', [-56.0, 0.123, 99.6])

    # Each element is a  7 bit signed integer
    c = Array('int7', [-3, 0, 120])

You can then access and modify the ``Array`` with the usual notation::

    a[1:4]  # Array('uint4', [5, 5, 3])
    b[0]    # -56.0
    c[-1]   # 120

    a[0] = 2
    b.extend([0.0, -1.5])

Conversion between ``Array`` types can be done using the :meth:`astype` method.
If elements of the old array don't fit or don't make sense in the new array then the relevant exceptions will be raised. ::

    >>> x = Array('float64', [89.3, 1e34, -0.00000001, 34])
    >>> y = x.astype('float16')
    >>> y
    Array('float16', [89.3125, inf, -0.0, 34.0])
    >>> y = y.astype('p4binary')
    >>> y
    Array('p4binary', [88.0, 240.0, 0.0, 32.0])
    >>> y.astype('uint8')
    Array('uint8', [88, 240, 0, 32])
    >>> y.astype('uint7')
    bitstring.CreationError: 240 is too large an unsigned integer for a bitstring of length 7. The allowed range is [0, 127].

You can also reinterpret the data by changing the :attr:`dtype` property directly.
This will not copy any data but will cause the current data to be shown differently. ::

    >>> x = Array('int16', [-5, 100, -4])
    >>> x
    Array('int16', [-5, 100, -4])
    >>> x.dtype = 'int8'
    >>> x
    Array('int8', [-1, -5, 0, 100, -1, -4])


The data for the array is stored internally as a :class:`BitArray` object.
It can be directly accessed using the :attr:`data` property.
You can freely manipulate the internal data using all of the methods available for the :class:`BitArray` class.

The :class:`Array` object also has a :attr:`trailing_bits` read-only data member, which consists of the end bits of the :attr:`data` that are left over when the :class:`Array` is interpreted using the :attr:`dtype`.
Typically :attr:`trailing_bits` will be an empty :class:`BitArray` but if you change the length of the :attr:`data` or change the :attr:`dtype` specification there may be some bits left over.

Some methods, such as :meth:`~Array.append` and :meth:`~Array.extend` will raise an exception if used when :attr:`trailing_bits` is not empty, as it not clear how these should behave in this case.
You can however still use :meth:`~Array.insert` which will always leave the :attr:`trailing_bits` unchanged.

The :attr:`dtype` string can be a type code such as ``'>H'`` or ``'=d'`` but it can also be a string defining any format which has a fixed-length in bits, for example ``'int12'``, ``'bfloat'``, ``'bytes5'`` or ``'bool'``.

Note that the typecodes must include an endianness character to give the byte ordering.
This is more like the ``struct`` module typecodes, and is different to the ``array.array`` typecodes which are always native-endian.

The correspondence between the big-endian type codes and bitstring dtype strings is given in the table below.

=========   ===================
Type code   bitstring dtype
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
In the bitstring dtypes the default is big-endian, but you can specify little or native endian using ``'le'`` or ``'ne'`` modifiers, for example:

============  =============================
Type code     bitstring dtype
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

----

Methods
-------

.. method:: Array.append(x: float | int | str | bytes) -> None

    Add a new element with value `x` to the end of the Array.
    The type of `x` should be appropriate for the type of the Array.

    Raises a ``ValueError`` if the Array's bit length is not a multiple of its dtype length (see :attr:`~Array.trailing_bits`).

.. method:: Array.astype(dtype: Dtype | str) -> Array

    Cast the ``Array`` to the new `dtype` and return the result. ::

        >>> a = Array('float64', [-990, 34, 1, 0.25])
        >>> a.data
        BitArray('0xc08ef0000000000040410000000000003ff00000000000003fd0000000000000')
        >>> b = a.astype('float16')
        >>> b.data
        BitArray('0xe3bc50403c003400')
        >>> a == b
        Array('bool', [True, True, True, True])


.. method:: Array.byteswap() -> None

    Change the byte endianness of each element.

    Raises a ``ValueError`` if the format is not an integer number of bytes long. ::

        >>> a = Array('uint32', [100, 1, 999])
        >>> a.byteswap()
        >>> a
        Array('uint32', [1677721600, 16777216, 3875733504])
        >>> a.dtype = 'uintle32'
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

    For floating point types, using a `value` of ``float('nan')`` will count the number of elements for which ``math.isnan()`` returns ``True``.

.. method:: Array.equals(other: Any) -> bool

    Equality test - `other` can be either another bitstring Array or an ``array``.
    Returns ``True`` if the dtypes are equivalent and the underlying bit data is the same, otherwise returns ``False``. ::

        >>> a = Array('u8', [1, 2, 3, 2, 1])
        >>> a[0:3].equals(a[-1:-4:-1])
        True
        >>> b = Array('i8', [1, 2, 3, 2, 1])
        >>> a.equals(b)
        False

    To compare only the values contained in the Array, extract them using :meth:`~Array.tolist` first::

        >>> a.tolist() == b.tolist()
        True

    Note that the ``==`` operator will perform an element-wise equality check and return a new ``Array`` of dtype ``'bool'`` (or raise an exception).

        >>> a == b
        Array('bool', [True, True, True, True, True])


.. method:: Array.extend(iterable: Iterable | Array) -> None

    Extend the Array by constructing new elements from the values in a list or other iterable.

    The `iterable` can be another ``Array`` or an ``array.array``, but only if the dtype is the same. ::

        >>> a = Array('int5', [-5, 0, 10])
        >>> a.extend([3, 2, 1])
        >>> a.extend(a[0:3] // 5)
        >>> a
        Array('int5', [-5, 0, 10, 3, 2, 1, -1, 0, 2])

.. method:: Array.fromfile(f: BinaryIO, n: int | None = None) -> None

    Append items read from a file object.

.. method:: Array.insert(i: int, x: float | int | str | bytes) -> None

    Insert an item at a given position. ::

        >>> a = Array('p3binary', [-10, -5, -0.5, 5, 10])
        >>> a.insert(3, 0.5)
        >>> a
        Array('p3binary', [-10.0, -5.0, -0.5, 0.5, 5.0, 10.0])


.. method:: Array.pop(i: int | None = None) -> float | int | str | bytes

    Remove and return the item at position i.

    If a position isn't specified the final item is returned and removed. ::

        >>> Array('bytes3', [b'ABC', b'DEF', b'ZZZ'])
        >>> a.pop(0)
        b'ABC'
        >>> a.pop()
        b'ZZZ'
        >>> a.pop()
        b'DEF'


.. method:: Array.pp(fmt: str | None = None, width: int = 120, show_offset: bool = True, stream: TextIO = sys.stdout) -> None

    Pretty print the Array.

    The format string `fmt` defaults to the Array's current :attr:`dtype`, but any other valid Array format string can be used.

    If a `fmt` doesn't have an explicit length, the Array's :attr:`itemsize` will be used.

    A pair of comma-separated format strings can also be used - if both formats specify a length they must be the same. For example ``'float, hex16'`` or ``'u4, b4'``.

    The output will try to stay within `width` characters per line, but will always output at least one element value.

    Setting `show_offset` to ``False`` will hide the element index on each line of the output.

    An output `stream` can be specified. This should be an object with a ``write`` method and the default is ``sys.stdout``.

        >>> a = Array('u20', bytearray(range(100)))
        >>> a.pp(width=70, show_offset=False)
        <Array fmt='u20', length=40, itemsize=20 bits, total data size=100 bytes> [
             16  131844   20576  460809   41136  789774   61697   70163
          82257  399128  102817  728093  123378    8482  143938  337447
         164498  666412  185058  995377  205619  275766  226179  604731
         246739  933696  267300  214085  287860  543050  308420  872015
         328981  152404  349541  481369  370101  810334  390662   90723
        ]

        >>> a.pp('hex32', width=70)
        <Array fmt='hex32', length=25, itemsize=32 bits, total data size=100 bytes> [
          0: 00010203 04050607 08090a0b 0c0d0e0f 10111213 14151617 18191a1b
          7: 1c1d1e1f 20212223 24252627 28292a2b 2c2d2e2f 30313233 34353637
         14: 38393a3b 3c3d3e3f 40414243 44454647 48494a4b 4c4d4e4f 50515253
         21: 54555657 58595a5b 5c5d5e5f 60616263
        ]

        >>> a.pp('i12, hex', show_offset=False, width=70)
        <Array fmt='i12, hex', length=66, itemsize=12 bits, total data size=100 bytes> [
            0   258    48  1029    96  1800 : 000 102 030 405 060 708
          144 -1525   192  -754   241    17 : 090 a0b 0c0 d0e 0f1 011
          289   788   337  1559   385 -1766 : 121 314 151 617 181 91a
          433  -995   481  -224   530   547 : 1b1 c1d 1e1 f20 212 223
          578  1318   626 -2007   674 -1236 : 242 526 272 829 2a2 b2c
          722  -465   771   306   819  1077 : 2d2 e2f 303 132 333 435
          867  1848   915 -1477   963  -706 : 363 738 393 a3b 3c3 d3e
         1012    65  1060   836  1108  1607 : 3f4 041 424 344 454 647
         1156 -1718  1204  -947  1252  -176 : 484 94a 4b4 c4d 4e4 f50
         1301   595  1349  1366  1397 -1959 : 515 253 545 556 575 859
         1445 -1188  1493  -417  1542   354 : 5a5 b5c 5d5 e5f 606 162
        ] + trailing_bits = 0x63

    By default the output will have colours added in the terminal. This can be disabled - see :data:`bitstring.options.no_color` for more information.


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

----

Special Methods
---------------

Type promotion
""""""""""""""

Many operations can be performed between two ``Array`` objects.
For these to be valid the dtypes of the ``Array`` objects must be numerical, that is they must represent an integer or floating point value.
Some operations have tighter restrictions, such as the shift operators ``<<`` and ``>>`` requiring integers only.

The dtype of the resulting ``Array`` is calculated by applying these rules:

**Rule 0**: For comparison operators (``<``, ``>=``, ``==``, ``!=`` etc.) the result is always an ``Array`` of dtype ``'bool'``.

For other operators, one of the two input ``Array`` dtypes is used as the output dtype by applying the remaining rules in order until a winner is found:

* **Rule 1**: Floating point types always win against integer types.
* **Rule 2**: Signed integer types always win against unsigned integer types.
* **Rule 3**: Longer types win against shorter types.
* **Rule 4**: In a tie the first type wins.

Some examples should help illustrate:

=========== ================   ============ ================  ===    ==================
**Rule 0**  ``'uint8'``             ``<=``    ``'float64'``    →        ``'bool'``
**Rule 1**  ``'int32'``             ``+``      ``'float16'``   →        ``'float16'``
**Rule 2**  ``'uint20'``            ``//``    ``'int10'``      →        ``'int10'``
**Rule 3**  ``'int8'``              ``*``     ``'int16'``      →        ``'int16'``
**Rule 4**  ``'float16'``           ``-=``    ``'bfloat'``     →         ``'float16'``
=========== ================   ============ ================  ===    ==================

Comparison operators
""""""""""""""""""""

Comparison operators can operate between two ``Array`` objects, or between an ``Array`` and a scalar quantity (usually a number).

Note that they always produce an ``Array`` of :attr:`~Array.dtype` ``'bool'``, including the equality and inequality operators.

To test the boolean equality of two Arrays use the :meth:`~Array.equals` method instead.

.. method:: Array.__eq__(self, other: int | float | str | BitsType | Array) -> Array

    ``a1 == a2``

.. method:: Array.__ne__(self, other: int | float | str | BitsType | Array) -> Array

    ``a1 != a2``

.. method:: Array.__lt__(self, other: int | float | Array) -> Array

    ``a1 < a2``

.. method:: Array.__le__(self, other: int | float | Array) -> Array

    ``a1 <= a2``

.. method:: Array.__gt__(self, other: int | float | Array) -> Array

    ``a1 > a2``

.. method:: Array.__ge__(self, other: int | float | Array) -> Array

    ``a1 >= a2``


Numerical operators
"""""""""""""""""""

.. method:: Array.__add__(other: int | float | Array) -> Array

    ``a + x``

.. method:: Array.__sub__(self, other: int | float | Array) -> Array

    ``a - x``

.. method:: Array.__mul__(self, other: int | float | Array) -> Array

    ``a * x``

.. method:: Array.__truediv__(self, other: int | float | Array) -> Array

    ``a / x``

.. method:: Array.__floordiv__(self, other: int | float | Array) -> Array

    ``a // x``

.. method:: Array.__rshift__(self, other: int | Array) -> Array

    ``a >> i``

.. method:: Array.__lshift__(self, other: int | Array) -> Array

    ``a << i``

.. method:: Array.__mod__(self, other: int | Array) -> Array

    ``a % i``

.. method:: Array.__neg__(self) -> Array

    ``-a``

.. method:: Array.__abs__(self) -> Array

    ``abs(a)``


Bitwise operators
"""""""""""""""""

.. method:: Array.__and__(self, other: Bits) -> Array

    ``a & bs``

        >>> a &= '0b1110'

.. method:: Array.__or__(self, other: Bits) -> Array

    ``a | bs``

        >>> a |= '0x7fff'

.. method:: Array.__xor__(self, other: Bits) -> Array

    ``a ^ bs``

        >>> a ^= bytearray([56, 23])


Python language operators
"""""""""""""""""""""""""

.. method:: Array.__len__(self) -> int

    ``len(a)``

    Return the number of elements in the Array. ::

        >>> a = Array('uint20', [1, 2, 3])
        >>> len(a)
        3
        >>> a.dtype = 'uint1'
        >>> len(a)
        60


.. method:: Array.__getitem__(self, key: int | slice) -> float | int | str | bytes | Array

    ``a[i]``

    ``a[start:end:step]``


.. method:: Array.__setitem__(self, key: int | slice, value) -> None

    ``a[i] = x``

    ``a[start:end:step] = x``

.. method:: Array.__delitem__(self, key: int | slice) -> None

    ``del a[i]``

    ``del[start:end:step]``

----

Properties
----------

.. attribute:: Array.data
    :type: BitArray

    The bit data of the ``Array``, as a ``BitArray``. Read and write, and can be freely manipulated with all ``BitArray`` methods.

    Note that some ``Array`` methods such as :meth:`~Array.append` and :meth:`~Array.extend` require the  :attr:`~Array.data` to have a length that is a multiple of the ``Array``'s :attr:`~Array.itemsize`.

.. attribute:: Array.dtype
    :type: Dtype

    The data type used to initialise the ``Array`` type. Read and write.

    Changing the ``dtype`` for an already formed ``Array`` will cause all of the bit data to be reinterpreted and can change the length of the ``Array``.
    However, changing the ``dtype`` won't change the underlying bit data in any way.

    Note that some ``Array`` methods such as :meth:`~Array.append` and :meth:`~Array.extend` require the bit data to have a length that is a multiple of the ``Array``'s :attr:`~Array.itemsize`.

.. attribute:: Array.itemsize
    :type: int

    The size *in bits* of each item in the ``Array``. Read-only.

    Note that this gives a value in bits, unlike the equivalent in the ``array`` module which gives a value in bytes. ::

        >>> a = Array('>h')
        >>> b = Array('bool')
        >>> a.itemsize
        16
        >>> b.itemsize
        1

.. attribute:: Array.trailing_bits
    :type: BitArray

    A ``BitArray`` object equal to the end of the ``data`` that is not a multiple of the ``itemsize``. Read only.

    This will typically be an empty ``BitArray``, but if the ``dtype`` or the ``data`` of an ``Array`` object has been altered after its creation then there may be left-over bits at the end of the data.

    Note that any methods that append items to the ``Array`` will fail with a ``ValueError`` if there are any trailing bits.


