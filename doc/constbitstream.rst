.. currentmodule:: bitstring

The ConstBitStream class
------------------------

.. class:: ConstBitStream([auto, length, offset, **kwargs])

    The :class:`ConstBitArray` class is the base class for :class:`ConstBitStream` and so all of its methods are also available for :class:`ConstBitStream` objects. The initialiser is also the same as for :class:`ConstBitArray` and so won't be repeated here.

    A :class:`ConstBitStream` is a :class:`ConstBitArray` with added methods and properties that allow it to be parsed as a stream of bits.


    .. method:: bytealign()

       Aligns to the start of the next byte (so that :attr:`pos` is a multiple of 8) and returns the number of bits skipped.

       If the current position is already byte aligned then it is unchanged. ::

            >>> s = ConstBitStream('0xabcdef')
            >>> s.pos += 3
            >>> s.bytealign()
            5
            >>> s.pos
            8

    .. method:: peek(fmt)

        Reads from the current bit position :attr:`pos` in the bitstring according to the *fmt* string or integer and returns the result.

        The bit position is unchanged.

        For information on the format string see the entry for the :meth:`read` method. ::
        
            >>> s = ConstBitStream('0x123456')
            >>> s.peek(16)
            ConstBitStream('0x1234')
            >>> s.peek('hex:8')
            '0x12'

    .. method:: peeklist(fmt, **kwargs)

        Reads from current bit position :attr:`pos` in the bitstring according to the *fmt* string(s) and returns a list of results.

        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is not advanced to after the read items.

        See the entries for :meth:`read` and :meth:`readlist` for more information.

    .. method:: read(fmt)

        Reads from current bit position :attr:`pos` in the bitstring according the the format string and returns a single result. If not enough bits are available then all bits to the end of the bitstring will be used.

        *fmt* is either a token string that describes how to interpret the next bits in the bitstring or an integer. If it's an integer then that number of bits will be read, and returned as a new bitstring. Otherwise the tokens are:

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
        ``bool``         next bit as a boolean (True or False).
        ==============   ===============================================

        For example::

            >>> s = ConstBitStream('0x23ef55302')
            >>> s.read('hex:12')
            '0x23e'
            >>> s.read('bin:4')
            '0b1111'
            >>> s.read('uint:5')
            10
            >>> s.read('bits:4')
            ConstBitStream('0xa')

        The :meth:`~ConstBitStream.read` method is useful for reading exponential-Golomb codes. ::

            >>> s = ConstBitStream('se=-9, ue=4')
            >>> s.read('se')
            -9
            >>> s.read('ue')
            4

    .. method:: readlist(fmt, **kwargs)

        Reads from current bit position :attr:`pos` in the bitstring according to the *fmt* string(s)/integer(s) and returns a list of results. If not enough bits are available then all bits to the end of the bitstring will be used.

        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is advanced to after the read items.

        See the entry for :meth:`read` for information on the format strings.

        For multiple items you can separate using commas or given multiple parameters::

            >>> s = ConstBitStream('0x43fe01ff21')
            >>> s.readlist('hex:8, uint:6')
            ['0x43', 63]
            >>> s.readlist(['bin:3', 'intle:16'])
            ['0b100', -509]
            >>> s.pos = 0
            >>> s.readlist('hex:b, uint:d', b=8, d=6)
            ['0x43', 63]


    .. attribute:: bytepos

        Property for setting and getting the current byte position in the bitstring.
        
        When used as a getter will raise a :exc:`ByteAlignError` if the current position in not byte aligned.

    .. attribute:: pos
    .. attribute:: bitpos

        Read and write property for setting and getting the current bit position in the bitstring. Can be set to any value from ``0`` to :attr:`len`.

        The :attr:`pos` and :attr:`bitpos` properties are exactly equivalent - you can use whichever you prefer. ::

            if s.pos < 100:
                s.pos += 10 

