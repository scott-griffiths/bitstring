.. currentmodule:: bitstring

.. _upgrading_to_version_5:

######################
Upgrading to version 5
######################

This guide is for code being moved from bitstring 4.4.x to bitstring 5.x.

If your project is using bitstring and performance isn't an
issue then the best course of action may be to ignore version 5 and pin your bitstring
dependency to <5.

The main change in version 5 is that bitstrings no longer store a stream
position. The bit data is represented by :class:`Bits` or :class:`BitArray`,
and sequential reading is handled by a separate :class:`Reader`.

Minimum Python version
======================

bitstring 5 requires Python 3.11 or later. If your package metadata pins
bitstring and Python versions, update both together, for example::

    requires-python = ">=3.11"
    dependencies = ["bitstring>=5"]

The ``bitarray`` dependency has also been removed. The core bit storage is now
provided by the required ``tibs`` dependency. If there are problems downloading, building or
installing tibs then please file a bug report with either project.

Replace stream classes with Reader
==================================

The ``ConstBitStream`` and ``BitStream`` classes have been removed. Bit data is
held by :class:`Bits` or :class:`BitArray`, and a :class:`Reader` supplies the
stream position::

    # bitstring 4
    s = ConstBitStream("0x160120f")
    value = s.read("uint12")

    # bitstring 5
    r = Reader(Bits("0x160120f"))
    value = r.read_value("u12")

There is no ``Reader.read``. In version 4, ``read()`` did two unrelated jobs
depending on the type of its argument; version 5 gives each its own name, so
that every reading method says what it returns::

    # bitstring 4
    header = s.read("uint12")      # an interpreted value
    payload = s.read(n)            # n bits

    # bitstring 5
    header = r.read_value("u12")
    payload = r.read_bits(n)

The version 4 names are not kept as working aliases, so every old call site
raises an error explaining its replacement rather than quietly doing something
different.

.. list-table::
   :header-rows: 1

   * - Version 4
     - Version 5
   * - ``s.read("u8")``
     - :meth:`Reader.read_value`
   * - ``s.read(n)``
     - :meth:`Reader.read_bits`
   * - ``s.readlist(fmt)``
     - :meth:`Reader.read_list`
   * - ``s.peek("u8")``, ``s.peek(n)``
     - :meth:`Reader.peek_value`, :meth:`Reader.peek_bits`
   * - ``s.peeklist(fmt)``
     - :meth:`Reader.bookmark` around :meth:`Reader.read_list`
   * - ``s.readto(bs)``
     - :meth:`Reader.read_past`
   * - ``s.bytealign()``
     - :meth:`Reader.align`
   * - ``s.find(bs, start=s.pos)``
     - :meth:`Reader.seek_to`
   * - ``s.rfind(bs)``
     - :meth:`Reader.seek_back_to`
   * - ``s.pos``, ``s.bitpos``
     - :attr:`Reader.pos`
   * - ``s.bytepos``
     - :attr:`Reader.bytepos`
   * - ``len(s) - s.pos``
     - :attr:`Reader.remaining`

.. warning::

    Version 4's ``readto()`` read up to **and including** the match, so it
    becomes :meth:`Reader.read_past`. :meth:`Reader.read_to` is a different
    method that stops **before** the match. Translating ``readto`` to the
    similarly spelled ``read_to`` will silently return short data.

Peeking is only provided for single values. Version 4's ``peeklist()`` becomes
a :meth:`Reader.bookmark` block, which restores the position afterwards and can
contain any mixture of reads and seeks::

    # bitstring 4
    kind, size = s.peeklist("uint8, uint16")

    # bitstring 5
    with r.bookmark():
        kind, size = r.read_list("u8, u16")

Version 5 also adds :meth:`Reader.read_array` for reading many items of one
dtype at once.

For mutable data, wrap a :class:`BitArray`. The wrapped object is available as
:attr:`Reader.bits`, and it is the original object rather than a copy::

    # bitstring 4
    s = BitStream("0x001122")
    first = s.read("uint8")
    s.append("0xff")

    # bitstring 5
    r = Reader(BitArray("0x001122"))
    first = r.read_value("u8")
    r.bits.append("0xff")

The reader position is independent of the wrapped bitstring. Mutating
``r.bits`` does not automatically adjust :attr:`Reader.pos`.

