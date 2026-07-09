.. currentmodule:: bitstring

Bits
====

The ``Bits`` class is the simplest type in the bitstring module, and represents an immutable sequence of bits. This is the best class to use if you will not need to modify the data after creation.

.. class:: Bits(auto: BitsType | None, /, length: int | None = None, **kwargs)

    Creates a new bitstring.
    You must specify either no initialiser, just an 'auto' value as the first parameter, or a keyword argument such as ``bin``, ``hex``, ``oct``, ``u``, ``i``, ``f`` or ``bool`` to indicate the data type.
    If no initialiser is given then a zeroed bitstring of ``length`` bits is created.

    The initialiser for the :class:`Bits` class is precisely the same as for :class:`BitArray`.

    Specifying ``length`` is mandatory when using the various integer initialisers.
    It must be large enough that a bitstring can contain the integer in ``length`` bits.
    It must also be specified for the float initialisers (the only valid values are 16, 32 and 64).
    For construction from bytes or files, including construction with offsets or truncation, use :meth:`Bits.from_bytes` or :meth:`Bits.from_file`. ::

           >>> s1 = Bits(hex='0x934')
           >>> s2 = Bits(oct='0o4464')
           >>> s3 = Bits(bin='0b001000110100')
           >>> s4 = Bits(i=-1740, length=12)
           >>> s5 = Bits(u=2356, length=12)
           >>> s6 = Bits.from_bytes(b'\x93@', length=12)
           >>> s1 == s2 == s3 == s4 == s5 == s6
           True

    See also :ref:`auto_init`, which describes the string-based auto initialiser. ::

        >>> s = Bits('u12=32, 0b110')
        >>> t = Bits('0o755, ue=12, i:3=-1')

    In the methods below we use ``BitsType`` to indicate that values can be promoted to bitstrings where needed.

----

Methods
-------

.. method:: Bits.all(value: bool, pos: Iterable[int] | None = None) -> bool

   Returns ``True`` if all of the specified bits are all set to *value*, otherwise returns ``False``.

   If *value* is ``True`` then ``1`` bits are checked for, otherwise ``0`` bits are checked for.

   *pos* should be an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -len(s)`` or ``pos > len(s)``. It defaults to the whole bitstring.

       >>> s = Bits('i15=-1')
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

    As ``Bits`` is immutable this can return ``self``. For a mutable copy use :meth:`to_bitarray`.


.. method:: Bits.count(value: bool) -> int

    Returns the number of bits set to *value*.

    *value* can be ``True`` or ``False`` or anything that can be cast to a bool, so you could equally use ``1`` or ``0``.

        >>> s = BitArray.from_zeros(1000000)
        >>> s.set(1, [4, 44, 444444])
        >>> s.count(1)
        3
        >>> s.count(False)
        999997

    If you need to count more than just single bits you can use :meth:`~Bits.findall`, for example ``len(list(s.findall('0xabc')))``.
    Note that if the bitstring is very sparse, as in the example here, it could be quicker to find and count all the set bits with something like ``len(list(s.findall('0b1')))``. For bitstrings with more entropy the ``count`` method will be much quicker than finding.


.. method:: Bits.cut(bits: int, *, start: int | None = None, end: int | None = None, count: int | None = None) -> Iterator[Bits]

    Returns a generator for slices of the bitstring of length *bits*.

    At most *count* items are returned and the range is given by the slice *[start:end]*, which defaults to the whole bitstring. ::

        >>> s = BitArray('0x1234')
        >>> for nibble in s.cut(4):
        ...     s.prepend(nibble)
        >>> print(s)
        0x43211234


.. method:: Bits.endswith(bs: BitsType, *, start: int | None = None, end: int | None = None) -> bool

    Returns ``True`` if the bitstring ends with the sub-string *bs*, otherwise returns ``False``.

    A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring. ::

        >>> s = Bits('0x35e22')
        >>> s.endswith('0b10, 0x22')
        True
        >>> s.endswith('0x22', start=13)
        False


