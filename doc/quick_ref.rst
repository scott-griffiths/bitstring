.. currentmodule:: bitstring

.. _quick_reference:

******************
Quick Reference
******************
This section lists the bitstring module's classes together with all their methods and attributes. The next section goes into full detail with examples.

The first four classes are bit containers, so that each element is a single bit.
They differ based on whether they can be modified after creation and on whether they have the concept of a current bit position.

.. list-table::
   :widths: 30 15 15 40
   :header-rows: 1

   * - Class
     - Mutable?
     - Streaming methods?
     -
   * - ``Bits``
     - ✘
     - ✘
     - An efficient, immutable container of bits.
   * - ``BitArray``
     - ✔
     - ✘
     - Like ``Bits`` but it can be changed after creation.
   * - ``ConstBitStream``
     - ✘
     - ✔
     - Immutable like ``Bits`` but with a bit position and reading methods.
   * - ``BitStream``
     - ✔
     - ✔
     - Mutable like ``BitArray`` but with a bit position and reading methods.


The final class is a flexible container whose elements are fixed-length bitstrings.

.. list-table::
   :widths: 30 15 15 40

   * - ``Array``
     - ✔
     - ✘
     - An efficient list-like container where each item has a fixed-length binary format.


----

Bits
----

``Bits`` is the most basic class and is just a container of bits. It is immutable, so once created its value cannot change.

Constructor
^^^^^^^^^^^

``Bits(auto, length: Optional[int], offset: Optional[int], **kwargs)``

The `auto` parameter can be many different types, including parsable strings, a file handle, a bytes or bytearray object, an integer or an iterable.

A single initialiser from `kwargs` can be used instead of `auto`, including  ``bin``, ``hex``, ``oct``, ``bool``, ``uint``, ``int``, ``float``, ``bytes`` and ``filename``.

Examples::

   Bits('0xef')
   Bits(float=-50.5, length=32)
   Bits('uint10=99')
   Bits(uint=99, length=10)

Methods
^^^^^^^

* :meth:`~Bits.all` -- Check if all specified bits are set to 1 or 0.
* :meth:`~Bits.any` -- Check if any of specified bits are set to 1 or 0.
* :meth:`~Bits.copy` -- Return a copy of the bitstring.
* :meth:`~Bits.count` -- Count the number of bits set to 1 or 0.
* :meth:`~Bits.cut` -- Create generator of constant sized chunks.
* :meth:`~Bits.endswith` -- Return whether the bitstring ends with a sub-bitstring.
* :meth:`~Bits.find` -- Find a sub-bitstring in the current bitstring.
* :meth:`~Bits.findall` -- Find all occurrences of a sub-bitstring in the current bitstring.
* :meth:`~Bits.join` -- Join bitstrings together using current bitstring.
* :meth:`~Bits.pp` -- Pretty print the bitstring.
* :meth:`~Bits.rfind` -- Seek backwards to find a sub-bitstring.
* :meth:`~Bits.split` -- Create generator of chunks split by a delimiter.
* :meth:`~Bits.startswith` -- Return whether the bitstring starts with a sub-bitstring.
* :meth:`~Bits.tobitarray` -- Return bitstring as a ``bitarray`` object from the `bitarray <https://pypi.org/project/bitarray>`_ package.
* :meth:`~Bits.tobytes` -- Return bitstring as bytes, padding if needed.
* :meth:`~Bits.tofile` -- Write bitstring to file, padding if needed.
* :meth:`~Bits.unpack` -- Interpret bits using format string.


Special methods
^^^^^^^^^^^^^^^

Also available are operators that will return a new bitstring (or check for equality):

* :meth:`[] <Bits.__getitem__>` -- Get an element or slice.
* :meth:`== <Bits.__eq__>` / :meth:`\!= <Bits.__ne__>` -- Equality tests.
* :meth:`+ <Bits.__add__>` -- Concatenate with another bitstring.
* :meth:`* <Bits.__mul__>` -- Concatenate multiple copies of the current bitstring.
* :meth:`~ <Bits.__invert__>` -- Invert every bit of the bitstring.
* :meth:`\<\< <Bits.__lshift__>` -- Shift bits to the left.
* :meth:`>> <Bits.__rshift__>` -- Shift bits to the right.
* :meth:`& <Bits.__and__>` -- Bit-wise AND between two bitstrings.
* :meth:`| <Bits.__or__>` -- Bit-wise OR between two bitstrings.
* :meth:`^ <Bits.__xor__>` -- Bit-wise XOR between two bitstrings.

