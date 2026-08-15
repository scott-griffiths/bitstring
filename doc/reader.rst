.. currentmodule:: bitstring

Reader
======

.. class:: Reader(bits: Bits | BitArray, pos: int = 0)

    Wraps a :class:`Bits` or :class:`BitArray` object with a bit position for
    sequential reading. The bitstring must already be a :class:`Bits` or
    :class:`BitArray`, and *pos* must be within it.

A :class:`Reader` is a cursor over bit data. The data itself belongs to the
wrapped :class:`Bits` or :class:`BitArray`; the reader adds a current bit
position and a set of methods that read from it and move it along. ::

    >>> r = Reader(Bits('0x160120f'))
    >>> r.read_value('u12')
    352
    >>> r.pos
    12

Every method is anchored at :attr:`~Reader.pos`. None of them take an absolute
range to work on, so a reader works forwards through the data unless you move
it back yourself, either by setting the position or with
:meth:`~Reader.seek_back_to`. Whole-bitstring operations remain available
on the wrapped object, which is exposed as :attr:`Reader.bits` and is the
original object rather than a copy. If it is a :class:`BitArray` then it can be
mutated through the reader, for example ``r.bits.append('0xff')``. Mutating the
wrapped object never updates :attr:`~Reader.pos` automatically.

Reading
-------

There is no plain ``read`` method. Each reading method instead says what it
returns:

* :meth:`Reader.read_value` returns a single interpreted value.
* :meth:`Reader.read_bits` returns a :class:`Bits` of a given length.
* :meth:`Reader.read_list` returns a list of values.
* :meth:`Reader.read_array` returns an :class:`Array` of values.

::

    >>> r = Reader(Bits('0x160120f'))
    >>> r.read_bits(12).hex
    '160'
    >>> r.pos = 0
    >>> r.read_value('u12')
    352
    >>> r.read_list('u12, bin3')
    [288, '111']
    >>> r.remaining
    1

:meth:`~Reader.read_value` takes one dtype, either as a string such as ``'u12'``
or as a :class:`Dtype` object, and returns one value. A format with more than
one token in it is an error - use :meth:`~Reader.read_list` for those, which
also takes the keyword arguments that a format may need for its lengths.

Reading raw bits can be done either way. If the length is known when the code
is written then ``r.read_value('bits12')`` works, as ``bits`` is an ordinary
dtype; :meth:`~Reader.read_bits` additionally allows a length that is only
known at run time::

    n = r.read_value('u8') * 8      # a length read from the data itself
    payload = r.read_bits(n)

If there are not enough bits left for a read then a :exc:`ReadError` is raised
and :attr:`~Reader.pos` is left where it was. That is true of every method on
this class: the position moves only when the operation succeeds.

Looking ahead
-------------

Looking ahead is usually a matter of a single value - a tag, a length or a
marker that decides how the bits after it should be read.
:meth:`Reader.peek_value` and :meth:`Reader.peek_bits` do that, returning what
the matching read would have returned but leaving the position alone::

    >>> r = Reader(Bits('0x01ff'))
    >>> r.peek_value('u8')
    1
    >>> r.pos
    0

There are deliberately no peeking versions of :meth:`~Reader.read_list` and
:meth:`~Reader.read_array`. To look ahead over more than a single value, use
:meth:`Reader.bookmark`. It is a context manager that restores the position
when the block ends, whether or not an exception was raised, and any
combination of reads and seeks can be used inside it::

    >>> r = Reader(Bits('0x01ff02'))
    >>> with r.bookmark():
    ...     kind, size = r.read_list('u8, u16')
    >>> r.pos      # unchanged by the block above
    0

This is also the way to undo a read that turned out to be the wrong one, by
reading inside a bookmark and only repeating it outside once the data has been
identified.

Moving the position
-------------------

:attr:`Reader.pos` is an ordinary read/write property, so it can be set
directly or adjusted with ``+=``. Setting it outside the data raises a
``ValueError``. :attr:`Reader.bytepos` is the same position measured in
bytes, and :attr:`Reader.remaining` and :attr:`Reader.at_end` describe how much
is left::

    >>> r = Reader(Bits('0x160120f'), pos=8)
    >>> r.bytepos
    1
    >>> r.remaining
    20
    >>> r.pos += 20
    >>> r.at_end
    True

