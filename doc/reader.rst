.. currentmodule:: bitstring

Reader
======

.. class:: Reader(bits: Bits | BitArray, pos: int = 0)

    Wraps a :class:`Bits` or :class:`BitArray` object with a bit position for
    sequential reading.

    The wrapped bitstring is exposed directly as :attr:`bits`. If it is a
    :class:`BitArray` then it can be mutated through the reader, for example
    ``r.bits.append('0xff')``. Mutating the wrapped object never updates
    :attr:`pos` automatically.

Reading and peeking
-------------------

The :meth:`Reader.read` and :meth:`Reader.read_list` methods interpret bits starting at
:attr:`Reader.pos` and advance the position. The matching :meth:`Reader.peek` and
:meth:`Reader.peek_list` methods return the same values without changing the position.

For example::

    >>> r = Reader(Bits('0x160120f'))
    >>> r.read(12).hex
    '160'
    >>> r.pos = 0
    >>> r.read('u12')
    352
    >>> r.read_list('u12, bin3')
    [288, '111']

If a read fails then :attr:`Reader.pos` is restored to its value before the read.

The position is deliberately lax: assigning to :attr:`Reader.pos`, :attr:`Reader.bitpos` or
:attr:`Reader.bytepos` stores the integer value without checking it against the wrapped
bitstring length. Reading methods will raise an error if the position is not
usable when they need it.

Methods
-------

.. method:: Reader.read(fmt: str | int | Dtype) -> int | float | str | Bits | bool | bytes | None

    Reads from :attr:`Reader.pos` according to *fmt* and advances the position.

    If *fmt* is an integer then that many bits are returned as a bitstring. If it
    is a string or :class:`Dtype` then the corresponding dtype is read.

.. method:: Reader.read_list(fmt: str | list[str | int | Dtype], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

    Reads one or more format tokens and returns a list of values.

.. method:: Reader.peek(fmt: str | int | Dtype) -> int | float | str | Bits | bool | bytes | None

    Like :meth:`Reader.read`, but leaves :attr:`Reader.pos` unchanged.

.. method:: Reader.peek_list(fmt: str | list[str | int | Dtype], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

    Like :meth:`Reader.read_list`, but leaves :attr:`Reader.pos` unchanged.

.. method:: Reader.read_to(bs: BitsType, *, bytealigned: bool | None = None) -> Bits

    Reads up to and including the next occurrence of *bs*.

.. method:: Reader.byte_align() -> int

    Aligns :attr:`Reader.pos` to the next byte boundary and returns the number of bits
    skipped.

.. method:: Reader.find(bs: BitsType, *, start: int | None = None, end: int | None = None, bytealigned: bool | None = None) -> int | None

    Searches the wrapped bitstring and sets :attr:`Reader.pos` to the match position if
    *bs* is found. Returns the match position, or ``None`` if not found.

.. method:: Reader.rfind(bs: BitsType, *, start: int | None = None, end: int | None = None, bytealigned: bool | None = None) -> int | None

    Searches backwards and sets :attr:`Reader.pos` to the match position if *bs* is
    found. Returns the match position, or ``None`` if not found.

.. method:: Reader.__len__() -> int

    ``len(r)`` returns the length in bits of the wrapped bitstring.

Properties
----------

.. attribute:: Reader.bits
    :type: Bits | BitArray

    The wrapped bitstring object. This is the original object, not a copy.

.. attribute:: Reader.pos
    :type: int
.. attribute:: Reader.bitpos
    :type: int

    The current bit position. These aliases store any integer value.

.. attribute:: Reader.bytepos
    :type: int

    The current byte position. Reading this property requires :attr:`Reader.pos` to be
    byte aligned and raises :exc:`ByteAlignError` otherwise.