Operations that used the stream's current position should now pass
``r.pos`` explicitly and then update it if needed::

    # bitstring 4
    s = BitStream("0x001122")
    s.pos = 8
    s.insert("0xff")

    # bitstring 5
    r = Reader(BitArray("0x001122"), pos=8)
    inserted = Bits("0xff")
    r.bits.insert(r.pos, inserted)
    r.pos += len(inserted)

As in version 4, assigning a position outside ``0`` to ``len(r.bits)`` raises a
``ValueError``. If you are reading from a :class:`BitArray` that you are also
growing, append the new data first and then set the position.

Update pack() usage
===================

:func:`pack` now returns :class:`Bits`. In version 4 it returned ``BitStream``,
so code that immediately read from or mutated the result needs to be updated.

For reading, wrap the result in :class:`Reader`::

    # bitstring 4
    s = pack("uint8, uint8", 1, 2)
    first = s.read("uint8")

    # bitstring 5
    bits = pack("u8, u8", 1, 2)
    r = Reader(bits)
    first = r.read_value("u8")

For mutation, convert the result to :class:`BitArray`::

    # bitstring 4
    s = pack("uint8", 1)
    s.append("0xff")

    # bitstring 5
    s = pack("u8", 1).to_mutable()
    s.append("0xff")

Replace stream searching with seeks
===================================

:meth:`Bits.find` and :meth:`Bits.rfind` now return ``int | None``. In version 4
they returned a single-item tuple for success and an empty tuple for failure.

This means a match at bit position zero evaluates as ``False`` if tested
directly. Test explicitly against ``None``::

    # bitstring 4
    found = s.find("0xff")
    if found:
        pos = found[0]

    # bitstring 5
    pos = s.find("0xff")
    if pos is not None:
        ...

``Reader`` has no ``find`` or ``rfind``. Searching that moves the position is
now done by the seek methods, which return ``True`` or ``False`` and leave
:attr:`Reader.pos` untouched on a miss::

    # bitstring 4
    if s.find("0xff", start=s.pos):
        print(s.pos)

    # bitstring 5
    if r.seek_to("0xff"):
        print(r.pos)

There are two forward seeks. :meth:`Reader.seek_to` leaves the position at the
start of the match and :meth:`Reader.seek_past` leaves it just after. Prefer
``seek_past`` when looping, since ``seek_to`` on its own will find the same
match every time::

    # bitstring 4
    while s.find("0x000001", start=s.pos, bytealigned=True):
        s.pos += 24
        handle(s.read(n))

    # bitstring 5
    while r.seek_past("0x000001", bytealigned=True):
        handle(r.read_bits(n))

Note two differences from version 4's stream ``find``. It searched from the
start of the data unless given ``start=s.pos``, and so could move the position
backwards; the seek methods always search from the current position.
:meth:`Reader.seek_back_to` is the only one that searches backwards, and it
considers only matches that end at or before the current position.

The ``bytealigned`` keyword is spelled the same way here as on :meth:`Bits.find`
and the other whole-bitstring methods, and must be passed by keyword on all of
them.

To search without moving the position, use the wrapped object directly:
``r.bits.find(bs, start=r.pos)``.

Remove reliance on range checking exceptions
============================================

Methods taking ``start`` and ``end`` arguments no longer raise a
``ValueError`` for out of range values. Instead the values are clamped to the
ends of the bitstring, in the same way as slice indices and the equivalent
``str`` methods, with an ``end`` before the ``start`` giving an empty range.
This applies to ``find``, ``rfind``, ``findall``, ``cut``, ``split``,
``startswith``, ``endswith``, ``replace``, ``reverse``, ``rol``, ``ror`` and
``byteswap``::

    # bitstring 4
    s = Bits("0x0123")
    s.find("0x1", start=0, end=100)  # Raised ValueError

    # bitstring 5
    s.find("0x1", start=0, end=100)  # end is clamped to len(s), finds 4

Code that relied on catching these exceptions to detect out of range values
should check the positions against ``len(s)`` explicitly instead.

Swap insert() and overwrite() arguments
=======================================

:meth:`BitArray.insert` and :meth:`BitArray.overwrite` now take the bit
position first and the bitstring second, matching ``list.insert``,
``array.array.insert`` and :meth:`Array.insert`::

    # bitstring 4
    s.insert("0xff", 8)
    s.overwrite("0xff", 8)

    # bitstring 5
    s.insert(8, "0xff")
    s.overwrite(8, "0xff")

