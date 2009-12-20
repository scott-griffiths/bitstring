*********
Reference
*********

BitString and Bits
==================

.. class:: BitString
.. class:: Bits

The bitstring module provides just two classes, ``BitString`` and ``Bits``. These share many methods as ``Bits`` is the base class for ``BitString``. The distinction between them is that ``Bits`` represents an immutable sequence of bits whereas ``BitString`` objects support many methods that mutate their contents.

If you need to change the contents of a bitstring then you must use the ``BitString`` class. If you need to use bitstrings as keys in a dictionary or members of a set then you must use the ``Bits`` class (``Bits`` are hashable).

The public methods, special methods and properties of both classes are detailed in this section.

Note that in places where a bitstring can be used as a parameter, any other valid input to the ``auto`` initialiser can also be used. This means that the parameter can also be a format string which consists of tokens:

* Starting with ``hex=``, or simply starting with ``0x`` implies hexadecimal. e.g. ``0x013ff``, ``hex=013ff``

* Starting with ``oct=``, or simply starting with ``0o`` implies octal. e.g. ``0o755``, ``oct=755``

* Starting with ``bin=``, or simply starting with ``0b`` implies binary. e.g. ``0b0011010``, ``bin=0011010``

* Starting with ``int:`` or ``uint:`` followed by a length in bits and ``=`` gives base-2 integers. e.g. ``uint:8=255``, ``int:4=-7``

* To get big, little and native-endian whole-byte integers append ``be``, ``le`` or ``ne`` respectively to the ``uint`` or ``int`` identifier. e.g. ``uintle:32=1``, ``intne:16=-23``

* For floating point numbers use ``float:`` followed by the length in bits and ``=`` and the number. The default is big-endian, but you can also append ``be``, ``le`` or ``ne`` as with integers. e.g. ``float:64=0.2``, ``floatle:32=-0.3e12``

* Starting with ``ue=`` or ``se=`` implies an exponential-Golomb coded integer. e.g. ``ue=12``, ``se=-4``

Multiples tokens can be joined by separating them with commas, so for example ``se=4, 0b1, se=-1`` represents the concatenation of three elements.

The ``auto`` parameter also accepts a list or tuple, whose elements will be evaluated as booleans (imagine calling ``bool()`` on each item) and the bits set to ``1`` for ``True`` items and ``0`` for ``False`` items.

Finally if you pass in a file object, presumably opened in read-binary mode, then the bitstring will be formed from the contents of the file.

For the :func:`read`, :func:`unpack`, :func:`pack` and :func:`peek` functions you can use compact format strings similar to those used in the ``struct`` and ``array`` modules. These start with an endian identifier: ``>`` for big-endian, ``<`` for little-endian or ``@`` for native-endian. This must be followed by at least one of these codes:

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

Class properties
----------------

Bitstring objects use a wide range of properties for getting and setting different interpretations on the binary data, as well as accessing bit lengths and positions.

The different interpretations such as ``bin``, ``hex``, ``uint`` etc. are not stored as part of the object, but are calculated as needed.

.. attribute:: bin

``s.bin``

Read and write property for setting and getting the representation of the ``BitString`` as a binary string starting with ``0b``.

When used as a getter, the returned value is always calculated - the value is never cached. When used as a setter the length of the ``BitString`` will be adjusted to fit its new contents. ::

 if s.bin == '0b001':
     s.bin = '0b1111'
 # Equivalent to s.append('0b1')
 s.bin += '1'

.. attribute:: bytepos

``s.bytepos``

Read and write property for setting and getting the current byte position in the ``BitString``.
When used as a getter will raise a ``BitStringError`` if the current position in not byte aligned.

.. attribute:: bytes

``s.bytes``

Read and write property for setting and getting the underlying byte data that contains the ``BitString``.

Set using an ordinary Python string - the length will be adjusted to contain the data.

When used as a getter the ``BitString`` must be a whole number of byte long or a ``ValueError`` will be raised.

An alternative is to use the :func:`tobytes()` method, which will pad with between zero and seven ``0`` bits to make it byte aligned if needed. ::

 >>> s = BitString(bytes='\x12\xff\x30')
 >>> s.bytes
 '\x12\xff0'
 >>> s.hex = '0x12345678'
 >>> s.bytes
 '\x124Vx'

.. attribute:: hex

``s.hex``

Read and write property for setting and getting the hexadecimal representation of the ``BitString``.

When used as a getter the value will be preceded by ``0x``, which is optional when setting the value. If the ``BitString`` is not a multiple of four bits long then getting its hex value will raise a ``ValueError``. ::

 >>> s = BitString(bin='1111 0000')
 >>> s.hex
 '0xf0'
 >>> s.hex = 'abcdef'
 >>> s.hex
 '0xabcdef'

.. attribute:: int

``s.int``

