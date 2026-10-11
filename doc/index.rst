
.. currentmodule:: bitstring

.. image:: bitstring_logo.png
   :width: 400px


`bitstring <https://github.com/scott-griffiths/bitstring/>`_  is a Python module to help make the creation and analysis of all types of bit-level binary data as simple and efficient as possible.

It has been maintained since 2006.

Since version 5.0 its core has been `tibs <https://github.com/scott-griffiths/tibs>`_, a faster Rust-based library for binary data by the same author.
For performance-critical bit work that doesn't need bitstring's higher-level format handling, tibs can also be used directly.


.. image:: https://github.com/scott-griffiths/bitstring/actions/workflows/.github/workflows/ci.yml/badge.svg
   :target: https://github.com/scott-griffiths/bitstring/actions/workflows/ci.yml

.. image:: https://img.shields.io/readthedocs/bitstring
   :target: https://bitstring.readthedocs.io/en/stable/

.. image:: https://img.shields.io/codacy/grade/8869499b2eed44548fa1a5149dd451f4?logo=codacy
   :target: https://app.codacy.com/gh/scott-griffiths/bitstring/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade

.. image:: https://img.shields.io/pepy/dt/bitstring?logo=python&logoColor=white&labelColor=blue&color=blue
   :target: https://www.pepy.tech/projects/bitstring

.. image:: https://img.shields.io/pypi/dm/bitstring?label=%40&labelColor=blue&color=blue
   :target: https://pypistats.org/packages/bitstring


------

.. important::

   These docs describe bitstring 5, which has breaking changes from version 4.
   See :ref:`upgrading_to_version_5` for help moving existing code across, or the
   `4.4 documentation <https://bitstring.readthedocs.io/en/4.4.0/>`_ if you're staying on version 4.


Overview
========

* Efficiently store and manipulate binary data in idiomatic Python.
* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit level slicing, joining, searching, replacing and more.
* Use :class:`Reader` to read from and interpret bitstrings sequentially.
* Create efficiently stored arrays of any fixed-length format.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Open source software, released under the MIT licence.

It is not difficult to manipulate binary data in Python, for example using the ``struct`` and ``array`` modules, but it can be quite fiddly and time consuming even for quite small tasks, especially if you are not dealing with whole-byte data.

The bitstring module provides support for many different bit formats, allowing easy and efficient storage, interpretation and construction.


Examples
^^^^^^^^

A bitstring can be built from mixed formats, then sliced, searched, appended to and interpreted in different ways::

    >>> s = bitstring.BitArray('0x4f8e220')
    >>> s.unpack('u12, hex8, bin')
    [1272, 'e2', '00100000']
    >>> '0b11000' in s
    True
    >>> s += 'f32=0.001'
    >>> s.bin
    '010011111000111000100010000000111010100000110001001001101111'
    >>> s[-32:].f
    0.0010000000474974513

An :class:`Array` is like an ``array.array``, but its items can be any fixed-length format, and it can be converted to another format or operated on element-wise::

    >>> a = bitstring.Array('u16', [0, 1, 4, 6, 11, 2, 8, 7])
    >>> b = a.astype('u5')
    >>> b.data
    BitArray('0x0048658907')
    >>> a[::2] *= 5
    >>> a
    Array('u16', [0, 1, 20, 6, 55, 2, 40, 7])
    >>> a >> 2
    Array('u16', [0, 0, 5, 1, 13, 0, 10, 1])


Documentation Quick Start
^^^^^^^^^^^^^^^^^^^^^^^^^

You can take a look at the introductory walkthrough notebook `here <https://github.com/scott-griffiths/bitstring/blob/main/doc/walkthrough.ipynb>`_.

The :ref:`quick_reference` provides a summary of the classes and their methods.

The :ref:`reference` section has a complete list of all the classes, methods, properties and functions of the bitstring module, together with short examples for many items.

If you are moving code from bitstring 4.x to 5.x, see :ref:`upgrading_to_version_5`.


.. toctree::
   :hidden:

   self

.. toctree::
    :hidden:

    quick_reference
    reference
    appendices


Installation and download
^^^^^^^^^^^^^^^^^^^^^^^^^


To install the latest release from PyPI, use::

    pip install bitstring

To stay on the 4.x line, pin the version::

    pip install "bitstring<5"

To download the module, as well as for defect reports, enhancement requests and Git repository browsing go to `the project's home on GitHub. <https://github.com/scott-griffiths/bitstring/>`_

Release Notes
^^^^^^^^^^^^^

To see what's been added, improved or fixed, see the `release notes <https://github.com/scott-griffiths/bitstring/blob/main/release_notes.md>`_ on GitHub.


Credits
^^^^^^^

Created by Scott Griffiths in 2006 to help with ad hoc parsing and creation of compressed video files.
Maintained and expanded ever since as it became unexpectedly popular.
Thanks to all those who have contributed ideas, code and bug reports over the years.
