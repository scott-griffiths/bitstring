
.. currentmodule:: bitstring

.. image:: bitstring_logo.png
   :width: 400px


`bitstring <https://github.com/scott-griffiths/bitstring/>`_  is a Python module to help make the creation and analysis of all types of bit-level binary data as simple and efficient as possible.

It has been maintained since 2006.


.. image:: https://github.com/scott-griffiths/bitstring/actions/workflows/.github/workflows/ci.yml/badge.svg
   :target: https://github.com/scott-griffiths/bitstring/actions/workflows/ci.yml

.. image:: https://img.shields.io/readthedocs/bitstring
   :target: https://bitstring.readthedocs.io/en/latest/

.. image:: https://img.shields.io/codacy/grade/8869499b2eed44548fa1a5149dd451f4?logo=codacy
   :target: https://app.codacy.com/gh/scott-griffiths/bitstring/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade

.. image:: https://img.shields.io/pepy/dt/bitstring?logo=python&logoColor=white&labelColor=blue&color=blue
   :target: https://www.pepy.tech/projects/bitstring

.. image:: https://img.shields.io/pypi/dm/bitstring?label=%40&labelColor=blue&color=blue)
   :target: https://pypistats.org/packages/bitstring


------

Overview
========

* Efficiently store and manipulate binary data in idiomatic Python.
* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit level slicing, joining, searching, replacing and more.
* Read from and interpret bitstrings as streams of binary data.
* Create efficiently stored arrays of any fixed-length format.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Open source software, released under the MIT licence.

It is not difficult to manipulate binary data in Python, for example using the ``struct`` and ``array`` modules, but it can be quite fiddly and time consuming even for quite small tasks, especially if you are not dealing with whole-byte data.

The bitstring module provides support many different bit formats, allowing easy and efficient storage, interpretation and construction.


Documentation Quick Start
^^^^^^^^^^^^^^^^^^^^^^^^^

You can take a look at the introductory walkthrough notebook `here <https://github.com/scott-griffiths/bitstring/blob/main/doc/walkthrough.ipynb>`_.

The :ref:`quick_reference` provides a summary of the classes and their methods.

The :ref:`reference` section has a complete list of all the classes, methods, properties and functions of the bitstring module, together with short examples for many items.

    * :class:`Bits` - an immutable container of bits.
    * :class:`BitArray` - adds mutating methods to ``Bits``.
    * :class:`BitStream` - adds a bit position and read methods.
    * :class:`Array` - an array of bitstrings of the same type.


.. toctree::
   :hidden:

   self

.. toctree::
    :hidden:

    quick_reference
    reference
    appendices


Mixed format bitstrings
^^^^^^^^^^^^^^^^^^^^^^^

If you have binary data (or want to construct it) from multiple types then you could use the :class:`BitArray` class.
The example below constructs a 28 bit bitstring from a hexadecimal string, then unpacks it into multiple bit interpretations.
It also demonstrates how it can be flexibly modified and sliced using standard notation, and how properties such as ``bin`` and ``float`` can be used to interpret the data.

::

    >>> s = bitstring.BitArray('0x4f8e220')
    >>> s.unpack('uint12, hex8, bin')
    [1272, 'e2', '00100000']
    >>> '0b11000' in s
    True
    >>> s += 'f32=0.001'
    >>> s.bin
    '010011111000111000100010000000111010100000110001001001101111'
    >>> s[-32:].float
    0.0010000000474974513


The module also supplies the :class:`BitStream` class, which adds a bit position so that objects can also be read from, searched in, and navigated in, similar to a file or stream.

Bitstrings are designed to be as lightweight as possible and can be considered to be just a list of binary digits. They are however stored efficiently - although there are a variety of ways of creating and viewing the binary data, the bitstring itself just stores the byte data, and all views are calculated as needed, and are not stored as part of the object.

The different views or interpretations on the data are accessed through properties such as :attr:`~Bits.hex`, :attr:`~Bits.bin` and :attr:`~Bits.int`, and an extensive set of functions is supplied for modifying, navigating and analysing the binary data.

There are also a companion classes called :class:`Bits` and :class:`ConstBitStream` which are immutable versions of :class:`BitArray` and :class:`BitStream` respectively.
See the reference documentation for full details.

Arrays of bitstrings
^^^^^^^^^^^^^^^^^^^^

If you are dealing with just one type of data but perhaps it's not one of the dozen or so supported in the ``array`` module in the standard library, then we have you covered with the :class:`Array` class.

A ``bitstring.Array`` works in a similar way to a ``array.array``, except that you can efficiently pack in any fixed-length binary format.

Want an array of 5 bit unsigned integers, or of 8 or 16 bit floating point numbers? No problem.
You can also easily change the data's interpretation, convert to another format, and freely modify the underlying data which is stored as a :class:`BitArray` object.

::

    >>> a = bitstring.Array('uint16', [0, 1, 4, 6, 11, 2, 8, 7])
    >>> a.data
    BitArray('0x0000000100040006000b000200080007')
    >>> b = a.astype('uint5')
    >>> b.data
    BitArray('0x0048658907')
    >>> a.tolist() == b.tolist()
    True

You can also take and set slices as you'd expect, and apply operations to each element in the ``Array``. ::

    >>> a[::2] *= 5
    >>> a
    Array('uint16', [0, 1, 20, 6, 55, 2, 40, 7])
    >>> a >> 2
    Array('uint16', [0, 0, 5, 1, 13, 0, 10, 1])


Installation and download
^^^^^^^^^^^^^^^^^^^^^^^^^


To install just ``pip install bitstring``.

To download the module, as well as for defect reports, enhancement requests and Git repository browsing go to `the project's home on GitHub. <https://github.com/scott-griffiths/bitstring/>`_

Release Notes
^^^^^^^^^^^^^

To see what been added, improved or fixed, and possibly also to see what's coming in the next version, see the `release notes <https://github.com/scott-griffiths/bitstring/blob/main/release_notes.md>`_ on GitHub.


Credits
^^^^^^^

Created by Scott Griffiths in 2006 to help with ad hoc parsing and creation of compressed video files. Maintained and expanded ever since as it became unexpectedly popular. Thanks to all those who have contributed ideas, code and bug reports over the years.

These docs are styled using the `Piccolo theme <https://github.com/piccolo-orm/piccolo_theme>`_.


