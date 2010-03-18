Classes
=======

BitString and Bits
------------------

The bitstring module provides just two classes, :class:`BitString` and :class:`Bits`. These share many methods as :class:`Bits` is the base class for :class:`BitString`. The distinction between them is that :class:`Bits` represents an immutable sequence of bits whereas :class:`BitString` objects support many methods that mutate their contents.

If you need to change the contents of a bitstring then you must use the :class:`BitString` class. If you need to use bitstrings as keys in a dictionary or members of a set then you must use the :class:`Bits` class (:class:`Bits` are hashable). Otherwise you can use whichever you prefer, but note that :class:`Bits` objects can potentially be more efficent than :class:`BitString` objects. In this section the generic term 'bitstring' means either a :class:`Bits` or a :class:`BitString` object.

Note that the bit position within the bitstring (the position from which reads occur) can change without affecting the equality operation. This means that the :attr:`pos` and :attr:`bytepos` properties can change even for a :class:`Bits` object.

The public methods, special methods and properties of both classes are detailed in this section.

The auto initialiser
^^^^^^^^^^^^^^^^^^^^

Note that in places where a bitstring can be used as a parameter, any other valid input to the ``auto`` initialiser can also be used. This means that the parameter can also be a format string which consists of tokens:

* Starting with ``hex=``, or simply starting with ``0x`` implies hexadecimal. e.g. ``0x013ff``, ``hex=013ff``

* Starting with ``oct=``, or simply starting with ``0o`` implies octal. e.g. ``0o755``, ``oct=755``

* Starting with ``bin=``, or simply starting with ``0b`` implies binary. e.g. ``0b0011010``, ``bin=0011010``

* Starting with ``int:`` or ``uint:`` followed by a length in bits and ``=`` gives base-2 integers. e.g. ``uint:8=255``, ``int:4=-7``

* To get big, little and native-endian whole-byte integers append ``be``, ``le`` or ``ne`` respectively to the ``uint`` or ``int`` identifier. e.g. ``uintle:32=1``, ``intne:16=-23``

* For floating point numbers use ``float:`` followed by the length in bits and ``=`` and the number. The default is big-endian, but you can also append ``be``, ``le`` or ``ne`` as with integers. e.g. ``float:64=0.2``, ``floatle:32=-0.3e12``

* Starting with ``ue=`` or ``se=`` implies an exponential-Golomb coded integer. e.g. ``ue=12``, ``se=-4``

Multiples tokens can be joined by separating them with commas, so for example ``se=4, 0b1, se=-1`` represents the concatenation of three elements.

Parentheses and multiplicative factors can also be used, for example ``2*(0b10, 0xf)`` is equivalent to ``0b10, 0xf, 0b10, 0xf``. The multiplying factor must come before the thing it is being used to repeat.

The ``auto`` parameter also accepts other types:

* A list or tuple, whose elements will be evaluated as booleans (imagine calling ``bool()`` on each item) and the bits set to ``1`` for ``True`` items and ``0`` for ``False`` items.
* A positive integer, used to create a bitstring of that many zero bits.
* A file object, presumably opened in read-binary mode, from which the bitstring will be formed.
* A bool (``True`` or ``False``) which will be converted to a single ``1`` or ``0`` bit respectively.



Compact format strings
^^^^^^^^^^^^^^^^^^^^^^

For the :meth:`Bits.read`, :meth:`Bits.unpack`, :meth:`Bits.peek` methods and :func:`pack` function you can use compact format strings similar to those used in the :mod:`struct` and :mod:`array` modules. These start with an endian identifier: ``>`` for big-endian, ``<`` for little-endian or ``@`` for native-endian. This must be followed by at least one of these codes:

+------+------------------------------------+
|Code  |      Interpretation                |
+======+====================================+
|``b`` |      8 bit signed integer          |
+------+------------------------------------+
|``B`` |      8 bit unsigned integer        |
+------+------------------------------------+
|``h`` |      16 bit signed integer         |
+------+------------------------------------+
|``H`` |      16 bit unsigned integer	    |
+------+------------------------------------+
|``l`` |      32 bit signed integer         |
+------+------------------------------------+
|``L`` |      32 bit unsigned integer	    |
+------+------------------------------------+
|``q`` |      64 bit signed integer         |
+------+------------------------------------+
|``Q`` |      64 bit unsigned integer       |
+------+------------------------------------+
|``f`` |      32 bit floating point number  |
+------+------------------------------------+
|``d`` |      64 bit floating point number  |
+------+------------------------------------+

For more detail see :ref:`compact_format`.

The ``Bits`` class
------------------

