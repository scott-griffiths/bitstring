
Miscellany
==========

Other Functions
---------------

``bytealign``
^^^^^^^^^^^^^

:meth:`Bits.bytealign` advances between zero and seven bits to make the :attr:`pos` a multiple of eight. It returns the number of bits advanced. ::

 >>> a = BitString('0x11223344')
 >>> a.pos = 1
 >>> skipped = a.bytealign()
 >>> print(skipped, a.pos)
 7 8
 >>> skipped = a.bytealign()
 >>> print(skipped, a.pos)
 0 8

``reverse``
^^^^^^^^^^^

This simply reverses the bits of the :class:`BitString` in place. You can optionally specify a range of bits to reverse. ::

 >>> a = BitString('0b000001101')
 >>> a.reverse()
 >>> a.bin
 '0b101100000'
 >>> a.reverse(0, 4)
 >>> a.bin
 '0b110100000'

``reversebytes``
^^^^^^^^^^^^^^^^

This reverses the bytes of the :class:`BitString` in place. You can optionally specify a range of bits to reverse. If the length to reverse isn't a multiple of 8 then a :exc:`Error` is raised. ::

 >>> a = BitString('0x123456')
 >>> a.reversebytes()
 >>> a.hex
 '0x563412'
 >>> a.reversebytes(0, 16)
 >>> a.hex
 '0x345612'

``tobytes``
^^^^^^^^^^^

Returns the byte data contained in the bitstring as a ``bytes`` object (equivalent to a ``str`` if you're using Python 2.6). This differs from using the plain :meth:`bytes` property in that if the bitstring isn't a whole number of bytes long then it will be made so by appending up to seven zero bits. ::

 >>> BitString('0b1').tobytes()
 '\x80'

``tofile``
^^^^^^^^^^

Writes the byte data contained in the bitstring to a file. The file should have been opened in a binary write mode, for example::

 >>> f = open('newfile', 'wb')
 >>> BitString('0xffee3241fed').tofile(f)

In exactly the same manner as with :meth:`Bits.tobytes`, up to seven zero bits will be appended to make the file a whole number of bytes long.

``startswith / endswith``
^^^^^^^^^^^^^^^^^^^^^^^^^

These act like the same named functions on strings, that is they return ``True`` if the bitstring starts or ends with the parameter given. Optionally you can specify a range of bits to use. ::

 >>> s = BitString('0xef133')
 >>> s.startswith('0b111011')
 True
 >>> s.endswith('0x4')
 False

``ror / rol``
^^^^^^^^^^^^^

To rotate the bits in a :class:`BitString` use :meth:`BitString.ror` and :meth:`BitString.rol` for right and left rotations respectively. The changes are done in-place. ::

 >>> s = BitString('0x00001')
 >>> s.rol(6)
 >>> s.hex
 '0x00040'

Special Methods
---------------

A few of the special methods have already been covered, for example :meth:`Bits.__add__` and :meth:`BitString.__iadd__` (the ``+`` and ``+=`` operators) and :meth:`Bits.__getitem__` and :meth:`BitString.__setitem__` (reading and setting slices via ``[]``). Here are the rest:

``__len__``
^^^^^^^^^^^^^^^

This implements the :func:`len` function and returns the length of the bitstring in bits.

It's recommended that you use the :attr:`len` property instead of the function as a limitation of Python means that the function will raise an :exc:`OverflowError` if the bitstring has more than ``sys.maxsize`` elements (that's typically 256MB of data).

There's not much more to say really, except to emphasise that it is always in bits and never bytes. ::

 >>> len(BitString('0x00'))
 8

``__str__ / __repr__``
^^^^^^^^^^^^^^^^^^^^^^

These get called when you try to print a bitstring. As bitstrings have no preferred interpretation the form printed might not be what you want - if not then use the :attr:`hex`, :attr:`bin`, :attr:`int` etc. properties. The main use here is in interactive sessions when you just want a quick look at the bitstring. The :meth:`Bits.__repr__` tries to give a code fragment which if evaluated would give an equal bitstring.

The form used for the bitstring is generally the one which gives it the shortest representation. If the resulting string is too long then it will be truncated with ``...`` - this prevents very long bitstrings from tying up your interactive session while they print themselves. ::

 >>> a = BitString('0b1111 111')
 >>> print(a)
 0b1111111
 >>> a
 BitString('0b1111111')
 >>> a += '0b1'
 >>> print(a)
 0xff
 >>> print(a.bin)
 0b11111111

``__eq__ / __ne__``
^^^^^^^^^^^^^^^^^^^

The equality of two bitstring objects is determined by their binary representations being equal. If you have a different criterion you wish to use then code it explicitly, for example ``a.int  ==  b.int`` could be true even if ``a  ==  b`` wasn't (as they could be different lengths). ::

 >>> BitString('0b0010') == '0x2'
 True
 >>> BitString('0x2') != '0o2'
 True

``__invert__``
^^^^^^^^^^^^^^

To get a bit-inverted copy of a bitstring use the ``~`` operator::

 >>> a = BitString('0b0001100111')
 >>> print(a)
 0b0001100111
 >>> print(~a)
 0b1110011000
 >>> ~~a == a
 True

``__lshift__ / __rshift__ / __ilshift__ / __irshift__``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bitwise shifts can be achieved using ``<<``, ``>>``, ``<<=`` and ``>>=``. Bits shifted off the left or right are replaced with zero bits. If you need special behaviour, such as keeping the sign of two's complement integers then do the shift on the property instead, for example use ``a.int >>= 2``. ::

 >>> a = BitString('0b10011001')
 >>> b = a << 2
 >>> print(b)
 0b01100100
 >>> a >>= 2
 >>> print(a)
 0b00100110

``__mul__ / __imul__ / __rmul__``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Multiplication of a bitstring by an integer means the same as it does for ordinary strings: concatenation of multiple copies of the bitstring. ::

 >>> a = BitString('0b10')*8
 >>> print(a.bin)
 0b1010101010101010

``__copy__``
^^^^^^^^^^^^

This allows the bitstring to be copied via the :mod:`copy` module. ::

 >>> import copy
 >>> a = BitString('0x4223fbddec2231')
 >>> b = copy.copy(a)
 >>> b == a
 True
 >>> b is a
 False

It's not terribly exciting, and isn't the only method of making a copy. Using ``b  =  BitString(a)`` is another option, but ``b  =  a[:]`` may be more familiar to some.

``__and__ / __or__ / __xor__ / __iand__ / __ior__ / __ixor__``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bit-wise AND, OR and XOR are provided for bitstring objects of equal length only (otherwise a :exc:`ValueError` is raised). ::

 >>> a = BitString('0b00001111')
 >>> b = BitString('0b01010101')
 >>> print((a&b).bin)
 0b00000101
 >>> print((a|b).bin)
 0b01011111
 >>> print((a^b).bin)
 0b01010000
 >>> b &= '0x1f'
 >>> print(b.bin)
 0b00010101