Properties
^^^^^^^^^^

* :attr:`~Bits.bin` / ``b`` -- The bitstring as a binary string.
* :attr:`~Bits.bool` -- For single bit bitstrings, interpret as True or False.
* :attr:`~Bits.bytes` -- The bitstring as a bytes object.
* :attr:`~Bits.float` / ``floatbe`` / ``f`` -- Interpret as a big-endian floating point number.
* :attr:`~Bits.floatle` -- Interpret as a little-endian floating point number.
* :attr:`~Bits.floatne` -- Interpret as a native-endian floating point number.
* :attr:`~Bits.float8_143` -- Interpret as an 8 bit float with float8_143 format.
* :attr:`~Bits.float8_152` -- Interpret as an 8 bit float with float8_152 format.
* :attr:`~Bits.bfloat` / ``bfloatbe`` -- Interpret as a big-endian bfloat floating point number.
* :attr:`~Bits.bfloatle` -- Interpret as a little-endian bfloat floating point number.
* :attr:`~Bits.bfloatne` -- Interpret as a native-endian bfloat floating point number.
* :attr:`~Bits.hex` / ``h`` -- The bitstring as a hexadecimal string.
* :attr:`~Bits.int` / ``i`` -- Interpret as a two's complement signed integer.
* :attr:`~Bits.intbe` -- Interpret as a big-endian signed integer.
* :attr:`~Bits.intle` -- Interpret as a little-endian signed integer.
* :attr:`~Bits.intne` -- Interpret as a native-endian signed integer.
* :attr:`~Bits.len` -- Length of the bitstring in bits.
* :attr:`~Bits.oct` / ``o`` -- The bitstring as an octal string.
* :attr:`~Bits.se` -- Interpret as a signed exponential-Golomb code.
* :attr:`~Bits.ue` -- Interpret as an unsigned exponential-Golomb code.
* :attr:`~Bits.sie` -- Interpret as a signed interleaved exponential-Golomb code.
* :attr:`~Bits.uie` -- Interpret as an unsigned interleaved exponential-Golomb code.
* :attr:`~Bits.uint` / ``u`` -- Interpret as a two's complement unsigned integer.
* :attr:`~Bits.uintbe` -- Interpret as a big-endian unsigned integer.
* :attr:`~Bits.uintle` -- Interpret as a little-endian unsigned integer.
* :attr:`~Bits.uintne` -- Interpret as a native-endian unsigned integer.

----


BitArray
--------

``Bits`` ⟶ ``BitArray``

This class adds mutating methods to ``Bits``. The constructor is the same as for ``Bits``.

Additional methods
^^^^^^^^^^^^^^^^^^

All of the methods listed above for the ``Bits`` class are available, plus:

* :meth:`~BitArray.append` -- Append a bitstring.
* :meth:`~BitArray.byteswap` -- Change byte endianness in-place.
* :meth:`~BitArray.clear` -- Remove all bits from the bitstring.
* :meth:`~BitArray.insert` -- Insert a bitstring.
* :meth:`~BitArray.invert` -- Flip bit(s) between one and zero.
* :meth:`~BitArray.overwrite` -- Overwrite a section with a new bitstring.
* :meth:`~BitArray.prepend` -- Prepend a bitstring.
* :meth:`~BitArray.replace` -- Replace occurrences of one bitstring with another.
* :meth:`~BitArray.reverse` -- Reverse bits in-place.
* :meth:`~BitArray.rol` -- Rotate bits to the left.
* :meth:`~BitArray.ror` -- Rotate bits to the right.
* :meth:`~BitArray.set` -- Set bit(s) to 1 or 0.

Additional special methods
^^^^^^^^^^^^^^^^^^^^^^^^^^