:meth:`Reader.align` moves forwards to the next multiple of a given boundary and
returns how many bits it skipped. It defaults to byte alignment, and raises a
``ValueError`` if there are not enough bits left to reach the boundary::

    >>> r = Reader(Bits.from_zeros(64), pos=3)
    >>> r.align()
    5
    >>> r.align(32)
    24
    >>> r.pos
    32

Searching
---------

Searching moves the reader to a marker in the data. Searches run forwards from
the current position, and return ``True`` or ``False`` rather than a position,
so that a match at bit zero isn't mistaken for a failure. On a failure the
position is not moved.

:meth:`Reader.seek_to` leaves the position at the start of the match, and
:meth:`Reader.seek_past` leaves it just after the match. The search starts at
the current position, so a match already under the cursor is found where it is
and nothing moves. That makes ``while r.seek_to(...)`` an infinite loop, and
``seek_past`` the one to loop on::

    >>> r = Reader(Bits('0x0000010c0000011f'))
    >>> while r.seek_past('0x000001', bytealigned=True):
    ...     print(r.read_value('u8'))
    12
    31

:meth:`Reader.read_to` and :meth:`Reader.read_past` do the same two moves but
also return the bits passed over, the difference between them being whether the
match itself is included::

    >>> r = Reader(Bits('0xaabbcc00dd'))
    >>> r.read_to('0x00', bytealigned=True).hex
    'aabbcc'
    >>> r.read_past('0x00', bytealigned=True).hex
    '00'

The two families differ in how they report a missing match. The seeks return
``False``, as not finding something is a normal outcome of looking for it. The
reads raise a :exc:`ReadError`, as with any other read that cannot be
satisfied.

:meth:`Reader.seek_back_to` is the only method that searches backwards. Only
matches that end at or before the current position are considered, so the
position always ends up further back than it started and
``while r.seek_back_to(...)`` does make progress. Like :meth:`~Reader.seek_to`
it leaves the position at the start of the match.

All five searching methods take the same optional *bytealigned* argument, to
match only on byte boundaries::

    >>> r = Reader(Bits('0x00120034'))
    >>> r.seek_to('0x0034', bytealigned=True)
    True
    >>> r.bytepos
    2

To search without moving the position, use the wrapped object directly, which
gives the full :meth:`Bits.find` interface including an explicit range::

    >>> pos = r.bits.find('0x00', start=r.pos)

Errors
------

.. list-table::
   :header-rows: 1

   * - Exception
     - Raised when
   * - :exc:`ReadError`
     - A read needs more bits than are left, or a searching read does not find
       its match.
   * - ``ValueError``
     - A position is set outside the data, :attr:`Reader.bytepos` is read
       while the position is not byte aligned, :meth:`~Reader.align` cannot
       reach its boundary before the end, or an argument does not make sense,
       such as a negative length, an empty bitstring to search for, or a
       multi-token format given to :meth:`~Reader.read_value`.
   * - ``TypeError``
     - An argument is of the wrong type for the method, such as an integer
       given to :meth:`~Reader.read_value` or a bitstring to
       :meth:`~Reader.read_bits`.

:exc:`ReadError` subclasses ``ValueError``, so ``except ValueError`` catches the
first two rows together if you don't need to distinguish them.

In every case the position is left unchanged, so a failed read can be caught
and retried differently.

----

Methods
-------

.. method:: Reader.align(boundary: int = 8, /) -> int

    Moves :attr:`Reader.pos` forwards to the next multiple of *boundary* bits
    and returns the number of bits skipped. If the position is already on a
    boundary then nothing is moved and ``0`` is returned. This covers byte
    alignment as ``align()`` and generalises to 16-bit or 32-bit boundaries for
    free.

    Raises a ``ValueError`` if *boundary* is not positive, or if aligning would
    move past the end of the data, in which case the position does not move. ::

        >>> r = Reader(Bits.from_zeros(64), pos=3)
        >>> r.align()
        5

