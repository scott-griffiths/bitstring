.. currentmodule:: bitstring

Packing
-------

Another method of creating :class:`BitStream` objects is to use the :func:`pack` function. This takes a format specifier which is a string with comma separated tokens, and a number of items to pack according to it. It's signature is ``bitstring.pack(format, *values, **kwargs)``.

For example using just the ``*values`` arguments we can say::

    s = bitstring.pack('hex:32, uint:12, uint:12', '0x000001b3', 352, 288)

which is equivalent to initialising as::

    s = BitStream('0x0000001b3, uint:12=352, uint:12=288')

The advantage of the pack function is if you want to write more general code for creation. ::

    def foo(a, b, c, d):
        return bitstring.pack('uint:8, 0b110, int:6, bin, bits', a, b, c, d)
 
    s1 = foo(12, 5, '0b00000', '')
    s2 = foo(101, 3, '0b11011', s1)

Note how you can use some tokens without sizes (such as ``bin`` and ``bits`` in the above example), and use values of any length to fill them. If the size had been specified then a :exc:`ValueError` would be raised if the parameter given was the wrong length. Note also how bitstring literals can be used (the ``0b110`` in the bitstring returned by ``foo``) and these don't consume any of the items in ``*values``.

You can also include keyword, value pairs (or an equivalent dictionary) as the final parameter(s). The values are then packed according to the positions of the keywords in the format string. This is most easily explained with some examples. Firstly the format string needs to contain parameter names::

    format = 'hex:32=start_code, uint:12=width, uint:12=height'

Then we can make a dictionary with these parameters as keys and pass it to pack::

    d = {'start_code': '0x000001b3', 'width': 352, 'height': 288}
    s = bitstring.pack(format, **d)

Another method is to pass the same information as keywords at the end of pack's parameter list::

    s = bitstring.pack(format, width=352, height=288, start_code='0x000001b3')

The tokens in the format string that you must provide values for are:

=============       ================================================================
``int:n``           ``n`` bits as a signed integer.
``uint:n``          ``n`` bits as an unsigned integer.
``intbe:n``         ``n`` bits as a big-endian whole byte signed integer.
``uintbe:n``        ``n`` bits as a big-endian whole byte unsigned integer.
``intle:n``         ``n`` bits as a little-endian whole byte signed integer.
``uintle:n``        ``n`` bits as a little-endian whole byte unsigned integer.
``intne:n``         ``n`` bits as a native-endian whole byte signed integer.
``uintne:n``        ``n`` bits as a native-endian whole byte unsigned integer.
``float:n``         ``n`` bits as a big-endian floating point number (same as ``floatbe``). 
``floatbe:n``       ``n`` bits as a big-endian floating point number (same as ``float``).
``floatle:n``       ``n`` bits as a little-endian floating point number. 
``floatne:n``       ``n`` bits as a native-endian floating point number. 
``hex[:n]``         [``n`` bits as] a hexadecimal string.
``oct[:n]``         [``n`` bits as] an octal string.
``bin[:n]``         [``n`` bits as] a binary string.
``bits[:n]``        [``n`` bits as] a new bitstring.
``bool[:1]``        single bit as a boolean (True or False).
``ue``              an unsigned integer as an exponential-Golomb code.
``se``              a signed integer as an exponential-Golomb code.
``uie``             an unsigned integer as an interleaved exponential-Golomb code.
``sie``             a signed integer as an interleaved exponential-Golomb code.
=============       ================================================================

and you can also include constant bitstring tokens constructed from any of the following:

================     ===============================================================
``0b...``            binary literal.
``0o...``            octal literal.
``0x...``            hexadecimal literal.
``int:n=m``          signed integer ``m`` in ``n`` bits.
``uint:n=m``         unsigned integer ``m`` in ``n`` bits.
``intbe:n=m``        big-endian whole byte signed integer ``m`` in ``n`` bits.
``uintbe:n=m``       big-endian whole byte unsigned integer ``m`` in ``n`` bits.
``intle:n=m``        little-endian whole byte signed integer ``m`` in ``n`` bits.
``uintle:n=m``       little-endian whole byte unsigned integer ``m`` in ``n`` bits.
``intne:n=m``        native-endian whole byte signed integer ``m`` in ``n`` bits.
``uintne:n=m``       native-endian whole byte unsigned integer ``m`` in ``n`` bits.
``float:n=f``        big-endian floating point number ``f`` in ``n`` bits.
``floatbe:n=f``      big-endian floating point number ``f`` in ``n`` bits.
``floatle:n=f``      little-endian floating point number ``f`` in ``n`` bits.
``floatne:n=f``      native-endian floating point number ``f`` in ``n`` bits.
``ue=m``             exponential-Golomb code for unsigned integer ``m``.
``se=m``             exponential-Golomb code for signed integer ``m``.
``uie=m``            interleaved exponential-Golomb code for unsigned integer ``m``.
``sie=m``            interleaved exponential-Golomb code for signed integer ``m``.
``bool=b``           a single bit, either True or False.
``pad:n``            ``n`` zero bits (for use as padding).
================     ===============================================================

You can also use a keyword for the length specifier in the token, for example::

    s = bitstring.pack('int:n=-1', n=100)

And finally it is also possible just to use a keyword as a token::

    s = bitstring.pack('hello, world', world='0x123', hello='0b110')

As you would expect, there is also an :meth:`~Bits.unpack` function that takes a bitstring and unpacks it according to a very similar format string. This is covered later in more detail, but a quick example is::

    >>> s = bitstring.pack('ue, oct:3, hex:8, uint:14', 3, '0o7', '0xff', 90)
    >>> s.unpack('ue, oct:3, hex:8, uint:14')
    [3, '7', 'ff', 90]

.. _compact_format:

Compact format strings
^^^^^^^^^^^^^^^^^^^^^^

Another option when using :func:`pack`, as well as other methods such as :meth:`~ConstBitStream.read` and :meth:`~BitArray.byteswap`, is to use a format specifier similar to those used in the :mod:`struct` and :mod:`array` modules. These consist of a character to give the endianness, followed by more single characters to give the format.

The endianness character must start the format string and unlike in the struct module it is not optional (except when used with :meth:`~BitArray.byteswap`):

=====   =============
``>``   Big-endian
``<``   Little-endian
``@``   Native-endian
=====   =============

For 'network' endianness use ``>`` as network and big-endian are equivalent. This is followed by at least one of these format characters:

=====   ===============================
``b``   8 bit signed integer
``B``   8 bit unsigned integer
``h``   16 bit signed integer
``H``   16 bit unsigned integer
``l``   32 bit signed integer
``L``   32 bit unsigned integer
``q``   64 bit signed integer
``Q``   64 bit unsigned integer
``f``   32 bit floating point number
``d``   64 bit floating point number
=====   ===============================

The exact type is determined by combining the endianness character with the format character, but rather than give an exhaustive list a single example should explain:

======  ======================================   ============
``>h``  Big-endian 16 bit signed integer         ``intbe:16``
``<h``  Little-endian 16 bit signed integer      ``intle:16``
``@h``  Native-endian 16 bit signed integer      ``intne:16``
======  ======================================   ============

As you can see all three are signed integers in 16 bits, the only difference is the endianness. The native-endian ``@h`` will equal the big-endian ``>h`` on big-endian systems, and equal the little-endian ``<h`` on little-endian systems. For the single byte codes ``b`` and ``B`` the endianness doesn't make any difference, but you still need to specify one so that the format string can be parsed correctly.

An example::

    s = bitstring.pack('>qqqq', 10, 11, 12, 13)

is equivalent to ::

    s = bitstring.pack('intbe:64, intbe:64, intbe:64, intbe:64', 10, 11, 12, 13)

Just as in the struct module you can also give a multiplicative factor before the format character, so the previous example could be written even more concisely as ::

    s = bitstring.pack('>4q', 10, 11, 12, 13)

You can of course combine these format strings with other initialisers, even mixing endiannesses (although I'm not sure why you'd want to)::

    s = bitstring.pack('>6h3b, 0b1, <9L', *range(18))

This rather contrived example takes the numbers 0 to 17 and packs the first 6 as signed big-endian 2-byte integers, the next 3 as single bytes, then inserts a single 1 bit, before packing the remaining 9 as little-endian 4-byte unsigned integers.