.. class:: Bits([auto, length, offset, **kwargs])

    Creates a new bitstring. You must specify either no initialiser, just an ``auto`` value, or one of the keyword arguments ``bytes``, ``bin``, ``hex``, ``oct``, ``uint``, ``int``, ``uintbe``, ``intbe``, ``uintle``, ``intle``, ``uintne``, ``intne``, ``se``, ``ue``, ``float``, ``floatbe``, ``floatle``, ``floatne`` or ``filename``. If no initialiser is given then a zeroed bitstring of ``length`` bits is created.

    The initialiser for the :class:`Bits` class is precisely the same as for :class:`BitString`.

    ``offset`` is optional for most initialisers, but only really useful for ``bytes`` and ``filename``. It gives a number of bits to ignore at the start of the bitstring.

    Specifying ``length`` is mandatory when using the various integer initialisers. It must be large enough that a bitstring can contain the integer in ``length`` bits. It is an error to specify ``length`` when using the ``ue`` or ``se`` initialisers. For other initialisers ``length`` can be used to truncate data from the end of the input value. ::

     >>> s1 = Bits(hex='0x934')
     >>> s2 = Bits(oct='0o4464')
     >>> s3 = Bits(bin='0b001000110100')
     >>> s4 = Bits(int=-1740, length=12)
     >>> s5 = Bits(uint=2356, length=12)
     >>> s6 = Bits(bytes='\x93@', length=12)
     >>> s1 == s2 == s3 == s4 == s5 == s6
     True

    For information on the use of the ``auto`` initialiser see the introduction to this section. ::

     >>> s = Bits('uint:12=32, 0b110')
     >>> t = Bits('0o755, ue:12, int:3=-1') 

    .. method:: allset(pos)

       Returns ``True`` if one or many bits are all set to ``1``, otherwise returns ``False``.

       *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``

       See also :meth:`Bits.allunset`.

    .. method:: allunset(pos)

       Returns ``True`` if one or many bits are all set to ``0``, otherwise returns ``False``.

       *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as    slice indices and it will raise an :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``

       See also :meth:`Bits.allset`.

    .. method:: anyset(pos)

       Returns ``True`` if any of one or many bits are set to ``1``, otherwise returns ``False``.

       *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``

       See also :meth:`Bits.anyunset`.

    .. method:: anyunset(pos)

       Returns ``True`` if any of one or many bits are set to ``0``, otherwise returns ``False``.

       *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``

       See also :meth:`Bits.anyset`.

    .. method:: bytealign()

       Aligns to the start of the next byte (so that :attr:`pos` is a multiple of 8) and returns the number of bits skipped.

       If the current position is already byte aligned then it is unchanged. ::

         >>> s = Bits('0xabcdef')
         >>> s.pos += 3
         >>> s.bytealign()
         5
         >>> s.pos
         8

    .. method:: cut(bits[, start, end, count])

        Returns a generator for slices of the bitstring of length *bits*.

        At most *count* items are returned and the range is given by the slice *[start:end]*, which defaults to the whole bitstring. ::

         >>> s = BitString('0x1234')
         >>> for nibble in s.cut(4):
         ...     s.prepend(nibble)
         >>> print(s)
         0x43211234


    .. method:: endswith(bs[, start, end])

        Returns ``True`` if the bitstring ends with the sub-string *bs*, otherwise returns ``False``.

        A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring. ::

         >>> s = Bits('0x35e22')
         >>> s.endswith('0b10, 0x22')
         True
         >>> s.endswith('0x22', start=13)
         False

    .. method:: find(bs[, start, end, bytealigned=False])

        Searches for *bs* in the current bitstring and sets :attr:`pos` to the start of *bs* and returns ``True`` if found, otherwise it returns ``False``.

        If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions (which is generally much faster than searching for it in every possible bit position). *start* and *end* give the search range and default to the whole bitstring. ::

         >>> s = Bits('0x0023122')
         >>> s.find('0b000100', bytealigned=True)
         True
         >>> s.pos
         16

    .. method:: findall(bs[, start, end, count, bytealigned=False])

        Searches for all occurrences of *bs* (even overlapping ones) and returns a generator of their bit positions.

        If *bytealigned* is ``True`` then *bs* will only be looked for at byte aligned positions. *start* and *end* optionally define a search range and default to the whole bitstring.

        The *count* paramater limits the number of items that will be found - the default is to find all occurences. ::

         >>> s = Bits('0xab220101')*5
         >>> list(s.findall('0x22', bytealigned=True))
         [8, 40, 72, 104, 136]

    .. method:: join(sequence)

        Returns the concatenation of the bitstrings in the iterable *sequence* joined with ``self`` as a separator. ::

         >>> s = Bits().join(['0x0001ee', 'uint:24=13', '0b0111'])
         >>> print(s)
         0x0001ee00000d7
         
         >>> s = Bits('0b1').join(['0b0']*5)
         >>> print(s.bin)
         0b010101010

    .. method:: peek(format)

        Reads from the current bit position :attr:`pos` in the bitstring according to the *format* string and returns result.

        The bit position is unchanged.

        For information on the format string see the entry for the :meth:`Bits.read` method.

    .. method:: peeklist(*format, **kwargs)

        Reads from current bit position :attr:`pos` in the bitstring according to the *format* string(s) and returns a list of results.

        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is not advanced to after the read items.

        See the entries for :meth:`Bits.read` and :meth:`Bits.readlist` for more information.

    .. method:: peekbit()

        Returns the next bit in the current bitstring as a new bitstring but does not advance the position. 

    .. method:: peekbits(bits)

        Returns the next *bits* bits of the current bitstring as a new bitstring but does not advance the position. ::

         >>> s = Bits('0xf01')
         >>> s.pos = 4
         >>> s.peekbits(4)
         Bits('0x0')
         >>> s.peekbits(8)
         Bits('0x01')

    .. method:: peekbitlist(*bits)

        Reads multiple *bits* from the current position and returns a list of bitstring objects, but does not advance the position. ::

         >>> s = Bits('0xf01')
         >>> for bs in s.peekbits(2, 2, 8):
         ...     print(bs)
         0b11
         0b11
         0x01
         >>> s.pos
         0 

    .. method:: peekbyte()

        Returns the next byte of the current bitstring as a new bitstring but does not advance the position. 

    .. method:: peekbytes(*bytes)

        Returns the next *bytes* bytes of the current bitstring as a new bitstring but does not advance the position.

        If multiple bytes are specified then a list of bitstring objects is returned.

    .. method:: peekbytelist(*bytes)

        Reads multiple *bytes* from the current position and returns a list of bitstring objects, but does not advance the position. ::

         >>> s = Bits('0x34eedd')
         >>> print(s.peekbytelist(1, 2))
         [Bits('0x34'), Bits('0xeedd')]

    .. method:: read(format)

        Reads from current bit position :attr:`pos` in the bitstring according the the format string and returns a single result. If not enough bits are available then all bits to the end of the bitstring will be used.

        *format* is a token string that describe how to interpret the next bits in the bitstring. The tokens are:

        ==============   ===============================================
        ``int:n``        ``n`` bits as a signed integer.
        ``uint:n``       ``n`` bits as an unsigned integer.
        ``float:n``      ``n`` bits as a floating point number.
        ``intbe:n``      ``n`` bits as a big-endian signed integer.
        ``uintbe:n``     ``n`` bits as a big-endian unsigned integer.
        ``floatbe:n``    ``n`` bits as a big-endian float.
        ``intle:n``      ``n`` bits as a little-endian signed int.
        ``uintle:n``     ``n`` bits as a little-endian unsigned int.
        ``floatle:n``    ``n`` bits as a little-endian float.
        ``intne:n``      ``n`` bits as a native-endian signed int.
        ``uintne:n``     ``n`` bits as a native-endian unsigned int.
        ``floatne:n``    ``n`` bits as a native-endian float.
        ``hex:n``        ``n`` bits as a hexadecimal string.
        ``oct:n``        ``n`` bits as an octal string.
        ``bin:n``        ``n`` bits as a binary string.
        ``ue``           next bits as an unsigned exp-Golomb.
        ``se``           next bits as a signed exp-Golomb.
        ``bits:n``       ``n`` bits as a new bitstring.
        ``bytes:n``      ``n`` bytes as ``bytes`` object.
        ==============   ===============================================

        For example::

         >>> s = Bits('0x23ef55302')
         >>> s.read('hex12')
         '0x23e'
         >>> s.read('bin:4')
         '0b1111'
         >>> s.read('uint:5')
         10
         >>> s.read('bits:4')
         Bits('0xa')

        The :meth:`Bits.read` method is useful for reading exponential-Golomb codes, which can't be read easily by :meth:`Bits.readbits` as their lengths aren't know beforehand. ::

         >>> s = Bits('se=-9, ue=4')
         >>> s.read('se')
         -9
         >>> s.read('ue')
         4

    .. method:: readlist(*format, **kwargs)

        Reads from current bit position :attr:`pos` in the bitstring according to the *format* string(s) and returns a list of results. If not enough bits are available then all bits to the end of the bitstring will be used.

        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is advanced to after the read items.

        See the entry for :meth:`Bits.read` for information on the format strings.

        For multiple items you can separate using commas or given multiple parameters::

         >>> s = Bits('0x43fe01ff21')
         >>> s.readlist('hex:8, uint:6')
         ['0x43', 63]
         >>> s.readlist('bin:3', 'intle:16')
         ['0b100', -509]
         >>> s.pos = 0
         >>> s.readlist('hex:b, uint:d', b=8, d=6)
         ['0x43', 63]

    .. method:: readbit()

        Returns the next bit of the current bitstring as a new bitstring and advances the position. 

    .. method:: readbits(bits)

        Returns the next *bits* bits of the current bitstring as a new bitstring and advances the position. ::

         >>> s = Bits('0x0001e2')
         >>> s.readbits(16)
         Bits('0x0001')
         >>> s.readbits(3).bin
         '0b111'

    .. method:: readbitlist(*bits)

        Reads multiple *bits* from the current bitstring and returns a list of bitstring objects.
        The position is advanced to after the read items. ::

         >>> s = Bits('0x0001e2')
         >>> s.readbitlist(16, 3)
         [Bits('0x0001'), Bits('0b111')]
         >>> s.readbitlist(1)
         [Bits('0b0')]

    .. method:: readbyte()

        Returns the next byte of the current bitstring as a new bitstring and advances the position. 

    .. method:: readbytes(bytes)

        Returns the next *bytes* bytes of the current bitstring as a new bitstring and advances the position.

    .. method:: readbytelist(*bytes)

        Reads multiple bytes from the current bitstring and returns a list of bitstring objects.

        The position is advanced to after the read items.

    .. method:: rfind(bs[, start, end, bytealigned=False])

        Searches backwards for *bs* in the current bitstring and returns ``True`` if found, otherwise returns ``False``.

        If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions. *start* and *end* give the search range and default to ``0`` and :attr:`len` respectively.

        Note that as it's a reverse search it will start at *end* and finish at *start*. ::

         >>> s = Bits('0o031544')
         >>> s.rfind('0b100')
         True
         >>> s.pos
         15
         >>> s.rfind('0b100', end=17)
         True
         >>> s.pos
         12

    .. method:: split(delimiter[, start, end, count, bytealigned=False])

        Splits the bitstring into sections that start with *delimiter*. Returns a generator for bitstring objects.

        The first item generated is always the bits before the first occurrence of delimiter (even if empty). A slice can be optionally specified with *start* and *end*, while *count* specifies the maximum number of items generated.

        If *bytealigned* is ``True`` then the delimiter will only be found if it starts at a byte aligned position. ::

         >>> s = Bits('0x42423')
         >>> [bs.bin for bs in s.split('0x4')]
         ['', '0b01000', '0b01001000', '0b0100011']

    .. method:: startswith(bs[, start, end])

        Returns ``True`` if the bitstring starts with the sub-string *bs*, otherwise returns ``False``.

        A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring.

    .. method:: tobytes()

        Returns the bitstring as a ``bytes`` object (equivalent to a ``str`` in Python 2.6).

        The returned value will be padded at the end with between zero and seven ``0`` bits to make it byte aligned.

        The :meth:`Bits.tobytes` method can also be used to output your bitstring to a file - just open a file in binary write mode and write the function's output. ::

         >>> s = Bits(bytes='hello')
         >>> s += '0b01'
         >>> s.tobytes()
         'hello@'

    .. method:: tofile(f)

        Writes the bitstring to the file object *f*, which should have been opened in binary write mode.

        The data written will be padded at the end with between zero and seven ``0`` bits to make it byte aligned. ::

         >>> f = open('newfile', 'wb')
         >>> Bits('0x1234').tofile(f)

    .. method:: unpack(*format, **kwargs)

        Interprets the whole bitstring according to the *format* string(s) and returns a list of bitstring objects.
        
        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string.

        *format* is one or more strings with comma separated tokens that describe how to interpret the next bits in the bitstring. See the entry for :meth:`Bits.read` for details. ::

         >>> s = Bits('int:4=-1, 0b1110')
         >>> i, b = s.unpack('int:4, bin')

        If a token doesn't supply a length (as with ``bin`` above) then it will try to consume the rest of the bitstring. Only one such token is allowed.
    
    .. method:: __add__(bs)
    .. method:: __radd__(bs)

        ``s1 + s2``

        Concatenate two bitstring objects and return the result. Either bitstring can be 'auto' initialised. ::

         s = Bits(ue=132) + '0xff'
         s2 = '0b101' + s 

    .. method:: __and__(bs)
    .. method:: __rand__(bs)

        ``s1 & s2``

        Returns the bit-wise AND between two bitstrings, which must have the same length otherwise a :exc:`ValueError` is raised. ::

         >>> print(Bits('0x33') & '0x0f')
         0x03

    .. method:: __contains__(bs)

        ``bs in s``

        Returns ``True`` if *bs* can be found in the bitstring, otherwise returns ``False``.

        Equivalent to using :meth:`Bits.find`, except that :attr:`pos` will not be changed so you don't know where it was found. ::

         >>> '0b11' in Bits('0x06')
         True
         >>> '0b111' in Bits('0x06')
         False

    .. method:: __copy__()

        ``s2 = copy.copy(s1)``

        This allows the :mod:`copy` module to correctly copy bitstrings. Other equivalent methods are to initialise a new bitstring with the old one or to take a complete slice. ::

         >>> import copy
         >>> s = Bits('0o775')
         >>> s_copy1 = copy.copy(s)
         >>> s_copy2 = Bits(s)
         >>> s_copy3 = s[:]
         >>> s == s_copy1 == s_copy2 == s_copy3
         True

    .. method:: __eq__(bs)

        ``s1 == s2``

        Compares two bitstring objects for equality, returning ``True`` if they have the same binary representation, otherwise returning ``False``. ::

         >>> Bits('0o7777') == '0xfff'
         True
         >>> a = Bits(uint=13, length=8)
         >>> b = Bits(uint=13, length=10)
         >>> a == b
         False

    .. method:: __getitem__(key)

        ``s[start:end:step]``

        Returns a slice of the bitstring.

        The usual slice behaviour applies except that the step parameter gives a multiplicative factor for ``start`` and ``end`` (i.e. the bits 'stepped over' are included in the slice). ::

         >>> s = Bits('0x0123456')
         >>> s[0:4]
         Bits('0x1')
         >>> s[0:3:8]
         Bits('0x012345')

    .. method:: __hash__()
    
        ``hash(s)``
        
        Returns an integer hash of the :class:`Bits`.
        
        This method is not available for the :class:`BitString` class, as only immutable objects should be hashed. You typically won't need to call it directly, instead it is used for dictionary keys and in sets.
         
    .. method:: __invert__()

        ``~s``

        Returns the bitstring with every bit inverted, that is all zeros replaced with ones, and all ones replaced with zeros.

        If the bitstring is empty then a :exc:`BitStringError` will be raised. ::

         >>> s = Bits(‘0b1110010’)
         >>> print(~s)
         0b0001101
         >>> print(~s & s)
         0b0000000

    .. method:: __len__()

        ``len(s)``

        Returns the length of the bitstring in bits if it is less than ``sys.maxsize``, otherwise raises :exc:`OverflowError`.

        It's recommended that you use the :attr:`len` property rather than the :func:`len` function because of the function's behaviour for large bitstring objects, although calling the special function directly will always work. ::

         >>> s = Bits(filename='11GB.mkv')
         >>> s.len
         93944160032
         >>> len(s)
         OverflowError: long int too large to convert to int
         >>> s.__len__()
         93944160032

    .. method:: __lshift__(n)

        ``s << n``

        Returns the bitstring with its bits shifted *n* places to the left. The *n* right-most bits will become zeros. ::

         >>> s = Bits('0xff') 
         >>> s << 4
         Bits('0xf0')

    .. method:: __mul__(n)
    .. method:: __rmul__(n)

        ``s * n / n * s``

        Return bitstring consisting of *n* concatenations of another. ::

         >>> a = Bits('0x34')
         >>> b = a*5
         >>> print(b)
         0x3434343434

    .. method:: __ne__(bs)

        ``s1 != s2``

        Compares two bitstring objects for inequality, returning ``False`` if they have the same binary representation, otherwise returning ``True``. 

    .. method:: __or__(bs)
    .. method:: __ror__(bs)

        ``s1 | s2``

        Returns the bit-wise OR between two bitstring, which must have the same length otherwise a :exc:`ValueError` is raised. ::

         >>> print(Bits('0x33') | '0x0f')
         0x3f

    .. method:: __repr__()

        ``repr(s)``

        A representation of the bitstring that could be used to create it (which will often not be the form used to create it). 

        If the result is too long then it will be truncated with ``...`` and the length of the whole will be given. ::

         >>> Bits(‘0b11100011’)
         Bits(‘0xe3’)

    .. method:: __rshift__(n)

        ``s >> n``

        Returns the bitstring with its bits shifted *n* places to the right. The *n* left-most bits will become zeros. ::

         >>> s = Bits(‘0xff’)
         >>> s >> 4
         Bits(‘0x0f’)

    .. method:: __str__()

        ``print(s)``

        Used to print a representation of of the bitstring, trying to be as brief as possible.

        If the bitstring is a multiple of 4 bits long then hex will be used, otherwise either binary or a mix of hex and binary will be used. Very long strings will be truncated with ``...``. ::

         >>> s = Bits('0b1')*7
         >>> print(s)
         0b1111111 
         >>> print(s + '0b1')
         0xff

    .. method:: __xor__(bs)
    .. method:: __rxor__(bs)

        ``s1 ^ s2``

        Returns the bit-wise XOR between two bitstrings, which must have the same length otherwise a :exc:`ValueError` is raised. ::

         >>> print(Bits('0x33') ^ '0x0f')
         0x3c