.. method:: Reader.bookmark()

    Returns a context manager that restores :attr:`Reader.pos` to its current
    value when the block ends. The position is restored whether the block
    completes normally or raises.

    Any mixture of reads and seeks can be used inside the block, so this is the
    general way to look ahead. :meth:`Reader.peek_value` and
    :meth:`Reader.peek_bits` are shorthand for the single-value case. ::

        >>> r = Reader(Bits('0x160120f'))
        >>> with r.bookmark():
        ...     header = r.read_list('u12, u12')
        >>> r.pos
        0

.. classmethod:: Reader.from_file(source: str | Path | BinaryIO, /, *, length: int | None = None, offset: int = 0) -> Reader

    Creates a reader over the contents of a file, positioned at the start. The
    arguments are the same as for :meth:`Bits.from_file`, and the file is read
    as an immutable :class:`Bits`. ::

        >>> r = Reader.from_file('data.bin')
        >>> magic = r.read_bits(32)

.. method:: Reader.peek_bits(n: int, /) -> Bits

    As :meth:`Reader.read_bits`, but leaves :attr:`Reader.pos` unchanged.

.. method:: Reader.peek_value(dtype: str | Dtype, /) -> int | float | str | Bits | bool | bytes | None | tuple

    As :meth:`Reader.read_value`, but leaves :attr:`Reader.pos` unchanged. ::

        >>> r = Reader(Bits('0x01ff'))
        >>> r.peek_value('u8')
        1
        >>> r.pos
        0

.. method:: Reader.read_array(dtype: str | Dtype, /, n: int | None = None) -> Array

    Reads *n* items of type *dtype* and returns them as an :class:`Array`,
    advancing :attr:`Reader.pos` past them.

    If *n* is not given then as many whole items as will fit in the
    remaining bits are read. Any bits left over at the end are not read, and can
    be checked with :attr:`Reader.remaining`.

    Raises a :exc:`ReadError` if *n* is given and there are not enough bits
    for that many items, in which case the position does not move, and a
    ``ValueError`` if *n* is negative. ::

        >>> r = Reader(Bits('0x0102030405'))
        >>> r.read_array('u8', 3)
        Array('u8', [1, 2, 3])

.. method:: Reader.read_bits(n: int, /) -> Bits

    Reads *n* bits and returns them as a :class:`Bits`, advancing
    :attr:`Reader.pos` by *n*.

    Raises a :exc:`ReadError` if fewer than *n* bits remain, and a
    ``ValueError`` if *n* is negative. For a length that is fixed when the code
    is written, ``read_value('bits8')`` is equivalent to ``read_bits(8)``. ::

        >>> r = Reader(Bits('0x160120f'))
        >>> r.read_bits(12).hex
        '160'

.. method:: Reader.read_list(fmt: str | Dtype | list[str | int | Dtype], **kwargs) -> list[int | float | str | Bits | bool | bytes | None]

    Reads one or more format tokens and returns a list of values, advancing
    :attr:`Reader.pos` past all of them. ::

        >>> r = Reader(Bits('0x160120f'))
        >>> r.read_list('u12, u12, bin3')
        [352, 288, '111']

.. method:: Reader.read_past(bs: BitsType, /, bytealigned: bool = False) -> Bits

    Searches forwards for *bs* and reads up to and including it, leaving
    :attr:`Reader.pos` just after the match. A loop of ``read_past`` calls
    therefore always makes progress.

    Raises a :exc:`ReadError` if *bs* is not found, in which case the position
    does not move, and a ``ValueError`` if it is empty. Use
    :meth:`Reader.seek_past` instead if a missing match is expected. ::

        >>> r = Reader(Bits('0xaabbcc00dd'))
        >>> r.read_past('0x00', bytealigned=True).hex
        'aabbcc00'

.. method:: Reader.read_to(bs: BitsType, /, bytealigned: bool = False) -> Bits

    Searches forwards for *bs* and reads up to but not including it, leaving
    :attr:`Reader.pos` at the start of the match. The match itself is left to be
    read next.

    Raises a :exc:`ReadError` if *bs* is not found, in which case the position
    does not move, and a ``ValueError`` if it is empty. ::

        >>> r = Reader(Bits('0xaabbcc00dd'))
        >>> r.read_to('0x00', bytealigned=True).hex
        'aabbcc'