Read and write property for setting and getting the signed two’s complement integer representation of the ``BitString``.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised. ::

 >>> s = BitString('0xf3')
 >>> s.int
 -13
 >>> s.int = 1232
 ValueError: int 1232 is too large for a BitString of length 8.

.. attribute:: intbe

``s.intbe``

Read and write property for setting and getting the byte-wise big-endian signed two's complement integer representation of the ``BitString``.

Only valid if ``s`` is whole-byte, in which case it is equal to ``s.int``, otherwise a ``ValueError`` is raised.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

.. attribute:: intle

``s.intle``

Read and write property for setting and getting the byte-wise little-endian signed two's complement integer representation of the ``BitString``.

Only valid if ``s`` is whole-byte, in which case it is equal to ``s[::-8].int``, i.e. the integer representation of the byte-reversed ``BitString``.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

.. attribute:: intne

``s.intne``

Read and write property for setting and getting the byte-wise native-endian signed two's complement integer representation of the ``BitString``.

Only valid if ``s`` is whole-byte, and will equal either the big-endian or the little-endian integer representation depending on the platform being used.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

.. attribute:: float
.. attribute:: floatbe

``s.float``

Read and write property for setting and getting the floating point representation of the ``BitString``.

The ``BitString`` must be either 32 or 64 bits long to support the floating point interpretations.

