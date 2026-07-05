
****************
Introduction
****************

.. module:: bitstring
.. moduleauthor:: Scott Griffiths <dr.scottgriffiths@gmail.com>


The bitstring classes
---------------------

Four classes are provided by the bitstring module. Two are simple containers of bits:

* :class:`Bits`: This is the most basic class. It is immutable and so its contents can't be changed after creation.
* :class:`BitArray`: This adds mutating methods to its base class.

:class:`Bits` and :class:`BitArray` are intended to loosely mirror the ``bytes`` and ``bytearray`` types in Python.
The term 'bitstring' is used in this documentation to refer generically to either of these classes.

The :class:`Reader` class wraps either a :class:`Bits` or :class:`BitArray` object with a bit position for sequential reading.
The :class:`Array` class is a container of fixed-length bitstrings.
The rest of this introduction mostly concerns the more basic types - for more details on :class:`Array` you can go directly to the reference documentation, but understanding how bit format strings are specified will be helpful.


To summarise when to use each class:

* If you need to change the contents of the bitstring then use :class:`BitArray`. Truncating, replacing, inserting, appending etc. are not available for :class:`Bits`.
* If you need to use a bitstring as the key in a dictionary or as a member of a ``set`` then use :class:`Bits`. :class:`BitArray` objects are mutable and so cannot be used in these ways.
* If you are creating directly from a file then :class:`BitArray` will read the whole file into memory whereas :class:`Bits` will not, so using :class:`Bits` allows extremely large files to be examined.
* If you need sequential reads then create a :class:`Reader` around either kind of bitstring.
* If you don't need the extra functionality of a particular class then the simpler ones might be faster and more memory efficient. The fastest and most memory efficient class is :class:`Bits`.

The :class:`Bits` class is the base class of :class:`BitArray`. This means that ``isinstance(s, Bits)`` will be true for both bit container classes.

----

Constructing bitstrings
-----------------------

When initialising a bitstring you need to specify at most one initialiser.
This can either be the first parameter in the constructor ('auto' initialisation, described below), or using a keyword argument for a data type.

``Bits(auto, /, length: int | None = None, offset: int | None = None, **kwargs)``

Some of the keyword arguments that can be used are:

* ``bytes`` : A ``bytes`` object, for example read from a binary file.
* ``hex``, ``oct``, ``bin``: Hexadecimal, octal or binary strings.
* ``i``, ``u``: Signed or unsigned bit-wise big-endian binary integers. ``int`` and ``uint`` are compatibility aliases.
* ``ile``, ``ule``: Signed or unsigned byte-wise little-endian binary integers.
* ``ibe``, ``ube``: Signed or unsigned byte-wise big-endian binary integers.
* ``ine``, ``une``: Signed or unsigned byte-wise native-endian binary integers.
* ``f`` / ``fbe``, ``fle``, ``fne``: Big, little and native endian floating point numbers. ``float`` is a compatibility alias.
* ``bool`` : A boolean (i.e. True or False).

There are also various other flavours of 16-bit, 8-bit and smaller floating point types (see :ref:`Exotic floats`) and exponential-Golomb integer types (see :ref:`exp-golomb`).

The ``f``, ``i`` and ``u`` names are preferred for bit-wise big-endian floats and integers.
The data type name can be combined with its length if appropriate, or the length can be specified separately.

For example::

   a = Bits(hex='deadbeef')
   b = BitArray(f32=100.25)  # or = BitArray(f=100.25, length=32)
   c = Bits.from_file('a_big_file')
   d = Bits(u12=105)
   e = BitArray(bool=True)

Note that some types need a length to be specified, some don't need one, and others can infer the length from the value.

Another way to create a bitstring is via the ``pack`` function, which packs multiple values according to a given format.
See the entry on :func:`pack` for more information.

----

.. _auto_init:

The auto initialiser
--------------------

The first parameter when creating a bitstring is a positional only parameter, referred to as 'auto'.
It is most commonly a formatted string, a bytes-like object, or another bitstring.
For other common construction modes use explicit factory methods:

* :meth:`Bits.from_bools` for an iterable whose elements are evaluated as booleans.
* :meth:`Bits.from_zeros` or :meth:`Bits.from_ones` for repeated zero or one bits.
* :meth:`Bits.from_file` for a file path or binary file object.
* :meth:`Bits.from_bytes` for bytes-like data with optional bit offset and length.
* :meth:`Bits.from_joined` for concatenating many bitstrings.
* :meth:`Bits.from_tibs` for interoperation with the lower-level ``tibs`` library.

If it is a string then that string will be parsed into tokens to construct the binary data:

* Starting with ``'0x'`` or ``'hex='`` implies hexadecimal. e.g. ``'0x013ff'``, ``'hex=013ff'``
* Starting with ``'0o'`` or ``'oct='`` implies octal. e.g. ``'0o755'``, ``'oct=755'``
* Starting with ``'0b'`` or ``'bin='`` implies binary. e.g. ``'0b0011010'``, ``'bin=0011010'``
* Starting with ``'i'`` or ``'u'`` followed by a length in bits and ``'='`` gives base-2 integers. e.g. ``'u8=255'``, ``'i4=-7'``
* To get big, little and native-endian whole-byte integers append ``'be'``, ``'le'`` or ``'ne'`` respectively to the ``'u'`` or ``'i'`` identifier. e.g. ``'ule32=1'``, ``'ine16=-23'``
* For floating point numbers use ``'f'`` followed by the length in bits and ``'='`` and the number. The default is big-endian, but you can also append ``'be'``, ``'le'`` or ``'ne'`` as with integers. e.g. ``'f64=0.2'``, ``'fle32=-0.3e12'``
* Starting with ``'ue='``, ``'uie='``, ``'se='`` or ``'sie='`` implies an exponential-Golomb coded integer. e.g. ``'ue=12'``, ``'sie=-4'``

Multiples tokens can be joined by separating them with commas, so for example ``'u4=4, 0b1, se=-1'`` represents the concatenation of three elements.

Parentheses and multiplicative factors can also be used, for example ``'2*(0b10, 0xf)'`` is equivalent to ``'0b10, 0xf, 0b10, 0xf'``.
The multiplying factor must come before the thing it is being used to repeat.

Promotion to bitstrings
^^^^^^^^^^^^^^^^^^^^^^^

Almost anywhere that a bitstring is expected you can substitute something that will get 'auto' promoted to a bitstring.
For example::

    >>> BitArray('0xf') == '0b1111'
    True

Here the equals operator is expecting another bitstring so creates one from the string.
The right hand side gets promoted to ``Bits('0b1111')``.

Methods that need another bitstring as a parameter will also 'auto' promote, for example::

    for bs in s.split('0x40'):
        if bs.endswith('0b111'):
            bs.append([1, 0])
            ...

    if 'u8=42' in bs:
        bs.prepend(b'\x01')


which illustrates a variety of methods promoting strings, iterables and a bytes object to bitstrings.

Promotion is intentionally broader than the public constructor, but integers are still not promoted.
They raise a ``TypeError`` because an integer is more likely to be a mistaken value than a deliberate request for that many zero bits::

    >>> a = BitArray.from_zeros(100)  # Create bitstring with 100 zeroed bits.
    >>> a += 0xff          # TypeError - 0xff is the same as the integer 255.
    >>> a += '0xff'        # Probably what was meant - append eight '1' bits.
    >>> a += Bits.from_zeros(255)     # If you really want to do it then code it explicitly.


``BitsType``
^^^^^^^^^^^^

.. class:: BitsType(Bits | str | Iterable[Any] | BinaryIO | bytearray | bytes | memoryview)

    The ``BitsType`` type is used in the documentation in a number of places where an object of any type that can be promoted to a bitstring is acceptable.

    It's just a union of types rather than an actual class (though it's documented here as a class as I could find no alternative).
    It's not user accessible, but is just a shorthand way of saying any of the above types.

----

Keyword initialisers
--------------------

