.. currentmodule:: bitstring

ConstBitStream Class
====================

.. class:: ConstBitStream([__auto, length, offset, pos, **kwargs])

    The :class:`Bits` class is the base class for :class:`ConstBitStream` and so all of its methods are also available for :class:`ConstBitStream` objects. The initialiser is the same as for :class:`Bits` except that an initial bit position :attr:`pos` can be given (defaults to 0).

    A :class:`ConstBitStream` is a :class:`Bits` with added methods and properties that allow it to be parsed as a stream of bits.

Methods
-------

bytealign
^^^^^^^^^
    .. method:: ConstBitStream.bytealign()

       Aligns to the start of the next byte (so that :attr:`pos` is a multiple of 8) and returns the number of bits skipped.

       If the current position is already byte aligned then it is unchanged. ::

            >>> s = ConstBitStream('0xabcdef')
            >>> s.pos += 3
            >>> s.bytealign()
            5
            >>> s.pos
            8

peek
^^^^
    .. method:: ConstBitStream.peek(fmt)

        Reads from the current bit position :attr:`pos` in the bitstring according to the *fmt* string or integer and returns the result.

        The bit position is unchanged.

        For information on the format string see the entry for the :meth:`read` method. ::
        
            >>> s = ConstBitStream('0x123456')
            >>> s.peek(16)
            ConstBitStream('0x1234')
            >>> s.peek('hex8')
            '12'

peeklist
^^^^^^^^
    .. method:: ConstBitStream.peeklist(fmt, **kwargs)

        Reads from current bit position :attr:`pos` in the bitstring according to the *fmt* string or iterable and returns a list of results.

        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is not advanced to after the read items.

        See the entries for :meth:`read` and :meth:`readlist` for more information.

read
^^^^
    .. method:: ConstBitStream.read(fmt)

        Reads from current bit position :attr:`pos` in the bitstring according the format string and returns a single result. If not enough bits are available then a :exc:`ReadError` is raised.

        *fmt* is either a token string that describes how to interpret the next bits in the bitstring or an integer.
        If it's an integer then that number of bits will be read, and returned as a new bitstring.
        A full list of the tokens is given in :ref:`format_tokens`.

        For example::

            >>> s = ConstBitStream('0x23ef55302')
            >>> s.read('hex12')
            '23e'
            >>> s.read('bin4')
            '1111'
            >>> s.read('u5')
            10
            >>> s.read('bits4')
            ConstBitStream('0xa')

        The :meth:`~ConstBitStream.read` method is useful for reading exponential-Golomb codes. ::

            >>> s = ConstBitStream('se=-9, ue=4')
            >>> s.read('se')
            -9
            >>> s.read('ue')
            4

        The ``pad`` token is not very useful when used in :meth:`~ConstBitStream.read` as it just skips a number of bits and returns ``None``. However when used within :meth:`~ConstBitStream.readlist` or :meth:`~Bits.unpack` it allows unimportant part of the bitstring to be simply ignored.

readlist
^^^^^^^^
    .. method:: ConstBitStream.readlist(fmt, **kwargs)

        Reads from current bit position :attr:`pos` in the bitstring according to the *fmt* string or iterable and returns a list of results. If not enough bits are available then a :exc:`ReadError` is raised.

        A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is advanced to after the read items.

        See :ref:`format_tokens` for information on the format strings.

        For multiple items you can separate using commas or given multiple parameters::

            >>> s = ConstBitStream('0x43fe01ff21')
            >>> s.readlist('hex8, uint6')
            ['43', 63]
            >>> s.readlist(['bin3', 'intle16'])
            ['100', -509]
            >>> s.pos = 0
            >>> s.readlist('hex:b, uint:d', b=8, d=6)
            ['43', 63]

readto
^^^^^^
    .. method:: ConstBitStream.readto(bs, bytealigned)

        Reads up to and including the next occurrence of the bitstring *bs* and returns the results. If *bytealigned* is `True` it will look for the bitstring starting only at whole-byte positions.

        Raises a :exc:`ReadError` if *bs* is not found, and :exc:`ValueError` if *bs* is empty.

            >>> s = ConstBitStream('0x47000102034704050647')
            >>> s.readto('0x47', bytealigned=True)
            BitStream('0x47')
            >>> s.readto('0x47', bytealigned=True)
            BitStream('0x0001020347')
            >>> s.readto('0x47', bytealigned=True)
            BitStream('0x04050647')

Properties
----------

The ``ConstBitStream`` and ``BitStream`` classes have the concept of a current bit position.
This position will be set to zero by default on construction, and will be modified by many of the methods described above as the stream is being read.

Using :meth:`~Bits.find` or :meth:`~Bits.rfind` will move ``pos`` to the start of the substring if it is found.

Note that the ``pos`` property isn’t considered a part of the bitstring's identity; this allows it to vary for immutable ``ConstBitStream`` objects and means that it doesn’t affect equality or hash values.
It also will be reset to zero if a bitstring is copied.


bytepos
^^^^^^^
    .. attribute:: ConstBitStream.bytepos

        Property for setting and getting the current byte position in the bitstring.
        The value of ``pos`` will always be ``bytepos * 8`` as the two values are not independent.
        
        When used as a getter will raise a :exc:`ByteAlignError` if the current position in not byte aligned.

pos / bitpos
^^^^^^^^^^^^
    .. attribute:: ConstBitStream.pos
    .. attribute:: ConstBitStream.bitpos

        Read and write property for setting and getting the current bit position in the bitstring. Can be set to any value from ``0`` to ``len(s)``.

        The :attr:`pos` and :attr:`bitpos` properties are exactly equivalent - you can use whichever you prefer. ::

            if s.pos < 100:
                s.pos += 10 


