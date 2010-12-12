.. currentmodule:: bitstring

``class ConstBitArray(object)``
-------------------------------

A ``ConstBitArray`` is the most basic class. It is immutable, so once created its value cannot change. It is a base class for all the other classes in the `bitstring` module.

Methods
^^^^^^^

    :meth:`all` -- Check if all specified bits are set to 1 or 0.
    :meth:`any` -- Check if any of specified bits are set to 1 or 0.
    :meth:`cut` -- Create generator of constant sized chunks.
    :meth:`endswith` -- Return whether the bitstring ends with a sub-string.
    :meth:`find` -- Find a sub-bitstring in the current bitstring.
    :meth:`findall` -- Find all occurences of a sub-bitstring in the current bitstring.
    :meth:`join` -- Join bitstrings together using current bitstring.
    :meth:`rfind` -- Seek backwards to find a sub-bitstring.
    :meth:`split` -- Create generator of chunks split by a delimiter.
    :meth:`startswith` -- Return whether the bitstring starts with a sub-bitstring.
    :meth:`tobytes` -- Return bitstring as bytes, padding if needed.
    :meth:`tofile` -- Write bitstring to file, padding if needed.
    :meth:`unpack` -- Interpret bits using format string.

Special methods
^^^^^^^^^^^^^^^

    Also available are the operators ``[]``, ``==``, ``!=``, ``+``, ``*``, ``~``, ``<<``, ``>>``, ``&``, ``|``, ``^``.

Properties
^^^^^^^^^^

    :attr:`bin` -- The bitstring as a binary string.
    :attr:`bool` -- For single bit bitstrings, interpret as True or False.
    :attr:`bytes` -- The bitstring as a bytes object.
    :attr:`float` -- Interpret as a floating point number.
    :attr:`floatbe` -- Interpret as a big-endian floating point number.
    :attr:`floatle` -- Interpret as a little-endian floating point number.
    :attr:`floatne` -- Interpret as a native-endian floating point number.
    :attr:`hex` -- The bitstring as a hexadecimal string.
    :attr:`int` -- Interpret as a two's complement signed integer.
    :attr:`intbe` -- Interpret as a big-endian signed integer.
    :attr:`intle` -- Interpret as a little-endian signed integer.
    :attr:`intne` -- Interpret as a native-endian signed integer.
    :attr:`len` -- Length of the bitstring in bits.
    :attr:`oct` -- The bitstring as an octal string.
    :attr:`se` -- Interpret as a signed exponential-Golomb code.
    :attr:`ue` -- Interpret as an unsigned exponential-Golomb code.
    :attr:`uint` -- Interpret as a two's complement unsigned integer.
    :attr:`uintbe` -- Interpret as a big-endian unsigned integer.
    :attr:`uintle` -- Interpret as a little-endian unsigned integer.
    :attr:`uintne` -- Interpret as a native-endian unsigned integer.

``class BitArray(ConstBitArray)``
---------------------------------

This class adds mutating methods to `ConstBitArray`.

Additional methods
^^^^^^^^^^^^^^^^^^

    :meth:`append` -- Append a bitstring.
    :meth:`byteswap` -- Change byte endianness in-place.
    :meth:`insert` -- Insert a bitstring.
    :meth:`invert` -- Flip bit(s) between one and zero.
    :meth:`overwrite` -- Overwrite a section with a new bitstring.
    :meth:`prepend` -- Prepend a bitstring.
    :meth:`replace` -- Replace occurences of one bitstring with another.
    :meth:`reverse` -- Reverse bits in-place.
    :meth:`rol` -- Rotate bits to the left.
    :meth:`ror` -- Rotate bits to the right.
    :meth:`set` -- Set bit(s) to 1 or 0.
    
Additional special methods
^^^^^^^^^^^^^^^^^^^^^^^^^^

    Mutating operators are available: ``[]``, ``<<=``, ``>>=``, ``*=``, ``&=``, ``|=`` and ``^=``.
    
Attributes
^^^^^^^^^^

    The same as ``ConstBitArray``, except that they are all writable as well as readable.


``class ConstBitStream(ConstBitArray)``
---------------------------------------

This class, previously known as just ``Bits`` (which is an alias for backward-compatibility), adds a bit position and methods to read and navigate in the bitstream.

Additional methods
^^^^^^^^^^^^^^^^^^

    bytealign() -- Align to next byte boundary.
    peek() -- Peek at and interpret next bits as a single item.
    peeklist() -- Peek at and interpret next bits as a list of items.
    read() -- Read and interpret next bits as a single item.
    readlist() -- Read and interpret next bits as a list of items.

Additional attributes
^^^^^^^^^^^^^^^^^^^^^

    :attr:`bytepos` -- The current byte position in the bitstring.
    :attr:`pos` -- The current bit position in the bitstring.


``class BitStream(BitArray, ConstBitStream)``
---------------------------------------------

This class, also known as ``BitString`` contains all of the 'stream' elements of ``ConstBitStream`` and adds all of the mutating methods of ``BitArray``.


