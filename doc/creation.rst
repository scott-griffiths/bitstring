.. currentmodule:: bitstring

Creation
========

You can create bitstrings in a variety of ways. Internally they are stored as byte arrays, which means that no space is wasted, and a bitstring containing 10MB of binary data will only take up 10MB of memory.

The bitstring classes
---------------------

Four classes are provided by the bitstring module: :class:`BitStream` and :class:`BitArray` together with their immutable versions :class:`ConstBitStream` and :class:`ConstBitArray`:

 * :class:`ConstBitArray` ``(object)``: This is the most basic class. It is immutable and so its contents can't be changed after creation.
 * :class:`BitArray` ``(ConstBitArray)``: This adds mutating methods to its base class.
 * :class:`ConstBitStream` ``(ConstBitArray)``: This adds methods and properties to allow the bits to be treated as a stream of bits, with a bit position and reading/parsing methods.
 * :class:`BitStream` ``(BitArray, ConstBitStream)``: This is the most versative class, having both the bitstream methods and the mutating methods.

Before verion 2.1 ``BitStream`` was known as ``BitString`` and ``ConstBitStream`` was known as ``Bits``. These old names are still available for backward compatibility but the use of ``Bits`` in particular is discouraged as I plan to rename ``ConstBitArray`` to ``Bits`` in version 3.

The term 'bitstring' is used in this manual to refer generically to any of these classes.

Most of the exampes in this manual use the :class:`BitArray` class, with :class:`BitStream` used when necessary. For most uses the non-const classes are more versatile and so probably your best choice when starting to use the module.

To summarise when to use each class:

* If you need to change the contents of the bitstring then you must use :class:`BitArray` or :class:`BitStream`. Truncating, replacing, inserting, appending etc. are not available for the const classes.
* If you need to use a bitstring as the key in a dictionary or as a member of a ``set`` then you must use :class:`ConstBitArray` or a :class:`ConstBitStream`. As :class:`BitArray` and :class:`BitStream` objects are mutable they do not support hashing and so cannot be used in these ways.
* If you are creating directly from a file then a :class:`BitArray` or :class:`BitStream` will read the file into memory whereas a :class:`ConstBitArray` or :class:`ConstBitStream` will not, so using the const classes allows extremely large files to be examined.
* If you don't need the extra functionality of a particular class then the simpler ones might be faster and more memory efficient. The fastest and most memory efficient class is :class:`ConstBitArray`.
The :class:`ConstBitArray` class is the base class of the other three class. This means that ``isinstance(s, ConstBitArray)`` will be true if ``s`` is an instance of any of the four classes.


Using the constructor
---------------------
When initialising a bitstring you need to specify at most one initialiser. These will be explained in full below, but briefly they are:

* ``auto`` : Either a specially formatted string, a list or tuple, a file object, integer, bytearray, bytes or another bitstring.
* ``bytes`` : A ``bytes`` object (a ``str`` in Python 2.6), for example read from a binary file.
* ``hex``, ``oct``, ``bin``: Hexadecimal, octal or binary strings.
* ``int``, ``uint``: Signed or unsigned bit-wise big-endian binary integers.
* ``intle``, ``uintle``: Signed or unsigned byte-wise little-endian binary integers.
* ``intbe``, ``uintbe``: Signed or unsigned byte-wise big-endian binary integers.
* ``intne``, ``uintne``: Signed or unsigned byte-wise native-endian binary integers.
* ``float`` / ``floatbe``, ``floatle``, ``floatne``: Big, little and native endian floating point numbers.
* ``se``, ``ue`` : Signed or unsigned exponential-Golomb coded integers.
* ``bool`` : A boolean (i.e. True or False).
* ``filename`` : Directly from a file, without reading into memory.

From a hexadecimal string
^^^^^^^^^^^^^^^^^^^^^^^^^

    >>> c = BitArray(hex='0x000001b3')
    >>> c.hex
    '0x000001b3'

The initial ``0x`` or ``0X`` is optional. Whitespace is also allowed and is ignored. Note that the leading zeros are significant, so the length of ``c`` will be 32.

If you include the initial ``0x`` then you can use the ``auto`` initialiser instead. As it is the first parameter in :class:`__init__<ConstBitArray>` this will work equally well::

    c = BitArray('0x000001b3')

From a binary string
^^^^^^^^^^^^^^^^^^^^

    >>> d = BitArray(bin='0011 00')
    >>> d.bin
    '0b001100'

