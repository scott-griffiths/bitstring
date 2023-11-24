.. currentmodule:: bitstring

Bits
====

The ``Bits`` class is the simplest type in the bitstring module, and represents an immutable sequence of bits. This is the best class to use if you will not need to modify the data after creation and don't need streaming methods.

.. class:: Bits(auto: BitsType | int | None, /, length: int | None = None, offset: int | None = None, **kwargs)

    Creates a new bitstring. You must specify either no initialiser, just an 'auto' value as the first parameter, or one of the keyword arguments ``bytes``, ``bin``, ``hex``, ``oct``, ``uint``, ``int``, ``uintbe``, ``intbe``, ``uintle``, ``intle``, ``uintne``, ``intne``, ``se``, ``ue``, ``sie``, ``uie``, ``float``, ``floatbe``, ``floatle``, ``floatne``, ``e4m3float``, ``e5m2float``, ``bfloat``, ``bfloatbe``, ``bfloatle``, ``bfloatne``, ``bool`` or ``filename``. If no initialiser is given then a zeroed bitstring of ``length`` bits is created.

    The initialiser for the :class:`Bits` class is precisely the same as for :class:`BitArray`, :class:`BitStream` and :class:`ConstBitStream`.

    ``offset`` is available when using the ``bytes`` or ``filename`` initialisers. It gives a number of bits to ignore at the start of the bitstring.

    Specifying ``length`` is mandatory when using the various integer initialisers. It must be large enough that a bitstring can contain the integer in ``length`` bits. It must also be specified for the float initialisers (the only valid values are 16, 32 and 64). It is optional for the ``bytes`` and ``filename`` initialisers and can be used to truncate data from the end of the input value. ::

           >>> s1 = Bits(hex='0x934')
           >>> s2 = Bits(oct='0o4464')
           >>> s3 = Bits(bin='0b001000110100')
           >>> s4 = Bits(int=-1740, length=12)
           >>> s5 = Bits(uint=2356, length=12)
           >>> s6 = Bits(bytes=b'\x93@', length=12)
           >>> s1 == s2 == s3 == s4 == s5 == s6
           True

    See also :ref:`auto_init`, which allows many different types to be used to initialise a bitstring. ::

        >>> s = Bits('uint12=32, 0b110')
        >>> t = Bits('0o755, ue=12, int:3=-1')

    In the methods below we use ``BitsType`` to indicate that any of the types that can auto initialise can be used.


Methods
-------


.. method:: Bits.all(value: bool, pos: Iterable[int] | None = None) -> bool

   Returns ``True`` if all of the specified bits are all set to *value*, otherwise returns ``False``.

   If *value* is ``True`` then ``1`` bits are checked for, otherwise ``0`` bits are checked for.

   *pos* should be an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -len(s)`` or ``pos > len(s)``. It defaults to the whole bitstring.

       >>> s = Bits('int15=-1')
       >>> s.all(True, [3, 4, 12, 13])
       True
       >>> s.all(1)
       True


.. method:: Bits.any(value: bool, pos: Iterable[int] | None = None) -> bool

   Returns ``True`` if any of the specified bits are set to *value*, otherwise returns ``False``.

   If *value* is ``True`` then ``1`` bits are checked for, otherwise ``0`` bits are checked for.

   *pos* should be an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -len(s)`` or ``pos > len(s)``. It defaults to the whole bitstring.

       >>> s = Bits('0b11011100')
       >>> s.any(False, range(6))
       True
       >>> s.any(1)
       True


.. method:: Bits.copy() -> Bits

    Returns a copy of the bitstring.

    ``s.copy()`` is equivalent to the shallow copy ``s[:]`` and creates a new copy of the bitstring in memory.


.. method:: Bits.count(value: bool) -> int

    Returns the number of bits set to *value*.

    *value* can be ``True`` or ``False`` or anything that can be cast to a bool, so you could equally use ``1`` or ``0``.

        >>> s = BitArray(1000000)
        >>> s.set(1, [4, 44, 444444])
        >>> s.count(1)
        3
        >>> s.count(False)
        999997

    If you need to count more than just single bits you can use :meth:`~Bits.findall`, for example ``len(list(s.findall('0xabc')))``.
    Note that if the bitstring is very sparse, as in the example here, it could be quicker to find and count all the set bits with something like ``len(list(s.findall('0b1')))``. For bitstrings with more entropy the ``count`` method will be much quicker than finding.