.. method:: Reader.read_value(dtype: str | Dtype, /) -> int | float | str | Bits | bool | bytes | None

    Reads one dtype from :attr:`Reader.pos` and returns its interpreted value,
    advancing the position past the bits used.

    *dtype* is given either as a string such as ``'u12'`` or as a
    :class:`Dtype`. A format containing more than one token raises a
    ``ValueError``; use :meth:`Reader.read_list` for those. A dtype with no
    length, such as ``'u'``, uses all of the remaining bits, which must be a
    whole number of items.

    Raises a :exc:`ReadError` if fewer bits remain than the dtype needs, in
    which case the position does not move.

    Variable-length dtypes such as ``'ue'`` read as many bits as the value
    needs::

        >>> r = Reader(Bits('ue=12, ue=3'))
        >>> r.read_value('ue')
        12
        >>> r.read_value('ue')
        3

.. method:: Reader.seek_back_to(bs: BitsType, /, bytealigned: bool = False) -> bool

    Searches backwards for the previous occurrence of *bs*. Only matches that
    end at or before :attr:`Reader.pos` are considered, so the position always
    ends up further back than it started and ``while r.seek_back_to(bs)`` makes
    progress. If it is found then the position is moved to the start of the
    match and ``True`` is returned, otherwise the position is left alone and
    ``False`` is returned.

    Raises a ``ValueError`` if *bs* is empty. ::

        >>> r = Reader(Bits('0x00ff00ff'), pos=32)
        >>> r.seek_back_to('0xff')
        True
        >>> r.pos
        24

.. method:: Reader.seek_past(bs: BitsType, /, bytealigned: bool = False) -> bool

    Searches forwards from :attr:`Reader.pos` for *bs*. If it is found then the
    position is moved to just after the match and ``True`` is returned,
    otherwise the position is left alone and ``False`` is returned.

    Raises a ``ValueError`` if *bs* is empty. This is the method to use for
    loops, as it always makes progress::

        >>> r = Reader(Bits('0x0000010c0000011f'))
        >>> while r.seek_past('0x000001', bytealigned=True):
        ...     print(r.read_value('u8'))
        12
        31

.. method:: Reader.seek_to(bs: BitsType, /, bytealigned: bool = False) -> bool

    Searches forwards from :attr:`Reader.pos` for *bs*. If it is found then the
    position is moved to the start of the match and ``True`` is returned,
    otherwise the position is left alone and ``False`` is returned.

    Raises a ``ValueError`` if *bs* is empty. A match already under the cursor
    is found where it is and nothing moves, so repeating this call without
    reading anything finds the same match each time - see
    :meth:`Reader.seek_past`. ::

        >>> r = Reader(Bits('0xaabbcc00dd'))
        >>> r.seek_to('0x00', bytealigned=True)
        True
        >>> r.bytepos
        3

.. method:: Reader.__len__() -> int

    ``len(r)`` returns the length in bits of the wrapped bitstring. Use
    :attr:`Reader.remaining` for the number of bits still to be read.

----

Properties
----------

.. attribute:: Reader.at_end
    :type: bool

    Read-only. ``True`` if the position is at the end of the data, so that no
    further bits can be read.

.. attribute:: Reader.bits
    :type: Bits | BitArray

    Read-only. The wrapped bitstring object. This is the original object, not a
    copy, so a :class:`BitArray` can still be modified through it. To read
    different data, create a new :class:`Reader`.

.. attribute:: Reader.bytepos
    :type: int

    The current position in bytes. Reading this property requires
    :attr:`Reader.pos` to be byte aligned and raises a ``ValueError``
    otherwise. Setting it sets :attr:`Reader.pos` to eight times the value, and
    raises a ``ValueError`` if that is outside the data.

.. attribute:: Reader.pos
    :type: int

    The current bit position. It must be between zero and the length of the
    wrapped bitstring, and setting it outside that range raises a
    ``ValueError``.

    If you are reading from a :class:`BitArray` while also growing it, append
    the new data first and then set the position.

.. attribute:: Reader.remaining
    :type: int

    Read-only. The number of bits between the current position and the end of
    the data, that is ``len(r) - r.pos``.