.. method:: Bits.find(bs: BitsType, *, start: int | None = None, end: int | None = None, bytealigned: bool = False) -> int | None

    Searches for *bs* in the current bitstring and returns the start position if found, otherwise it returns ``None``.

    As bit position zero is a valid result, use ``s.find(...) is not None`` when testing whether a match was found.

    If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions (which is generally much faster than searching for it in every possible bit position). *start* and *end* give the search range and default to the whole bitstring. ::

        >>> s = Bits('0x0023122')
        >>> s.find('0b000100', bytealigned=True)
        16


.. method:: Bits.findall(bs: BitsType, *, start: int | None = None, end: int | None = None, count: int | None = None, bytealigned: bool = False) -> Iterable[int]

    Searches for all occurrences of *bs* (even overlapping ones) and returns a generator of their bit positions.

    If *bytealigned* is ``True`` then *bs* will only be looked for at byte aligned positions. *start* and *end* optionally define a search range and default to the whole bitstring.

    The *count* parameter limits the number of items that will be found - the default is to find all occurrences. ::

        >>> s = Bits('0xab220101')*5
        >>> list(s.findall('0x22', bytealigned=True))
        [8, 40, 72, 104, 136]


.. classmethod:: Bits.from_string(s: str, /) -> Bits

    Creates a new bitstring from the formatted string *s*.
    It is equivalent to creating a new bitstring using *s* as the first parameter, but can be clearer to write and will be slightly faster.
    The old ``fromstring`` spelling remains available as a compatibility alias.


        >>> b1 = Bits('i16=91')
        >>> b2 = Bits.from_string('i16=91')
        >>> b1 == b2
        True

.. classmethod:: Bits.from_dtype(dtype: str | Dtype, value: Any, /) -> Bits

    Creates a new bitstring by packing *value* according to *dtype*. ::

        >>> Bits.from_dtype('u10', 85)
        Bits('0b0001010101')

.. classmethod:: Bits.from_bytes(data: bytes | bytearray | memoryview, /, *, length: int | None = None, offset: int = 0) -> Bits

    Creates a new bitstring from a bytes-like object, with optional bit *offset* and *length*.

.. classmethod:: Bits.from_bools(iterable: Iterable[Any], /) -> Bits

    Creates a new bitstring from an iterable, using ``bool(item)`` for each bit.

.. classmethod:: Bits.from_zeros(length: int, /) -> Bits

    Creates a new bitstring containing *length* zero bits.

.. classmethod:: Bits.from_ones(length: int, /) -> Bits

    Creates a new bitstring containing *length* one bits.

.. classmethod:: Bits.from_joined(sequence: Iterable[BitsType], /) -> Bits

    Creates a new bitstring by concatenating the bitstrings in *sequence*.

.. classmethod:: Bits.from_file(source: str | Path | BinaryIO, /, *, length: int | None = None, offset: int = 0) -> Bits

    Creates a new bitstring from a file path or binary file object.

.. classmethod:: Bits.from_tibs(tibs_obj: tibs.Tibs | tibs.Mutibs, /) -> Bits

    Creates a new bitstring from a ``tibs.Tibs`` or ``tibs.Mutibs`` instance.

    This is an interop helper for the lower-level `tibs <https://github.com/scott-griffiths/tibs>`_ library that backs bitstring 5. ``Bits`` may share immutable ``tibs.Tibs`` data directly.
    Mutable ``tibs.Mutibs`` data is accepted, but is copied before being used by bitstring.

.. method:: Bits.to_bitarray() -> BitArray

    Returns a mutable copy of the bitstring.

.. method:: Bits.to_tibs() -> tibs.Tibs

    Returns the data as a ``tibs.Tibs`` instance.

    This is intended for interoperation with the lower-level ``tibs`` library. As ``tibs.Tibs`` is immutable, ``Bits`` can return the underlying object directly.
    No ``to_mutibs`` method is provided; use tibs' own conversion methods if you need a mutable tibs object.


.. method:: Bits.join(sequence: Iterable) -> Bits

    Returns the concatenation of the bitstrings in the iterable *sequence* joined with ``self`` as a separator. ::

        >>> s = Bits().join(['0x0001ee', 'u:24=13', '0b0111'])
        >>> print(s)
        0x0001ee00000d7

        >>> s = Bits('0b1').join(['0b0']*5)
        >>> print(s.bin)
        010101010


