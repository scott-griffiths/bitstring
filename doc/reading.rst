******************************
Reading, Parsing and Unpacking
******************************

Reading and parsing
---------------------

A common need is to parse a large bitstring into smaller parts. Functions for reading in the bitstring as if it were a file or stream are provided and will return new bitstrings. These new objects are top-level bitstring objects and can be interpreted using properties or could be read from themselves to form a hierarchy of reads.

In order to behave like a file or stream, every bitstring has a property :attr:`pos` which is the current position from which reads occur. :attr:`pos` can range from zero (its value on construction) to the length of the bitstring, a position from which all reads will fail as it is past the last bit.

The property :attr:`bytepos` is also available, and is useful if you are only dealing with byte data and don't want to always have to divide the bit position by eight. Note that if you try to use :attr:`bytepos` and the bitstring isn't byte aligned (i.e. :attr:`pos` isn't a multiple of 8) then a :exc:`Error` exception will be raised.

``read / readlist``
^^^^^^^^^^^^^^^^^^^
For simple reading of a number of bits you can use :meth:`Bits.read` with an integer argument. The following example does some simple parsing of an MPEG-1 video stream (the stream is provided in the ``test`` directory if you downloaded the source archive). ::

 >>> s = Bits(filename='test/test.m1v')
 >>> print(s.pos)
 0
 >>> start_code = s.read(32).hex
 >>> width = s.read(12).uint
 >>> height = s.read(12).uint
 >>> print(start_code, width, height, s.pos)
 0x000001b3 352 288 56
 >>> s.pos += 37
 >>> flags = s.read(2)
 >>> constrained_parameters_flag = flags.read(1)
 >>> load_intra_quantiser_matrix = flags.read(1)
 >>> print(s.pos, flags.pos)
 95 2

If you want to read multiple items in one go you can use :meth:`Bits.readlist`. This can take one or more integer parameters and return a list of bitstring objects. So for example instead of writing::

 a = s.read(32)
 b = s.read(8)
 c = s.read(24)

you can equivalently use just::

 a, b, c = s.readlist([32, 8, 24]) 

Reading using format strings
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :meth:`Bits.read` / :meth:`Bits.readlist` methods can also take a format string similar to that used in the auto initialiser. Only one token should be provided to :meth:`Bits.read` and a single value is returned. To read multiple tokens use :meth:`Bits.readlist`, which unsurprisingly returns a list.

The format string consists of comma separated tokens that describe how to interpret the next bits in the bitstring. The tokens are:

==============  ===================================================================
``int:n``       ``n`` bits as a signed integer.
``uint:n``      ``n`` bits as an unsigned integer.
``intbe:n``	    ``n`` bits as a byte-wise big-endian signed integer.
``uintbe:n``    ``n`` bits as a byte-wise big-endian unsigned integer.
``intle:n``     ``n`` bits as a byte-wise little-endian signed integer.
``uintle:n``    ``n`` bits as a byte-wise little-endian unsigned integer.
``intne:n``     ``n`` bits as a byte-wise native-endian signed integer.
``uintne:n``    ``n`` bits as a byte-wise native-endian unsigned integer.
``float:n``     ``n`` bits as a big-endian floating point number (same as ``floatbe``). 
``floatbe:n``   ``n`` bits as a big-endian floating point number (same as ``float``).
``floatle:n``   ``n`` bits as a little-endian floating point number. 
``floatne:n``   ``n`` bits as a native-endian floating point number. 
``hex:n``       ``n`` bits as a hexadecimal string.
``oct:n``       ``n`` bits as an octal string.
``bin:n``       ``n`` bits as a binary string.
``bits:n``      ``n`` bits as a new bitstring.
``bytes:n``     ``n`` bytes as a ``bytes`` object.
``ue``          next bits as an unsigned exponential-Golomb code.
``se``          next bits as a signed exponential-Golomb code.
==============  ===================================================================

So in the earlier example we could have written::

 start_code = s.read('hex:32')
 width = s.read('uint:12')
 height = s.read('uint:12')

and we also could have combined the three reads as::

 start_code, width, height = s.readlist('hex:32, 12, 12')

where here we are also taking advantage of the default ``uint`` interpretation for the second and third tokens.

You are allowed to use one 'stretchy' token in a :meth:`Bits.readlist`. This is a token without a length specified which will stretch to fill encompass as many bits as possible. This is often useful when you just want to assign something to 'the rest' of the bitstring::

 a, b, everthing_else = s.readlist('intle:16, intle:24, bits')

In this example the ``bits`` token will consist of everything left after the first two tokens are read, and could be empty.

It is an error to use more than one stretchy token, or to use a ``ue`` or ``se`` token after a stretchy token (the reason you can't use exponential-Golomb codes after a stretchy token is that the codes can only be read forwards; that is you can't ask "if this code ends here, where did it begin?" as there could be many possible answers).

``peek``
^^^^^^^^

In addition to the read functions there are matching peek functions. These are identical to the read except that they do not advance the position in the bitstring to after the read elements. ::

 s = BitString('0x4732aa34')
 if s.peek(8) == '0x47':
     t = s.read(16)          # t is first 2 bytes '0x4732'
 else:
     s.find('0x47')


Unpacking
---------

The :meth:`Bits.unpack` method works in a very similar way to :meth:`Bits.readlist`. The major difference is that it interprets the whole bitstring from the start, and takes no account of the current :attr:`pos`. It's a natural complement of the :func:`pack` function. ::

 s = pack('uint:10, hex, int:13, 0b11', 130, '3d', -23)
 a, b, c, d = s.unpack('uint:10, hex, int:13, bin:2')

Seeking
-------

The properties :attr:`pos` and :attr:`bytepos` are available for getting and setting the position, which is zero on creation of the bitstring.

Note that you can only use :attr:`bytepos` if the position is byte aligned, i.e. the bit position is a multiple of 8. Otherwise a :exc:`ByteAlignError` exception is raised.

For example::

 >>> s = BitString('0x123456')
 >>> s.pos
 0
 >>> s.bytepos += 2
 >>> s.pos                    # note pos verses bytepos
 16
 >>> s.pos += 4
 >>> print(s.read('bin:4'))   # the final nibble '0x6'
 0b0110

Finding and replacing
---------------------

``find / rfind``
^^^^^^^^^^^^^^^^

To search for a sub-string use the :meth:`Bits.find` method. If the find succeeds it will set the position to the start of the next occurrence of the searched for string and return ``True``, otherwise it will return ``False``. By default the sub-string will be found at any bit position - to allow it to only be found on byte boundaries set ``bytealigned=True``.

 >>> s = BitString('0x00123400001234')
 >>> found = s.find('0x1234', bytealigned=True)
 >>> print(found, s.bytepos)
 True 1
 >>> found = s.find('0xff', bytealigned=True)
 >>> print(found, s.bytepos)
 False 1

:meth:`Bits.rfind` does much the same as :meth:`Bits.find`, except that it will find the last occurrence, rather than the first. ::

 >>> t = BitString('0x0f231443e8')
 >>> found = t.rfind('0xf')           # Search all bit positions in reverse
 >>> print(found, t.pos)
 True 31                              # Found within the 0x3e near the end

For all of these finding functions you can optionally specify a ``start`` and / or ``end`` to narrow the search range. Note though that because it's searching backwards :meth:`Bits.rfind` will start at ``end`` and end at ``start`` (so you always need ``start``  <  ``end``).

``findall``
^^^^^^^^^^^

To find all occurrences of a bitstring inside another (even overlapping ones), use :meth:`Bits.findall`. This returns a generator for the bit positions of the found strings. ::

 >>> r = BitString('0b011101011001')
 >>> ones = r.findall('0b1')
 >>> print(list(ones))
 [1, 2, 3, 5, 7, 8, 11]

``replace``
^^^^^^^^^^^

To replace all occurrences of one :class:`BitString` with another use :meth:`BitString.replace`. The replacements are done in-place, and the number of replacements made is returned. This methods changes the contents of the bitstring and so isn't available for the :class:`Bits` class. ::

 >>> s = BitString('0b110000110110')
 >>> s.replace('0b110', '0b1111')
 3            # The number of replacements made
 >>> s.bin
 '0b111100011111111'