The special methods available for the ``Bits`` class are all available, plus some which will modify the bitstring:

* :meth:`[] <BitArray.__setitem__>` -- Set an element or slice.
* :meth:`del <BitArray.__delitem__>` -- Delete an element or slice.
* :meth:`+= <BitArray.__iadd__>` -- Append bitstring to the current bitstring.
* :meth:`*= <BitArray.__imul__>` -- Concatenate multiple copies of the current bitstring.
* :meth:`\<\<= <BitArray.__ilshift__>` -- Shift bits in-place to the left.
* :meth:`>>= <BitArray.__irshift__>` -- Shift bits in-place to the right.
* :meth:`&= <BitArray.__iand__>` -- In-place bit-wise AND between two bitstrings.
* :meth:`|= <BitArray.__ior__>` -- In-place bit-wise OR between two bitstrings.
* :meth:`^= <BitArray.__ixor__>` -- In-place bit-wise XOR between two bitstrings.


Properties
^^^^^^^^^^

The same as ``Bits``, except that they are all (with the exception of ``len``) writable as well as readable.

----

ConstBitStream
--------------

``Bits`` ⟶ ``ConstBitStream``

This class adds a bit position and methods to read and navigate in an immutable bitstream.
If you wish to use streaming methods on a large file without changing it then this is often the best class to use.

All of the methods, special methods and properties listed above for the ``Bits`` class are available, plus:

Additional methods
^^^^^^^^^^^^^^^^^^

* :meth:`~ConstBitStream.bytealign` -- Align to next byte boundary.
* :meth:`~ConstBitStream.peek` -- Peek at and interpret next bits as a single item.
* :meth:`~ConstBitStream.peeklist` -- Peek at and interpret next bits as a list of items.
* :meth:`~ConstBitStream.read` -- Read and interpret next bits as a single item.
* :meth:`~ConstBitStream.readlist` -- Read and interpret next bits as a list of items.
* :meth:`~ConstBitStream.readto` -- Read up to and including next occurrence of a bitstring.

Additional properties
^^^^^^^^^^^^^^^^^^^^^

* :attr:`~ConstBitStream.bytepos` -- The current byte position in the bitstring.
* :attr:`~ConstBitStream.pos` -- The current bit position in the bitstring.

----

BitStream
---------

``Bits`` ⟶ ``BitArray / ConstBitStream`` ⟶ ``BitStream``


This class contains all of the 'stream' elements of ``ConstBitStream`` and adds all of the mutating methods of ``BitArray``.
It has all the methods, special methods and properties of the ``Bits``, ``BitArray`` and ``ConstBitArray`` classes.

It is the most general of the four classes, but it is usually best to choose the simplest class for your use case.

----

Array
-----

The bitstring ``Array`` is similar to the ``array`` type in the ``array`` module, except that it is far more flexible.
The ``fmt`` specifies a fixed-length format for each element of the ``Array``, and it behaves largely like a list.

Both the format and the underlying bit data (stored as a ``BitArray``) can be freely modified after creation, and element-wise operations can be used on the ``Array``.

Constructor
^^^^^^^^^^^

``Array(fmt: str, initializer, trailing_bits)``

The `fmt` can be a struct-like type code, or a single fixed-length token as used in the ``Bits`` class.

The `inititalizer` will typically be an iterable such as a list, but can also be many other things including an open binary file, a bytes or bytearray object, another ``bitstring.Array`` or an ``array.array``.

The `trailing_bits` typically isn't used in construction, and specifies bits left over after interpreting the stored binary data according to the format `fmt`.
Modifying the data or format after creation may cause the `trailing_bits` to not be empty.

Examples::

    Array('>H', [1, 10, 20])
    Array('float16', a_file_object)
    Array('int4', stored_bytes)


Methods
^^^^^^^

