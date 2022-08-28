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

The format string consists of comma separated tokens of the form ``name:length=value``. See the entry for :meth:`~ConstBitStream.read` for more details.

The tokens can be 'literals', like ``0xef``, ``0b110``, ``uint:8=55``, etc. which just represent a set sequence of bits.

They can also have the value missing, in which case the values contained in ``*values`` will be used. ::

 >>> a = pack('bin:3, hex:4', '001', 'f')
 >>> b = pack('uint:10', 33)

A dictionary or keyword arguments can also be provided. These will replace items in the format string. ::

 >>> c = pack('int:a=b', a=10, b=20)
 >>> d = pack('int:8=a, bin=b, int:4=a', a=7, b='0b110')
 
Plain names can also be used as follows::

 >>> e = pack('a, b, b, a', a='0b11', b='0o2')
 
Tokens starting with an endianness identifier (``<``, ``>`` or ``@``) implies a struct-like compact format string (see :ref:`compact_format`). For example this packs three little-endian 16-bit integers::

 >>> f = pack('<3h', 12, 3, 108)

And of course you can combine the different methods in a single pack.

A :exc:`ValueError` will be raised if the ``*values`` are not all used up by the format string, and if a value provided doesn't match the length specified by a token.


Command line usage
------------------

The bitstring module can be called from the command line to perform simple operations. For example::

    $ python -m bitstring int:16=-400
    0xfe70

    $ python -m bitstring float:32=0.2 bin
    00111110010011001100110011001101

    $ python -m bitstring 0xff "3*0b01,0b11" uint
    65367

    $ python -m bitstring hex=01, uint:12=352.hex
    01160

Command-line parameters are concatenated and a bitstring created from them. If the final parameter is either an interpretation string or ends with a ``.`` followed by an interpretation string then that interpretation of the bitstring will be used when printing it. If no interpretation is given then the bitstring is just printed.


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

