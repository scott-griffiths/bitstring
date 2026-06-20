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

The :meth:`read` and :meth:`readlist` methods interpret bits starting at
:attr:`pos` and advance the position. The matching :meth:`peek` and
:meth:`peeklist` methods return the same values without changing the position.

For example::

    >>> r = Reader(Bits('0x160120f'))
    >>> r.read(12).hex
    '160'
    >>> r.pos = 0
    >>> r.read('uint12')
    352
    >>> r.readlist('uint12, bin3')
    [288, '111']

If a read fails then :attr:`pos` is restored to its value before the read.

The position is deliberately lax: assigning to :attr:`pos`, :attr:`bitpos` or
:attr:`bytepos` stores the integer value without checking it against the wrapped
bitstring length. Reading methods will raise an error if the position is not
usable when they need it.

Methods
-------

.. method:: Reader.read(fmt: str | int | Dtype) -> int | float | str | Bits | bool | bytes | None

    Reads from :attr:`pos` according to *fmt* and advances the position.

    If *fmt* is an integer then that many bits are returned as a bitstring. If it
    is a string or :class:`Dtype` then the corresponding dtype is read.

.. method:: Reader.readlist(fmt: str | list[str | int | Dtype], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

    Reads one or more format tokens and returns a list of values.

.. method:: Reader.peek(fmt: str | int | Dtype) -> int | float | str | Bits | bool | bytes | None

    Like :meth:`read`, but leaves :attr:`pos` unchanged.

.. method:: Reader.peeklist(fmt: str | list[str | int | Dtype], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

    Like :meth:`readlist`, but leaves :attr:`pos` unchanged.

.. method:: Reader.readto(bs: BitsType, bytealigned: bool | None = None) -> Bits

    Reads up to and including the next occurrence of *bs*.

.. method:: Reader.bytealign() -> int

    Aligns :attr:`pos` to the next byte boundary and returns the number of bits
    skipped.

.. method:: Reader.find(bs: BitsType, start: int | None = None, end: int | None = None, bytealigned: bool | None = None) -> tuple[int] | tuple[()]

    Searches the wrapped bitstring and sets :attr:`pos` to the match position if
    *bs* is found.

.. method:: Reader.rfind(bs: BitsType, start: int | None = None, end: int | None = None, bytealigned: bool | None = None) -> tuple[int] | tuple[()]

    Searches backwards and sets :attr:`pos` to the match position if *bs* is
    found.

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

    The current byte position. Reading this property requires :attr:`pos` to be
    byte aligned and raises :exc:`ByteAlignError` otherwise.
