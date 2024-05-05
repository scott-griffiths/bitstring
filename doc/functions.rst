.. currentmodule:: bitstring

Functions
---------

pack
^^^^
.. function:: pack(format[, *values, **kwargs])

   Packs the values and keyword arguments according to the *format* string and returns a new :class:`BitStream`.
   
   :param format: string with comma separated tokens
   :param values: extra values used to construct the :class:`BitStream`
   :param kwargs: a dictionary of token replacements
   :rtype: BitStream

The format string consists of comma separated tokens, see :ref:`format_tokens` and :ref:`compact_format` for details.

The tokens can be 'literals', like ``0xef``, ``0b110``, ``uint8=55``, etc. which just represent a set sequence of bits.

They can also have the value missing, in which case the values contained in ``*values`` will be used. ::

 >>> a = pack('bin3, hex4', '001', 'f')
 >>> b = pack('uint10', 33)

A dictionary or keyword arguments can also be provided. These will replace items in the format string. ::

 >>> c = pack('int:a=b', a=10, b=20)
 >>> d = pack('int8=a, bin=b, int4=a', a=7, b='0b110')
 
Plain names can also be used as follows::

 >>> e = pack('a, b, b, a', a='0b11', b='0o2')
 
Tokens starting with an endianness identifier (``<``, ``>`` or ``=``) implies a struct-like compact format string (see :ref:`compact_format`). For example this packs three little-endian 16-bit integers::

 >>> f = pack('<3h', 12, 3, 108)

And of course you can combine the different methods in a single pack.

A :exc:`ValueError` will be raised if the ``*values`` are not all used up by the format string, and if a value provided doesn't match the length specified by a token.



As an example of using just the ``*values`` arguments we can say::

    s = bitstring.pack('hex32, uint12, uint12', '0x000001b3', 352, 288)

which is equivalent to initialising as::

    s = BitStream('0x0000001b3, uint12=352, uint12=288')

The advantage of the pack function is if you want to write more general code for creation. ::

    def foo(a, b, c, d):
        return bitstring.pack('uint8, 0b110, int6, bin, bits', a, b, c, d)

    s1 = foo(12, 5, '0b00000', '')
    s2 = foo(101, 3, '0b11011', s1)

Note how you can use some tokens without sizes (such as ``bin`` and ``bits`` in the above example), and use values of any length to fill them.
If the size had been specified then a :exc:`ValueError` would be raised if the parameter given was the wrong length.
Note also how bitstring literals can be used (the ``0b110`` in the bitstring returned by ``foo``) and these don't consume any of the items in ``*values``.

You can also include keyword, value pairs (or an equivalent dictionary) as the final parameter(s).
The values are then packed according to the positions of the keywords in the format string.
This is most easily explained with some examples. Firstly the format string needs to contain parameter names::

    format = 'hex32=start_code, uint12=width, uint12=height'

Then we can make a dictionary with these parameters as keys and pass it to pack::

    d = {'start_code': '0x000001b3', 'width': 352, 'height': 288}
    s = bitstring.pack(format, **d)

Another method is to pass the same information as keywords at the end of pack's parameter list::

    s = bitstring.pack(format, width=352, height=288, start_code='0x000001b3')


You can include constant bitstring tokens such as '0x101', '0xff', 'uint7=81' etc. and also use a keyword for the length specifier in the token, for example::

    s = bitstring.pack('0xabc, int:n=-1', n=100)

Finally it is also possible just to use a keyword as a token::

    s = bitstring.pack('hello, world', world='0x123', hello='0b110')

----

Options
-------
The bitstring module has an ``options`` object that allows certain module-wide behaviours to be set.

lsb0
^^^^

.. data:: bitstring.options.lsb0 : bool

By default bit numbering in the bitstring module is done from 'left' to 'right'. That is, from bit ``0`` at the start of the data to bit ``n - 1`` at the end. This allows bitstrings to be treated like an ordinary Python container that is only allowed to contain single bits.


The ``lsb0`` option allows bitstrings to use Least Significant Bit Zero
(LSB0) bit numbering; that is the right-most bit in the bitstring will
be bit 0, and the left-most bit will be bit (n-1), rather than the
other way around. LSB0 is a more natural numbering
system in many fields, but is the opposite to Most Significant Bit
Zero (MSB0) numbering which is the natural option when thinking of
bitstrings as standard Python containers.

For example, if you set a bitstring to be the binary ``010001111`` it will be stored in the same way for MSB0 and LSB0 but slicing, reading, unpacking etc. will all behave differently.

.. list-table:: MSB0 →
   :header-rows: 1

   * - bit index
     - 0
     - 1
     - 2
     - 3
     - 4
     - 5
     - 6
     - 7
     - 8
   * - value
     - ``0``
     - ``1``
     - ``0``
     - ``0``
     - ``0``
     - ``1``
     - ``1``
     - ``1``
     - ``1``

