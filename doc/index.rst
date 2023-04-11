
.. currentmodule:: bitstring

.. image:: bitstring_logo.png
   :width: 400px


`bitstring <https://github.com/scott-griffiths/bitstring/>`_ is a pure Python module that makes the creation, manipulation and analysis of binary data as simple and natural as possible.

It has been maintained since 2006 and now has about `20 million downloads per year. <https://pypistats.org/packages/bitstring>`_

You can try out an interactive walkthrough notebook on `binder <https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb>`_ (or the non-interactive version `here <https://github.com/scott-griffiths/bitstring/blob/main/doc/walkthrough.ipynb>`_).

.. image:: https://mybinder.org/badge_logo.svg
 :target: https://mybinder.org/v2/gh/scott-griffiths/bitstring/main?labpath=doc%2Fwalkthrough.ipynb



Overview
========

* Create bitstrings from hex, octal, binary, files, formatted strings, bytes, integers and floats of different endiannesses.
* Powerful binary packing and unpacking functions.
* Bit level slicing, joining, searching, replacing and more.
* Read from and interpret bitstrings as streams of binary data.
* Rich API - chances are that whatever you want to do there's a simple and elegant way of doing it.
* Supports Python 3.7 and later. Use bitstring version 3 for Python 2.7 and 3.x support.
* Open source software, released under the MIT licence.

A short example usage
---------------------

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


Installation and download
-------------------------

To install just ``pip install bitstring``.

To download the module, as well as for defect reports, enhancement requests and Git repository browsing go to `the project's home on GitHub. <https://github.com/scott-griffiths/bitstring/>`_

Documentation
-------------

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


Credits
-------

Created by Scott Griffiths in 2006 to help with ad hoc parsing and creation of compressed video files. Maintained and expanded ever since as it became unexpectedly popular. Thanks to all those who have contributed ideas and code (and bug reports) over the years.

These docs are styled using the `Piccolo theme <https://github.com/piccolo-orm/piccolo_theme>`_.