If the 'auto' initialiser isn't used then at most one keyword initialiser can be used.


From a hexadecimal string
^^^^^^^^^^^^^^^^^^^^^^^^^

    >>> c = BitArray(hex='0x000001b3')
    >>> c.hex
    '000001b3'

The initial ``0x`` or ``0X`` is optional. Whitespace is also allowed and is ignored. Note that the leading zeros are significant, so the length of ``c`` will be 32.

If you include the initial ``0x`` then you can use the 'auto' initialiser instead. As it is the first parameter in :class:`__init__<Bits>` this will work equally well::

    c = BitArray('0x000001b3')

From a binary string
^^^^^^^^^^^^^^^^^^^^

    >>> d = BitArray(bin='0011 00')
    >>> d.bin
    '001100'

An initial ``0b`` or ``0B`` is optional and whitespace will be ignored.

As with ``hex``, the 'auto' initialiser will work if the binary string is prefixed by ``0b``::

    >>> d = BitArray('0b001100')

From an octal string
^^^^^^^^^^^^^^^^^^^^

    >>> o = BitArray(oct='34100')
    >>> o.oct
    '34100'

An initial ``0o`` or ``0O`` is optional, but ``0o`` (a zero and lower-case 'o') is preferred as it is slightly more readable.

As with ``hex`` and ``bin``, the 'auto' initialiser will work if the octal string is prefixed by ``0o``::

    >>> o = BitArray('0o34100')


From an integer
^^^^^^^^^^^^^^^

    >>> e = BitArray(u=45, length=12)
    >>> f = BitArray(i=-1, length=7)
    >>> e.bin
    '000000101101'
    >>> f.bin
    '1111111'

For initialisation with signed and unsigned binary integers (``i`` and ``u`` respectively) the ``length`` parameter is mandatory, and must be large enough to contain the integer.
So for example if ``length`` is 8 then ``u`` can be in the range 0 to 255, while ``i`` can range from -128 to 127.
Two's complement is used to represent negative numbers.

The 'auto' initialiser can be used by giving the length in bits immediately after the ``i`` or ``u`` token, followed by an equals sign then the value::

    >>> e = BitArray('u12=45')
    >>> f = BitArray('i7=-1')

For mutable bitstrings you can change value by assigning to a property with a length::

    >>> e = BitArray()
    >>> e.u12 = 45
    >>> f = BitArray()
    >>> f.i7 = -1

The plain ``i`` and ``u`` initialisers are bit-wise big-endian. That is to say that the most significant bit comes first and the least significant bit comes last, so the unsigned number one will have a ``1`` as its final bit with all other bits set to ``0``. These can be any number of bits long. For whole-byte bitstring objects there are more options available with different endiannesses.

Big and little-endian integers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    >>> big_endian = BitArray(ube=1, length=16)
    >>> little_endian = BitArray(ule=1, length=16)
    >>> native_endian = BitArray(une=1, length=16)

There are unsigned and signed versions of three additional 'endian' types. The unsigned versions are used above to create three bitstrings.

The first of these, ``big_endian``, is equivalent to just using the plain bit-wise big-endian ``u`` initialiser, except that all ``ibe`` or ``ube`` interpretations must be of whole-byte bitstrings, otherwise a :exc:`ValueError` is raised.

The second, ``little_endian``, is interpreted as least significant byte first, i.e. it is a byte reversal of ``big_endian``. So we have::

    >>> big_endian.hex
    '0001'
    >>> little_endian.hex
    '0100'

Finally we have ``native_endian``, which will equal either ``big_endian`` or ``little_endian``, depending on whether you are running on a big or little-endian machine (if you really need to check then use ``import sys; sys.byteorder``).

From a floating point number
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    >>> f1 = BitArray(f=10.3, length=32)
    >>> f2 = BitArray('f64=5.4e31')

Floating point numbers can be used for initialisation provided that the bitstring is 16, 32 or 64 bits long. Standard Python floating point numbers are 64 bits long, so if you use 32 bits then some accuracy could be lost. The 16 bit version has very limited range and is used mainly in specialised areas such as machine learning.