.. method:: Bits.cut(bits: int, start: int | None = None, end: int | None = None, count: int | None = None) -> Iterator[Bits]

    Returns a generator for slices of the bitstring of length *bits*.

    At most *count* items are returned and the range is given by the slice *[start:end]*, which defaults to the whole bitstring. ::

        >>> s = BitArray('0x1234')
        >>> for nibble in s.cut(4):
        ...     s.prepend(nibble)
        >>> print(s)
        0x43211234


.. method:: Bits.endswith(bs: BitsType, start: int | None = None, end: int | None = None) -> bool

    Returns ``True`` if the bitstring ends with the sub-string *bs*, otherwise returns ``False``.

    A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring. ::

        >>> s = Bits('0x35e22')
        >>> s.endswith('0b10, 0x22')
        True
        >>> s.endswith('0x22', start=13)
        False


.. method:: Bits.find(bs: BitsType, start: int | None = None, end: int | None = None, bytealigned: bool | None = None) -> Tuple[int] | Tuple[()]

    Searches for *bs* in the current bitstring and sets :attr:`~ConstBitStream.pos` to the start of *bs* and returns it in a tuple if found, otherwise it returns an empty tuple.

    The reason for returning the bit position in a tuple is so that it evaluates as True even if the bit position is zero. This allows constructs such as ``if s.find('0xb3'):`` to work as expected.

    If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions (which is generally much faster than searching for it in every possible bit position). *start* and *end* give the search range and default to the whole bitstring. ::

        >>> s = Bits('0x0023122')
        >>> s.find('0b000100', bytealigned=True)
        (16,)


.. method:: Bits.findall(bs: BitsType, start: int | None = None, end: int | None = None, count: int | None = None, bytealigned: bool | None = None) -> Iterable[int]

    Searches for all occurrences of *bs* (even overlapping ones) and returns a generator of their bit positions.

    If *bytealigned* is ``True`` then *bs* will only be looked for at byte aligned positions. *start* and *end* optionally define a search range and default to the whole bitstring.

    The *count* parameter limits the number of items that will be found - the default is to find all occurrences. ::

        >>> s = Bits('0xab220101')*5
        >>> list(s.findall('0x22', bytealigned=True))
        [8, 40, 72, 104, 136]


.. method:: Bits.join(sequence: Iterable) -> Bits

    Returns the concatenation of the bitstrings in the iterable *sequence* joined with ``self`` as a separator. ::

        >>> s = Bits().join(['0x0001ee', 'uint:24=13', '0b0111'])
        >>> print(s)
        0x0001ee00000d7

        >>> s = Bits('0b1').join(['0b0']*5)
        >>> print(s.bin)
        010101010


.. method:: Bits.pp(fmt: str | None = None, width: int = 120, sep: str = ' ', show_offset: bool = True, stream: TextIO = sys.stdout) -> None

    Pretty print the bitstring's value according to the *fmt*. Either a single, or two comma separated formats can be specified, together with options for setting the maximum display *width*, the number of bits to display in each group, and the separator to print between groups.

        >>> s = Bits(int=-98987987293452, length=200)
        >>> s.pp(width=80)
          0: 11111111 11111111 11111111 11111111 11111111 11111111   ff ff ff ff ff ff
         48: 11111111 11111111 11111111 11111111 11111111 11111111   ff ff ff ff ff ff
         96: 11111111 11111111 11111111 11111111 11111111 11111111   ff ff ff ff ff ff
        144: 11111111 10100101 11111000 10010000 00101110 00101010   ff a5 f8 90 2e 2a
        192: 11110100                                                f4

        >>> s.pp('h16, b', width=80, show_offset=False, sep=' / ')
        ffff / ffff / ffff   1111111111111111 / 1111111111111111 / 1111111111111111
        ffff / ffff / ffff   1111111111111111 / 1111111111111111 / 1111111111111111
        ffff / ffff / ffff   1111111111111111 / 1111111111111111 / 1111111111111111
        ffa5 / f890 / 2e2a   1111111110100101 / 1111100010010000 / 0010111000101010
        f4                   11110100

    The available formats are ``'bin'``, ``'oct'``, ``'hex'`` and ``'bytes'``. A bit length can be specified after the format (with an optional `:`) to give the number of bits represented by each group, otherwise the default is based on the format or formats selected. Using a length of zero removes all separators and displays one block of characters per line for each format in *fmt* (e.g. ``'hex0'``).

    The ``'hex'``, ``'oct'`` and ``'bin'`` format string can be replaced with just their initial letter.

    For the ``'bytes'`` format, characters from the 'Latin Extended-A' unicode block are used for non-ASCII and unprintable characters.

    If the bitstring cannot be represented in a format due to it's length not being a multiple of the number of bits represented by each character then an :exc:`InterpretError` will be raised.

    An output *stream* can be specified. This should be an object with a ``write`` method and the default is ``sys.stdout``.


