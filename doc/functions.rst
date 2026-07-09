.. currentmodule:: bitstring

Functions
---------

pack
^^^^
.. function:: pack(format[, *values, **kwargs])

   Packs the values and keyword arguments according to the *format* string and returns a new :class:`Bits` object.
   
   :param format: string with comma separated tokens
   :param values: extra values used to construct the :class:`Bits`
   :param kwargs: a dictionary of token replacements
   :rtype: Bits

The format string consists of comma separated tokens, see :ref:`format_tokens` and :ref:`compact_format` for details.

The tokens can be 'literals', like ``0xef``, ``0b110``, ``u8=55``, etc. which just represent a set sequence of bits.

They can also have the value missing, in which case the values contained in ``*values`` will be used. ::

 >>> a = pack('bin3, hex4', '001', 'f')
 >>> b = pack('u10', 33)

A dictionary or keyword arguments can also be provided. These will replace items in the format string. ::

 >>> c = pack('i:a=b', a=10, b=20)
 >>> d = pack('i8=a, bin=b, i4=a', a=7, b='0b110')
 
Plain names can also be used as follows::

 >>> e = pack('a, b, b, a', a='0b11', b='0o2')
 
Tokens starting with an endianness identifier (``<``, ``>`` or ``=``) implies a struct-like compact format string (see :ref:`compact_format`). For example this packs three little-endian 16-bit integers::

 >>> f = pack('<3h', 12, 3, 108)

And of course you can combine the different methods in a single pack.

A :exc:`ValueError` will be raised if the ``*values`` are not all used up by the format string, and if a value provided doesn't match the length specified by a token.



As an example of using just the ``*values`` arguments we can say::

    s = bitstring.pack('hex32, u12, u12', '0x000001b3', 352, 288)

which is equivalent to initialising as::

    s = Bits('0x000001b3, u12=352, u12=288')

The advantage of the pack function is if you want to write more general code for creation. ::

    def foo(a, b, c, d):
        return bitstring.pack('u8, 0b110, i6, bin, bits', a, b, c, d)

    s1 = foo(12, 5, '0b00000', '')
    s2 = foo(101, 3, '0b11011', s1)

Note how you can use some tokens without sizes (such as ``bin`` and ``bits`` in the above example), and use values of any length to fill them.
If the size had been specified then a :exc:`ValueError` would be raised if the parameter given was the wrong length.
Note also how bitstring literals can be used (the ``0b110`` in the bitstring returned by ``foo``) and these don't consume any of the items in ``*values``.

You can also include keyword, value pairs (or an equivalent dictionary) as the final parameter(s).
The values are then packed according to the positions of the keywords in the format string.
This is most easily explained with some examples. Firstly the format string needs to contain parameter names::

    format = 'hex32=start_code, u12=width, u12=height'

Then we can make a dictionary with these parameters as keys and pass it to pack::

    d = {'start_code': '0x000001b3', 'width': 352, 'height': 288}
    s = bitstring.pack(format, **d)

Another method is to pass the same information as keywords at the end of pack's parameter list::

    s = bitstring.pack(format, width=352, height=288, start_code='0x000001b3')


You can include constant bitstring tokens such as '0x101', '0xff', 'u7=81' etc. and also use a keyword for the length specifier in the token, for example::

    s = bitstring.pack('0xabc, i:n=-1', n=100)

Finally it is also possible just to use a keyword as a token::

    s = bitstring.pack('hello, world', world='0x123', hello='0b110')

----

Options
-------
The bitstring module has an ``options`` object that allows module-wide behaviours to be set.

.. data:: options

    Module-wide options object.


no_color
^^^^^^^^

.. data:: options.no_color
    :type: bool

The bitstring module can use ANSI escape codes to colourise the output of the :meth:`Bits.pp` and :meth:`Array.pp` methods.
If a ``NO_COLOR`` environment variable is found and is not an empty string then this option will be set to ``True``, otherwise it defaults to ``False``.
See https://no-color.org for more information.

The terminal colours can also be turned off by setting ``bitstring.options.no_color`` to ``True``.

Exceptions
----------

.. exception:: Error(Exception)

    Base class for all module exceptions.

.. exception:: InterpretError(Error, ValueError)

    Inappropriate interpretation of binary data. For example using the 'bytes' property on a bitstring that isn't a whole number of bytes long.

.. exception:: ByteAlignError(Error)

    Whole-byte position or length needed.

.. exception:: CreationError(Error, ValueError)

    Inappropriate argument during bitstring creation.

.. exception:: ReadError(Error, IndexError)

    Reading or peeking past the end of a bitstring.