* :meth:`~Array.append` -- Append a single item to the end of the Array.
* :meth:`~Array.byteswap` -- Change byte endianness of all items.
* :meth:`~Array.count` -- Count the number of occurences of a value.
* :meth:`~Array.extend` -- Append multiple items to the end of the Array from an iterable.
* :meth:`~Array.fromfile` -- Append items read from a file object.
* :meth:`~Array.insert` -- Insert an item at a given position.
* :meth:`~Array.pop` -- Return and remove an item.
* :meth:`~Array.reverse` -- Reverse the order of all items.
* :meth:`~Array.tobytes` -- Return Array data as bytes object, padding with zero bits at end if needed.
* :meth:`~Array.tofile` -- Write Array data to a file, padding with zero bits at end if needed.
* :meth:`~Array.tolist` -- Return Array items as a list.

Special methods
^^^^^^^^^^^^^^^

These non-mutating special methods are available. Where appropriate they return a new ``Array``.

* :meth:`[] <Array.__getitem__>` -- Get an element or slice.
* :meth:`== <Array.__eq__>` / :meth:`\!= <Array.__ne__>` -- Equality tests.
* :meth:`+ <Array.__add__>` -- Concatenate Arrays, or add value to each element.
* :meth:`- <Array.__sub__>` -- Subtract value from each element.
* :meth:`* <Array.__mul__>` -- Multiply each element by a value.
* :meth:`/ <Array.__truediv__>` -- Divide each element by a value.
* :meth:`// <Array.__floordiv__>` -- Floor divide each element by a value.
* :meth:`\<\< <Array.__lshift__>` -- Shift bits of each element to the left.
* :meth:`>> <Array.__rshift__>` -- Shift bits of each element to the right.
* :meth:`& <Array.__and__>` -- Bit-wise AND of each element.
* :meth:`| <Array.__or__>` -- Bit-wise OR of each element.
* :meth:`^ <Array.__xor__>` -- Bit-wise XOR of each element.

Mutating versions of many of the methods are also available.

* :meth:`[] <Array.__setitem__>` -- Get an element or slice.
* :meth:`del <Array.__delitem__>` -- Delete an element or slice.
* :meth:`+= <Array.__iadd__>` -- Concatenate Array, or add value to each element in-place.
* :meth:`-= <Array.__isub__>` -- Subtract value from each element in-place.
* :meth:`*= <Array.__imul__>` -- Multiply each element by a value in-place.
* :meth:`/= <Array.__itruediv__>` -- Divide each element by a value in-place.
* :meth:`//= <Array.__ifloordiv__>` -- Floor divide each element by a value in-place.
* :meth:`\<\<= <Array.__ilshift__>` -- Shift bits of each element to the left in-place.
* :meth:`>>= <Array.__irshift__>` -- Shift bits of each element to the right in-place.
* :meth:`&= <Array.__iand__>` -- In-place bit-wise AND of each element.
* :meth:`|= <Array.__ior__>` -- In-place bit-wise OR of each element.
* :meth:`^= <Array.__ixor__>` -- In-place bit-wise XOR of each element.


Properties
^^^^^^^^^^

* :attr:`~Array.data` -- The complete binary data in a ``BitArray`` object. Can be freely modified.
* :attr:`~Array.fmt` -- The format string or typecode. Can be freely modified.
* :attr:`~Array.itemsize` -- The length *in bits* of a single item. Read only.
* :attr:`~Array.trailing_bits` -- If the data length is not a multiple of the fmt length, this BitArray gives the leftovers at the end of the data.

----

Module level
------------

Functions
^^^^^^^^^
* :func:`~bitstring.pack` -- Create a new ``BitStream`` according to a format string and values.

Exceptions
^^^^^^^^^^
* :class:`~bitstring.Error` -- Base class for module exceptions.
* :class:`~bitstring.ReadError` -- Reading or peeking past the end of a bitstring.
* :class:`~bitstring.InterpretError` -- Inappropriate interpretation of binary data.
* :class:`~bitstring.ByteAlignError` -- Whole-byte position or length needed.
* :class:`~bitstring.CreationError` -- Inappropriate argument during bitstring creation.

Module variables
^^^^^^^^^^^^^^^^
* :data:`~bitstring.bytealigned` -- Determines whether a number of methods default to working only on byte boundaries.
* :data:`~bitstring.lsb0` -- If True, index bits with the least significant bit (the final bit) as bit zero.