If the underlying floating point methods on your machine are not IEEE 754 compliant then using the float interpretations is undefined (this is unlikely unless you're on some very unusual hardware).

The ``float`` property is bit-wise big-endian, which as all floats must be whole-byte is exactly equivalent to the byte-wise big-endian ``floatbe``. 

.. attribute:: floatle

``s.floatle``

Read and write property for setting and getting the byte-wise little-endian floating point representation of the ``BitString``.

.. attribute:: floatne

``s.floatne``

Read and write property for setting and getting the byte-wise native-endian floating point representation of the ``BitString``.

.. attribute:: len
.. attribute:: length

``s.len``

Read-only properties that give the length of the ``BitString`` in bits (``len`` and ``length`` are equivalent).

This is almost equivalent to using ``len(s)``, expect that for large ``BitString`` objects ``len()`` may fail with an ``OverflowError``, whereas the ``len`` property continues to work.

.. attribute:: oct

``s.oct``

Read and write property for setting and getting the octal representation of the ``BitString``.

When used as a getter the value will be preceded by ``0o``, which is optional when setting the value. If the ``BitString`` is not a multiple of three bits long then getting its oct value will raise a ``ValueError``. ::

 >>> s = BitString('0b111101101')
 >>> s.oct
 '0o755'
 >>> s.oct = '01234567'
 >>> s.oct
 '0o01234567'

.. attribute:: pos
.. attribute:: bitpos

``s.pos``

Read and write property for setting and getting the current bit position in the ``BitString``. Can be set to any value from ``0`` to ``s.len``.

The ``pos`` and ``bitpos`` properties are exactly equivalent - you can use whichever you prefer. ::

 if s.pos < 100:
     s.pos += 10 

.. attribute:: se

``s.se``

Read and write property for setting and getting the signed exponential-Golomb code representation of the ``BitString``.

The property is set from an signed integer, and when used as a getter a ``BitStringError`` will be raised if the ``BitString`` is not a single code. ::

 >>> s = BitString(se=-40)
 >>> s.bin
 0b0000001010001
 >>> s += '0b1'
 >>> s.se
 BitStringError: BitString is not a single exponential-Golomb code.

.. attribute:: ue

``s.ue``

Read and write property for setting and getting the unsigned exponential-Golomb code representation of the ``BitString``.

The property is set from an unsigned integer, and when used as a getter a ``BitStringError`` will be raised if the ``BitString`` is not a single code.

.. attribute:: uint

``s.uint``

Read and write property for setting and getting the unsigned base-2 integer representation of the ``BitString``.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

.. attribute:: uintbe

``s.uintbe``

Read and write property for setting and getting the byte-wise big-endian unsigned base-2 integer representation of the ``BitString``.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

.. attribute:: uintle

``s.uintle``

Read and write property for setting and getting the byte-wise little-endian unsigned base-2 integer representation of the ``BitString``.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

.. attribute:: uintne

``s.uintne``

Read and write property for setting and getting the byte-wise native-endian unsigned base-2 integer representation of the ``BitString``.

When used as a setter the value must fit into the current length of the ``BitString``, else a ``ValueError`` will be raised.

Class methods
-------------

.. function:: allset

``s.allset(pos)``

Returns ``True`` if one or many bits are all set to ``1``, otherwise returns ``False``.

``pos`` can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an ``IndexError`` if ``pos < -s.len`` or ``pos > s.len``

See also :func:`allunset`.

.. function:: allunset

``s.allunset(pos)``

Returns ``True`` if one or many bits are all set to ``0``, otherwise returns ``False``.

``pos`` can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an ``IndexError`` if ``pos < -s.len`` or ``pos > s.len``

See also :func:`allset`.

.. function:: anyset

``s.anyset(pos)``

Returns ``True`` if any of one or many bits are set to ``1``, otherwise returns ``False``.

``pos`` can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an ``IndexError`` if ``pos < -s.len`` or ``pos > s.len``

See also :func:`anyunset`.

.. function:: anyunset

``s.anyunset(pos)``

Returns ``True`` if any of one or many bits are set to ``0``, otherwise returns ``False``.

``pos`` can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise an ``IndexError`` if ``pos < -s.len`` or ``pos > s.len``

See also :func:`anyset`.

.. function:: append

``s.append(bs)``

``BitString`` only.

Join a ``BitString`` to the end of the current ``BitString``. ::

 >>> s = BitString('0xbad')
 >>> s.append('0xf00d')
 >>> s
 BitString('0xbadf00d')

.. function:: bytealign

``s.bytealign()``

Aligns to the start of the next byte (so that ``s.pos`` is a multiple of 8) and returns the number of bits skipped.

If the current position is already byte aligned then it is unchanged. ::

 >>> s = BitString('0xabcdef')
 >>> s.advancebits(3)
 >>> s.bytealign()
 5
 >>> s.pos
 8

.. function:: cut

``s.cut(bits, start=None, end=None, count=None)``

Returns a generator for slices of the bitstring of length ``bits``.

At most ``count`` items are returned and the range is given by the slice ``[start:end]``, which defaults to the whole bitstring. ::

 >>> s = BitString('0x1234')
 >>> for nibble in s.cut(4):
 ...     s.prepend(nibble)
 >>> print(s)
 0x43211234

.. function:: delete

``s.delete(bits, pos=None)``

``BitString`` only.

Removes ``bits`` bits from the ``BitString`` at position ``pos``. 

If ``pos`` is not specified then the current position is used. Is equivalent to ``del s[pos:pos+bits]``. ::

 >>> s = BitString('0b1111001')
 >>> s.delete(2, 4)
 >>> print(s)
 0b11111

.. function:: endswith

``s.endswith(bs, start=None, end=None)``

Returns ``True`` if the bitstring ends with the sub-string ``bs``, otherwise returns ``False``.

A slice can be given using the ``start`` and ``end`` bit positions and defaults to the whole bitstring. ::

 >>> s = BitString('0x35e22')
 >>> s.endswith('0b10, 0x22')
 True
 >>> s.endswith('0x22', start=13)
 False

.. function:: find

``s.find(bs, start=None, end=None, bytealigned=False)``

Searches for ``bs`` in the current bitstring and sets ``pos`` to the start of ``bs`` and returns ``True`` if found, otherwise it returns ``False``.

If ``bytealigned`` is ``True`` then it will look for ``bs`` only at byte aligned positions (which is generally much faster than searching for it in every possible bit position). ``start`` and ``end`` give the search range and default to the whole bitstring. ::

 >>> s = BitString('0x0023122')
 >>> s.find('0b000100', bytealigned=True)
 True
 >>> s.pos
 16

.. function:: findall

``s.findall(bs, start=None, end=None, count=None, bytealigned=False)``

Searches for all occurrences of ``bs`` (even overlapping ones) and returns a generator of their bit positions.

If ``bytealigned`` is ``True`` then ``bs`` will only be looked for at byte aligned positions. ``start`` and ``end`` optionally define a search range and default to the whole bitstring.

The ``count`` paramater limits the number of items that will be found - the default is to find all occurences. ::

 >>> s = BitString('0xab220101')*5
 >>> list(s.findall('0x22', 
          bytealigned=True))
 [8, 40, 72, 104, 136]

.. function:: insert

``s.insert(bs, pos=None)``

``BitString`` only.

Inserts ``bs`` at ``pos``. After insertion ``pos`` will be immediately after the inserted bitstring.

The default for ``pos`` is the current position. ::

 >>> s = BitString('0xccee')
 >>> s.insert('0xd', 8)
 >>> s
 BitString('0xccdee')
 >>> s.insert('0x00')
 >>> s
 BitString('0xccd00ee')

.. function:: join

``s.join(bsl)``

Returns the concatenation of the BitString objects in the list ``bsl`` joined with ``s`` as a separator. ::

 >>> s = BitString().join(['0x0001ee', 'uint:24=13', '0b0111'])
 >>> print(s)
 0x0001ee00000d7
 
 >>> s = BitString('0b1').join(['0b0']*5)
 >>> print(s.bin)
 0b010101010

.. function:: overwrite

``s.overwrite(bs, pos=None)``

``BitString`` only.

Replaces the contents of the current ``BitString`` with ``bs`` at ``pos``. After overwriting ``pos`` will be immediately after the overwritten section.

The default for ``pos`` is the current position. ::

 >>> s = BitString(length=10)
 >>> s.overwrite('0b111', 3)
 >>> s
 BitString('0b0001110000')
 >>> s.pos
 6

.. function:: peek

``s.peek(format)``

Reads from the current bit position ``pos`` in the bitstring according the the format string and returns a new bitstring.

The bit position is unchanged after calling ``peek``.

For information on the format string see the entry for the :func:`read` function.

.. function:: peeklist

``s.peeklist(*format)``

Reads from current bit position pos in the bitstring according to the ``format`` string and returns a list of bitstring objects.

The position is not advanced to after the read items.

See the entries for :func:`read` and :func:`readlist` for more information.

.. function:: peekbit

``s.peekbit()``

Returns the next bit in the current bitstring as a new bitstring but does not advance the position. 

.. function:: peekbits

``s.peekbits(bits)``

Returns the next ``bits`` bits of the current bitstring as a new bitstring but does not advance the position. ::

 >>> s = BitString('0xf01')
 >>> s.pos = 4
 >>> s.peekbits(4)
 BitString('0x0')
 >>> s.peekbits(8)
 BitString('0x01')

.. function:: peekbitlist

``s.peekbitlist(*bits)``

Reads multiple bits from the current position and returns a list of bitstring objects, but does not advance the position. ::

 >>> s = BitString('0xf01')
 >>> for bs in s.peekbits(2, 2, 8):
 ...     print(bs)
 0b11
 0b11
 0x01
 >>> s.pos
 0 

.. function:: peekbyte

``s.peekbyte()``

Returns the next byte of the current bitstring as a new bitstring but does not advance the position. 

.. function:: peekbytes

``s.peekbytes(*bytes)``

Returns the next ``bytes`` bytes of the current bitstring as a new bitstring but does not advance the position.

If multiple bytes are specified then a list of bitstring objects is returned.

.. function:: peekbytelist

``s.peekbytelist(*bytes)``

Reads multiple bytes from the current position and returns a list of bitstring objects, but does not advance the position. ::

 >>> s = BitString('0x34eedd')
 >>> print(s.peekbytelist(1, 2))
 [BitString('0x34'), BitString('0xeedd')]

.. function:: prepend

``s.prepend(bs)``

``BitString`` only.

Inserts ``bs`` at the beginning of the current ``BitString``. ::

 >>> s = BitString('0b0')
 >>> s.prepend('0xf')
 >>> s
 BitString('0b11110')

.. function:: read

``s.read(format)``

Reads from current bit position pos in the bitstring according the the format string and returns a single bitstring. If not enough bits are available then all bits to the end of the bitstring will be used.

``format`` is a token string that describe how to interpret the next bits in the bitstring. The tokens are:

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

 >>> s = BitString('0x23ef55302')
 >>> s.read('hex12')
 '0x23e'
 >>> s.read('bin:4')
 '0b1111'
 >>> s.read('uint:5')
 10
 >>> s.read('bits:4')
 BitString('0xa')

The ``read`` function is useful for reading exponential-Golomb codes, which can't be read easily by ``readbits`` as their lengths aren't know beforehand. ::

 >>> s = BitString('se=-9, ue=4')
 >>> s.read('se')
 -9
 >>> s.read('ue')
 4

.. function:: readlist

``s.readlist(*format)``

Reads from current bit position ``pos`` in the bitstring according to the ``format`` string(s) and returns a list of bitstring objects. If not enough bits are available then all bits to the end of the bitstring will be used.

The position is advanced to after the read items.

See the entry for :func:`read` for information on the format strings.

For multiple items you can separate using commas or given multiple parameters::

 >>> s = BitString('0x43fe01ff21')
 >>> s.readlist('hex:8, uint:6')
 ['0x43', 63]
 >>> s.readlist('bin:3', 'intle:16')
 ['0b100', -509]

.. function:: readbit

``s.readbit()``

Returns the next bit of the current bitstring as a new bitstring and advances the position. 

.. function:: readbits

``s.readbits(bits)``

Returns the next ``bits`` bits of the current bitstring as a new bitstring and advances the position. ::

 >>> s = BitString('0x0001e2')
 >>> s.readbits(16)
 BitString('0x0001')
 >>> s.readbits(3).bin
 '0b111'

.. function:: readbitlist

``s.readbitlist(*bits)``

Reads multiple bits from the current bitstring and returns a list of bitstring objects.
The position is advanced to after the read items. ::

 >>> s = BitString('0x0001e2')
 >>> s.readbitlist(16, 3)
 [BitString('0x0001'), BitString('0b111')]
 >>> s.readbitlist(1)
 [BitString('0b0')]

.. function:: readbyte

``s.readbyte()``

Returns the next byte of the current bitstring as a new bitstring and advances the position. 

.. function:: readbytes

``s.readbytes(bytes)``

Returns the next ``bytes`` bytes of the current bitstring as a new bitstring and advances the position.

.. function:: readbytelist

``s.readbytelist(*bytes)``

Reads multiple bytes from the current bitstring and returns a list of bitstring objects.

The position is advanced to after the read items.

.. function:: replace

``s.replace(old, new, start=None, end=None, count=None, bytealigned=False)``

Finds occurrences of ``old`` and replaces them with ``new``. Returns the number of replacements made.

If ``bytealigned`` is ``True`` then replacements will only be made on byte boundaries. ``start`` and ``end`` give the search range and default to ``0`` and ``s.length`` respectively. If ``count`` is specified then no more than this many replacements will be made. ::

 >>> s = BitString('0b0011001')
 >>> s.replace('0b1', '0xf')
 3
 >>> print(s.bin)
 0b0011111111001111
 >>> s.replace('0b1', '', count=6)
 6
 >>> print(s.bin)
 0b0011001111

.. function:: reverse

``s.reverse(start=None, end=None)``

``BitString`` only.

Reverses bits in the ``BitString`` in-place.

``start`` and ``end`` give the range and default to ``0`` and ``s.length`` respectively. ::

 >>> a = BitString('0b10111')
 >>> a.reversebits()
 >>> a.bin
 '0b11101'

.. function:: reversebytes

``s.reversebytes(start=None, end=None)``

``BitString`` only.

Reverses bytes in the ``BitString`` in-place.

``start`` and ``end`` give the range and default to ``0`` and ``s.length`` respectively. Note that ``start`` and ``end`` are specified in bits so if ``end - start`` is not a multiple of 8 then a ``BitStringError`` is raised.

Can be used to change the endianness of the ``BitString``. ::

 >>> s = BitString('uintle:32=1234')
 >>> s.reversebytes()
 >>> print(s.uintbe)
 1234

.. function:: rfind

``s.rfind(bs, start=None, end=None, bytealigned=False)``

Searches backwards for ``bs`` in the current bitstring and returns ``True`` if found, otherwise returns ``False``.

If ``bytealigned`` is ``True`` then it will look for ``bs`` only at byte aligned positions. ``start`` and ``end`` give the search range and default to ``0`` and ``s.length`` respectively.

Note that as it's a reverse search it will start at ``end`` and finish at ``start``. ::

 >>> s = BitString('0o031544')
 >>> s.rfind('0b100')
 True
 >>> s.pos
 15
 >>> s.rfind('0b100', end=17)
 True
 >>> s.pos
 12

.. function:: rol

``s.rol(bits)``

``BitString`` only.

Rotates the contents of the ``BitString`` in-place by ``bits`` bits to the left.

Raises ``ValueError`` if ``bits < 0``. ::

 >>> s = BitString('0b01000001')
 >>> s.rol(2)
 >>> s.bin
 '0b00000101'

.. function:: ror

``s.ror(bits)``

``BitString`` only.

Rotates the contents of the ``BitString`` in-place by ``bits`` bits to the right.

Raises ``ValueError`` if ``bits < 0``.

.. function:: set

``s.set(pos)``

Sets one or many bits to ``1``. ``pos`` can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise ``IndexError`` if ``pos < -s.len`` or ``pos > s.len``.

Using ``s.set(x)`` is considerably more efficent than other equivalent methods such as ``s[x] = 1``, ``s[x] = "0b1"`` or ``s.overwrite('0b1', x)``.

See also :func:`unset`. ::

 >>> s = BitString('0x0000')
 >>> s.set(-1)
 >>> print(s)
 0x0001
 >>> s.set((0, 4, 5, 7, 9))
 >>> s.bin
 '0b1000110101000001'

.. function:: split

``s.split(delimiter, start=None, end=None, count=None, bytealigned=False)``

Splits ``s`` into sections that start with ``delimiter``. Returns a generator for bitstring objects.

The first item generated is always the bits before the first occurrence of delimiter (even if empty). A slice can be optionally specified with ``start`` and ``end``, while ``count`` specifies the maximum number of items generated.

If ``bytealigned`` is ``True`` then the delimiter will only be found if it starts at a byte aligned position. ::

 >>> s = BitString('0x42423')
 >>> [bs.bin for bs in s.split('0x4')]
 ['', '0b01000', '0b01001000', '0b0100011']

.. function:: startswith

``s.startswith(bs, start=None, end=None)``

Returns ``True`` if the bitstring starts with the sub-string ``bs``, otherwise returns ``False``.

A slice can be given using the ``start`` and ``end`` bit positions and defaults to the whole bitstring.

.. function:: tobytes

``s.tobytes()``

Returns the bitstring as a ``bytes`` object (equivalent to a ``str`` in Python 2.6).

The returned value will be padded at the end with between zero and seven ``0`` bits to make it byte aligned.

The ``tobytes`` function can also be used to output your bitstring to a file - just open a file in binary write mode and write the function's output. ::

 >>> s.bytes = 'hello'
 >>> s += '0b01'
 >>> s.tobytes()
 'hello@'

.. function:: tofile

``s.tofile(f)``

Writes the bitstring to the file object ``f``.

The data written will be padded at the end with between zero and seven ``0`` bits to make it byte aligned. ::

 >>> f = open('newfile', 'wb')
 >>> BitString('0x1234').tofile(f)

.. function:: truncateend

``s.truncateend(bits)``

``BitString`` only.

Remove the last ``bits`` bits from the end of the ``BitString``.

A ``ValueError`` is raised if you try to truncate a negative number of bits, or more bits than the ``BitString`` contains. ::

 >>> s = BitString('0xabcdef')
 >>> s.truncateend(12)
 >>> s
 BitString('0xabc')

.. function:: truncatestart

``s.truncatestart(bits)``

``BitString`` only.

Remove the first ``bits`` bits from the start of the ``BitString``.

A ``ValueError`` is raised if you try to truncate a negative number of bits, or more bits than the ``BitString`` contains. ::

 >>> s = BitString('0xabcdef')
 >>> s.truncatestart(12)
 >>> s
 BitString('0xdef')

.. function:: unpack

``s.unpack(*format)``

Interprets the whole bitstring according to the ``format`` string(s) and returns a list of bitstring objects.

``format`` is one or more strings with comma separated tokens that describe how to interpret the next bits in the bitstring. See the entry for :func:`read` for details. ::

 >>> s = BitString('int:4=-1, 0b1110')
 >>> i, b = s.unpack('int:4, bin')

If a token doesn't supply a length (as with ``bin`` above) then it will try to consume the rest of the bitstring. Only one such token is allowed.

.. function:: unset

``s.unset(pos)``

Sets one or many bits to ``0``. ``pos`` can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise ``IndexError`` if ``pos < -s.len`` or ``pos > s.len``.

Using ``s.unset(x)`` is considerably more efficent than other equivalent methods such as ``s[x] = 0``, ``s[x] = "0b0"`` or ``s.overwrite('0b0', x)``.

See also :func:`set`. ::



Class special methods
---------------------

.. function:: __add__
.. function:: __radd__

``s1 + s2``

Concatenate two bitstring objects and return the result. Either ``s1`` or ``s2`` can be 'auto' initialised. ::

 s = BitString(ue=132) + '0xff'
 s2 = '0b101' + s 

.. function:: __and__
.. function:: __rand__

``s1 & s2``

Returns the bit-wise AND between ``s1`` and ``s2``, which must have the same length otherwise a ``ValueError`` is raised. ::

 >>> print(BitString('0x33') & '0x0f')
 0x03

.. function:: __contains__

``bs in s``

Returns ``True`` if ``bs`` can be found in ``s``, otherwise returns ``False``.

Equivalent to using :func:`find`, except that ``pos`` will not be changed so you don't know where it was found. ::

 >>> '0b11' in BitString('0x06')
 True
 >>> '0b111' in BitString('0x06')
 False

.. function:: __copy__

``s2 = copy.copy(s1)``

This allows the ``copy`` module to correctly copy bitstring objects. Other equivalent methods are to initialise a new bitstring with the old one or to take a complete slice. ::

 >>> import copy
 >>> s = BitString('0o775')
 >>> s_copy1 = copy.copy(s)
 >>> s_copy2 = BitString(s)
 >>> s_copy3 = s[:]
 >>> s == s_copy1 == s_copy2 == s_copy3
 True

.. function:: __delitem__

``del s[start:end:step]``

Deletes the slice specified.

After deletion ``pos`` will be at the deleted slice's position.

.. function:: __eq__

``s1 == s2``

Compares two bitstring objects for equality, returning ``True`` if they have the same binary representation, otherwise returning ``False``. ::

 >>> BitString('0o7777') == '0xfff'
 True
 >>> a = BitString(uint=13, length=8)
 >>> b = BitString(uint=13, length=10)
 >>> a == b
 False

.. function:: __getitem__

``s[start:end:step]``

Returns a slice of ``s``.

The usual slice behaviour applies except that the step parameter gives a multiplicative factor for ``start`` and ``end`` (i.e. the bits 'stepped over' are included in the slice). ::

 >>> s = BitString('0x0123456')
 >>> s[0:4]
 BitString('0x1')
 >>> s[0:3:8]
 BitString('0x012345')

.. function:: __iadd__

``s1 += s2``

``BitString`` only.

Append a ``BitString`` to the current ``BitString`` and return the result. ::

 >>> s = BitString(ue=423)
 >>> s += BitString(ue=12)
 >>> s.read('ue')
 423
 >>> s.read('ue')
 12

.. function:: __ilshift__

``s <<= n``

Shifts the bits in ``s`` in place to the left by ``n`` places. Returns ``self``. Bits shifted off the left hand side are lost, and replaced by ``0`` bits on the right hand side.

.. function:: __imul__

``s *= n``

Concatenates ``n`` copies of ``s`` and returns ``self``. Raises ``ValueError`` if ``n < 0``. ::

 >>> s = BitString(‘0xef’)
 >>> s *= 3
 >>> print(s)
 0xefefef

.. function:: __init__


``s = BitString(auto=None, length=None, offset=0, bytes=None, filename=None, hex=None, bin=None, oct=None, uint=None, int=None, uintbe=None, intbe=None, uintle=None, intle=None, uintne=None, intne=None, ue=None, se=None, float=None, floatbe=None, floatle=None, floatne=None)``

Creates a new bitstring. You must specify at most one of the initialisers ``auto``, ``bytes``, ``bin``, ``hex``, ``oct``, ``uint``, ``int``, ``uintbe``, ``intbe``, ``uintle``, ``intle``, ``uintne``, ``intne``, ``se``, ``ue``, ``float``, ``floatbe``, ``floatle``, ``floatne`` or ``filename``. If no initialiser is given then a zeroed bitstring of length bits is created.

The initialiser for the ``Bits`` class is precisely the same as for ``BitString``.

``offset`` is optional for most initialisers, but only really useful for ``bytes`` and ``filename``. It gives a number of bits to ignore at the start of the bitstring.

Specifying ``length`` is mandatory when using the various integer initialisers. It must be large enough that a bitstring can contain the integer in ``length`` bits. It is an error to specify ``length`` when using the ``ue`` or ``se`` initialisers. For other initialisers ``length`` can be used to truncate data from the end of the input value. ::

 >>> s1 = BitString(hex='0x934')
 >>> s2 = BitString(oct='0o4464')
 >>> s3 = BitString(bin='0b001000110100')
 >>> s4 = BitString(int=-1740, length=12)
 >>> s5 = BitString(uint=2356, length=12)
 >>> s6 = BitString(bytes='\x93@', length=12)
 >>> s1 == s2 == s3 == s4 == s5 == s6
 True

For information on the use of the ``auto`` initialiser see the introduction to this reference section. ::

 >>> s = BitString('uint:12=32, 0b110')
 >>> t = BitString('0o755, ue:12, int:3=-1') 

.. function:: __invert__

``~s``

Returns the bitstring with every bit inverted, that is all zeros replaced with ones, and all ones replaced with zeros.

If the bitstring is empty then a ``BitStringError`` will be raised. ::

 >>> s = BitString(‘0b1110010’)
 >>> print(~s)
 0b0001101
 >>> print(~s & s)
 0b0000000

.. function:: __irshift__

``s >>= n``

Shifts the bits in ``s`` in place by ``n`` places to the right and returns ``self``. The ``n`` left-most bits will become zeros. ::

 >>> s = BitString('0b110')
 >>> s >>= 2
 >>> s.bin
 '0b001'

.. function:: __len__

``len(s)``

Returns the length of the bitstring in bits if it is less than ``sys.maxsize``, otherwise raises ``OverflowError``.

It's recommended that you use the ``len`` property rather than the ``len`` function because of the function's behaviour for large bitstring objects, although calling the special function directly will always work. ::

 >>> s = BitString(filename='11GB.mkv')
 >>> s.len
 93944160032L
 >>> len(s)
 OverflowError: long int too large to convert to int
 >>> s.__len__()
 93944160032L

.. function:: __lshift__

``s << n``

Returns the bitstring with its bits shifted ``n`` places to the left. The ``n`` right-most bits will become zeros. ::

 >>> s = BitString('0xff') 
 >>> s << 4
 BitString('0xf0')

.. function:: __mul__
.. function:: __rmul__

``s * n / n * s``

Return bitstring consisting of n concatenations of s. ::

 >>> a = BitString('0x34')
 >>> b = a*5
 >>> print(b)
 0x3434343434

.. function:: __ne__

``s1 != s2``

Compares two bitstring objects for inequality, returning ``False`` if they have the same binary representation, otherwise returning ``True``. 

.. function:: __or__
.. function:: __ror__

``s1 | s2``

Returns the bit-wise OR between ``s1`` and ``s2``, which must have the same length otherwise a ``ValueError`` is raised. ::

 >>> print(BitString('0x33') | '0x0f')
 0x3f

.. function:: __repr__

``repr(s)``

A representation of the bitstring that could be used to create it (which will often not be the form used to create it). 

If the result is too long then it will be truncated with ``...`` and the length of the whole will be given. ::

 >>> BitString(‘0b11100011’)
 BitString(‘0xe3’)

.. function:: __rshift__

``s >> n``

Returns the bitstring with its bits shifted ``n`` places to the right. The ``n`` left-most bits will become zeros. ::

 >>> s = BitString(‘0xff’)
 >>> s >> 4
 BitString(‘0x0f’)

.. function:: __setitem__

``s1[start:end:step] = s2``

Replaces the slice specified with ``s2``. ::

 >>> s = BitString('0x00112233')
 >>> s[1:2:8] = '0xfff'
 >>> print(s)
 0x00fff2233
 >>> s[-12:] = '0xc'
 >>> print(s)
 0x00fff2c

.. function:: __str__

``print(s)``

Prints a representation of ``s``, trying to be as brief as possible.

If ``s`` is a multiple of 4 bits long then hex will be used, otherwise either binary or a mix of hex and binary will be used. Very long strings will be truncated with ``...``. ::

 >>> s = BitString('0b1')*7
 >>> print(s)
 0b1111111 
 >>> print(s + '0b1')
 0xff

.. function:: __xor__
.. function:: __rxor__

``s1 ^ s2``

Returns the bit-wise XOR between ``s1`` and ``s2``, which must have the same length otherwise a ``ValueError`` is raised. Either ``s1`` or ``s2`` can be a string for the ``auto`` initialiser. ::

 >>> print(BitString('0x33') ^ '0x0f')
 0x3c


Module methods
--------------

.. function:: pack

``s = bitstring.pack(format, *values, **kwargs)``

Packs the values and keyword arguments according to the ``format`` string and returns a new ``BitString``.

The format string consists of comma separated tokens of the form ``name:length=value``. See the entry for :func:`read` for more details.

The tokens can be 'literals', like ``0xef``, ``0b110``, ``uint:8=55``, etc. which just represent a set sequence of bits.

They can also have the value missing, in which case the values contained in ``*values`` will be used. ::

 >>> a = pack('bin:3, hex:4', '001', 'f')
 >>> b = pack('uint:10', 33)

A dictionary or keyword arguments can also be provided. These will replace items in the format string. ::

 >>> c = pack('int:a=b', a=10, b=20)
 >>> d = pack('int:8=a, bin=b, int:4=a', a=7, b='0b110')
 
Plain names can also be used as follows::

 >>> e = pack('a, b, b, a', a='0b11', b='0o2')
 
Tokens starting with an endianness identifier (``<``, ``>`` or ``@``) implies a struct-like compact format string. For example this packs three little-endian 16-bit integers::

 >>> f = pack('<3h', 12, 3, 108)

And of course you can combine the different methods in a single pack.

A ``ValueError`` will be raised if the ``*values`` are not all used up by the format string, and if a value provided doesn't match the length specified by a token.


Deprecated methods
------------------
These methods were all present in the 1.0 release, but have now been deprecated to simplify the API as they have trivial alternatives and offer no extra functionality.

There are no current plans to remove them, but this could happen for version 2.0 so their use is discouraged.

.. function:: advancebit

(deprecated)

``s.advancebit()``

Advances position by 1 bit.

Equivalent to ``s.pos += 1``. 

.. function:: advancebits

(deprecated)

``s.advancebits(bits)``

Advances position by ``bits`` bits.

Equivalent to ``s.pos += bits``.

.. function:: advancebyte

(deprecated)

``s.advancebyte()``

Advances position by 8 bits.

Equivalent to ``s.pos += 8``.

.. function:: advancebytes

(deprecated)

``s.advancebytes(bytes)``

Advances position by ``8*bytes`` bits.

Equivalent to ``s.pos += 8*bytes``.

.. function:: retreatbit

(deprecated)

``s.retreatbit()``

Retreats position by 1 bit.

Equivalent to ``s.pos -= 1``. 

.. function:: retreatbits

(deprecated)

``s.retreatbits(bits)``

Retreats position by ``bits`` bits.

Equivalent to ``s.pos -= bits``. 

.. function:: retreatbyte

(deprecated)

``s.retreatbyte()``

Retreats position by 8 bits.

Equivalent to ``s.pos -= 8``.

.. function:: retreatbytes

(deprecated)

``s.retreatbytes(bytes)``

Retreats position by ``bytes*8`` bits.

Equivalent to ``s.pos -= 8*bytes``.

.. function:: seek

(deprecated)

``s.seek(pos)``

Moves the current position to ``pos``.

Equivalent to ``s.pos = pos``. 

.. function:: seekbyte

(deprecated)

``s.seekbyte(bytepos)``

Moves the current position to ``bytepos``.

Equivalent to ``s.bytepos = bytepos``, or ``s.pos = bytepos*8``. 

.. function:: slice

(deprecated)

``s.slice(start, end, step)``

Returns the ``BitString`` slice ``s[start*step : end*step]``.

It's use is equivalent to using the slice notation ``s[start:end:step]``; see ``__getitem__`` for examples.

.. function:: tell

(deprecated)

``s.tell()``

Returns the current bit position.

Equivalent to using the ``pos`` property as a getter.

.. function:: tellbyte

(deprecated)

``s.tellbyte()``

Returns the current byte position.

Equivalent to using the ``bytepos`` property as a getter.

