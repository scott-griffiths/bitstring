.. currentmodule:: bitstring

BitArray Class
==============

.. class:: BitArray([auto, length, offset, **kwargs])

    The :class:`Bits` class is the base class for :class:`BitArray` and so (with the exception of :meth:`~Bits.__hash__`) all of its methods are also available for :class:`BitArray` objects. The initialiser is also the same as for :class:`Bits` and so won't be repeated here.

    A :class:`BitArray` is a mutable :class:`Bits`, and so the one thing all of the methods listed here have in common is that  they can modify the contents of the bitstring.

Methods
-------

append
^^^^^^
    .. method:: BitArray.append(bs)

       Join a :class:`BitArray` to the end of the current :class:`BitArray`. ::

           >>> s = BitArray('0xbad')
           >>> s.append('0xf00d')
           >>> s
           BitArray('0xbadf00d')

byteswap
^^^^^^^^
    .. method:: BitArray.byteswap([fmt, start, end, repeat=True])
    
       Change the endianness of the :class:`BitArray` in-place according to *fmt*. Return the number of swaps done.
       
       The *fmt* can be an integer, an iterable of integers or a compact format string similar to those used in :func:`pack` (described in :ref:`compact_format`). It defaults to 0, which means reverse as many bytes as possible. The *fmt* gives a pattern of byte sizes to use to swap the endianness of the :class:`BitArray`. Note that if you use a compact format string then the endianness identifier (``<``, ``>`` or ``@``) is not needed, and if present it will be ignored.
       
       *start* and *end* optionally give a slice to apply the transformation to (it defaults to the whole :class:`BitArray`). If *repeat* is ``True`` then the byte swapping pattern given by the *fmt* is repeated in its entirety as many times as possible.
       
           >>> s = BitArray('0x00112233445566')
           >>> s.byteswap(2)
           3
           >>> s
           BitArray('0x11003322554466')
           >>> s.byteswap('h')
           3
           >>> s
           BitArray('0x00112233445566')
           >>> s.byteswap([2, 5])
           1
           >>> s
           BitArray('0x11006655443322')
        
       It can also be used to swap the endianness of the whole :class:`BitArray`. ::

           >>> s = BitArray('uintle:32=1234')
           >>> s.byteswap()
           >>> print(s.uintbe)
           1234

clear
^^^^^
    .. method:: BitArray.clear()

        Removes all bits from the bitstring.

        ``s.clear()`` is equivalent to ``del s[:]`` and simply makes the bitstring empty.

insert
^^^^^^
    .. method:: BitArray.insert(bs, pos)

        Inserts *bs* at *pos*.

        When used with the :class:`BitStream` class the *pos* is optional, and if not present the current bit position will be used. After insertion the property :attr:`~ConstBitStream.pos` will be immediately after the inserted bitstring. ::

            >>> s = BitStream('0xccee')
            >>> s.insert('0xd', 8)
            >>> s
            BitStream('0xccdee')
            >>> s.insert('0x00')
            >>> s
            BitStream('0xccd00ee')

invert
^^^^^^
    .. method:: BitArray.invert([pos])
    
        Inverts one or many bits from ``1`` to ``0`` or vice versa.
        
        *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise :exc:`IndexError` if ``pos < -len(s)`` or ``pos > len(s)``. The default is to invert the entire :class:`BitArray`. ::
        
            >>> s = BitArray('0b111001')
            >>> s.invert(0)
            >>> s.bin
            '011001'
            >>> s.invert([-2, -1])
            >>> s.bin
            '011010'
            >>> s.invert()
            >>> s.bin
            '100101'

overwrite
^^^^^^^^^
    .. method:: BitArray.overwrite(bs, pos)

        Replaces the contents of the current :class:`BitArray` with *bs* at *pos*.

        When used with the :class:`BitStream` class the *pos* is optional, and if not present the current bit position will be used. After insertion the property :attr:`~ConstBitStream.pos` will be immediately after the overwritten bitstring. ::

            >>> s = BitArray(length=10)
            >>> s.overwrite('0b111', 3)
            >>> s
            BitArray('0b0001110000')
            >>> s.pos
            6

prepend
^^^^^^^
    .. method:: BitArray.prepend(bs)

        Inserts *bs* at the beginning of the current :class:`BitArray`. ::

            >>> s = BitArray('0b0')
            >>> s.prepend('0xf')
            >>> s
            BitArray('0b11110')

replace
^^^^^^^
    .. method:: BitArray.replace(old, new[, start, end, count, bytealigned])

        Finds occurrences of *old* and replaces them with *new*. Returns the number of replacements made.

        If *bytealigned* is ``True`` then replacements will only be made on byte boundaries. *start* and *end* give the search range and default to ``0`` and :attr:`~Bits.len` respectively. If *count* is specified then no more than this many replacements will be made. ::

            >>> s = BitArray('0b0011001')
            >>> s.replace('0b1', '0xf')
            3
            >>> print(s.bin)
            0011111111001111
            >>> s.replace('0b1', '', count=6)
            6
            >>> print(s.bin)
            0011001111