In MSB0 everything behaves like an ordinary Python container. Bit zero is the left-most bit and reads/slices happen from left to right.

.. list-table:: ← LSB0
   :header-rows: 1

   * - bit index
     - 8
     - 7
     - 6
     - 5
     - 4
     - 3
     - 2
     - 1
     - 0
   * - value
     - ``0``
     - ``1``
     - ``0``
     - ``0``
     - ``0``
     - ``1``
     - ``1``
     - ``1``
     - ``1``

In LSB0 the final, right-most bit is labelled as bit zero. Reads and slices happen from right to left.

When bitstrings (or slices of bitstrings) are interpreted as integers and other types the left-most bit is considered as the most significant bit. It's important to note that this is the case irrespective of whether the first or last bit is considered the bit zero, so for example if you were to interpret a whole bitstring as an integer, its value would be the same with and without `lsb0` being set to `True`.

To illustrate this, for the example above this means that the bin and int representations would be ``010001111`` and ``143`` respectively for both MSB0 and LSB0 bit numbering.

To switch from the default MSB0, use ``bitstring.options.lsb0``. This defaults to ``False`` and unless explicitly stated all examples and documentation related to the bitstring module use the default MSB0 indexing.

    >>> bitstring.options.lsb0 = True

Slicing is still done with the start bit smaller than the end bit.
For example:

    >>> s = Bits('0b010001111')
    >>> s[0:5]  # LSB0 so this is the right-most five bits
    Bits('0b01111')
    >>> s[0]
    True

.. note::
    In some standards and documents using LSB0 notation the slice of the final five bits would be shown as ``s[5:0]``, which is reasonable as bit 5 comes before bit 0 when reading left to right, but this notation isn't used in this module as it clashes too much with the usual Python notation.

Negative indices work as you'd expect, with the first stored
bit being ``s[-1]`` and the final stored bit being ``s[-n]``.

Reading, peeking and unpacking of bitstrings are also affected by the ``lsb0`` flag, so reading always increments the bit position, and will move from right to left if ``lsb0`` is ``True``. Because of the way that exponential-Golomb codes are read (with the left-most bits determining the length of the code) these interpretations are not available in LSB0 mode, and using them will raise an exception.

For ``BitStream`` and ``ConstBitStream`` objects changing the value of ``bitstring.options.lsb0`` invalidates the current position in the bitstring, unless that value is ``0``, and future results are undefined. Basically don't perform reads or change the current bit position before switching the bit numbering system!

bytealigned
^^^^^^^^^^^

.. data:: bitstring.options.bytealigned : bool

A number of methods take a bytealigned parameter to indicate that they should only work on byte boundaries (e.g. :meth:`~Bits.find`, :meth:`~Bits.findall`, :meth:`~Bits.split` and :meth:`~BitArray.replace`). This parameter defaults to ``bitstring.options.bytealigned``, which itself defaults to ``False``, but can be changed to modify the default behaviour of the methods. For example::

    >>> a = BitArray('0x00 ff 0f ff')
    >>> a.find('0x0f')
    (4,)    # found first not on a byte boundary
    >>> a.find('0x0f', bytealigned=True)
    (16,)   # forced looking only on byte boundaries
    >>> bitstring.options.bytealigned = True  # Change default behaviour
    >>> a.find('0x0f')
    (16,)
    >>> a.find('0x0f', bytealigned=False)
    (4,)

If you’re only working with bytes then this can help avoid some errors and save some typing.

mxfp_overflow
^^^^^^^^^^^^^
.. data:: bitstring.options.mxfp_overflow : str

This option can be used to change the out-of-range behaviour of some 8-bit floating point types.
The default value is ``'saturate'`` but it can also be set to ``'overflow'``.
See :ref:`Exotic floats` for details.

no_color
^^^^^^^^

.. data:: bitstring.options.no_color : bool

The bitstring module can use ANSI escape codes to colourise the output of the :meth:`Bits.pp` and :meth:`Array.pp` methods.
If a ``NO_COLOR`` environment variable is found and is not an empty string then this option will be set to ``True``, otherwise it defaults to ``False``.
See https://no-color.org for more information.

The terminal colours can also be turned off by setting ``bitstring.options.no_color`` to ``True``.

----

Command Line Usage
------------------

The bitstring module can be called from the command line to perform simple operations. For example::

    $ python -m bitstring int16=-400
    0xfe70

    $ python -m bitstring float32=0.2 bin
    00111110010011001100110011001101

    $ python -m bitstring 0xff "3*0b01,0b11" uint
    65367

    $ python -m bitstring hex=01, uint12=352.hex
    01160

Command-line parameters are concatenated and a bitstring created from them. If the final parameter is either an interpretation string or ends with a ``.`` followed by an interpretation string then that interpretation of the bitstring will be used when printing it. If no interpretation is given then the bitstring is just printed.

----

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

