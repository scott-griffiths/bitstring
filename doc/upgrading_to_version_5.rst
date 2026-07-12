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

bitstring 5 requires Python 3.10 or later. If your package metadata pins
bitstring and Python versions, update both together, for example::

    requires-python = ">=3.10"
    dependencies = ["bitstring>=5"]

The ``bitarray`` dependency has also been removed. The core bit storage is now
provided by the required ``tibs`` dependency. If there are problems downloading, building or
installing tibs then please file a bug report with either project.

Replace stream classes with Reader
==================================

The ``ConstBitStream`` and ``BitStream`` classes have been removed.

For immutable data, wrap a :class:`Bits` object in a :class:`Reader`::

    # bitstring 4
    s = ConstBitStream("0x160120f")
    value = s.read("uint12")

    # bitstring 5
    r = Reader(Bits("0x160120f"))
    value = r.read("u12")

For mutable data, wrap a :class:`BitArray`. The wrapped object is available as
:attr:`Reader.bits`, and it is the original object rather than a copy::

    # bitstring 4
    s = BitStream("0x001122")
    first = s.read("uint8")
    s.append("0xff")

    # bitstring 5
    r = Reader(BitArray("0x001122"))
    first = r.read("u8")
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
    r.bits.insert(inserted, r.pos)
    r.pos += len(inserted)

``Reader.pos`` is deliberately lax. Assigning to :attr:`~Reader.pos`
or :attr:`~Reader.bytepos` stores the integer value
without checking it against the current length. A later read or search will
raise an error if the position cannot be used.

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
    first = r.read("u8")

For mutation, convert the result to :class:`BitArray`::

    # bitstring 4
    s = pack("uint8", 1)
    s.append("0xff")

    # bitstring 5
    s = pack("u8", 1).to_bitarray()
    s.append("0xff")

Update find() and rfind() checks
================================

:meth:`Bits.find`, :meth:`Bits.rfind`, :meth:`Reader.find` and
:meth:`Reader.rfind` now return ``int | None``. In version 4 they returned a
single-item tuple for success and an empty tuple for failure.

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

If you used stream searching to move the current position, use
:class:`Reader`::

    # bitstring 4
    if s.find("0xff", start=s.pos):
        print(s.pos)

    # bitstring 5
    if r.find("0xff", start=r.pos) is not None:
        print(r.pos)

Use explicit construction helpers
=================================

Some constructor forms that relied on the type of the first positional
argument have been removed or should be avoided. Use the explicit factory
methods instead.

For zero-filled bitstrings, replace integer construction with
:meth:`Bits.from_zeros` or :meth:`BitArray.from_zeros`::

    # bitstring 4
    a = Bits(100)
    b = BitArray(100)

    # bitstring 5
    a = Bits.from_zeros(100)
    b = BitArray.from_zeros(100)

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

Replace bitarray compatibility
==============================

If you used the external ``bitarray`` package, convert explicitly. For exact
bit lengths, :meth:`Bits.from_bools` is the most direct replacement. For
byte-oriented data, use :meth:`Bits.from_bytes` with an explicit length::

    bits = Bits.from_bools(bitarray_obj)
    bits = Bits.from_bytes(bitarray_obj.tobytes(), length=len(bitarray_obj))

The old ``tobitarray()`` method returned an object from the external
``bitarray`` package and has been removed. :meth:`Bits.to_bitarray` returns a
bitstring :class:`BitArray` instead. If you still need an external
``bitarray`` object, create it explicitly using that package's API, for example
from the bitstring as an iterable of booleans or from :meth:`Bits.to_bytes`.

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
    value = r.read("floatle32")

    # bitstring 5
    n = len(s)
    data = s.hex
    bits = s.unpack("bin12, u8")
    value = r.read("fle32")

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

Make optional range arguments keyword-only
==========================================

Several methods now require optional range and search arguments to be named.
This makes calls harder to misread and leaves the first positional arguments
for the data being operated on.

Update calls like this::

    # bitstring 4
    s.find("0xff", 8, 64)
    s.findall("0b1", 0, 100, 3)
    s.split("0x00", 8)
    a.replace("0b0", "0b1", 4, 20)
    a.reverse(8, 24)

    # bitstring 5
    s.find("0xff", start=8, end=64)
    s.findall("0b1", start=0, end=100, count=3)
    s.split("0x00", start=8)
    a.replace("0b0", "0b1", start=4, end=20)
    a.reverse(start=8, end=24)

The affected methods are :meth:`Bits.cut`, :meth:`Bits.find`,
:meth:`Bits.findall`, :meth:`Bits.rfind`, :meth:`Bits.split`,
:meth:`BitArray.replace`, :meth:`BitArray.reverse`, :meth:`BitArray.rol` and
:meth:`BitArray.ror`.

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

Prefer the new underscored method names
=======================================

Version 5 adds underscored spellings for several older method names. The old
names remain as compatibility aliases, but new code and documentation should
use the underscored names.

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
   * - ``fromfile(f)``
     - :meth:`Array.from_file`
   * - ``readlist(fmt)``
     - :meth:`Reader.read_list`
   * - ``peeklist(fmt)``
     - :meth:`Reader.peek_list`
   * - ``readto(bs)``
     - :meth:`Reader.read_to`
   * - ``bytealign()``
     - :meth:`Reader.byte_align`

Remove command-line usage
=========================

The ``python -m bitstring`` command-line interface has been removed. Use a
small Python script or shell one-liner for any remaining uses.

Suggested upgrade order
=======================

For a large codebase, the least surprising order is:

1. Update imports to remove ``ConstBitStream`` and ``BitStream``.
2. Introduce :class:`Reader` wherever code uses ``pos``, ``read``, ``peek`` or
   stream-style searching.
3. Update :func:`pack` call sites that relied on the old ``BitStream`` return
   value.
4. Change ``find`` and ``rfind`` checks to use ``is not None``, and add
   keywords to optional range and search arguments.
5. Replace ``bytes=``, ``filename=`` and other removed constructor forms with
   explicit factory methods.
6. Replace direct ``bitarray`` compatibility with explicit conversion.
7. Replace removed aliases, prefer current dtype names, and rename
   ``Dtype.build`` / ``Dtype.parse``.
8. Replace removed global options and modes with explicit dtypes or per-call
   arguments.
9. Remove any remaining ``python -m bitstring`` usage.
10. Optionally update compatibility aliases such as ``tobytes`` and
    ``readlist`` to their preferred underscored names.