An initial ``0b`` or ``0B`` is optional and whitespace will be ignored.

As with ``hex``, the ``auto`` initialiser will work if the binary string is prefixed by ``0b``::
 
    >>> d = BitArray('0b001100')

From an octal string
^^^^^^^^^^^^^^^^^^^^

    >>> o = BitArray(oct='34100')
    >>> o.oct
    '0o34100'

An initial ``0o`` or ``0O`` is optional, but ``0o`` (a zero and lower-case 'o') is preferred as it is slightly more readable. 

As with ``hex`` and ``bin``, the ``auto`` initialiser will work if the octal string is prefixed by ``0o``::

    >>> o = BitArray('0o34100')
    

From an integer
^^^^^^^^^^^^^^^

    >>> e = BitArray(uint=45, length=12)
    >>> f = BitArray(int=-1, length=7)
    >>> e.bin
    '0b000000101101'
    >>> f.bin
    '0b1111111'

For initialisation with signed and unsigned binary integers (``int`` and ``uint`` respectively) the ``length`` parameter is mandatory, and must be large enough to contain the integer. So for example if ``length`` is 8 then ``uint`` can be in the range 0 to 255, while ``int`` can range from -128 to 127. Two's complement is used to represent negative numbers.

The auto initialise can be used by giving a colon and the length in bits immediately after the ``int`` or ``uint`` token, followed by an equals sign then the value::

    >>> e = BitArray('uint:12=45')
    >>> f = BitArray('int:7=-1')

The plain ``int`` and ``uint`` initialisers are bit-wise big-endian. That is to say that the most significant bit comes first and the least significant bit comes last, so the unsigned number one will have a ``1`` as its final bit with all other bits set to ``0``. These can be any number of bits long. For whole-byte bitstring objects there are more options available with different endiannesses.

Big and little-endian integers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    >>> big_endian = BitArray(uintbe=1, length=16) 
    >>> little_endian = BitArray(uintle=1, length=16)
    >>> native_endian = BitArray(uintne=1, length=16)

There are unsigned and signed versions of three additional 'endian' types. The unsigned versions are used above to create three bitstrings.

The first of these, ``big_endian``, is equivalent to just using the plain bit-wise big-endian ``uint`` initialiser, except that all ``intbe`` or ``uintbe`` interpretations must be of whole-byte bitstrings, otherwise a :exc:`ValueError` is raised.

The second, ``little_endian``, is interpreted as least significant byte first, i.e. it is a byte reversal of ``big_endian``. So we have::

    >>> big_endian.hex
    '0x0001'
    >>> little_endian.hex
    '0x0100'

Finally we have ``native_endian``, which will equal either ``big_endian`` or ``little_endian``, depending on whether you are running on a big or little-endian machine (if you really need to check then use ``import sys; sys.byteorder``).

From a floating point number
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

    >>> f1 = BitArray(float=10.3, length=32)
    >>> f2 = BitArray('float:64=5.4e31')

Floating point numbers can be used for initialisation provided that the bitstring is 32 or 64 bits long. Standard Python floating point numbers are 64 bits long, so if you use 32 bits then some accuracy could be lost.

Note that the exact bits used to represent the floating point number could be platform dependent. Most PCs will conform to the IEEE 754 standard, and presently other floating point representations are not supported (although they should work on a single platform - it just might get confusing if you try to interpret a generated bitstring on another platform).

Similar to the situation with integers there are big and little endian versions. The plain ``float`` is big endian and so ``floatbe`` is just an alias.

As with other initialisers you can also auto initialise, as demonstrated with the second example below::

    >>> little_endian = BitArray(floatle=0.0, length=64)
    >>> native_endian = BitArray('floatne:32=-6.3')

Exponential-Golomb codes
^^^^^^^^^^^^^^^^^^^^^^^^

Initialisation with integers represented by exponential-Golomb codes is also possible. ``ue`` is an unsigned code while ``se`` is a signed code::

    >>> g = BitArray(ue=12)
    >>> h = BitArray(se=-402)
    >>> g.bin
    '0b0001101'
    >>> h.bin
    '0b0000000001100100101'

For these initialisers the length of the bitstring is fixed by the value it is initialised with, so the length parameter must not be supplied and it is an error to do so. If you don't know what exponential-Golomb codes are then you are in good company, but they are quite interesting, so I’ve included a section on them (see :ref:`exp-golomb`).

