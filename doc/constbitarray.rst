.. currentmodule:: bitstring

The Bits class
-----------------------

.. class:: Bits([auto, length, offset, **kwargs])

    Creates a new bitstring. You must specify either no initialiser, just an ``auto`` value, or one of the keyword arguments ``bytes``, ``bin``, ``hex``, ``oct``, ``uint``, ``int``, ``uintbe``, ``intbe``, ``uintle``, ``intle``, ``uintne``, ``intne``, ``se``, ``ue``, ``sie``, ``uie``, ``float``, ``floatbe``, ``floatle``, ``floatne``, ``bool`` or ``filename``. If no initialiser is given then a zeroed bitstring of ``length`` bits is created.

    The initialiser for the :class:`Bits` class is precisely the same as for :class:`BitArray`, :class:`BitStream` and :class:`ConstBitStream`.

    ``offset`` is available when using the ``bytes`` or ``filename`` initialisers. It gives a number of bits to ignore at the start of the bitstring.

    Specifying ``length`` is mandatory when using the various integer initialisers. It must be large enough that a bitstring can contain the integer in ``length`` bits. It must also be specified for the float initialisers (the only valid values are 32 and 64). It is optional for the ``bytes`` and ``filename`` initialisers and can be used to truncate data from the end of the input value. ::

           >>> s1 = Bits(hex='0x934')
           >>> s2 = Bits(oct='0o4464')
           >>> s3 = Bits(bin='0b001000110100')
           >>> s4 = Bits(int=-1740, length=12)
           >>> s5 = Bits(uint=2356, length=12)
           >>> s6 = Bits(bytes=b'\x93@', length=12)
           >>> s1 == s2 == s3 == s4 == s5 == s6
           True

    For information on the use of ``auto`` see :ref:`auto_init`. ::

        >>> s = Bits('uint:12=32, 0b110')
        >>> t = Bits('0o755, ue:12, int:3=-1')

    .. method:: all(value[, pos])

       Returns ``True`` if all of the specified bits are all set to *value*, otherwise returns ``False``.

       If *value* is ``True`` then ``1`` bits are checked for, otherwise ``0`` bits are checked for.
       
       *pos* should be an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``. It defaults to the whole bitstring.
       
           >>> s = Bits('int:15=-1')
           >>> s.all(True, [3, 4, 12, 13])
           True
           >>> s.all(1)
           True

    .. method:: any(value[, pos])

       Returns ``True`` if any of the specified bits are set to *value*, otherwise returns ``False``.

       If *value* is ``True`` then ``1`` bits are checked for, otherwise ``0`` bits are checked for.

       *pos* should be an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an :exc:`IndexError` if ``pos < -s.len`` or ``pos > s.len``. It defaults to the whole bitstring.

           >>> s = Bits('0b11011100')
           >>> s.any(False, range(6))
           True
           >>> s.any(1)
           True

    .. method:: count(value)
        
        Returns the number of bits set to *value*.
        
        *value* can be ``True`` or ``False`` or anything that can be cast to a bool, so you could equally use ``1`` or ``0``.
        
            >>> s = BitString(1000000)
            >>> s.set(1, [4, 44, 444444])
            >>> s.count(1)
            3
            >>> s.count(False)
            999997    

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

    .. method:: find(bs[, start, end, bytealigned])

        Searches for *bs* in the current bitstring and sets :attr:`pos` to the start of *bs* and returns it in a tuple if found, otherwise it returns an empty tuple.
        
        The reason for returning the bit position in a tuple is so that it evaluates as True even if the bit position is zero. This allows constructs such as ``if s.find('0xb3'):`` to work as expected.

        If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions (which is generally much faster than searching for it in every possible bit position). *start* and *end* give the search range and default to the whole bitstring. ::

            >>> s = Bits('0x0023122')
            >>> s.find('0b000100', bytealigned=True)
            (16,)

    .. method:: findall(bs[, start, end, count, bytealigned])

        Searches for all occurrences of *bs* (even overlapping ones) and returns a generator of their bit positions.

        If *bytealigned* is ``True`` then *bs* will only be looked for at byte aligned positions. *start* and *end* optionally define a search range and default to the whole bitstring.

        The *count* parameter limits the number of items that will be found - the default is to find all occurrences. ::

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
            010101010

    .. method:: rfind(bs[, start, end, bytealigned])
    
        Searches backwards for *bs* in the current bitstring and sets :attr:`pos` to the start of *bs* and returns it in a tuple if found, otherwise it returns an empty tuple.
        
        The reason for returning the bit position in a tuple is so that it evaluates as True even if the bit position is zero. This allows constructs such as ``if s.rfind('0xb3'):`` to work as expected.

        If *bytealigned* is ``True`` then it will look for *bs* only at byte aligned positions. *start* and *end* give the search range and default to ``0`` and :attr:`len` respectively.

        Note that as it's a reverse search it will start at *end* and finish at *start*. ::

            >>> s = Bits('0o031544')
            >>> s.rfind('0b100')
            (15,)
            >>> s.rfind('0b100', end=17)
            (12,)

    .. method:: split(delimiter[, start, end, count, bytealigned])

        Splits the bitstring into sections that start with *delimiter*. Returns a generator for bitstring objects.

        The first item generated is always the bits before the first occurrence of delimiter (even if empty). A slice can be optionally specified with *start* and *end*, while *count* specifies the maximum number of items generated.

        If *bytealigned* is ``True`` then the delimiter will only be found if it starts at a byte aligned position. ::

            >>> s = Bits('0x42423')
            >>> [bs.bin for bs in s.split('0x4')]
            ['', '01000', '01001000', '0100011']

    .. method:: startswith(bs[, start, end])

        Returns ``True`` if the bitstring starts with the sub-string *bs*, otherwise returns ``False``.

        A slice can be given using the *start* and *end* bit positions and defaults to the whole bitstring.

    .. method:: tobytes()

        Returns the bitstring as a ``bytes`` object (equivalent to a ``str`` in Python 2.7).

        The returned value will be padded at the end with between zero and seven ``0`` bits to make it byte aligned.

        This method can also be used to output your bitstring to a file - just open a file in binary write mode and write the function's output. ::

            >>> s = Bits(bytes=b'hello')
            >>> s += '0b01'
            >>> s.tobytes()
            b'hello@'

    .. method:: tofile(f)

        Writes the bitstring to the file object *f*, which should have been opened in binary write mode.

        The data written will be padded at the end with between zero and seven ``0`` bits to make it byte aligned. ::

            >>> f = open('newfile', 'wb')
            >>> Bits('0x1234').tofile(f)

    .. method:: unpack(fmt, **kwargs)

        Interprets the whole bitstring according to the *fmt* string or iterable and returns a list of bitstring objects.
        
        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string.

        *fmt* is an iterable or a string with comma separated tokens that describe how to interpret the next bits in the bitstring. See the entry for :meth:`read` for details. ::

            >>> s = Bits('int:4=-1, 0b1110')
            >>> i, b = s.unpack('int:4, bin')

        If a token doesn't supply a length (as with ``bin`` above) then it will try to consume the rest of the bitstring. Only one such token is allowed.
    
    .. attribute:: bin

        Property for the representation of the bitstring as a binary string.
         
    .. attribute:: bool

       Property for representing the bitstring as a boolean (``True`` or ``False``).
       
       If the bitstring is not a single bit then the getter will raise an :exc:`InterpretError`.

    .. attribute:: bytes

        Property representing the underlying byte data that contains the bitstring.

        When used as a getter the bitstring must be a whole number of byte long or a :exc:`InterpretError` will be raised.

        An alternative is to use the :meth:`tobytes` method, which will pad with between zero and seven ``0`` bits to make it byte aligned if needed. ::
       
            >>> s = Bits('0x12345678')
            >>> s.bytes
            b'\x124Vx'

    .. attribute:: hex

        Property representing the hexadecimal value of the bitstring.

        If the bitstring is not a multiple of four bits long then getting its hex value will raise an :exc:`InterpretError`. ::

            >>> s = Bits(bin='1111 0000')
            >>> s.hex
            'f0'

    .. attribute:: int

        Property for the signed two’s complement integer representation of the bitstring.

    .. attribute:: intbe

        Property for the byte-wise big-endian signed two's complement integer representation of the bitstring.

        Only valid for whole-byte bitstrings, in which case it is equal to ``s.int``, otherwise an :exc:`InterpretError` is raised.


    .. attribute:: intle

        Property for the byte-wise little-endian signed two's complement integer representation of the bitstring.

        Only valid for whole-byte bitstring, in which case it is equal to ``s[::-8].int``, i.e. the integer representation of the byte-reversed bitstring.

    .. attribute:: intne

        Property for the byte-wise native-endian signed two's complement integer representation of the bitstring.

        Only valid for whole-byte bitstrings, and will equal either the big-endian or the little-endian integer representation depending on the platform being used.


    .. attribute:: float
    .. attribute:: floatbe

        Property for the floating point representation of the bitstring.

        The bitstring must be either 32 or 64 bits long to support the floating point interpretations, otherwise an :exc:`InterpretError` will be raised.

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

        If the bitstring is not a multiple of three bits long then getting its octal value will raise a :exc:`InterpretError`. ::

            >>> s = BitString('0b111101101')
            >>> s.oct
            '755'
            >>> s.oct = '01234567'
            >>> s.oct
            '01234567'

    .. attribute:: se

        Property for the signed exponential-Golomb code representation of the bitstring.

        When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code. ::

            >>> s = BitString(se=-40)
            >>> s.bin
            0000001010001
            >>> s += '0b1'
            >>> s.se
            Error: BitString is not a single exponential-Golomb code.

    .. attribute:: ue

        Property for the unsigned exponential-Golomb code representation of the bitstring.

        When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code.

    .. attribute:: sie

        Property for the signed interleaved exponential-Golomb code representation of the bitstring.

        When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code.

    .. attribute:: uie

        Property for the unsigned interleaved exponential-Golomb code representation of the bitstring.

        When used as a getter an :exc:`InterpretError` will be raised if the bitstring is not a single code.

    .. attribute:: uint

        Property for the unsigned base-2 integer representation of the bitstring.

    .. attribute:: uintbe

        Property for the byte-wise big-endian unsigned base-2 integer representation of the bitstring.

    .. attribute:: uintle

        Property for the byte-wise little-endian unsigned base-2 integer representation of the bitstring.

    .. attribute:: uintne

        Property for the byte-wise native-endian unsigned base-2 integer representation of the bitstring.


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
            
    .. method:: __bool__()
    
        ``if s:``
        
        Returns ``True`` if at least one bit is set to 1, otherwise returns ``False``.
        
        This special method is used in Python 3 only; for Python 2.7 the equivalent is called ``__nonzero__``, but the details are exactly the same. ::
        
            >>> bool(Bits())
            False
            >>> bool(Bits('0b0000010000'))
            True
            >>> bool(Bits('0b0000000000'))
            False

    .. method:: __contains__(bs)

        ``bs in s``

        Returns ``True`` if *bs* can be found in the bitstring, otherwise returns ``False``.

        Similar to using :meth:`~Bits.find`, except that you are only told if it is found, and not where it was found. ::

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

    .. method:: __hash__()
    
        ``hash(s)``
        
        Returns an integer hash of the :class:`Bits`.
        
        This method is not available for the :class:`BitArray` or :class:`BitStream` classes, as only immutable objects should be hashed. You typically won't need to call it directly, instead it is used for dictionary keys and in sets.
         
    .. method:: __invert__()

        ``~s``

        Returns the bitstring with every bit inverted, that is all zeros replaced with ones, and all ones replaced with zeros.

        If the bitstring is empty then an :exc:`Error` will be raised. ::

            >>> s = ConstBitStream(‘0b1110010’)
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

    .. method:: __nonzero__()
    
        See :meth:`__bool__`.

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

        Used to print a representation of the bitstring, trying to be as brief as possible.

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