reverse
^^^^^^^
    .. method:: BitArray.reverse([start, end])

        Reverses bits in the :class:`BitArray` in-place.

        *start* and *end* give the range and default to ``0`` and :attr:`~Bits.len` respectively. ::

            >>> a = BitArray('0b10111')
            >>> a.reverse()
            >>> a.bin
            '11101'

rol
^^^
    .. method:: BitArray.rol(bits[, start, end])

        Rotates the contents of the :class:`BitArray` in-place by *bits* bits to the left.

        *start* and *end* define the slice to use and default to ``0`` and :attr:`~Bits.len` respectively.
        
        Raises :exc:`ValueError` if ``bits < 0``. ::

            >>> s = BitArray('0b01000001')
            >>> s.rol(2)
            >>> s.bin
            '00000101'

ror
^^^
    .. method:: BitArray.ror(bits[, start, end])

        Rotates the contents of the :class:`BitArray` in-place by *bits* bits to the right.

        *start* and *end* define the slice to use and default to ``0`` and :attr:`~Bits.len` respectively.
        
        Raises :exc:`ValueError` if ``bits < 0``.

set
^^^
    .. method:: BitArray.set(value[, pos])

        Sets one or many bits to either ``1`` (if *value* is ``True``) or ``0`` (if *value* isn't ``True``). *pos* can be either a single bit position or an iterable of bit positions. Negative numbers are treated in the same way as slice indices and it will raise :exc:`IndexError` if ``pos < -len(s)`` or ``pos > len(s)``. The default is to set every bit in the :class:`BitArray`.

        Using ``s.set(True, x)`` can be more efficient than other equivalent methods such as ``s[x] = 1``, ``s[x] = "0b1"`` or ``s.overwrite('0b1', x)``, especially if many bits are being set. ::

            >>> s = BitArray('0x0000')
            >>> s.set(True, -1)
            >>> print(s)
            0x0001
            >>> s.set(1, (0, 4, 5, 7, 9))
            >>> s.bin
            '1000110101000001'
            >>> s.set(0)
            >>> s.bin
            '0000000000000000'

Properties
----------

Note that the ``bin``, ``oct``, ``hex``, ``int``, ``uint`` and ``float`` properties can all be shortened to their initial letter.
The short properties can also have a length in bits appended to them to make properties such as ``u8`` or ``f64``. These properties with lengths can be used to quickly create a new bitstring. ::

    >>> a = BitArray()
    >>> a.f32 = 17.6
    >>> a.h
    '418ccccd'
    >>> a.i7 = -1
    >>> a.b
    '1111111'


bin / b
^^^^^^^
    .. attribute:: BitArray.bin
       :noindex:
    .. attribute:: BitArray.b
       :noindex:

        Writable version of :attr:`Bits.bin`.

bool
^^^^
    .. attribute:: BitArray.bool
       :noindex:

       Writable version of :attr:`Bits.bool`.

bytes
^^^^^
    .. attribute:: BitArray.bytes
       :noindex:

        Writable version of :attr:`Bits.bytes`.

hex / h
^^^^^^^
    .. attribute:: BitArray.hex
       :noindex:
    .. attribute:: BitArray.h
       :noindex:

        Writable version of :attr:`Bits.hex`.

int / i
^^^^^^^
    .. attribute:: BitArray.int
       :noindex:
    .. attribute:: BitArray.i
       :noindex:

        Writable version of :attr:`Bits.int`. The ``i`` property can have a bit length appended to it such as ``i32`` or ``i5`` to specify the new length of the bitstring. Using a length too small to contain the value given will raise a :exc:`CreationError`.
                
        When used  as a setter without a new length the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised. ::

            >>> s = BitArray('0xf3')
            >>> s.int
            -13
            >>> s.int = 1232
            ValueError: int 1232 is too large for a BitArray of length 8.

intbe
^^^^^
    .. attribute:: BitArray.intbe
       :noindex:

        Writable version of :attr:`Bits.intbe`.
        
        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.        

intle
^^^^^
    .. attribute:: BitArray.intle
       :noindex:

        Writable version of :attr:`Bits.intle`.

        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.

intne
^^^^^
    .. attribute:: BitArray.intne
       :noindex:

        Writable version of :attr:`Bits.intne`.

        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.

float / floatbe / f
^^^^^^^^^^^^^^^^^^^
    .. attribute:: BitArray.float
       :noindex:
    .. attribute:: BitArray.floatbe
       :noindex:
    .. attribute:: BitArray.f
       :noindex:

        Writable version of :attr:`Bits.float`. The standard ``float``, the big-endian ``floatbe` and the shortened ``f`` are all equivalent.

        The ``f`` property can have a bit length appended to it such as ``f32`` or ``f64`` to specify the new length of the bitstring. Using a length that doesn't support any floating point types will raise a :exc:`CreationError`.

floatle
^^^^^^^
    .. attribute:: BitArray.floatle
       :noindex:

        Writable version of :attr:`Bits.floatle`.

floatne
^^^^^^^
    .. attribute:: BitArray.floatne
       :noindex:

        Writable version of :attr:`Bits.floatne`.

oct / o
^^^^^^^
    .. attribute:: BitArray.oct
       :noindex:
    .. attribute:: BitArray.o
       :noindex:

        Writable version of :attr:`Bits.oct`.

se
^^
    .. attribute:: BitArray.se
       :noindex:

        Writable version of :attr:`Bits.se`.

ue
^^
    .. attribute:: BitArray.ue
       :noindex:

        Writable version of :attr:`Bits.uie`.

sie
^^^
    .. attribute:: BitArray.sie
       :noindex:

        Writable version of :attr:`Bits.sie`.

uie
^^^
    .. attribute:: BitArray.uie
       :noindex:

        Writable version of :attr:`Bits.ue`.

uint / u
^^^^^^^^
    .. attribute:: BitArray.uint
       :noindex:
    .. attribute:: BitArray.u
       :noindex:

        Writable version of :attr:`Bits.uint`.

        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.

uintbe
^^^^^^
    .. attribute:: BitArray.uintbe
       :noindex:

        Writable version of :attr:`Bits.uintbe`.

        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.

uintle
^^^^^^
    .. attribute:: BitArray.uintle
       :noindex:

        Writable version of :attr:`Bits.uintle`.
        
        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.

uintne
^^^^^^
    .. attribute:: BitArray.uintne
       :noindex:

        Writable version of :attr:`Bits.uintne`.

        When used as a setter the value must fit into the current length of the :class:`BitArray`, else a :exc:`ValueError` will be raised.

Special Methods
---------------

__delitem__
^^^^^^^^^^^
    .. method:: BitArray.__delitem__(key)

        ``del s[start:end:step]``

        Deletes the slice specified.

__iadd__
^^^^^^^^
    .. method:: BitArray.__iadd__(bs)

        ``s1 += s2``

        Appends *bs* to the current bitstring.
        
        Note that for :class:`BitArray` objects this will be an in-place change, whereas for :class:`Bits` objects using ``+=`` will not call this method - instead a new object will be created (it is equivalent to a copy and an :meth:`~Bits.__add__`). ::

            >>> s = BitArray(ue=423)
            >>> s += BitArray(ue=12)
            >>> s.read('ue')
            423
            >>> s.read('ue')
            12

__iand__
^^^^^^^^
    .. method:: BitArray.__iand__(bs)
    
        ``s &= bs``
        
        In-place bit-wise AND between two bitstrings. If the two bitstrings are not the same length then a :exc:`ValueError` is raised.        

__ilshift__
^^^^^^^^^^^
    .. method:: BitArray.__ilshift__(n)
    
        ``s <<= n``
        
        Shifts the bits in-place *n* bits to the left. The *n* right-most bits will become zeros and bits shifted off the left will be lost.

__imul__
^^^^^^^^
    .. method:: BitArray.__imul__(n)
    
        ``s *= n``
        
        In-place concatenation of *n* copies of the current bitstring.
        
            >>> s = BitArray('0xbad')
            >>> s *= 3
            >>> s.hex
            'badbadbad'

__ior__
^^^^^^^
    .. method:: BitArray.__ior__(bs)
    
        ``s |= bs``
        
        In-place bit-wise OR between two bitstrings. If the two bitstrings are not the same length then a :exc:`ValueError` is raised.        

__irshift__
^^^^^^^^^^^
    .. method:: BitArray.__irshift__(n)
    
        ``s >>= n``
        
        Shifts the bits in-place *n* bits to the right. The *n* left-most bits will become zeros and bits shifted off the right will be lost.

__ixor__
^^^^^^^^
    .. method:: BitArray.__ixor__(bs)

        ``s ^= bs``
        
        In-place bit-wise XOR between two bitstrings. If the two bitstrings are not the same length then a :exc:`ValueError` is raised.        

__setitem__
^^^^^^^^^^^
    .. method:: BitArray.__setitem__(key, value)

        ``s1[start:end:step] = s2``

        Replaces the slice specified with a new value. ::

            >>> s = BitArray('0x00000000')
            >>> s[::8] = '0xf'
            >>> print(s)
            0x80808080
            >>> s[-12:] = '0xf'
            >>> print(s)
            0x80808f