The ``auto`` initialiser may also be used by giving an equals sign and the value immediately after a ``ue`` or ``se`` token::

    >>> g = BitArray('ue=12')
    >>> h = BitArray('se=-402')

You may wonder why you would bother with ``auto`` in this case as the syntax is slightly longer. Hopefully all will become clear in the next section.

From raw byte data
^^^^^^^^^^^^^^^^^^

Using the length and offset parameters to specify the length in bits and an offset at the start to be ignored is particularly useful when initialising from raw data or from a file. ::

    a = BitArray(bytes=b'\x00\x01\x02\xff', length=28, offset=1)
    b = BitArray(bytes=open("somefile", 'rb').read())

The ``length`` parameter is optional; it defaults to the length of the data in bits (and so will be a multiple of 8). You can use it to truncate some bits from the end of the bitstring. The ``offset`` parameter is also optional and is used to truncate bits at the start of the data.

You can also use a ``bytearray`` object, either explicitly with a ``bytes=some_bytearray`` keyword or via the ``auto`` initialiser::

    c = BitArray(a_bytearray_object)
    
If you are using Python 3.x you can use this trick with ``bytes`` objects too. This should be used with caution as in Python 2 it will instead be interpreted as a string (it's not possible to distinguish between ``str`` and ``bytes`` in Python 2) and so your code won't work the same between Python versions. ::

    d = BitArray(b'\x23g$5')   # Use with caution! Only works correctly in Python 3.


From a file
^^^^^^^^^^^

Using the ``filename`` initialiser allows a file to be analysed without the need to read it all into memory. The way to create a file-based bitstring is::

    p = ConstBitArray(filename="my2GBfile")

This will open the file in binary read-only mode. The file will only be read as and when other operations require it, and the contents of the file will not be changed by any operations. If only a portion of the file is needed then the ``offset`` and ``length`` parameters (specified in bits) can be used.

Note that we created a :class:`ConstBitArray` here rather than a :class:`BitArray`, as they have quite different behaviour in this case. The immutable :class:`ConstBitArray` will never read the file into memory (except as needed by other operations), whereas if we had created a :class:`BitArray` then the whole of the file would immediately have been read into memory. This is because in creating a :class:`BitArray` you are implicitly saying that you want to modify it, and so it needs to be in memory.

It's also possible to use the ``auto`` initialiser for file objects. It's as simple as::

    f = open('my2GBfile', 'rb')
    p = ConstBitArray(f)


The auto initialiser
--------------------
The ``auto`` parameter is the first parameter in the :class:`__init__<ConstBitArray>` function and so the ``auto=`` can be omitted when using it. It accepts either a string, an iterable, another bitstring, an integer, a bytearray or a file object.

Strings starting with ``0x`` or ``hex:`` are interpreted as hexadecimal, ``0o`` or ``oct:`` implies octal, and strings starting with ``0b`` or ``bin:`` are interpreted as binary. You can also initialise with the various integer initialisers as described above. If given another bitstring it will create a copy of it, (non string) iterables are interpreted as boolean arrays and file objects acts a source of binary data. Finally you can use an integer to create a zeroed bitstring of that number of bits. ::

    >>> fromhex = BitArray('0x01ffc9')
    >>> frombin = BitArray('0b01')
    >>> fromoct = BitArray('0o7550')
    >>> fromint = BitArray('int:32=10')
    >>> fromfloat = BitArray('float:64=0.2')
    >>> acopy = BitArray(fromoct)
    >>> fromlist = BitArray([1, 0, 0])
    >>> f = open('somefile', 'rb')
    >>> fromfile = BitArray(f)
    >>> zeroed = BitArray(1000)
    >>> frombytes = BitArray(bytearray(b'xyz'))
 
It can also be used to convert between the :class:`BitArray` and :class:`ConstBitArray` classes::

    >>> immutable = ConstBitArray('0xabc')
    >>> mutable = BitArray(immutable)
    >>> mutable += '0xdef'
    >>> immutable = ConstBitArray(mutable)

As always the bitstring doesn't know how it was created; initialising with octal or hex might be more convenient or natural for a particular example but it is exactly equivalent to initialising with the corresponding binary string. ::

    >>> fromoct.oct
    '0o7550'
    >>> fromoct.hex
    '0xf68'
    >>> fromoct.bin
    '0b111101101000'
    >>> fromoct.uint
    3994
    >>> fromoct.int
    -152
 
    >>> BitArray('0o7777') == '0xfff'
    True
    >>> BitArray('0xf') == '0b1111'
    True
    >>> frombin[::-1] + '0b0' == fromlist
    True

Note how in the final examples above only one half of the ``==`` needs to be a bitstring, the other half gets ``auto`` initialised before the comparison is made. This is in common with many other functions and operators.

You can also chain together string initialisers with commas, which causes the individual bitstrings to be concatenated. ::

    >>> s = BitArray('0x12, 0b1, uint:5=2, ue=5, se=-1, se=4')
    >>> s.find('uint:5=2, ue=5')
    True
    >>> s.insert('0o332, 0b11, int:23=300', 4)

Again, note how the format used in the ``auto`` initialiser can be used in many other places where a bitstring is needed.

Packing
-------

Another method of creating :class:`BitArray` objects is to use the :func:`pack` function. This takes a format specifier which is a string with comma separated tokens, and a number of items to pack according to it. It's signature is ``bitstring.pack(format, *values, **kwargs)``.

For example using just the ``*values`` arguments we can say::

    s = bitstring.pack('hex:32, uint:12, uint:12', '0x000001b3', 352, 288)

which is equivalent to initialising as::

    s = BitArray('0x0000001b3, uint:12=352, uint:12=288')

The advantage of the pack function is if you want to write more general code for creation. ::

    def foo(a, b, c, d):
        return bitstring.pack('uint:8, 0b110, int:6, bin, bits', a, b, c, d)
 
    s1 = foo(12, 5, '0b00000', '')
    s2 = foo(101, 3, '0b11011', s1)

Note how you can use some tokens without sizes (such as ``bin`` and ``bits`` in the above example), and use values of any length to fill them. If the size had been specified then a :exc:`ValueError` would be raised if the parameter given was the wrong length. Note also how bitstring literals can be used (the ``0b110`` in the bitstring returned by ``foo``) and these don't consume any of the items in ``*values``.

You can also include keyword, value pairs (or an equivalent dictionary) as the final parameter(s). The values are then packed according to the positions of the keywords in the format string. This is most easily explained with some examples. Firstly the format string needs to contain parameter names::

    format = 'hex:32=start_code, uint:12=width, uint:12=height'

Then we can make a dictionary with these parameters as keys and pass it to pack::

    d = {'start_code': '0x000001b3', 'width': 352, 'height': 288}
    s = bitstring.pack(format, **d)

Another method is to pass the same information as keywords at the end of pack's parameter list::

    s = bitstring.pack(format, width=352, height=288, start_code='0x000001b3')

The tokens in the format string that you must provide values for are:

=============       ================================================================
``int:n``           ``n`` bits as a signed integer.
``uint:n``          ``n`` bits as an unsigned integer.
``intbe:n``         ``n`` bits as a big-endian whole byte signed integer.
``uintbe:n``        ``n`` bits as a big-endian whole byte unsigned integer.
``intle:n``         ``n`` bits as a little-endian whole byte signed integer.
``uintle:n``        ``n`` bits as a little-endian whole byte unsigned integer.
``intne:n``         ``n`` bits as a native-endian whole byte signed integer.
``uintne:n``        ``n`` bits as a native-endian whole byte unsigned integer.
``float:n``         ``n`` bits as a big-endian floating point number (same as ``floatbe``). 
``floatbe:n``       ``n`` bits as a big-endian floating point number (same as ``float``).
``floatle:n``       ``n`` bits as a little-endian floating point number. 
``floatne:n``       ``n`` bits as a native-endian floating point number. 
``hex[:n]``         [``n`` bits as] a hexadecimal string.
``oct[:n]``         [``n`` bits as] an octal string.
``bin[:n]``         [``n`` bits as] a binary string.
``bits[:n]``        [``n`` bits as] a new bitstring.
``bool``            single bit as a boolean (True or False).

``ue``              an unsigned integer as an exponential-Golomb code.
``se``              a signed integer as an exponential-Golomb code.
=============       ================================================================

and you can also include constant bitstring tokens constructed from any of the following:

================     ===============================================================
``0b...``            binary literal.
``0o...``            octal literal.
``0x...``            hexadecimal literal.
``int:n=m``          signed integer ``m`` in ``n`` bits.
``uint:n=m``         unsigned integer ``m`` in ``n`` bits.
``intbe:n=m``        big-endian whole byte signed integer ``m`` in ``n`` bits.
``uintbe:n=m``       big-endian whole byte unsigned integer ``m`` in ``n`` bits.
``intle:n=m``        little-endian whole byte signed integer ``m`` in ``n`` bits.
``uintle:n=m``       little-endian whole byte unsigned integer ``m`` in ``n`` bits.
``intne:n=m``        native-endian whole byte signed integer ``m`` in ``n`` bits.
``uintne:n=m``       native-endian whole byte unsigned integer ``m`` in ``n`` bits.
``float:n=f``        big-endian floating point number ``f`` in ``n`` bits.
``floatbe:n=f``      big-endian floating point number ``f`` in ``n`` bits.
``floatle:n=f``      little-endian floating point number ``f`` in ``n`` bits.
``floatne:n=f``      native-endian floating point number ``f`` in ``n`` bits.
``ue=m``             exponential-Golomb code for unsigned integer ``m``.
``se=m``             exponential-Golomb code for signed integer ``m``.
``bool=b``           a single bit, either True or False.
================     ===============================================================

You can also use a keyword for the length specifier in the token, for example::

    s = bitstring.pack('int:n=-1', n=100)

And finally it is also possible just to use a keyword as a token::

    s = bitstring.pack('hello, world', world='0x123', hello='0b110')

As you would expect, there is also an :meth:`~ConstBitArray.unpack` function that takes a bitstring and unpacks it according to a very similar format string. This is covered later in more detail, but a quick example is::

    >>> s = bitstring.pack('ue, oct:3, hex:8, uint:14', 3, '0o7', '0xff', 90)
    >>> s.unpack('ue, oct:3, hex:8, uint:14')
    [3, '0o7', '0xff', 90]

.. _compact_format:

Compact format strings
^^^^^^^^^^^^^^^^^^^^^^

Another option when using :func:`pack`, as well as other methods such as :meth:`~ConstBitArray.read` and :meth:`~BitArray.byteswap`, is to use a format specifier similar to those used in the :mod:`struct` and :mod:`array` modules. These consist of a character to give the endianness, followed by more single characters to give the format.

The endianness character must start the format string and unlike in the struct module it is not optional (except when used with :meth:`~BitArray.byteswap`):

=====   =============
``>``   Big-endian
``<``   Little-endian
``@``   Native-endian
=====   =============

For 'network' endianness use ``>`` as network and big-endian are equivalent. This is followed by at least one of these format characters:

=====   ===============================
``b``   8 bit signed integer
``B``   8 bit unsigned integer
``h``   16 bit signed integer
``H``   16 bit unsigned integer
``l``   32 bit signed integer
``L``   32 bit unsigned integer
``q``   64 bit signed integer
``Q``   64 bit unsigned integer
``f``   32 bit floating point number
``d``   64 bit floating point number
=====   ===============================

The exact type is determined by combining the endianness character with the format character, but rather than give an exhaustive list a single example should explain:

======  ======================================   ============
``>h``  Big-endian 16 bit signed integer         ``intbe:16``
``<h``  Little-endian 16 bit signed integer      ``intle:16``
``@h``  Native-endian 16 bit signed integer      ``intne:16``
======  ======================================   ============

As you can see all three are signed integers in 16 bits, the only difference is the endianness. The native-endian ``@h`` will equal the big-endian ``>h`` on big-endian systems, and equal the little-endian ``<h`` on little-endian systems. For the single byte codes ``b`` and ``B`` the endianness doesn't make any difference, but you still need to specify one so that the format string can be parsed correctly.

An example::

    s = bitstring.pack('>qqqq', 10, 11, 12, 13)

is equivalent to ::

    s = bitstring.pack('intbe:64, intbe:64, intbe:64, intbe:64', 10, 11, 12, 13)

Just as in the struct module you can also give a multiplicative factor before the format character, so the previous example could be written even more concisely as ::

    s = bitstring.pack('>4q', 10, 11, 12, 13)

You can of course combine these format strings with other initialisers, even mixing endiannesses (although I'm not sure why you'd want to)::

    s = bitstring.pack('>6h3b, 0b1, <9L', *range(18))

This rather contrived example takes the numbers 0 to 17 and packs the first 6 as signed big-endian 2-byte integers, the next 3 as single bytes, then inserts a single 1 bit, before packing the remaining 9 as little-endian 4-byte unsigned integers.

 
 