Calls using the old positional order raise a ``TypeError`` explaining the
change. Calls that already used keywords (``s.insert(bs=..., pos=...)``) work
unchanged.

Use explicit construction helpers
=================================

Some constructor forms that relied on the type of the first positional
argument have been removed or should be avoided. Use the explicit factory
methods instead.

For zero-filled bitstrings, replace integer construction with
:meth:`Bits.from_zeros` or :meth:`BitArray.from_zeros`. This applies to the
``length``-only keyword form as well::

    # bitstring 4
    a = Bits(100)
    b = BitArray(100)
    c = BitArray(length=100)

    # bitstring 5
    a = Bits.from_zeros(100)
    b = BitArray.from_zeros(100)
    c = BitArray.from_zeros(100)

Prefer :meth:`Bits.from_string` or :meth:`BitArray.from_string` over the old
``fromstring`` spelling. The old spelling still works as a compatibility
alias.::

    # bitstring 4
    s = Bits.fromstring("uint16=1000")
    t = BitArray.fromstring("0xff")

    # bitstring 5
    s = Bits.from_string("u16=1000")
    t = BitArray.from_string("0xff")

Lists and tuples containing only ``0``, ``1``, ``True`` and ``False`` can still
be used as the first positional argument. Use the other factory methods for
construction from values that are no longer accepted::

    # bitstring 4
    f = open("data.bin", "rb")
    b = Bits(f)
    f.close()
    c = Bits(io.BytesIO(b"\x01\x02"))
    d = Bits(array_obj)

    # bitstring 5
    with open("data.bin", "rb") as f:
        b = Bits.from_file(f)
    c = Bits.from_bytes(b"\x01\x02")
    d = Bits.from_bytes(array_obj.tobytes())

The ``bytes=`` keyword constructor and constructor-level ``offset=`` keyword
have also been removed. Use :meth:`Bits.from_bytes` or
:meth:`BitArray.from_bytes` instead::

    # bitstring 4
    s = Bits(bytes=b"\x0b\x1c\x2f", offset=4, length=12)

    # bitstring 5
    s = Bits.from_bytes(b"\x0b\x1c\x2f", offset=4, length=12)

The ``filename=`` keyword constructor has been removed. Use
:meth:`Bits.from_file` or :meth:`BitArray.from_file` instead::

    # bitstring 4
    s = Bits(filename="data.bin", offset=8, length=32)

    # bitstring 5
    s = Bits.from_file("data.bin", offset=8, length=32)

Use explicit Array construction
===============================

The :class:`Array` constructor now only accepts an iterable of values (such as
a list, another ``Array`` or an ``array.array``). The integer item count, raw
binary data and file object initialiser forms have been removed, as they were
ambiguous with iterables of values - for example ``Array('u8', b'\x01\x02')``
meant something different to ``Array('u8', [1, 2])`` even though ``bytes`` is
an iterable of integers. Use the explicit alternatives instead::

    # bitstring 4
    a = Array("u8", 100)
    b = Array("u8", b"some_bytes")
    c = Array("u8", open("data.bin", "rb"))

    # bitstring 5
    a = Array.from_zeros("u8", 100)
    b = Array.from_bytes("u8", b"some_bytes")
    c = Array.from_file("u8", "data.bin")

:meth:`Array.from_file` is now a constructor taking the dtype as its first
argument, like the other ``from_`` methods. The bitstring 4 instance method of
the same name (and its ``fromfile()`` alias) that appended items to an existing
``Array`` has been removed::

    # bitstring 4
    a = Array("u8")
    a.fromfile(f, 10)

    # bitstring 5
    a = Array.from_file("u8", f, 10)

To append file data to an existing ``Array``, extend from a newly read one,
for example ``a.extend(Array.from_file(a.dtype, f))``.

Check file object usage in from_file()
======================================

When :meth:`Bits.from_file` or :meth:`BitArray.from_file` is given a file
object it now reads from the object's current file position, where previously
the position was ignored and the whole file was used. Passing an in-memory
stream such as ``io.BytesIO`` now raises a ``TypeError`` - use
:meth:`Bits.from_bytes` for those instead. :meth:`Array.from_file` also reads
file objects from their current position.

Replace bitarray compatibility
==============================