The exact bits used to represent the floating point number will conform to the IEEE 754 standard, even if the machine being used does not use that standard internally.

Similar to the situation with integers there are big and little endian versions. The plain ``f`` is big endian, with ``float`` and ``fbe`` available as aliases.

As with other initialisers you can also 'auto' initialise, as demonstrated with the second example below::

    >>> little_endian = BitArray(fle=0.0, length=64)
    >>> native_endian = BitArray('fne:32=-6.3')

See also :ref:`Exotic floats` for information on other floating point representations that are supported (bfloat and different 8-bit and smaller float formats).

From exponential-Golomb codes
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Initialisation with integers represented by exponential-Golomb codes is also possible. ``ue`` is an unsigned code while ``se`` is a signed code. Interleaved exponential-Golomb codes are also supported via ``uie`` and ``sie``::

    >>> g = BitArray(ue=12)
    >>> h = BitArray(se=-402)
    >>> g.bin
    '0001101'
    >>> h.bin
    '0000000001100100101'

For these initialisers the length of the bitstring is fixed by the value it is initialised with, so the length parameter must not be supplied and it is an error to do so. If you don't know what exponential-Golomb codes are then you are in good company, but they are quite interesting, so I’ve included a section on them (see :ref:`exp-golomb`).

The 'auto' initialiser may also be used by giving an equals sign and the value immediately after a ``ue`` or ``se`` token::

    >>> g = BitArray('ue=12')
    >>> h = BitArray('se=-402')

You may wonder why you would bother doing this in this case as the syntax is slightly longer. Hopefully all will become clear in the next section.

From raw byte data
^^^^^^^^^^^^^^^^^^

Using the length and offset parameters to specify the length in bits and an offset at the start to be ignored is particularly useful when creating bitstrings from raw data. ::

    a = BitArray.from_bytes(b'\x00\x01\x02\xff', length=28, offset=1)
    b = BitArray.from_bytes(bytearray([0, 1, 2, 255]))

The ``length`` parameter is optional; it defaults to the length of the data in bits (and so will be a multiple of 8). You can use it to truncate some bits from the end of the bitstring. The ``offset`` parameter is also optional and is used to truncate bits at the start of the data.

You can also use a ``bytearray`` or a ``bytes`` object, either via :meth:`Bits.from_bytes` or via the 'auto' initialiser::

    c = BitArray(a_bytearray_object)
    d = BitArray(b'\x23g$5')


From a file
^^^^^^^^^^^

Using :meth:`Bits.from_file` with a path allows a file to be analysed without the need to read it all into memory. The way to create a file-based bitstring is::

    p = Bits.from_file("my200GBfile")

This will open the file in binary read-only mode. The file will only be read as and when other operations require it, and the contents of the file will not be changed by any operations. If only a portion of the file is needed then the ``offset`` and ``length`` parameters (specified in bits) can be used.

Note that we created a :class:`Bits` here rather than a :class:`BitArray`, as they have quite different behaviour in this case. The immutable :class:`Bits` will never read the file into memory (except as needed by other operations), whereas if we had created a :class:`BitArray` then the whole of the file would immediately have been read into memory. This is because in creating a :class:`BitArray` you are implicitly saying that you want to modify it, and so it needs to be in memory.

It's also possible to use :meth:`Bits.from_file` with a file object. It's as simple as::

    with open('my200GBfile', 'rb') as f:
        p = Bits.from_file(f)

.. note::

    For immutable ``Bits`` the file is memory mapped (mmap) in a read-only mode for efficiency.

    This behaves slightly differently depending on the platform; in particular Windows will lock the file against any further writing whereas Unix-like systems will not.
    This means that you won't be able to write to the file from Windows OS while the ``Bits`` object exists.

    The work-arounds for this are to either (i) Delete the object before opening the file for writing, (ii) Use ``BitArray`` which will read the whole file into memory or (iii) Stop using Windows (or run in WSL).