The ``BitString`` class
-----------------------

.. class:: BitString

    The :class:`Bits` class is the base class for :class:`BitString` and so (with the exception of :meth:`Bits.__hash__`) all of its methods are also available for :class:`BitString` objects. The initialiser is also the same as for :class:`Bits` and so won't be repeated here.

    A :class:`BitString` is a mutable :class:`Bits`, and so the one thing all of the methods listed here have in common is that  they can modify the contents of the bitstring.

    .. method:: append(bs)

       Join a :class:`BitString` to the end of the current :class:`BitString`. ::

        >>> s = BitString('0xbad')
        >>> s.append('0xf00d')
        >>> s
        BitString('0xbadf00d')

    .. method:: byteswap(format[, start, end, repeat=True])
    
       Change the endianness of the :class:`BitString` in-place according to the *format*. Return the number of swaps done.
       
       The *format* can be an integer, an iterable of integers or a compact format string similar to those used in :func:`pack` (described in :ref:`compact_format`). It gives a pattern of byte sizes to use to swap the endianness of the :class:`BitString`. Note that if you use a compact format string then the endianness identifier (``<``, ``>`` or ``@``) is not needed, and if present it will be ignored.
       
       *start* and *end* optionally give a slice to apply the transformation to (it defaults to the whole :class:`BitString`). If *repeat* is ``True`` then the byte swapping pattern given by the *format* is repeated in its entirety as many times as possible.
       
        >>> s = BitString('0x00112233445566')
        >>> s.byteswap(2)
        3
        >>> s
        BitString('0x11003322554466')
        >>> s.byteswap('h')
        3
        >>> s
        BitString('0x00112233445566')
        >>> s.byteswap([2, 5])
        1
        >>> s
        BitString('0x11006655443322')
        
    .. method:: insert(bs[, pos])

        Inserts *bs* at *pos*. After insertion the property :attr:`pos` will be immediately after the inserted bitstring.

        The default for *pos* is the current position. ::

         >>> s = BitString('0xccee')
         >>> s.insert('0xd', 8)
         >>> s
         BitString('0xccdee')
         >>> s.insert('0x00')
         >>> s
         BitString('0xccd00ee')

    .. method:: invert(pos)
    
        Inverts one or many bits from ``1`` to ``0`` or vice versa. *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``.

    .. method:: overwrite(bs[, pos])

        Replaces the contents of the current :class:`BitString` with *bs* at *pos*. After overwriting :attr:`pos` will be immediately after the overwritten section.

        The default for *pos* is the current position. ::

         >>> s = BitString(length=10)
         >>> s.overwrite('0b111', 3)
         >>> s
         BitString('0b0001110000')
         >>> s.pos
         6

    .. method:: prepend(bs)

        Inserts *bs* at the beginning of the current :class:`BitString`. ::

         >>> s = BitString('0b0')
         >>> s.prepend('0xf')
         >>> s
         BitString('0b11110')

    .. method:: replace(old, new[, start, end, count, bytealigned=False])

        Finds occurrences of *old* and replaces them with *new*. Returns the number of replacements made.

        If *bytealigned* is ``True`` then replacements will only be made on byte boundaries. *start* and *end* give the search range and default to ``0`` and :attr:`len` respectively. If *count* is specified then no more than this many replacements will be made. ::

         >>> s = BitString('0b0011001')
         >>> s.replace('0b1', '0xf')
         3
         >>> print(s.bin)
         0b0011111111001111
         >>> s.replace('0b1', '', count=6)
         6
         >>> print(s.bin)
         0b0011001111

    .. method:: reverse([start, end])

        Reverses bits in the :class:`BitString` in-place.

        *start* and *end* give the range and default to ``0`` and :attr:`len` respectively. ::

         >>> a = BitString('0b10111')
         >>> a.reversebits()
         >>> a.bin
         '0b11101'

    .. method:: reversebytes([start, end])

        Reverses bytes in the :class:`BitString` in-place.

        *start* and *end* give the range and default to ``0`` and :attr:`len` respectively. Note that *start* and *end* are specified in bits so if ``end - start`` is not a multiple of 8 then a :exc:`BitStringError` is raised.

        Can be used to change the endianness of the :class:`BitString`. ::

         >>> s = BitString('uintle:32=1234')
         >>> s.reversebytes()
         >>> print(s.uintbe)
         1234

    .. method:: rol(bits[, start, end])

        Rotates the contents of the :class:`BitString` in-place by *bits* bits to the left.

        *start* and *end* define the slice to use and default to ``0`` and :attr:`len` respectively.
        
        Raises :exc:`ValueError` if ``bits < 0``. ::

         >>> s = BitString('0b01000001')
         >>> s.rol(2)
         >>> s.bin
         '0b00000101'

    .. method:: ror(bits[, start, end])

        Rotates the contents of the :class:`BitString` in-place by *bits* bits to the right.

        *start* and *end* define the slice to use and default to ``0`` and :attr:`len` respectively.
        
        Raises :exc:`ValueError` if ``bits < 0``.

    .. method:: set(pos)

        Sets one or many bits to ``1``. *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``.

        Using ``s.set(x)`` is considerably more efficent than other equivalent methods such as ``s[x] = 1``, ``s[x] = "0b1"`` or ``s.overwrite('0b1', x)``.

        See also :meth:`BitString.unset`. ::

         >>> s = BitString('0x0000')
         >>> s.set(-1)
         >>> print(s)
         0x0001
         >>> s.set((0, 4, 5, 7, 9))
         >>> s.bin
         '0b1000110101000001'


    .. method:: unset(pos)

        Sets one or many bits to ``0``. *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``.

        Using ``s.unset(x)`` is considerably more efficent than other equivalent methods such as ``s[x] = 0``, ``s[x] = "0b0"`` or ``s.overwrite('0b0', x)``.

        See also :meth:`BitString.set`.

    .. method:: __delitem__(key)

        ``del s[start:end:step]``

        Deletes the slice specified.

        After deletion :attr:`pos` will be at the deleted slice's position.
        
    .. method:: __iadd__(bs)

        ``s1 += s2``

        Return the result of appending *bs* to the current bitstring.
        
        Note that for :class:`BitString` objects this will be an in-place change, whereas for :class:`Bits` objects using ``+=`` will not call this method - instead a new object will be created (it is equivalent to a copy and an :meth:`Bits.__add__`). ::

         >>> s = BitString(ue=423)
         >>> s += BitString(ue=12)
         >>> s.read('ue')
         423
         >>> s.read('ue')
         12
         
    .. method:: __setitem__(key, value)

        ``s1[start:end:step] = s2``

        Replaces the slice specified with a new value. ::

         >>> s = BitString('0x00112233')
         >>> s[1:2:8] = '0xfff'
         >>> print(s)
         0x00fff2233
         >>> s[-12:] = '0xc'
         >>> print(s)
         0x00fff2c