.. method:: Bits.pp(fmt: str | None = None, width: int = 120, sep: str = ' ', show_offset: bool = True, stream: TextIO = sys.stdout, color: bool | None = None) -> None

    Pretty print the bitstring's value according to the *fmt*. Either a single, or two comma separated formats can be specified, together with options for setting the maximum display *width*, the number of bits to display in each group, and the separator to print between groups.

        >>> s = Bits('0b10111100101101001')*20
        >>> s.pp(width=80)
        <Bits, fmt='bin8, hex', length=340 bits> [
          0: 10111100 10110100 11011110 01011010 01101111 00101101 : bc b4 de 5a 6f 2d
         48: 00110111 10010110 10011011 11001011 01001101 11100101 : 37 96 9b cb 4d e5
         96: 10100110 11110010 11010011 01111001 01101001 10111100 : a6 f2 d3 79 69 bc
        144: 10110100 11011110 01011010 01101111 00101101 00110111 : b4 de 5a 6f 2d 37
        192: 10010110 10011011 11001011 01001101 11100101 10100110 : 96 9b cb 4d e5 a6
        240: 11110010 11010011 01111001 01101001 10111100 10110100 : f2 d3 79 69 bc b4
        288: 11011110 01011010 01101111 00101101 00110111 10010110 : de 5a 6f 2d 37 96
        ] + trailing_bits = 0x9


        >>> s.pp('i20, hex', width=80, show_offset=False, sep=' / ')
        <Bits, fmt='i20, hex', length=340 bits> [
        -275635 / -107921 /  185209 /  433099 : bcb4d / e5a6f / 2d379 / 69bcb
         319066 /  455379 /  497307 / -215842 : 4de5a / 6f2d3 / 7969b / cb4de
         370418 / -182378 / -410444 / -137818 : 5a6f2 / d3796 / 9bcb4 / de5a6
         -53961 / -431684 / -307739 / -364755 : f2d37 / 969bc / b4de5 / a6f2d
         227689                               : 37969
        ]


    The available formats are any fixed-length dtypes, for example ``'bin'``, ``'oct'``, ``'hex'`` and ``'bytes'`` together with types with explicit lengths such as ``'u5'`` and ``'f16'``.
    A bit length can be specified after the format (with an optional `:`) to give the number of bits represented by each group, otherwise the default is based on the format or formats selected.

    For the ``'bytes'`` format, characters from the 'Latin Extended-A' unicode block are used for non-ASCII and unprintable characters.

    If the bitstring cannot be represented in a format due to its length not being a multiple of the number of bits represented by each character then an :exc:`InterpretError` will be raised.

    An output *stream* can be specified. This should be an object with a ``write`` method and the default is ``sys.stdout``.

    By default the output will have colours added in the terminal unless the ``NO_COLOR`` environment variable is set. Pass ``color=False`` to disable colours for a call, or ``color=True`` to force them on.


.. method:: Bits.rfind(bs: BitsType, *, start: int | None = None, end: int | None = None, bytealigned: bool = False) -> int | None

    Searches backwards for *bs* in the current bitstring and returns the start position if found, otherwise it returns ``None``.

    As bit position zero is a valid result, use ``s.rfind(...) is not None`` when testing whether a match was found.

    If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions. *start* and *end* give the search range and default to ``0`` and :attr:`len` respectively.

    Note that as it's a reverse search it will start at *end* and finish at *start*. ::

        >>> s = Bits('0o031544')
        >>> s.rfind('0b100')
        15
        >>> s.rfind('0b100', end=17)
        12

.. method:: Bits.split(delimiter: BitsType, *, start: int | None = None, end: int | None = None, count: int | None = None, bytealigned: bool = False) -> Iterable[Bits]

    Splits the bitstring into sections that start with *delimiter*. Returns a generator for bitstring objects.

    The first item generated is always the bits before the first occurrence of delimiter (even if empty). A slice can be optionally specified with *start* and *end*, while *count* specifies the maximum number of items generated.

    If *bytealigned* is ``True`` then the delimiter will only be found if it starts at a byte aligned position. ::

        >>> s = Bits('0x42423')
        >>> [bs.bin for bs in s.split('0x4')]
        ['', '01000', '01001000', '0100011']