.. method:: Bits.rfind(bs: BitsType, start: int | None = None, end: int | None = None, bytealigned: bool | None = None) -> Tuple[int] | Tuple[()]

    Searches backwards for *bs* in the current bitstring and sets :attr:`~ConstBitStream.pos` to the start of *bs* and returns it in a tuple if found, otherwise it returns an empty tuple.

    The reason for returning the bit position in a tuple is so that it evaluates as True even if the bit position is zero. This allows constructs such as ``if s.rfind('0xb3'):`` to work as expected.

    If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions. *start* and *end* give the search range and default to ``0`` and :attr:`len` respectively.

    Note that as it's a reverse search it will start at *end* and finish at *start*. ::

        >>> s = Bits('0o031544')
        >>> s.rfind('0b100')
        (15,)
        >>> s.rfind('0b100', end=17)
        (12,)

.. method:: Bits.split(delimiter: BitsType, start: int | None = None, end: int | None = None, count: int | None = None, bytealigned: bool | None = None) -> Iterable[Bits]

    Splits the bitstring into sections that start with *delimiter*. Returns a generator for bitstring objects.

    The first item generated is always the bits before the first occurrence of delimiter (even if empty). A slice can be optionally specified with *start* and *end*, while *count* specifies the maximum number of items generated.

    If *bytealigned* is ``True`` then the delimiter will only be found if it starts at a byte aligned position. ::

        >>> s = Bits('0x42423')
        >>> [bs.bin for bs in s.split('0x4')]
        ['', '01000', '01001000', '0100011']

.. method:: Bits.startswith(bs: BitsType, start: int | None = None, end: int | None = None) -> bool

    Returns ``True`` if the bitstring starts with the sub-string *bs*, otherwise returns ``False``.

    A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring. ::

        >>> s = BitArray('0xef133')
        >>> s.startswith('0b111011')
        True

.. method:: Bits.tobitarray() -> bitarray.bitarray

    Returns the bitstring as a ``bitarray`` object.

    Converts the bitstring to an equivalent ``bitarray`` object from the ``bitarray`` package.
    This shouldn't be confused with the ``BitArray`` type provided in the ``bitstring`` package - the ``bitarray`` package is a separate third-party way of representing binary objects.

    Note that ``BitStream`` and ``ConstBitStream`` types that have a bit position do support this method but the bit position information will be lost.



.. method:: Bits.tobytes() -> bytes

    Returns the bitstring as a ``bytes`` object.

    The returned value will be padded at the end with between zero and seven ``0`` bits to make it byte aligned.
    This differs from using the plain :attr:`~Bits.bytes` property which will not pad with zero bits and instead raises an exception if the bitstring is not a whole number of bytes long.

    This method can also be used to output your bitstring to a file - just open a file in binary write mode and write the function's output. ::

        >>> s = Bits(bytes=b'hello')
        >>> s += '0b01'
        >>> s.tobytes()
        b'hello@'

    This is equivalent to casting to a bytes object directly: ::

        >>> bytes(s)
        b'hello@'


.. method:: Bits.tofile(f: BinaryIO) -> None

    Writes the bitstring to the file object *f*, which should have been opened in binary write mode.

    The data written will be padded at the end with between zero and seven ``0`` bits to make it byte aligned. ::

        >>> f = open('newfile', 'wb')
        >>> Bits('0x1234').tofile(f)


.. method:: Bits.unpack(fmt: str | list[str | int], **kwargs) -> list[float | int | str | None | Bits]

    Interprets the whole bitstring according to the *fmt* string or iterable and returns a list of bitstring objects.

    A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string.

    *fmt* is an iterable or a string with comma separated tokens that describe how to interpret the next bits in the bitstring. See the  :ref:`format_tokens` for details. ::

        >>> s = Bits('int4=-1, 0b1110')
        >>> i, b = s.unpack('int:4, bin')

    If a token doesn't supply a length (as with ``bin`` above) then it will try to consume the rest of the bitstring. Only one such token is allowed.

    The ``unpack`` method is a natural complement of the :func:`pack` function. ::

        s = bitstring.pack('uint10, hex, int13, 0b11', 130, '3d', -23)
        a, b, c, d = s.unpack('uint10, hex, int13, bin2')