If you used the external ``bitarray`` package, convert explicitly. For exact
bit lengths, :meth:`Bits.from_bools` is the most direct replacement. For
byte-oriented data, use :meth:`Bits.from_bytes` with an explicit length::

    bits = Bits.from_bools(bitarray_obj)
    bits = Bits.from_bytes(bitarray_obj.tobytes(), length=len(bitarray_obj))

The old ``tobitarray()`` method returned an object from the external
``bitarray`` package and has been removed. Use :meth:`Bits.to_mutable` to get a
bitstring :class:`BitArray`. If you still need an external ``bitarray`` object,
create it explicitly using that package's API, for example from the bitstring as
an iterable of booleans or from :meth:`Bits.to_bytes`.

Update names and dtype spellings
================================

Version 5 removes a few legacy aliases and makes the short dtype names the
canonical spelling.

.. list-table::
   :header-rows: 1

   * - Version 4 spelling
     - Version 5 spelling
   * - ``s.len`` or ``s.length``
     - ``len(s)``
   * - ``s.b``, ``s.o`` or ``s.h``
     - ``s.bin``, ``s.oct`` or ``s.hex``
   * - ``b12``, ``o12`` or ``h12`` format tokens
     - ``bin12``, ``oct12`` or ``hex12``
   * - ``uint``, ``int`` or ``float``
     - Prefer ``u``, ``i`` or ``f``. The long names remain compatibility
       aliases.
   * - ``uintbe``, ``uintle``, ``intbe``, ``intle`` or ``floatle``
     - Prefer ``ube``, ``ule``, ``ibe``, ``ile`` or ``fle``.
   * - Native-endian names such as ``uintne``, ``une``, ``floatne`` or ``fne``
     - Use explicit big- or little-endian spellings such as ``ube``, ``ule``,
       ``f`` or ``fle``.
   * - Struct-style native prefixes ``'='`` or ``'@'``
     - Use ``'>'`` or ``'<'``.

The short numeric names ``u``, ``i`` and ``f`` remain valid. The plain ``f``
dtype is already big-endian, so both ``fbe`` and ``floatbe`` are compatibility
aliases for ``f``.

:class:`Dtype` stringification, :class:`Array` representations and
pretty-print headers use the preferred names::

    # bitstring 4
    n = s.length
    data = s.h
    bits = s.unpack("b12, uint8")
    value = s.read("floatle32")

    # bitstring 5
    n = len(s)
    data = s.hex
    bits = s.unpack("bin12, u8")
    value = r.read_value("fle32")

``Dtype.build`` and ``Dtype.parse`` have been renamed to
:meth:`Dtype.pack` and :meth:`Dtype.unpack`::

    # bitstring 4
    d = Dtype("uint8")
    bits = d.build(42)
    value = d.parse(bits)

    # bitstring 5
    d = Dtype("u8")
    bits = d.pack(42)
    value = d.unpack(bits)

Replace global options and modes
================================

The ``bitstring.options`` object and the old module-level option aliases have
been removed. Version 5 uses explicit dtype names, per-call arguments and the
``NO_COLOR`` environment variable instead of mutable process-wide state.

.. list-table::
   :header-rows: 1

   * - Version 4 setting
     - Version 5 replacement
   * - ``bitstring.options.lsb0 = True``
     - Removed. Indexing is always MSB0.
   * - ``bitstring.options.mxfp_overflow = "overflow"``
     - Use an explicit MXFP dtype suffix such as ``e4m3mxfp_overflow``.
   * - ``bitstring.bytealigned = True`` or ``bitstring.options.bytealigned = True``
     - Pass ``bytealigned=True`` to the operation that needs byte-aligned
       matching.
   * - ``bitstring.options.no_color = True``
     - Set ``NO_COLOR`` or pass ``color=False`` to :meth:`Bits.pp` or
       :meth:`Array.pp`.

Code that enabled LSB0 mode needs to translate positions explicitly. For a
single bit position ``i`` in a bitstring ``s``, the equivalent MSB0 position is
``len(s) - 1 - i``. Slice translations depend on the direction and bounds of
the original slice, so they should be reviewed case by case.

For MXFP packing, the overflow policy is now part of the dtype name. Use
``e4m3mxfp_saturate`` or ``e5m2mxfp_saturate`` for saturating behaviour, and
``e4m3mxfp_overflow`` or ``e5m2mxfp_overflow`` for overflow behaviour. The old
unsuffixed ``e4m3mxfp`` and ``e5m2mxfp`` names have been removed.