.. method:: Bits.startswith(bs: BitsType, *, start: int | None = None, end: int | None = None) -> bool

    Returns ``True`` if the bitstring starts with the sub-string *bs*, otherwise returns ``False``.

    A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring. ::

        >>> s = BitArray('0xef133')
        >>> s.startswith('0b111011')
        True


.. method:: Bits.to_bytes() -> bytes

    Returns the bitstring as a ``bytes`` object.

    The returned value will be padded at the end with between zero and seven ``0`` bits to make it byte aligned.
    This differs from using the plain :attr:`~Bits.bytes` property which will not pad with zero bits and instead raises an exception if the bitstring is not a whole number of bytes long.

    This method can also be used to output your bitstring to a file - just open a file in binary write mode and write the function's output. ::

        >>> s = Bits.from_bytes(b'hello')
        >>> s += '0b01'
        >>> s.to_bytes()
        b'hello@'

    This is equivalent to casting to a bytes object directly: ::

        >>> bytes(s)
        b'hello@'


.. method:: Bits.to_file(f: BinaryIO) -> None

    Writes the bitstring to the file object *f*, which should have been opened in binary write mode.

    The data written will be padded at the end with between zero and seven ``0`` bits to make it byte aligned.
    The file object remains open so the user must call ``.close()`` on it once they are finished.::

        >>> f = open('newfile', 'wb')
        >>> Bits('0x1234').to_file(f)


.. method:: Bits.unpack(fmt: str | list[str | int], **kwargs) -> list[float | int | str | Bits | bool | bytes | None]

    Interprets the whole bitstring according to the *fmt* string or iterable and returns a list of values.

    A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string.

    *fmt* is an iterable or a string with comma separated tokens that describe how to interpret the next bits in the bitstring. See the  :ref:`format_tokens` for details. ::

        >>> s = Bits('i4=-1, 0b1110')
        >>> i, b = s.unpack('i:4, bin')

    If a token doesn't supply a length (as with ``bin`` above) then it will try to consume the rest of the bitstring. Only one such token is allowed.

    The ``unpack`` method is a natural complement of the :func:`pack` function. ::

        s = bitstring.pack('u10, hex, i13, 0b11', 130, '3d', -23)
        a, b, c, d = s.unpack('u10, hex, i13, bin2')

----

Properties
----------

The many ways to interpret bitstrings can be accessed via properties.
These properties will be read-only for a ``Bits`` object, but are also writable for derived mutable types such as ``BitArray``.

Properties can also have a length in bits appended to them to such as ``u8`` or ``f64`` (for the ``bytes`` property the length is interpreted in bytes instead of bits).
These properties with lengths will cause an :exc:`InterpretError` to be raised if the bitstring is not of the specified length.

This list isn't exhaustive - see for example :ref:`Exotic floats` for information on bfloats and many 8-bit and smaller floating point formats.
Also see :ref:`exp-golomb` for some interesting variable length integer formats.

The ``i``, ``u`` and ``f`` properties are the preferred names for bit-wise big-endian integer and floating point interpretations.
The longer ``int``, ``uint`` and ``float`` names remain as compatibility aliases.


.. attribute:: Bits.bin
    :type: str

    Property for the representation of the bitstring as a binary string.

.. attribute:: Bits.bool
    :type: bool

    Property for representing the bitstring as a boolean (``True`` or ``False``).

    If the bitstring is not a single bit then the getter will raise an :exc:`InterpretError`.

.. attribute:: Bits.bytes
    :type: bytes

    Property representing the underlying byte data that contains the bitstring.

    When used as a getter the bitstring must be a whole number of byte long or a :exc:`InterpretError` will be raised.

    An alternative is to use the :meth:`to_bytes` method, which will pad with between zero and seven ``0`` bits to make it byte aligned if needed. ::

        >>> s = Bits('0x12345678')
        >>> s.bytes
        b'\x124Vx'