Class properties
----------------

Bitstrings use a wide range of properties for getting and setting different interpretations on the binary data, as well as accessing bit lengths and positions.

The different interpretations such as :attr:`bin`, :attr:`hex`, :attr:`uint` etc. are not stored as part of the object, but are calculated as needed. Note that these are only available as 'getters' for :class:`Bits` objects, but can also be 'setters' for the mutable :class:`BitString` objects.

.. attribute:: bin

    Property for the representation of the bitstring as a binary string starting with ``0b``.

    When used as a getter, the returned value is always calculated - the value is never cached. For :class:`BitString` objects it can also be used as a setter, in which case the length of the :class:`BitString` will be adjusted to fit its new contents. ::

     if s.bin == '0b001':
         s.bin = '0b1111'
     # Equivalent to s.append('0b1'), only for BitStrings, not Bits.
     s.bin += '1'

.. attribute:: bytepos

    Property for setting and getting the current byte position in the bitstring.
    When used as a getter will raise a :exc:`BitStringError` if the current position in not byte aligned.

.. attribute:: bytes

    Property representing the underlying byte data that contains the bitstring.

    For :class:`BitString` objects it can also be set using an ordinary Python string - the length will be adjusted to contain the data.

    When used as a getter the bitstring must be a whole number of byte long or a :exc:`ValueError` will be raised.

    An alternative is to use the :meth:`tobytes` method, which will pad with between zero and seven ``0`` bits to make it byte aligned if needed. ::

     >>> s = BitString(bytes='\x12\xff\x30')
     >>> s.bytes
     '\x12\xff0'
     >>> s.hex = '0x12345678'
     >>> s.bytes
     '\x124Vx'