::

    # bitstring 4
    bitstring.options.mxfp_overflow = "overflow"
    bits = Bits(e4m3mxfp=1e10)
    bitstring.bytealigned = True
    pos = bits.find("0xff")
    bitstring.options.no_color = True
    bits.pp()

    # bitstring 5
    bits = Bits(e4m3mxfp_overflow=1e10)
    pos = bits.find("0xff", bytealigned=True)
    bits.pp(color=False)

Apply MX scale factors yourself
===============================

The :class:`Dtype` scale factor has been removed. The ``scale=`` parameter, the
``scale='auto'`` option and the ``Dtype.scale`` property have all gone, and
passing ``scale=`` now raises a ``TypeError``.

An :class:`Array` stores just the elements, so apply the scale in your own code.
When reading, widen the dtype as you multiply - multiplying a narrow ``Array``
in place would round every value straight back into the narrow format::

    # bitstring 4
    a = Array(Dtype('e2m1mxfp', scale=2**10), values)
    scaled_values = a.tolist()

    # bitstring 5
    a = Array('e2m1mxfp', [v / 2**10 for v in values])
    scaled_values = Array('f64', [x * 2**10 for x in a]).to_list()

For ``scale='auto'``, the scale that version 4 calculated was the one lining the
largest absolute value up with the largest value the format can represent::

    largest = Bits('0b0111').e2m1mxfp  # 6.0, the largest e2m1mxfp value
    scale = 2 ** (math.floor(math.log2(max(abs(v) for v in values)))
                  - math.floor(math.log2(largest)))

Version 4 clamped this to the powers of two from 2\ :sup:`-127` to 2\ :sup:`127`
that the E8M0 format can hold, and used a scale of 1 when every value was zero.

A single multiplier over a whole ``Array`` isn't how the MX formats work - their
scales are per-block and stored in the data alongside the elements - so a
replacement is planned as block-scaled dtypes once the ``tibs`` core supports
them.

Prefer the new underscored method names
=======================================

Version 5 adds underscored spellings for several older method names. New code and
documentation should use the underscored names, but the old spellings are kept as
compatibility aliases and there is no need to change working code. They are not
deprecated and no ``DeprecationWarning`` is emitted for them.

.. list-table::
   :header-rows: 1

   * - Version 4 spelling
     - Preferred version 5 spelling
   * - ``tobytes()``
     - :meth:`Bits.to_bytes`
   * - ``tofile(f)``
     - :meth:`Bits.to_file`
   * - ``tolist()``
     - :meth:`Array.to_list`

The reading methods are not in this table - :class:`Reader` keeps no
compatibility aliases, and its version 4 equivalents are listed in
`Replace stream classes with Reader`_ instead.

Remove command-line usage
=========================

The ``python -m bitstring`` command-line interface has been removed. Use a
small Python script or shell one-liner for any remaining uses.

Suggested upgrade order
=======================

For a large codebase, the least surprising order is:

1. Update imports to remove ``ConstBitStream`` and ``BitStream``.
2. Introduce :class:`Reader` wherever code uses ``pos``, ``read``, ``peek`` or
   stream-style searching, splitting each ``read`` and ``peek`` call according
   to whether it wanted an interpreted value or raw bits.
3. Update :func:`pack` call sites that relied on the old ``BitStream`` return
   value.
4. Change :meth:`Bits.find` and :meth:`Bits.rfind` checks to use ``is not
   None``, and replace stream searching with :meth:`Reader.seek_to`,
   :meth:`Reader.seek_past` or :meth:`Reader.seek_back_to`.
5. Replace ``bytes=``, ``filename=`` and other removed constructor forms with
   explicit factory methods.
6. Replace direct ``bitarray`` compatibility with explicit conversion.
7. Replace removed aliases, prefer current dtype names, and rename
   ``Dtype.build`` / ``Dtype.parse``.
8. Replace removed global options and modes with explicit dtypes or per-call
   arguments, and move any ``Dtype`` scale factors into your own code.
9. Remove any remaining ``python -m bitstring`` usage.
10. Optionally update compatibility aliases such as ``tobytes`` and ``tolist``
    to their preferred underscored names.