.. attribute:: Bits.hex
    :type: str

    Property representing the hexadecimal value of the bitstring.

    If the bitstring is not a multiple of four bits long then getting its hex value will raise an :exc:`InterpretError`. ::

        >>> s = Bits(bin='1111 0000')
        >>> s.hex
        'f0'

.. attribute:: Bits.i
    :type: int
.. attribute:: Bits.int
    :type: int
    :noindex:

    Property for the signed two’s complement integer representation of the bitstring.
    ``int`` is a compatibility alias for ``i``.
    The longer endian-specific names ``intbe`` and ``intle`` are
    also compatibility aliases for ``ibe`` and ``ile``.

.. attribute:: Bits.ibe
    :type: int

    Property for the byte-wise big-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstrings, in which case it is equal to ``s.i``, otherwise an :exc:`InterpretError` is raised.

.. attribute:: Bits.ile
    :type: int

    Property for the byte-wise little-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstring, in which case it is equal to ``s[::-8].i``, i.e. the integer representation of the byte-reversed bitstring.

.. attribute:: Bits.f
    :type: float
.. attribute:: Bits.float
    :type: float
    :noindex:
.. attribute:: Bits.fbe
    :type: float

    Property for the floating point representation of the bitstring.
    ``float``, ``floatbe`` and ``fbe`` are compatibility aliases for ``f``.
    The longer endian-specific name ``floatle`` is also a compatibility alias for ``fle``.

    The bitstring must be 16, 32 or 64 bits long to support the floating point interpretations, otherwise an :exc:`InterpretError` will be raised.

    If the underlying floating point methods on your machine are not IEEE 754 compliant then using the float interpretations is undefined (this is unlikely unless you're on some very unusual hardware).

    The :attr:`f` property is bit-wise big-endian, which as all floats must be whole-byte is exactly equivalent to the byte-wise big-endian :attr:`fbe`.

.. attribute:: Bits.fle
    :type: float

    Property for the byte-wise little-endian floating point representation of the bitstring.

.. attribute:: Bits.oct
    :type: str

    Property for the octal representation of the bitstring.

    If the bitstring is not a multiple of three bits long then getting its octal value will raise a :exc:`InterpretError`. ::

        >>> s = Bits('0b111101101')
        >>> s.oct
        '755'


.. attribute:: Bits.u
    :type: int
.. attribute:: Bits.uint
    :type: int
    :noindex:

    Property for the unsigned base-2 integer representation of the bitstring.
    ``uint`` is a compatibility alias for ``u``.
    The longer endian-specific names ``uintbe`` and ``uintle`` are
    also compatibility aliases for ``ube`` and ``ule``.

.. attribute:: Bits.ube
    :type: int

    Property for the byte-wise big-endian unsigned base-2 integer representation of the bitstring.

.. attribute:: Bits.ule
    :type: int

    Property for the byte-wise little-endian unsigned base-2 integer representation of the bitstring.

.. attribute:: Bits.ue
    :type: int

    Property for the unsigned exponential-Golomb code interpretation of the bitstring.

.. attribute:: Bits.se
    :type: int

    Property for the signed exponential-Golomb code interpretation of the bitstring.

.. attribute:: Bits.uie
    :type: int

    Property for the unsigned interleaved exponential-Golomb code interpretation of the bitstring.

.. attribute:: Bits.sie
    :type: int

    Property for the signed interleaved exponential-Golomb code interpretation of the bitstring.

----

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
        >>> a = Bits(u=13, length=8)
        >>> b = Bits(u=13, length=10)
        >>> a == b
        False

    If you have a different criterion you wish to use then code it explicitly, for example ``a.i == b.i`` could be true even if ``a == b`` wasn't (as they could be different lengths).


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

    This method is not available for the :class:`BitArray` class, as only immutable objects should be hashed. You typically won't need to call it directly, instead it is used for dictionary keys and in sets.

.. method:: Bits.__invert__()

    ``~s``

    Returns the bitstring with every bit inverted, that is all zeros replaced with ones, and all ones replaced with zeros.

    If the bitstring is empty then an :exc:`Error` will be raised. ::

        >>> s = Bits('0b1110010')
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