Properties
----------

Note that the ``bin``, ``oct``, ``hex``, ``int``, ``uint`` and ``float`` properties can all be shortened to their initial letter. Properties can also have a length in bits appended to them to such as ``u8`` or ``f64`` (for the ``bytes`` property the length is interpreted in bytes instead of bits). These properties with lengths will cause an :exc:`InterpretError` to be raised if the bitstring is not of the specified length.

.. attribute:: Bits.bin
    :type: str
.. attribute:: Bits.b
    :type: str
    :noindex:

    Property for the representation of the bitstring as a binary string.

.. attribute:: Bits.bfloat
    :type: float
.. attribute:: Bits.bfloatbe
    :type: float

    Property for the 2 byte bfloat floating point representation of the bitstring.

    The bitstring must be 16 bits long to support this floating point interpretation, otherwise an :exc:`InterpretError` will be raised.

    The :attr:`bfloat` property is bit-wise big-endian, which as all floats must be whole-byte is exactly equivalent to the byte-wise big-endian :attr:`bfloatbe`.

    The ``bfloat`` properties are specialised representations mainly used in machine learning. They are essentially the first half of the IEEE 32-bit floats, so have the same range but with less accuracy. If you don't know what a bfloat is then you almost certainly want to use the ``float`` properties instead. See :ref:`Exotic floats` for more information.


.. attribute:: Bits.bfloatle
    :type: float

    Property for the byte-wise little-endian 2 byte bfloat floating point representation of the bitstring.

.. attribute:: Bits.bfloatne
    :type: float

    Property for the byte-wise native-endian 2 byte bfloat floating point representation of the bitstring.

.. attribute:: Bits.bool
    :type: bool

    Property for representing the bitstring as a boolean (``True`` or ``False``).

    If the bitstring is not a single bit then the getter will raise an :exc:`InterpretError`.

.. attribute:: Bits.bytes
    :type: bytes

    Property representing the underlying byte data that contains the bitstring.

    When used as a getter the bitstring must be a whole number of byte long or a :exc:`InterpretError` will be raised.

    An alternative is to use the :meth:`tobytes` method, which will pad with between zero and seven ``0`` bits to make it byte aligned if needed. ::

        >>> s = Bits('0x12345678')
        >>> s.bytes
        b'\x124Vx'

.. attribute:: Bits.hex
    :type: str
.. attribute:: Bits.h
    :type: str
    :noindex:

    Property representing the hexadecimal value of the bitstring.

    If the bitstring is not a multiple of four bits long then getting its hex value will raise an :exc:`InterpretError`. ::

        >>> s = Bits(bin='1111 0000')
        >>> s.hex
        'f0'

.. attribute:: Bits.int
    :type: int
.. attribute:: Bits.i
    :type: int
    :noindex:

    Property for the signed two’s complement integer representation of the bitstring.

.. attribute:: Bits.intbe
    :type: int

    Property for the byte-wise big-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstrings, in which case it is equal to ``s.int``, otherwise an :exc:`InterpretError` is raised.

.. attribute:: Bits.intle
    :type: int

    Property for the byte-wise little-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstring, in which case it is equal to ``s[::-8].int``, i.e. the integer representation of the byte-reversed bitstring.

.. attribute:: Bits.intne
    :type: int

    Property for the byte-wise native-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstrings, and will equal either the big-endian or the little-endian integer representation depending on the platform being used.

.. attribute:: Bits.float
    :type: float
.. attribute:: Bits.floatbe
    :type: float
