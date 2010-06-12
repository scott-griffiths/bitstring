Internals
=========

I am including some information on the internals of the :class:`BitString` class here, things that the general user shouldn’t need to know. The objects and methods described here all start with an underscore, which means that they are a private part of the implementation, not a part of the public interface and that that I reserve the right to change, rename and remove them at any time!

This section isn't complete, and may not even be accurate as I am in the process of refactoring the core, so with those disclaimers in mind...

The data in a :class:`BitString` can be considered to consist of three parts.

* The byte data, either contained in memory, or as part of a file.
* A length in bits.
* An offset to the data in bits.

Storing the data in byte form is pretty essential, as anything else could be very memory inefficient. Keeping an offset to the data allows lots of optimisations to be made as it means that the byte data doesn’t need to be altered for almost all operations. An example is in order::

 a = BitString('0x01ff00')
 b = a[7:12]

This is about as simple as it gets, but let’s look at it in detail. First a is created by parsing the string as hexadecimal (as it starts with ``0x``) and converting it to three data bytes ``\x01\xff\x00``. By default the length is the bit length of the whole string, so it’s 24 in this case, and the offset is zero.

Next, ``b`` is created from a slice of ``a``. This slice doesn’t begin or end on a byte boundary, so one way of obtaining it would be to copy the data in ``a`` and start doing bit-wise shifts to get it all in the right place. This can get really very computationally expensive, so instead we utilise the ``offset`` and ``length`` parameters.

The procedure is simply to copy the byte data containing the substring and set the ``offset`` and ``length`` to get the desired result. So in this example we have::

 a : bytes = '\x01\xff\x00', offset = 0, len = 24
 b : bytes = '\x01\xff', offset = 7, len = 5

This method also means that :class:`BitString` objects initialised from a file don’t have to copy anything into memory - the data instead is obtained with a byte offset into the file. This brings us onto the different types of datastores used.

The :class:`BitString` has a ``_datastore`` member, which at present is either a ``MemArray`` class or a ``FileArray`` class. The ``MemArray`` class is really just a light wrapper around a ``bytearray`` object that contains the real byte data, so when we were talking about the data earlier I was really referring to the byte data contained in the ``bytearray``, in the ``MemArray``, in the ``_datastore``, in the :class:`BitString` (but that seemed a bit much to give you in one go).
