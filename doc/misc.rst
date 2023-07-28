.. currentmodule:: bitstring

Miscellany
==========




``__str__ / __repr__``
^^^^^^^^^^^^^^^^^^^^^^

These get called when you try to print a bitstring. As bitstrings have no preferred interpretation the form printed might not be what you want - if not then use the :attr:`~Bits.hex`, :attr:`~Bits.bin`, :attr:`~Bits.int` etc. properties. The main use here is in interactive sessions when you just want a quick look at the bitstring. The :meth:`~Bits.__repr__` tries to give a code fragment which if evaluated would give an equal bitstring.

The form used for the bitstring is generally the one which gives it the shortest representation. If the resulting string is too long then it will be truncated with ``...`` - this prevents very long bitstrings from tying up your interactive session while they print themselves. ::

 >>> a = BitArray('0b1111 111')
 >>> print(a)
 0b1111111
 >>> a
 BitArray('0b1111111')
 >>> a += '0b1'
 >>> print(a)
 0xff
 >>> print(a.bin)
 11111111

``__eq__ / __ne__``
^^^^^^^^^^^^^^^^^^^

The equality of two bitstring objects is determined by their binary representations being equal. If you have a different criterion you wish to use then code it explicitly, for example ``a.int == b.int`` could be true even if ``a == b`` wasn't (as they could be different lengths). ::

 >>> BitArray('0b0010') == '0x2'
 True
 >>> BitArray('0x2') != '0o2'
 True



``__lshift__ / __rshift__ / __ilshift__ / __irshift__``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bitwise shifts can be achieved using ``<<``, ``>>``, ``<<=`` and ``>>=``. Bits shifted off the left or right are replaced with zero bits. If you need special behaviour, such as keeping the sign of two's complement integers then do the shift on the property instead, for example use ``a.int >>= 2``. ::

 >>> a = BitArray('0b10011001')
 >>> b = a << 2
 >>> print(b)
 0b01100100
 >>> a >>= 2
 >>> print(a)
 0b00100110

``__mul__ / __imul__ / __rmul__``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Multiplication of a bitstring by an integer means the same as it does for ordinary strings: concatenation of multiple copies of the bitstring. ::

 >>> a = BitArray('0b10')*8
 >>> print(a.bin)
 1010101010101010


``__and__ / __or__ / __xor__ / __iand__ / __ior__ / __ixor__``
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bit-wise AND, OR and XOR are provided for bitstring objects of equal length only (otherwise a :exc:`ValueError` is raised). ::

 >>> a = BitArray('0b00001111')
 >>> b = BitArray('0b01010101')
 >>> print((a&b).bin)
 00000101
 >>> print((a|b).bin)
 01011111
 >>> print((a^b).bin)
 01011010
 >>> b &= '0x1f'
 >>> print(b.bin)
 00010101
