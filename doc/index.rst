
.. currentmodule:: bitstring

.. image:: bitstring_logo.png
   :width: 400px


`bitstring <https://github.com/scott-griffiths/bitstring/>`_ is a Python package that makes the creation, manipulation and analysis of binary data as simple and natural as possible.

It has been maintained since 2006 and now has many millions of downloads per year.
You can try out an interactive walkthrough notebook on `binder <https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb>`_ (or the non-interactive version `here <https://github.com/scott-griffiths/bitstring/blob/main/doc/walkthrough.ipynb>`_).


.. image:: https://github.com/scott-griffiths/bitstring/actions/workflows/.github/workflows/ci.yml/badge.svg
 :target: https://github.com/scott-griffiths/bitstring/actions/workflows/ci.yml

.. image:: https://img.shields.io/readthedocs/bitstring

.. image:: https://img.shields.io/pypi/dm/bitstring?color=blue
 :target: https://pypistats.org/packages/bitstring

.. image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb



Overview
========

* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit level slicing, joining, searching, replacing and more.
* Read from and interpret bitstrings as streams of binary data.
* Create arrays of any fixed-length formats.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Supports Python 3.7 and later. Use bitstring version 3 for Python 2.7 and 3.x support.
* Open source software, released under the MIT licence.

It is not difficult to manipulate binary data in Python, for example using the ``struct`` and ``array`` modules, but it can be quite fiddly and time consuming even for quite small tasks, especially if you are not dealing with whole-byte data.

The bitstring module provides support many different bit formats, allowing easy and efficient storage, interpretation and construction.

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

.. warning ::
    This class was introduced in version 4.1.0 of bitstring, and is a 'beta' feature that may have some small changes in future point releases.

If you are dealing with just one type of data but perhaps it's not one of the dozen or so supported in the ``array`` module in the standard library, then we have you covered with the :class:`Array` class.

A ``bitstring.Array`` works in a similar way to a ``array.array``, except that you can efficiently pack in any fixed-length binary format.

Want an array of 5 bit unsigned integers, or of 8 or 16 bit floating point numbers? No problem.
You can also easily change the data's interpretation, convert to another format, and freely modify the underlying data which is stored as a :class:`BitArray` object.

::

    >>> a = bitstring.Array('uint16', [0, 1, 4, 6, 11, 2, 8, 7])
    >>> a.data
    BitArray('0x0000000100040006000b000200080007')
    >>> b = bitstring.Array('int5', a)
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


Documentation
^^^^^^^^^^^^^


The :ref:`manual` provides an introduction to the module and details most its capabilities.

The :ref:`reference` section has a complete list of all the classes, methods, properties and functions of the bitstring module, together with short examples for many items.

.. toctree::
   :hidden:

   self

.. toctree::
    :maxdepth: 2

    manual
    reference
    appendices


Installation and download
^^^^^^^^^^^^^^^^^^^^^^^^^


To install just ``pip install bitstring``.

To download the module, as well as for defect reports, enhancement requests and Git repository browsing go to `the project's home on GitHub. <https://github.com/scott-griffiths/bitstring/>`_


Credits
^^^^^^^


Created by Scott Griffiths in 2006 to help with ad hoc parsing and creation of compressed video files. Maintained and expanded ever since as it became unexpectedly popular. Thanks to all those who have contributed ideas and code (and bug reports) over the years.

These docs are styled using the `Piccolo theme <https://github.com/piccolo-orm/piccolo_theme>`_.