.. attribute:: hex

    Property representing the hexadecimal value of the bitstring.

    When used as a getter the value will be preceded by ``0x``, which is optional when setting the value of a :class:`BitString`. If the bitstring is not a multiple of four bits long then getting its hex value will raise a :exc:`ValueError`. ::

     >>> s = BitString(bin='1111 0000')
     >>> s.hex
     '0xf0'
     >>> s.hex = 'abcdef'
     >>> s.hex
     '0xabcdef'

.. attribute:: int

    Property for the signed two’s complement integer representation of the bitstring.

    When used on a :class:`BitString` as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised. ::

     >>> s = BitString('0xf3')
     >>> s.int
     -13
     >>> s.int = 1232
     ValueError: int 1232 is too large for a BitString of length 8.

.. attribute:: intbe

    Property for the byte-wise big-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstrings, in which case it is equal to ``s.int``, otherwise a :exc:`ValueError` is raised.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.

.. attribute:: intle

    Property for the byte-wise little-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstring, in which case it is equal to ``s[::-8].int``, i.e. the integer representation of the byte-reversed bitstring.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.

.. attribute:: intne

    Property for the byte-wise native-endian signed two's complement integer representation of the bitstring.

    Only valid for whole-byte bitstrings, and will equal either the big-endian or the little-endian integer representation depending on the platform being used.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.