.. attribute:: Bits.f
    :type: float
    :noindex:

    Property for the floating point representation of the bitstring.

    The bitstring must be 16, 32 or 64 bits long to support the floating point interpretations, otherwise an :exc:`InterpretError` will be raised.

    If the underlying floating point methods on your machine are not IEEE 754 compliant then using the float interpretations is undefined (this is unlikely unless you're on some very unusual hardware).

    The :attr:`float` property is bit-wise big-endian, which as all floats must be whole-byte is exactly equivalent to the byte-wise big-endian :attr:`floatbe`.

.. attribute:: Bits.floatle
    :type: float

    Property for the byte-wise little-endian floating point representation of the bitstring.

.. attribute:: Bits.floatne
    :type: float

    Property for the byte-wise native-endian floating point representation of the bitstring.

.. attribute:: Bits.e4m3float
    :type: float

    Property for an 8 bit floating point representation with 4 exponent bits and 3 mantissa bits.
    See :ref:`Exotic floats` for more information.

.. attribute:: Bits.e5m2float
    :type: float

    Property for an 8 bit floating point representation with 5 exponent bits and 2 mantissa bits.
    See :ref:`Exotic floats` for more information.

.. attribute:: Bits.len
    :type: int
.. attribute:: Bits.length
    :type: int
    :noindex:

    Read-only property that give the length of the bitstring in bits (:attr:`len` and ``length`` are equivalent).

    Using the ``len()`` built-in function is preferred in almost all cases, but these properties are available for backward compatibility. The only occasion where the properties are needed is if a 32-bit build of Python is being used and you have a bitstring whose length doesn't fit in a 32-bit unsigned integer. In that case ``len(s)`` may fail with an :exc:`OverflowError`, whereas ``s.len`` will still work. With 64-bit Python the problem shouldn't occur unless you have more than a couple of exabytes of data!

.. attribute:: Bits.oct
    :type: str
.. attribute:: Bits.o
    :type: str
    :noindex:

    Property for the octal representation of the bitstring.

    If the bitstring is not a multiple of three bits long then getting its octal value will raise a :exc:`InterpretError`. ::

        >>> s = Bits('0b111101101')
        >>> s.oct
        '755'
        >>> s.oct = '01234567'
        >>> s.oct
        '01234567'

.. attribute:: Bits.se
    :type: int

    Property for the signed exponential-Golomb code representation of the bitstring.

    When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code. ::

        >>> s = BitArray(se=-40)
        >>> s.bin
        0000001010001
        >>> s += '0b1'
        >>> s.se
        Error: BitString is not a single exponential-Golomb code.

.. attribute:: Bits.ue
    :type: int

    Property for the unsigned exponential-Golomb code representation of the bitstring.

    When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code.

.. attribute:: Bits.sie
    :type: int

    Property for the signed interleaved exponential-Golomb code representation of the bitstring.

    When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code.

.. attribute:: Bits.uie
    :type: int

    Property for the unsigned interleaved exponential-Golomb code representation of the bitstring.

    When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code.

.. attribute:: Bits.uint
    :type: int
.. attribute:: Bits.u
    :type: int
    :noindex:

    Property for the unsigned base-2 integer representation of the bitstring.

.. attribute:: Bits.uintbe
    :type: int

    Property for the byte-wise big-endian unsigned base-2 integer representation of the bitstring.

.. attribute:: Bits.uintle
    :type: int

    Property for the byte-wise little-endian unsigned base-2 integer representation of the bitstring.

.. attribute:: Bits.uintne
    :type: int

    Property for the byte-wise native-endian unsigned base-2 integer representation of the bitstring.


Special Methods
---------------

.. method:: Bits.__add__(bs)
.. method:: Bits.__radd__(bs)

    ``s1 + s2``

    Concatenate two bitstring objects and return the result. Either bitstring can be 'auto' initialised. ::

        s = Bits(ue=132) + '0xff'
        s2 = '0b101' + s

.. method:: Bits.__and__(bs)
.. method:: Bits.__rand__(bs)

    ``s1 & s2``

    Returns the bit-wise AND between two bitstrings, which must have the same length otherwise a :exc:`ValueError` is raised. ::

        >>> print(Bits('0x33') & '0x0f')
        0x03

.. method:: Bits.__bool__()

    ``if s:``

    Returns ``False`` if the bitstring is empty (has zero length), otherwise returns ``True``.

        >>> bool(Bits())
        False
        >>> bool(Bits('0b0000010000'))
        True
        >>> bool(Bits('0b0000000000'))
        True

.. method:: Bits.__contains__(bs)

    ``bs in s``

    Returns ``True`` if *bs* can be found in the bitstring, otherwise returns ``False``.

    Similar to using :meth:`~Bits.find`, except that you are only told if it is found, and not where it was found. ::

        >>> '0b11' in Bits('0x06')
        True
        >>> '0b111' in Bits('0x06')
        False

.. method:: Bits.__copy__()

    ``s2 = copy.copy(s1)``

    This allows the ``copy`` module to correctly copy bitstrings. Other equivalent methods are to initialise a new bitstring with the old one or to take a complete slice. ::

        >>> import copy
        >>> s = Bits('0o775')
        >>> s_copy1 = copy.copy(s)
        >>> s_copy2 = Bits(s)
        >>> s_copy3 = s[:]
        >>> s == s_copy1 == s_copy2 == s_copy3
        True

.. method:: Bits.__eq__(bs)

    ``s1 == s2``

    Compares two bitstring objects for equality, returning ``True`` if they have the same binary representation, otherwise returning ``False``. ::

        >>> Bits('0o7777') == '0xfff'
        True
        >>> a = Bits(uint=13, length=8)
        >>> b = Bits(uint=13, length=10)
        >>> a == b
        False

    If you have a different criterion you wish to use then code it explicitly, for example ``a.int == b.int`` could be true even if ``a == b`` wasn't (as they could be different lengths).


.. method:: Bits.__getitem__(key)

    ``s[start:end:step]``

    Returns a slice of the bitstring.

    The usual slice behaviour applies. ::

        >>> s = Bits('0x0123456')
        >>> s[4:8]
        Bits('0x1')
        >>> s[1::8] # 1st, 9th, 17th and 25th bits
        Bits('0x3')

    If a single element is asked for then either ``True`` or ``False`` will be returned. ::

        >>> s[0]
        False
        >>> s[-1]
        True

.. method:: Bits.__hash__()

    ``hash(s)``

    Returns an integer hash of the :class:`Bits`.

    This method is not available for the :class:`BitArray` or :class:`BitStream` classes, as only immutable objects should be hashed. You typically won't need to call it directly, instead it is used for dictionary keys and in sets.

.. method:: Bits.__invert__()

    ``~s``

    Returns the bitstring with every bit inverted, that is all zeros replaced with ones, and all ones replaced with zeros.

    If the bitstring is empty then an :exc:`Error` will be raised. ::

        >>> s = ConstBitStream(‘0b1110010’)
        >>> print(~s)
        0b0001101
        >>> print(~s & s)
        0b0000000
        >>> ~~s == s
        True

.. method:: Bits.__len__()

    ``len(s)``

    Returns the length of the bitstring in bits.

    If you are using a 32-bit Python build (which is quite unlikely these days) it's recommended that you use the :attr:`len` property rather than the :func:`len` function because of the function will raise a :exc:`OverflowError` if the length is greater than ``sys.maxsize``.



.. method:: Bits.__lshift__(n)

    ``s << n``

    Returns the bitstring with its bits shifted *n* places to the left. The *n* right-most bits will become zeros. ::

        >>> s = Bits('0xff')
        >>> s << 4
        Bits('0xf0')


.. method:: Bits.__mul__(n)
.. method:: Bits.__rmul__(n)

    ``s * n / n * s``

    Return bitstring consisting of *n* concatenations of another. ::

        >>> a = Bits('0x34')
        >>> b = a*5
        >>> print(b)
        0x3434343434

.. method:: Bits.__ne__(bs)

    ``s1 != s2``

    Compares two bitstring objects for inequality, returning ``False`` if they have the same binary representation, otherwise returning ``True``.


.. method:: Bits.__nonzero__()

    See :meth:`__bool__`.

.. method:: Bits.__or__(bs)
.. method:: Bits.__ror__(bs)

    ``s1 | s2``

    Returns the bit-wise OR between two bitstring, which must have the same length otherwise a :exc:`ValueError` is raised. ::

        >>> print(Bits('0x33') | '0x0f')
        0x3f

.. method:: Bits.__repr__()

    ``repr(s)``

    A representation of the bitstring that could be used to create it (which will often not be the form used to create it).

    If the result is too long then it will be truncated with ``...`` and the length of the whole will be given. ::

        >>> Bits(‘0b11100011’)
        Bits(‘0xe3’)

.. method:: Bits.__rshift__(n)

    ``s >> n``

    Returns the bitstring with its bits shifted *n* places to the right. The *n* left-most bits will become zeros. ::

        >>> s = Bits(‘0xff’)
        >>> s >> 4
        Bits(‘0x0f’)

.. method:: Bits.__str__()

    ``print(s)``

    Used to print a representation of the bitstring, trying to be as brief as possible.

    If the bitstring is a multiple of 4 bits long then hex will be used, otherwise either binary or a mix of hex and binary will be used. Very long strings will be truncated with ``...``. ::

        >>> s = Bits('0b1')*7
        >>> print(s)
        0b1111111
        >>> print(s + '0b1')
        0xff

    See also the :meth:`pp` method for ways to pretty-print the bitstring.

.. method:: Bits.__xor__(bs)
.. method:: Bits.__rxor__(bs)

    ``s1 ^ s2``

    Returns the bit-wise XOR between two bitstrings, which must have the same length otherwise a :exc:`ValueError` is raised. ::

        >>> print(Bits('0x33') ^ '0x0f')
        0x3c

