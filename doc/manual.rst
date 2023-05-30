.. currentmodule:: bitstring

.. _manual:

###########
User Manual
###########


While it is not difficult to manipulate binary data in Python, for example using the ``struct`` and ``array`` modules, it can be quite fiddly and time consuming even for quite small tasks, especially if you are not dealing only with whole-byte data.

The bitstring module provides four classes, :class:`BitStream`, :class:`BitArray`, :class:`ConstBitStream` and :class:`Bits`, instances of which can be constructed from integers, floats, hex, octal, binary, strings or files, but they all just represent a string of binary digits. I shall use the term 'bitstring' when referring generically to any of the classes, and use the class names for parts that apply to only one or another.

:class:`BitArray` objects can be sliced, joined, reversed, inserted into, overwritten, packed, unpacked etc. with simple functions or slice notation. :class:`BitStream` objects can also be read from, searched in, and navigated in, similar to a file or stream.

Bitstrings are designed to be as lightweight as possible and can be considered to be just a list of binary digits. They are however stored efficiently - although there are a variety of ways of creating and viewing the binary data, the bitstring itself just stores the byte data, and all views are calculated as needed, and are not stored as part of the object.

The different views or interpretations on the data are accessed through properties such as :attr:`~Bits.hex`, :attr:`~Bits.bin` and :attr:`~Bits.int`, and an extensive set of functions is supplied for modifying, navigating and analysing the binary data.

A complete reference for the module is given in the :ref:`reference` section, while the rest of this manual acts more like a tutorial or guided tour.


.. toctree::
   :maxdepth: 2

   creation
   packing
   interpretation
   slicing
   reading
   misc