.. attribute:: float
.. attribute:: floatbe

    Property for the floating point representation of the bitstring.

    The bitstring must be either 32 or 64 bits long to support the floating point interpretations, otherwise a :exc:`ValueError` will be raised.

    If the underlying floating point methods on your machine are not IEEE 754 compliant then using the float interpretations is undefined (this is unlikely unless you're on some very unusual hardware).

    The :attr:`float` property is bit-wise big-endian, which as all floats must be whole-byte is exactly equivalent to the byte-wise big-endian :attr:`floatbe`. 

.. attribute:: floatle

    Property for the byte-wise little-endian floating point representation of the bitstring.

.. attribute:: floatne

    Property for the byte-wise native-endian floating point representation of the bitstring.

.. attribute:: len
.. attribute:: length

    Read-only property that give the length of the bitstring in bits (:attr:`len` and :attr:`length` are equivalent).

    This is almost equivalent to using the ``len()`` built-in function, except that for large bitstrings ``len()`` may fail with an :exc:`OverflowError`, whereas the :attr:`len` property continues to work.

.. attribute:: oct

    Property for the octal representation of the bitstring.

    When used as a getter the value will be preceded by ``0o``, which is optional when setting the value of a :class:`BitString`. If the bitstring is not a multiple of three bits long then getting its octal value will raise a :exc:`ValueError`. ::

     >>> s = BitString('0b111101101')
     >>> s.oct
     '0o755'
     >>> s.oct = '01234567'
     >>> s.oct
     '0o01234567'

.. attribute:: pos
.. attribute:: bitpos

    Read and write property for setting and getting the current bit position in the bitstring. Can be set to any value from ``0`` to :attr:`len`.

    The :attr:`pos` and :attr:`bitpos` properties are exactly equivalent - you can use whichever you prefer. ::

     if s.pos < 100:
         s.pos += 10 

.. attribute:: se

    Property for the signed exponential-Golomb code representation of the bitstring.

    The property is set from an signed integer, and when used as a getter a :exc:`BitStringError` will be raised if the bitstring is not a single code. ::

     >>> s = BitString(se=-40)
     >>> s.bin
     0b0000001010001
     >>> s += '0b1'
     >>> s.se
     BitStringError: BitString is not a single exponential-Golomb code.

.. attribute:: ue

    Property for the unsigned exponential-Golomb code representation of the bitstring.

    The property is set from an unsigned integer, and when used as a getter a :exc:`BitStringError` will be raised if the bitstring is not a single code.

.. attribute:: uint

    Property for the unsigned base-2 integer representation of the bitstring.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.

.. attribute:: uintbe

    Property for the byte-wise big-endian unsigned base-2 integer representation of the bitstring.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.

.. attribute:: uintle

    Property for the byte-wise little-endian unsigned base-2 integer representation of the bitstring.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.

.. attribute:: uintne

    Property for the byte-wise native-endian unsigned base-2 integer representation of the bitstring.

    When used as a setter the value must fit into the current length of the :class:`BitString`, else a :exc:`ValueError` will be raised.


Exceptions
----------

.. exception:: BitStringError

Used for miscellaneous exceptions where built-in exception classes are not appropriate.
