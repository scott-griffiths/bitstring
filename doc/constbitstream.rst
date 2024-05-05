.. currentmodule:: bitstring

ConstBitStream
==============

.. class:: ConstBitStream(auto: BitsType | int | None, /, length: int | None = None, offset: int | None = None, pos: int = 0, **kwargs)

    The :class:`Bits` class is the base class for :class:`ConstBitStream` and so all of its methods are also available for :class:`ConstBitStream` objects. The initialiser is the same as for :class:`Bits` except that an initial bit position :attr:`pos` can be given (defaults to 0).

    A :class:`ConstBitStream` is a :class:`Bits` with added methods and properties that allow it to be parsed as a stream of bits.

----

Reading and parsing
---------------------

The :class:`BitStream` and :class:`ConstBitStream` classes contain number of methods for reading the bitstring as if it were a file or stream. Depending on how it was constructed the bitstream might actually be contained in a file rather than stored in memory, but these methods work for either case.

In order to behave like a file or stream, every bitstream has a property :attr:`~ConstBitStream.pos` which is the current position from which reads occur. :attr:`~ConstBitStream.pos` can range from zero (its default value on construction) to the length of the bitstream, a position from which all reads will fail as it is past the last bit. Note that the :attr:`~ConstBitStream.pos` property isn't considered a part of the bitstream's identity; this allows it to vary for immutable :class:`ConstBitStream` objects and means that it doesn't affect equality or hash values.

The property :attr:`~ConstBitStream.bytepos` is also available, and is useful if you are only dealing with byte data and don't want to always have to divide the bit position by eight. Note that if you try to use :attr:`~ConstBitStream.bytepos` and the bitstring isn't byte aligned (i.e. :attr:`~ConstBitStream.pos` isn't a multiple of 8) then a :exc:`ByteAlignError` exception will be raised.

Reading using format strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :meth:`~ConstBitStream.read` / :meth:`~ConstBitStream.readlist` methods can also take a format string similar to that used in the auto initialiser. Only one token should be provided to :meth:`~ConstBitStream.read` and a single value is returned. To read multiple tokens use :meth:`~ConstBitStream.readlist`, which unsurprisingly returns a list.

The format string consists of comma separated tokens that describe how to interpret the next bits in the bitstring.
The tokens are given in :ref:`format_tokens`.

For example we can read and interpret three quantities from a bitstream with::

    start_code = s.read('hex32')
    width = s.read('uint12')
    height = s.read('uint12')

and we also could have combined the three reads as::

    start_code, width, height = s.readlist('hex32, 2*uint12')

where here we are also using a multiplier to combine the format of the second and third tokens.

You are allowed to use one 'stretchy' token in a :meth:`~ConstBitStream.readlist`. This is a token without a length specified, which will stretch to fill encompass as many bits as possible. This is often useful when you just want to assign something to 'the rest' of the bitstring::

    a, b, everything_else = s.readlist('intle16, intle24, bits')

In this example the ``bits`` token will consist of everything left after the first two tokens are read, and could be empty.

It is an error to use more than one stretchy token, or to use a ``ue``, ``se``, ``uie`` or ``se`` token after a stretchy token (the reason you can't use exponential-Golomb codes after a stretchy token is that the codes can only be read forwards; that is you can't ask "if this code ends here, where did it begin?" as there could be many possible answers).

The ``pad`` token is a special case in that it just causes bits to be skipped over without anything being returned. This can be useful for example if parts of a binary format are uninteresting::

    a, b = s.readlist('pad12, uint4, pad4, uint8')

Peeking
^^^^^^^^

In addition to the read methods there are matching peek methods. These are identical to the read except that they do not advance the position in the bitstring to after the read elements. ::

    s = ConstBitStream('0x4732aa34')
    if s.peek(8) == '0x47':
        t = s.read(16)          # t is first 2 bytes '0x4732'
    else:
        s.find('0x47')


----

Methods
-------

.. method:: ConstBitStream.bytealign() -> int

   Aligns to the start of the next byte (so that :attr:`pos` is a multiple of 8) and returns the number of bits skipped.

   If the current position is already byte aligned then it is unchanged. ::

        >>> s = ConstBitStream('0xabcdef')
        >>> s.pos += 3
        >>> s.bytealign()
        5
        >>> s.pos
        8

.. method:: ConstBitStream.peek(fmt: str | int) -> int | float | str | Bits | bool | bytes | None

    Reads from the current bit position :attr:`pos` in the bitstring according to the *fmt* string or integer and returns the result.

    The bit position is unchanged.

    For information on the format string see the entry for the :meth:`read` method. ::

        >>> s = ConstBitStream('0x123456')
        >>> s.peek(16)
        ConstBitStream('0x1234')
        >>> s.peek('hex8')
        '12'

.. method:: ConstBitStream.peeklist(fmt: str | list[str | int], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

    Reads from current bit position :attr:`pos` in the bitstring according to the *fmt* string or iterable and returns a list of results.

    A dictionary or keyword arguments can also be provided. These will replace length identifiers in the format string. The position is not advanced to after the read items.

    See the entries for :meth:`read` and :meth:`readlist` for more information.

.. method:: ConstBitStream.read(fmt: str | int) -> int | float | str | Bits | bool | bytes | None

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

.. method:: ConstBitStream.readlist(fmt: str | list[str | int], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

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

.. method:: ConstBitStream.readto(bs: BitsType, bytealigned: bool | None = None) -> ConstBitStream

    Reads up to and including the next occurrence of the bitstring *bs* and returns the results. If *bytealigned* is `True` it will look for the bitstring starting only at whole-byte positions.

    Raises a :exc:`ReadError` if *bs* is not found, and :exc:`ValueError` if *bs* is empty.

        >>> s = ConstBitStream('0x47000102034704050647')
        >>> s.readto('0x47', bytealigned=True)
        ConstBitStream('0x47')
        >>> s.readto('0x47', bytealigned=True)
        ConstBitStream('0x0001020347')
        >>> s.readto('0x47', bytealigned=True)
        ConstBitStream('0x04050647')

----

Properties
----------

The ``ConstBitStream`` and ``BitStream`` classes have the concept of a current bit position.
This position will be set to zero by default on construction, and will be modified by many of the methods described above as the stream is being read.

Using :meth:`~Bits.find` or :meth:`~Bits.rfind` will move ``pos`` to the start of the substring if it is found.

Note that the ``pos`` property isn’t considered a part of the bitstring's identity; this allows it to vary for immutable ``ConstBitStream`` objects and means that it doesn't affect equality or hash values.
It also will be reset to zero if a bitstring is copied.


.. attribute:: ConstBitStream.bytepos
    :type: int

    Property for setting and getting the current byte position in the bitstring.
    The value of ``pos`` will always be ``bytepos * 8`` as the two values are not independent.

    When used as a getter will raise a :exc:`ByteAlignError` if the current position in not byte aligned.


.. attribute:: ConstBitStream.pos
    :type: int
.. attribute:: ConstBitStream.bitpos
    :type: int

    Read and write property for setting and getting the current bit position in the bitstring. Can be set to any value from ``0`` to ``len(s)``.

    The :attr:`pos` and :attr:`bitpos` properties are exactly equivalent - you can use whichever you prefer. ::

        if s.pos < 100:
            s.pos += 10


